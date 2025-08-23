from flask import Flask, request, render_template, redirect, url_for, jsonify
from google.cloud import storage
from werkzeug.utils import secure_filename
import subprocess
import os
import uuid
import logging
import shutil

# --- Configuration ---
CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET')
SECRET_KEY = os.environ.get('SECRET_KEY', 'a_very_strong_secret_key')
# --- End Configuration ---

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Validate required environment variables
if not CLOUD_STORAGE_BUCKET:
    logger.error("CLOUD_STORAGE_BUCKET environment variable is required")
    raise EnvironmentError("CLOUD_STORAGE_BUCKET environment variable must be set")

@app.route('/health')
def health_check():
    """Health check endpoint for load balancer and monitoring"""
    try:
        # Basic health check - verify app is running and storage is accessible
        storage_client = storage.Client()
        bucket = storage_client.bucket(CLOUD_STORAGE_BUCKET)
        # Just check if bucket exists (doesn't need to list contents)
        bucket.reload()
        return jsonify({
            'status': 'healthy',
            'service': 'wtfffmpeg',
            'bucket': CLOUD_STORAGE_BUCKET
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@app.route('/', methods=['GET', 'POST'])
def video_creator_page():
    if request.method == 'POST':
        image_file = request.files.get('image')
        audio_file = request.files.get('audio')
        resolution = request.form.get('resolution')

        if not all([image_file, audio_file, resolution]):
            return "Missing file(s) or resolution. Please go back and try again.", 400

        job_id = str(uuid.uuid4())
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
            vf_options = 'scale=1280:720'
            if resolution == '1080p':
                vf_options = 'scale=1920:1080'
            
            filter_complex = f'{vf_options}:force_original_aspect_ratio=decrease,pad={vf_options}:(ow-iw)/2:(oh-ih)/2,format=yuv420p'

            ffmpeg_command = [
                'ffmpeg', '-loop', '1', '-i', local_image_path, '-i', local_audio_path,
                '-c:v', 'libx264', '-tune', 'stillimage', '-c:a', 'aac', '-b:a', '192k',
                '-vf', filter_complex, '-shortest', local_output_path
            ]
            
            logger.info(f"Starting video processing for job {job_id}")
            subprocess.run(ffmpeg_command, check=True)

            storage_client = storage.Client()
            bucket = storage_client.bucket(CLOUD_STORAGE_BUCKET)
            blob = bucket.blob(f'{job_id}/{output_filename}')
            blob.upload_from_filename(local_output_path)
            
            logger.info(f"Video uploaded successfully for job {job_id}")
            download_url = blob.generate_signed_url(version='v4', expiration=900)
            
            return redirect(download_url)

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg processing failed for job {job_id}: {e}")
            return "Video processing failed. Please check your input files and try again.", 500
        except Exception as e:
            logger.error(f"An error occurred for job {job_id}: {e}")
            return "An error occurred during video creation. Check the logs for details.", 500
        finally:
            # Clean up temporary files
            try:
                if os.path.exists(local_temp_dir):
                    shutil.rmtree(local_temp_dir)
                    logger.info(f"Cleaned up temporary directory for job {job_id}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory for job {job_id}: {e}")

    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
