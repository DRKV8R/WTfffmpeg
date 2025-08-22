from flask import Flask, request, render_template, redirect, url_for
from google.cloud import storage
from werkzeug.utils import secure_filename
import subprocess
import os
import uuid

# --- Configuration ---
# The bucket name is passed in as an environment variable
CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET')
# --- End Configuration ---

app = Flask(__name__)
# A secret key is needed for features like flash messages, though we aren't using them in this version.
app.secret_key = 'a_strong_secret_key'

@app.route('/', methods=['GET', 'POST'])
def video_creator_page():
    if request.method == 'POST':
        image_file = request.files.get('image')
        audio_file = request.files.get('audio')
        resolution = request.form.get('resolution')

        if not all([image_file, audio_file, resolution]):
            return "Missing file(s) or resolution.", 400

        # Create a unique temporary directory in the writable /tmp/ folder
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
            # --- FFmpeg Command ---
            vf_options = 'scale=1280:720'
            if resolution == '1080p':
                vf_options = 'scale=1920:1080'
            
            filter_complex = f'{vf_options}:force_original_aspect_ratio=decrease,pad={vf_options}:(ow-iw)/2:(oh-ih)/2,format=yuv420p'

            ffmpeg_command = [
                'ffmpeg', '-loop', '1', '-i', local_image_path, '-i', local_audio_path,
                '-c:v', 'libx264', '-tune', 'stillimage', '-c:a', 'aac', '-b:a', '192k',
                '-vf', filter_complex, '-shortest', local_output_path
            ]
            subprocess.run(ffmpeg_command, check=True)

            # --- Upload to Google Cloud Storage ---
            storage_client = storage.Client()
            bucket = storage_client.bucket(CLOUD_STORAGE_BUCKET)
            blob = bucket.blob(f'{job_id}/{output_filename}')
            blob.upload_from_filename(local_output_path)
            
            # --- Generate a Download Link ---
            download_url = blob.generate_signed_url(version='v4', expiration=900) # 15 minutes
            return redirect(download_url)

        except Exception as e:
            # This will print the error to the Cloud Run logs for debugging
            print(f"An error occurred: {e}")
            return "An error occurred during video creation. Check the logs for details.", 500

    # This is what users see when they first visit the page
    return render_template('index.html')

if __name__ == "__main__":
    # This block is used for local testing, not by Gunicorn in production
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
