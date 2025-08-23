# WTfffmpeg

A simple web application that creates videos from static images and audio files using FFmpeg. Upload an image and audio file, select your desired resolution, and get a downloadable video in seconds.

## Features

- **Simple Upload Interface**: Drag and drop image and audio files
- **Multiple Resolutions**: Support for 720p and 1080p output
- **Cloud Storage**: Videos are stored in Google Cloud Storage with temporary download links
- **Serverless Architecture**: Runs on Google Cloud Run, scales to zero for cost efficiency
- **Format Support**: 
  - Images: JPEG, PNG, and other common formats
  - Audio: MP3, WAV, and other FFmpeg-supported formats
  - Output: MP4 videos with H.264 encoding

## Quick Start

1. Visit the deployed application
2. Upload an image file
3. Upload an audio file
4. Select your preferred resolution (720p or 1080p)
5. Click "Create Video"
6. Download your generated video

## Technology Stack

- **Backend**: Python Flask
- **Video Processing**: FFmpeg
- **Storage**: Google Cloud Storage  
- **Deployment**: Google Cloud Run (serverless)
- **Containerization**: Docker

## Deployment

### Recommended: Google Cloud Run

For the best experience and cost efficiency, deploy to Google Cloud Run which automatically scales to zero when not in use.

📖 **[Complete Cloud Run Deployment Guide](README_DEPLOY.md)**

The deployment guide includes:
- Step-by-step setup instructions
- Cost optimization strategies
- Monitoring and troubleshooting tips
- Security best practices

### Alternative: Google App Engine

The application also supports deployment to Google App Engine, though Cloud Run is recommended for better cost efficiency and performance.

## Local Development

### Prerequisites
- Python 3.11+
- FFmpeg installed on your system
- Google Cloud SDK (for cloud storage)

### Setup
```bash
# Clone the repository
git clone https://github.com/DRKV8R/WTfffmpeg.git
cd WTfffmpeg

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CLOUD_STORAGE_BUCKET="your-bucket-name"
export SECRET_KEY="your-secret-key"

# Run the application
python app.py
```

Visit http://localhost:8080 to use the application.

### Using Docker
```bash
# Build the image
docker build -t wtfffmpeg .

# Run the container
docker run -p 8080:8080 \
  -e CLOUD_STORAGE_BUCKET="your-bucket-name" \
  -e SECRET_KEY="your-secret-key" \
  wtfffmpeg
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `CLOUD_STORAGE_BUCKET` | Google Cloud Storage bucket for video storage | Yes | None |
| `SECRET_KEY` | Flask secret key for session security | No | Auto-generated |
| `PORT` | Port for the application to listen on | No | 8080 |

## API Endpoints

- `GET /` - Main application interface
- `POST /` - Video creation endpoint
- `GET /_health` - Health check endpoint (for Cloud Run)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. See the repository for license details.

## Support

For deployment issues, see the [deployment guide](README_DEPLOY.md).
For application bugs or feature requests, please open an issue on GitHub.