#!/bin/bash

# WTfffmpeg Deployment Script
# Project: yt-v8dr
# Service: master-v8dr (MASTER V8DR)
# Author: Automated deployment script
# Version: 1.0

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_ID="yt-v8dr"
REGION="us-central1"
SERVICE_NAME="master-v8dr"
BUCKET_NAME="yt-v8dr-wtfffmpeg-videos"
REPOSITORY_NAME="wtfffmpeg-repo"
SERVICE_ACCOUNT_NAME="master-v8dr-sa"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   WTfffmpeg Deployment Script${NC}"
echo -e "${BLUE}   Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}   Service: ${SERVICE_NAME}${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to print status messages
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Pre-flight checks
print_status "Running pre-flight checks..."

if ! command_exists gcloud; then
    print_error "gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

if ! command_exists git; then
    print_error "git not found. Please install git."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "Not authenticated with Google Cloud. Please run 'gcloud auth login'"
    exit 1
fi

# Set the project
print_status "Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Verify current project
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    print_error "Failed to set project to ${PROJECT_ID}. Current project: ${CURRENT_PROJECT}"
    exit 1
fi

print_status "Project set successfully: ${CURRENT_PROJECT}"

# Enable required APIs
print_status "Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    storage.googleapis.com \
    artifactregistry.googleapis.com

# Deploy using Cloud Build
print_status "Starting deployment with Cloud Build..."
echo -e "${YELLOW}This may take several minutes...${NC}"

BUILD_ID=$(gcloud builds submit --config cloudbuild.yaml . --format="value(id)")

if [ $? -eq 0 ]; then
    print_status "Cloud Build completed successfully!"
    print_status "Build ID: ${BUILD_ID}"
else
    print_error "Cloud Build failed!"
    exit 1
fi

# Get the service URL
print_status "Retrieving service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --format="value(status.url)")

if [ -n "$SERVICE_URL" ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   DEPLOYMENT SUCCESSFUL!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
    echo -e "${GREEN}Health Check: ${SERVICE_URL}/_health${NC}"
    echo -e "${GREEN}Bucket: gs://${BUCKET_NAME}${NC}"
    echo -e "${GREEN}Region: ${REGION}${NC}"
    echo -e "${GREEN}========================================${NC}"
    
    # Test health endpoint
    print_status "Testing health endpoint..."
    if curl -s --max-time 30 "${SERVICE_URL}/_health" > /dev/null; then
        print_status "Health check passed! Service is ready."
    else
        print_warning "Health check failed. Service may still be starting up."
        print_warning "Please wait a few minutes and try accessing the service."
    fi
    
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "1. Visit ${SERVICE_URL} to use the application"
    echo -e "2. Monitor logs: gcloud logging tail \"resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}\""
    echo -e "3. View metrics in Cloud Console: https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}/metrics"
    
else
    print_error "Failed to retrieve service URL!"
    exit 1
fi

# Optional: Show recent logs
if [ "$1" = "--show-logs" ]; then
    print_status "Showing recent logs..."
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}" \
        --limit=20 \
        --format="table(timestamp,severity,textPayload)"
fi

print_status "Deployment script completed successfully!"