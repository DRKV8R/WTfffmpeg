from flask import Flask, request, render_template, redirect, url_for
from google.cloud import storage
from werkzeug.utils import secure_filename
import subprocess
import os
import uuid
import logging
import sys

# --- Configuration ---
CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET')
SECRET_KEY = os.environ.get('SECRET_KEY', 'a_very_strong_secret_key')

# Enhanced configuration validation and logging
def validate_configuration():
    """Validate and log configuration status."""
    config_issues = []
    
    # Log startup configuration check
    logging.info("Starting WTfffmpeg configuration validation...")
    
    if not CLOUD_STORAGE_BUCKET:
        issue = 'CLOUD_STORAGE_BUCKET environment variable not set - video creation will fail'
        config_issues.append(issue)
        logging.warning(f"❌ {issue}")
        logging.info("💡 To fix: Set CLOUD_STORAGE_BUCKET environment variable in deployment")
    else:
        logging.info(f'✅ CLOUD_STORAGE_BUCKET configured: {CLOUD_STORAGE_BUCKET}')
        # Validate bucket name format
        import re
        if re.match(r'^[a-z0-9][a-z0-9._-]*[a-z0-9]$', CLOUD_STORAGE_BUCKET) and len(CLOUD_STORAGE_BUCKET) <= 63:
            logging.info(f'✅ Bucket name format is valid')
        else:
            logging.warning(f'⚠️  Bucket name format may be invalid: {CLOUD_STORAGE_BUCKET}')
    
    if SECRET_KEY == 'a_very_strong_secret_key':
        issue = 'Using default SECRET_KEY - consider setting custom SECRET_KEY for production'
        config_issues.append(issue)
        logging.warning(f"⚠️  {issue}")
        logging.info("💡 To fix: Set SECRET_KEY environment variable to a secure random string")
    else:
        logging.info('✅ Custom SECRET_KEY configured')
        if len(SECRET_KEY) >= 32:
            logging.info(f'✅ SECRET_KEY length is adequate ({len(SECRET_KEY)} characters)')
        else:
            logging.warning(f'⚠️  SECRET_KEY is short ({len(SECRET_KEY)} characters, recommend 32+)')
    
    # Log final configuration status
    if config_issues:
        logging.warning(f"Configuration validation completed with {len(config_issues)} issue(s)")
        for i, issue in enumerate(config_issues, 1):
            logging.warning(f"  {i}. {issue}")
    else:
        logging.info("✅ Configuration validation completed successfully - service ready")
    
    # Log service readiness status
    is_ready = bool(CLOUD_STORAGE_BUCKET)
    logging.info(f"🚀 Service ready for video creation: {is_ready}")
    
    return config_issues

# Validate configuration at startup
startup_issues = validate_configuration()
# --- End Configuration ---

# Configure logging for Cloud Run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

app = Flask(__name__)
app.secret_key = SECRET_KEY

@app.route('/_health')
def health_check():
    """Health check endpoint for Cloud Run readiness and liveness probes."""
    return {'status': 'healthy', 'service': 'wtfffmpeg'}, 200

@app.route('/_config')
def config_check():
    """Configuration check endpoint for troubleshooting deployment issues."""
    config_status = {
        'service': 'wtfffmpeg',
        'configuration': {
            'cloud_storage_bucket_configured': bool(CLOUD_STORAGE_BUCKET),
            'cloud_storage_bucket_value': CLOUD_STORAGE_BUCKET if CLOUD_STORAGE_BUCKET else 'NOT_SET',
            'secret_key_configured': bool(SECRET_KEY and SECRET_KEY != 'a_very_strong_secret_key'),
            'secret_key_source': 'environment' if SECRET_KEY != 'a_very_strong_secret_key' else 'default',
            'port': os.environ.get('PORT', '8080')
        },
        'issues': startup_issues,
        'ready_for_video_creation': bool(CLOUD_STORAGE_BUCKET)
    }
    
    status_code = 200 if config_status['ready_for_video_creation'] else 503
    return config_status, status_code

