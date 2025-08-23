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
if not CLOUD_STORAGE_BUCKET:
    logging.warning('CLOUD_STORAGE_BUCKET environment variable not set')
# --- End Configuration ---

# Configure logging for Cloud Run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'a_very_strong_secret_key')

@app.route('/_health')
def health_check():
    """Health check endpoint for Cloud Run readiness and liveness probes."""
    return {'status': 'healthy', 'service': 'wtfffmpeg'}, 200

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

        if not CLOUD_STORAGE_BUCKET:
            logging.error('Cloud Storage bucket not configured')
            return "Service configuration error. Please contact administrator.", 500

        job_id = str(uuid.uuid4())
        logging.info(f'Starting video creation job: {job_id}')
        
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
            logging.info(f'Running FFmpeg for job {job_id}')
            subprocess.run(ffmpeg_command, check=True)

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
            # Clean up temporary files
            try:
                import shutil
                if os.path.exists(local_temp_dir):
                    shutil.rmtree(local_temp_dir)
                    logging.info(f'Cleaned up temporary files for job {job_id}')
            except Exception as cleanup_error:
                logging.warning(f'Failed to clean up temporary files for job {job_id}: {cleanup_error}')

    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
