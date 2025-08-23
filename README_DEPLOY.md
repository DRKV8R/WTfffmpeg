# WTfffmpeg - Cloud Run Deployment Guide

This guide provides step-by-step instructions for deploying WTfffmpeg to Google Cloud Run, a serverless platform that scales to zero for optimal cost efficiency.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Build and Deploy](#build-and-deploy)
4. [Configuration](#configuration)
5. [Cost Optimization](#cost-optimization)
6. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
7. [Best Practices](#best-practices)

## Prerequisites

### Required Tools
- [Google Cloud CLI (gcloud)](https://cloud.google.com/sdk/docs/install)
- [Docker](https://docs.docker.com/get-docker/) (for local testing)
- Git
- A Google Cloud Project with billing enabled

### Required APIs
Enable the following APIs in your Google Cloud Project:
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

## Environment Setup

### 1. Set Project Variables
```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"  # Choose your preferred region
export SERVICE_NAME="wtfffmpeg"
export BUCKET_NAME="${PROJECT_ID}-wtfffmpeg-videos"
```

### 2. Authenticate with Google Cloud
```bash
gcloud auth login
gcloud config set project $PROJECT_ID
```

### 3. Create Cloud Storage Bucket
```bash
# Create bucket for video storage
gsutil mb gs://$BUCKET_NAME

# Set lifecycle policy to delete files after 1 day (cost optimization)
echo '{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 1}
      }
    ]
  }
}' > lifecycle.json

gsutil lifecycle set lifecycle.json gs://$BUCKET_NAME
rm lifecycle.json
```

### 4. Setup Artifact Registry (Recommended)
```bash
# Create repository for container images
gcloud artifacts repositories create wtfffmpeg-repo \
    --repository-format=docker \
    --location=$REGION \
    --description="WTfffmpeg container images"

# Configure Docker to use Artifact Registry
gcloud auth configure-docker $REGION-docker.pkg.dev
```

## Build and Deploy

### Method 1: Using Cloud Build (Recommended)

#### Quick Deploy
```bash
# Clone the repository
git clone https://github.com/DRKV8R/WTfffmpeg.git
cd WTfffmpeg

# Deploy using Cloud Build
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="CLOUD_STORAGE_BUCKET=$BUCKET_NAME" \
    --memory=4Gi \
    --cpu=2 \
    --timeout=3600 \
    --max-instances=10 \
    --min-instances=0 \
    --concurrency=1
```

#### Custom Build with Artifact Registry
```bash
# Build and push to Artifact Registry
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/wtfffmpeg-repo/wtfffmpeg

# Deploy from Artifact Registry
gcloud run deploy $SERVICE_NAME \
    --image=$REGION-docker.pkg.dev/$PROJECT_ID/wtfffmpeg-repo/wtfffmpeg \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="CLOUD_STORAGE_BUCKET=$BUCKET_NAME" \
    --memory=4Gi \
    --cpu=2 \
    --timeout=3600 \
    --max-instances=10 \
    --min-instances=0 \
    --concurrency=1
```

### Method 2: Using service.yaml Configuration

```bash
# Update service.yaml with your project details
sed -i "s/PROJECT_ID/$PROJECT_ID/g" service.yaml
sed -i "s/your-bucket-name/$BUCKET_NAME/g" service.yaml

# Build image
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/wtfffmpeg-repo/wtfffmpeg

# Update service.yaml image reference
sed -i "s|gcr.io/PROJECT_ID/wtfffmpeg|$REGION-docker.pkg.dev/$PROJECT_ID/wtfffmpeg-repo/wtfffmpeg|g" service.yaml

# Deploy using service configuration
gcloud run services replace service.yaml --region=$REGION
```

### Method 3: Local Docker Build

```bash
# Build locally
docker build -t wtfffmpeg .

# Tag for Artifact Registry
docker tag wtfffmpeg $REGION-docker.pkg.dev/$PROJECT_ID/wtfffmpeg-repo/wtfffmpeg

# Push to registry
docker push $REGION-docker.pkg.dev/$PROJECT_ID/wtfffmpeg-repo/wtfffmpeg

# Deploy
gcloud run deploy $SERVICE_NAME \
    --image=$REGION-docker.pkg.dev/$PROJECT_ID/wtfffmpeg-repo/wtfffmpeg \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="CLOUD_STORAGE_BUCKET=$BUCKET_NAME" \
    --memory=4Gi \
    --cpu=2 \
    --timeout=3600 \
    --max-instances=10 \
    --min-instances=0 \
    --concurrency=1
```

## Configuration

### Required Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `CLOUD_STORAGE_BUCKET` | Google Cloud Storage bucket name for video storage | Yes | None |
| `SECRET_KEY` | Flask secret key for session security | No | Auto-generated |
| `PORT` | Port for the application to listen on | No | 8080 |

### Setting Environment Variables

```bash
# Set environment variables
gcloud run services update $SERVICE_NAME \
    --region=$REGION \
    --set-env-vars="CLOUD_STORAGE_BUCKET=$BUCKET_NAME,SECRET_KEY=your-secure-secret-key"
```

### Service Account (Optional but Recommended)

For production deployments, create a dedicated service account:

```bash
# Create service account
gcloud iam service-accounts create wtfffmpeg-sa \
    --display-name="WTfffmpeg Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:wtfffmpeg-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Update Cloud Run service to use the service account
gcloud run services update $SERVICE_NAME \
    --region=$REGION \
    --service-account=wtfffmpeg-sa@$PROJECT_ID.iam.gserviceaccount.com
```

## Cost Optimization

### Scaling Configuration

The service is configured to scale to zero when not in use, minimizing costs:

- **Min instances**: 0 (scales to zero)
- **Max instances**: 10 (adjust based on expected load)
- **Concurrency**: 1 (one video processing per instance)
- **CPU**: 2 vCPU (sufficient for FFmpeg operations)
- **Memory**: 4GB (adequate for video processing)

### Storage Lifecycle

Videos are automatically deleted after 24 hours to minimize storage costs:

```bash
# Verify lifecycle policy
gsutil lifecycle get gs://$BUCKET_NAME
```

### Monitoring Costs

```bash
# Check Cloud Run usage
gcloud run services describe $SERVICE_NAME --region=$REGION

# Monitor storage usage
gsutil du -sh gs://$BUCKET_NAME
```

### Cost Estimation

Typical costs (US regions):
- **Cloud Run**: ~$0.24 per hour of active processing (scales to zero when idle)
- **Cloud Storage**: ~$0.02 per GB per month (with 1-day lifecycle)
- **Network**: ~$0.12 per GB of egress

For occasional use (few videos per day), monthly costs should be under $10.

## Monitoring and Troubleshooting

### Health Checks

The service includes a health check endpoint at `/_health`:

```bash
# Test health endpoint
curl https://YOUR_SERVICE_URL/_health
```

### Viewing Logs

```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
    --limit=50 \
    --format="table(timestamp,severity,textPayload)"

# Stream live logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME"
```

### Common Issues and Solutions

#### 1. Service Won't Start
**Symptoms**: Service shows "Service Unavailable"
**Solutions**:
- Check that `CLOUD_STORAGE_BUCKET` environment variable is set
- Verify the bucket exists and is accessible
- Check service logs for detailed error messages

```bash
gcloud run services describe $SERVICE_NAME --region=$REGION
gcloud logging read "resource.type=cloud_run_revision" --limit=10
```

#### 2. Video Processing Fails
**Symptoms**: "An error occurred during video creation"
**Solutions**:
- Check if FFmpeg is installed in the container
- Verify sufficient memory allocation (4GB recommended)
- Check file upload size limits

#### 3. Permission Errors
**Symptoms**: Storage-related errors in logs
**Solutions**:
- Verify service account has Storage Object Admin role
- Check bucket permissions
- Ensure the bucket exists in the correct project

```bash
# Check service account
gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(spec.template.spec.serviceAccountName)"

# Test bucket access
gsutil ls gs://$BUCKET_NAME
```

#### 4. Timeout Issues
**Symptoms**: Requests timeout before completion
**Solutions**:
- Increase timeout (current: 3600s/1 hour)
- Monitor processing time in logs
- Consider optimizing FFmpeg parameters

```bash
# Update timeout
gcloud run services update $SERVICE_NAME \
    --region=$REGION \
    --timeout=3600
```

### Performance Monitoring

Monitor key metrics in Cloud Console:
- Request count and latency
- Instance count (should scale to zero when idle)
- Memory and CPU utilization
- Error rate

## Best Practices

### Security
1. **Use HTTPS**: Cloud Run automatically provides HTTPS
2. **Service Account**: Use dedicated service account with minimal permissions
3. **Secret Management**: Use Secret Manager for sensitive configuration
4. **Input Validation**: The app validates file uploads and parameters

### Performance
1. **Container Concurrency**: Set to 1 for CPU-intensive video processing
2. **Resource Allocation**: 2 CPU + 4GB memory for optimal FFmpeg performance
3. **Scaling**: Max 10 instances to control costs and resource usage

### Reliability
1. **Health Checks**: Configured for readiness and liveness probes
2. **Logging**: Structured logging for better monitoring
3. **Error Handling**: Graceful error handling with cleanup
4. **Timeouts**: Generous timeout for video processing operations

### Cost Management
1. **Scale to Zero**: Automatic scaling to zero when idle
2. **Storage Lifecycle**: Automatic cleanup of generated videos
3. **Regional Deployment**: Deploy in region closest to users
4. **Monitoring**: Regular cost monitoring and alerts

## Getting Support

- **Cloud Run Documentation**: https://cloud.google.com/run/docs
- **Cloud Storage Documentation**: https://cloud.google.com/storage/docs
- **FFmpeg Documentation**: https://ffmpeg.org/documentation.html

For application-specific issues, check the application logs and health endpoint first.