@app.route('/', methods=['GET', 'POST'])
def video_creator_page():
    if request.method == 'POST':
        # Log request details
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        logging.info(f'📹 Video creation request received from {client_ip}')
        
        image_file = request.files.get('image')
        audio_file = request.files.get('audio')
        resolution = request.form.get('resolution')

        # Enhanced validation logging
        if not all([image_file, audio_file, resolution]):
            missing = []
            if not image_file: missing.append('image')
            if not audio_file: missing.append('audio')  
            if not resolution: missing.append('resolution')
            
            logging.warning(f'❌ Video creation rejected - missing: {", ".join(missing)} (client: {client_ip})')
            return "Missing file(s) or resolution. Please go back and try again.", 400

        # Configuration check with detailed logging
        if not CLOUD_STORAGE_BUCKET:
            error_msg = 'Service configuration error: CLOUD_STORAGE_BUCKET environment variable not configured. Please contact administrator.'
            logging.error(f'❌ Cloud Storage bucket not configured - video creation request rejected (client: {client_ip})')
            logging.error('💡 Administrator action required: Set CLOUD_STORAGE_BUCKET environment variable')
            logging.info(f'🔧 Diagnostic endpoints: /_health (service status), /_config (configuration details)')
            return render_template('config_error.html', error_message=error_msg), 500

        job_id = str(uuid.uuid4())
        logging.info(f'🎬 Starting video creation job {job_id} (client: {client_ip})')
        logging.info(f'📄 Job details: image={image_file.filename}, audio={audio_file.filename}, resolution={resolution}')
        
        local_temp_dir = f'/tmp/{job_id}'
        os.makedirs(local_temp_dir, exist_ok=True)

        image_filename = secure_filename(image_file.filename)
        audio_filename = secure_filename(audio_file.filename)
        output_filename = f'video_output_{os.path.splitext(image_filename)[0]}.mp4'

        local_image_path = os.path.join(local_temp_dir, image_filename)
        local_audio_path = os.path.join(local_temp_dir, audio_filename)
        local_output_path = os.path.join(local_temp_dir, output_filename)

        # Log file processing
        logging.info(f'💾 Saving uploaded files for job {job_id}')
        image_file.save(local_image_path)
        audio_file.save(local_audio_path)
        
        # Log file sizes for troubleshooting
        image_size = os.path.getsize(local_image_path)
        audio_size = os.path.getsize(local_audio_path)
        logging.info(f'📊 File sizes - image: {image_size} bytes, audio: {audio_size} bytes')

        try:
            if resolution == '1080p':
                scale_filter = 'scale=1920:1080'
                pad_size = '1920:1080'
            else:  # Default to 720p
                scale_filter = 'scale=1280:720'
                pad_size = '1280:720'
            
            filter_complex = f'{scale_filter}:force_original_aspect_ratio=decrease,pad={pad_size}:(ow-iw)/2:(oh-ih)/2,format=yuv420p'

            ffmpeg_command = [
                'ffmpeg', '-loop', '1', '-i', local_image_path, '-i', local_audio_path,
                '-c:v', 'libx264', '-tune', 'stillimage', '-c:a', 'aac', '-b:a', '192k',
                '-vf', filter_complex, '-shortest', local_output_path
            ]
            
            logging.info(f'🎥 Starting FFmpeg processing for job {job_id} (resolution: {resolution})')
            import time
            start_time = time.time()
            
            subprocess.run(ffmpeg_command, check=True)
            
            processing_time = time.time() - start_time
            output_size = os.path.getsize(local_output_path)
            logging.info(f'✅ FFmpeg processing completed for job {job_id} - {processing_time:.2f}s, output: {output_size} bytes')

            logging.info(f'☁️  Uploading video to Cloud Storage for job {job_id}')
            storage_client = storage.Client()
            bucket = storage_client.bucket(CLOUD_STORAGE_BUCKET)
            blob = bucket.blob(f'{job_id}/{output_filename}')
            
            upload_start = time.time()
            blob.upload_from_filename(local_output_path)
            upload_time = time.time() - upload_start
            
            download_url = blob.generate_signed_url(version='v4', expiration=900)
            
            logging.info(f'🎉 Video creation completed for job {job_id} - upload: {upload_time:.2f}s, total: {time.time() - start_time:.2f}s')
            logging.info(f'📥 Download URL generated (expires in 15 minutes)')
            
            return redirect(download_url)

        except subprocess.CalledProcessError as e:
            logging.error(f"❌ FFmpeg processing failed for job {job_id}: {e}")
            logging.error(f"🔧 Check input files are valid - image: {image_filename}, audio: {audio_filename}")
            return "An error occurred during video processing. Please check your input files and try again.", 500
        except Exception as e:
            logging.error(f"❌ Unexpected error in video creation for job {job_id}: {e}")
            logging.error(f"🔧 Check Cloud Storage bucket access and permissions")
            return "An error occurred during video creation. Check the logs for details.", 500
        finally:
            # Clean up temporary files
            try:
                import shutil
                if os.path.exists(local_temp_dir):
                    shutil.rmtree(local_temp_dir)
                    logging.info(f'🧹 Cleaned up temporary files for job {job_id}')
            except Exception as cleanup_error:
                logging.warning(f'⚠️  Failed to clean up temporary files for job {job_id}: {cleanup_error}')

    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
