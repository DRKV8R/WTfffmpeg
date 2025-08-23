# WTfffmpeg - GCP Deployment Guide

A Flask web application that creates videos from images and audio files using FFmpeg, deployed on Google Cloud Platform.

## Prerequisites

- Google Cloud Platform account with billing enabled
- Google Cloud SDK (gcloud) installed and configured
- A Google Cloud Storage bucket for storing output videos
- Docker (optional, for local testing)

## Environment Variables

Set the following environment variables:

- `CLOUD_STORAGE_BUCKET`: Your Google Cloud Storage bucket name
- `SECRET_KEY`: Flask secret key (optional, defaults to a standard key)
- `PORT`: Application port (automatically set by GCP, defaults to 8080 locally)

## Deployment Options

### Option 1: App Engine Deployment

1. **Setup your environment:**
   ```bash
   # Set your project ID
   export PROJECT_ID=your-project-id
   gcloud config set project $PROJECT_ID
   
   # Create a storage bucket
   gsutil mb gs://your-bucket-name
   ```

2. **Update configuration:**
   Edit `app.yaml` and set your bucket name:
   ```yaml
   env_variables:
     CLOUD_STORAGE_BUCKET: "your-bucket-name"
   ```

3. **Deploy to App Engine:**
   ```bash
   gcloud app deploy
   ```

### Option 2: Cloud Run Deployment (Recommended)

1. **Build and deploy using Cloud Build:**
   ```bash
   # Update cloudbuild.yaml substitutions
   gcloud builds submit --config cloudbuild.yaml \
     --substitutions=_BUCKET_NAME=your-bucket-name
   ```

2. **Or deploy manually:**
   ```bash
   # Build the container
   docker build -t gcr.io/$PROJECT_ID/wtfffmpeg .
   docker push gcr.io/$PROJECT_ID/wtfffmpeg
   
   # Deploy to Cloud Run
   gcloud run deploy wtfffmpeg \
     --image gcr.io/$PROJECT_ID/wtfffmpeg \
     --region us-central1 \
     --platform managed \
     --allow-unauthenticated \
     --set-env-vars CLOUD_STORAGE_BUCKET=your-bucket-name \
     --memory 2Gi \
     --cpu 1 \
     --timeout 600 \
     --max-instances 10
   ```

## Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export CLOUD_STORAGE_BUCKET=your-bucket-name
   export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
   ```

3. **Run locally:**
   ```bash
   python app.py
   ```

## Features

- **Health Check**: `/health` endpoint for monitoring
- **Auto-scaling**: Configured for GCP auto-scaling
- **Logging**: Structured logging for better debugging
- **Cleanup**: Automatic cleanup of temporary files
- **Error Handling**: Proper error handling and user feedback

## Architecture

- **Frontend**: Simple HTML form for file uploads
- **Backend**: Flask application with FFmpeg processing
- **Storage**: Google Cloud Storage for output videos
- **Compute**: App Engine or Cloud Run for scalable deployment
- **Monitoring**: Health check endpoint and structured logging

## Security Notes

- Set a strong `SECRET_KEY` environment variable in production
- Use IAM to secure your Google Cloud Storage bucket
- Consider implementing authentication for production use
- The health check endpoint is public but doesn't expose sensitive data

## Troubleshooting

- Check application logs: `gcloud logs tail -s wtfffmpeg`
- Verify storage bucket permissions
- Ensure FFmpeg is available in the container (included in Dockerfile)
- Check the health endpoint: `curl https://your-app-url/health`