from flask import Flask, request, render_template, redirect, url_for, send_file, jsonify
from werkzeug.utils import secure_filename
import subprocess
import os
import uuid
import logging
import sys
import time

# Conditional import for Google Cloud Storage
try:
    from google.cloud import storage
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    logging.warning("Google Cloud Storage not available - running in local mode")

# --- Configuration ---
CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET')
SECRET_KEY = os.environ.get('SECRET_KEY', 'a_very_strong_secret_key')

# Local storage configuration for when Google Cloud is not available
LOCAL_STORAGE_DIR = os.environ.get('LOCAL_STORAGE_DIR', '/tmp/wtfffmpeg_videos')
LOCAL_MODE = not CLOUD_STORAGE_BUCKET or not GOOGLE_CLOUD_AVAILABLE

# Ensure local storage directory exists in local mode
if LOCAL_MODE:
    os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
    logging.info(f'Running in LOCAL MODE - videos will be stored in: {LOCAL_STORAGE_DIR}')
else:
    logging.info(f'Running in CLOUD MODE - videos will be stored in: {CLOUD_STORAGE_BUCKET}')

# Enhanced configuration validation and logging
def validate_configuration():
    """Validate and log configuration status."""
    config_issues = []
    
    if LOCAL_MODE:
        if not GOOGLE_CLOUD_AVAILABLE:
            issue = 'Google Cloud Storage library not available - running in local mode'
            config_issues.append(issue)
            logging.info(issue)
        elif not CLOUD_STORAGE_BUCKET:
            issue = 'CLOUD_STORAGE_BUCKET environment variable not set - running in local mode'
            config_issues.append(issue)
            logging.info(issue)
        
        logging.info(f'Local storage directory: {LOCAL_STORAGE_DIR}')
    else:
        logging.info(f'CLOUD_STORAGE_BUCKET configured: {CLOUD_STORAGE_BUCKET}')
    
    if SECRET_KEY == 'a_very_strong_secret_key':
        issue = 'Using default SECRET_KEY - consider setting custom SECRET_KEY for production'
        config_issues.append(issue)
        logging.warning(issue)
    else:
        logging.info('Custom SECRET_KEY configured')
    
    return config_issues

def cleanup_old_videos():
    """Clean up videos older than 24 hours in local mode."""
    if not LOCAL_MODE:
        return
    
    try:
        current_time = time.time()
        for job_dir in os.listdir(LOCAL_STORAGE_DIR):
            job_path = os.path.join(LOCAL_STORAGE_DIR, job_dir)
            if os.path.isdir(job_path):
                # Check if directory is older than 24 hours
                dir_age = current_time - os.path.getmtime(job_path)
                if dir_age > 24 * 3600:  # 24 hours in seconds
                    import shutil
                    shutil.rmtree(job_path)
                    logging.info(f'Cleaned up old video directory: {job_dir}')
    except Exception as e:
        logging.warning(f'Error during video cleanup: {e}')

# Validate configuration at startup
startup_issues = validate_configuration()

# Clean up old videos in local mode
if LOCAL_MODE:
    cleanup_old_videos()
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

@app.route('/download/<job_id>/<filename>')
def download_video(job_id, filename):
    """Download endpoint for locally stored videos."""
    if not LOCAL_MODE:
        return "Download endpoint only available in local mode", 404
    
    # Validate job_id format (should be a UUID)
    try:
        uuid.UUID(job_id)
    except ValueError:
        return "Invalid job ID", 400
    
    # Secure the filename
    filename = secure_filename(filename)
    if not filename.endswith('.mp4'):
        return "Invalid file type", 400
    
    video_path = os.path.join(LOCAL_STORAGE_DIR, job_id, filename)
    
    if not os.path.exists(video_path):
        return "Video not found", 404
    
    try:
        return send_file(video_path, as_attachment=True, download_name=filename, mimetype='video/mp4')
    except Exception as e:
        logging.error(f"Error serving video {video_path}: {e}")
        return "Error serving video", 500

@app.route('/_config')
def config_check():
    """Configuration check endpoint for troubleshooting deployment issues."""
    config_status = {
        'service': 'wtfffmpeg',
        'mode': 'local' if LOCAL_MODE else 'cloud',
        'configuration': {
            'cloud_storage_bucket_configured': bool(CLOUD_STORAGE_BUCKET),
            'cloud_storage_bucket_value': CLOUD_STORAGE_BUCKET if CLOUD_STORAGE_BUCKET else 'NOT_SET',
            'google_cloud_available': GOOGLE_CLOUD_AVAILABLE,
            'local_storage_dir': LOCAL_STORAGE_DIR if LOCAL_MODE else 'NOT_USED',
            'secret_key_configured': bool(SECRET_KEY and SECRET_KEY != 'a_very_strong_secret_key'),
            'secret_key_source': 'environment' if SECRET_KEY != 'a_very_strong_secret_key' else 'default',
            'port': os.environ.get('PORT', '8080')
        },
        'issues': startup_issues,
        'ready_for_video_creation': True  # Always ready in local mode or when cloud is configured
    }
    
    return config_status, 200

@app.route('/', methods=['GET', 'POST'])
def video_creator_page():
    if request.method == 'POST':
        logging.info('Video creation request received')
        
        image_file = request.files.get('image')
        audio_file = request.files.get('audio')
        resolution = request.form.get('resolution')

        if not all([image_file, audio_file, resolution]):
            logging.warning('Missing required files or resolution')
            return "Missing file(s) or resolution. Please go back and try again.", 400

        # In local mode, we don't need cloud storage
        if not LOCAL_MODE and not CLOUD_STORAGE_BUCKET:
            error_msg = 'Service configuration error: CLOUD_STORAGE_BUCKET environment variable not configured. Please contact administrator.'
            logging.error('Cloud Storage bucket not configured - video creation request rejected')
            return error_msg, 500

        job_id = str(uuid.uuid4())
        logging.info(f'Starting video creation job: {job_id} (mode: {"local" if LOCAL_MODE else "cloud"})')
        
        # Use local storage dir for local mode, temp dir for cloud mode
        if LOCAL_MODE:
            local_temp_dir = os.path.join(LOCAL_STORAGE_DIR, job_id)
        else:
            local_temp_dir = f'/tmp/{job_id}'
        
        os.makedirs(local_temp_dir, exist_ok=True)

        image_filename = secure_filename(image_file.filename)
        audio_filename = secure_filename(audio_file.filename)
        output_filename = f'video_output_{os.path.splitext(image_filename)[0]}.mp4'

        local_image_path = os.path.join(local_temp_dir, image_filename)
        local_audio_path = os.path.join(local_temp_dir, audio_filename)
        local_output_path = os.path.join(local_temp_dir, output_filename)

        image_file.save(local_image_path)
        audio_file.save(local_audio_path)

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
            logging.info(f'Running FFmpeg for job {job_id}')
            subprocess.run(ffmpeg_command, check=True)

            if LOCAL_MODE:
                # In local mode, return download URL
                download_url = url_for('download_video', job_id=job_id, filename=output_filename, _external=True)
                logging.info(f'Video creation completed for job {job_id} - local download URL: {download_url}')
                
                # For Chrome extension, return JSON with download URL
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({'downloadUrl': url_for('download_video', job_id=job_id, filename=output_filename)})
                else:
                    # For web interface, redirect to download
                    return redirect(download_url)
            else:
                # Cloud mode - upload to Google Cloud Storage
                logging.info(f'Uploading video to Cloud Storage for job {job_id}')
                storage_client = storage.Client()
                bucket = storage_client.bucket(CLOUD_STORAGE_BUCKET)
                blob = bucket.blob(f'{job_id}/{output_filename}')
                blob.upload_from_filename(local_output_path)
                
                download_url = blob.generate_signed_url(version='v4', expiration=900)
                logging.info(f'Video creation completed for job {job_id}')
                return redirect(download_url)

        except Exception as e:
            logging.error(f"Error in video creation for job {job_id}: {e}")
            return "An error occurred during video creation. Check the logs for details.", 500
        finally:
            # Clean up temporary files (only in cloud mode, keep them in local mode for download)
            if not LOCAL_MODE:
                try:
                    import shutil
                    if os.path.exists(local_temp_dir):
                        shutil.rmtree(local_temp_dir)
                        logging.info(f'Cleaned up temporary files for job {job_id}')
                except Exception as cleanup_error:
                    logging.warning(f'Failed to clean up temporary files for job {job_id}: {cleanup_error}')

    return render_template('index.html', local_mode=LOCAL_MODE)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
