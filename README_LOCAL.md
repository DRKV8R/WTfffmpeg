# WTfffmpeg Local Mode Setup

This guide explains how to run WTfffmpeg in local mode without Google Cloud dependencies.

## Overview

WTfffmpeg can now operate in two modes:

1. **Cloud Mode** - Uses Google Cloud Storage (original functionality)
2. **Local Mode** - Stores videos locally without requiring Google Cloud

The application automatically detects which mode to use based on configuration.

## Local Mode Setup

### Prerequisites

- Python 3.11+
- FFmpeg installed on your system

### Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/DRKV8R/WTfffmpeg.git
   cd WTfffmpeg
   ```

2. Install dependencies (Google Cloud SDK not required for local mode):
   ```bash
   pip install flask gunicorn werkzeug
   ```

3. Run the application:
   ```bash
   python app.py
   ```

The application will automatically run in local mode since `CLOUD_STORAGE_BUCKET` is not set.

### Configuration

| Environment Variable | Description | Default (Local Mode) |
|---------------------|-------------|----------------------|
| `LOCAL_STORAGE_DIR` | Directory for storing videos locally | `/tmp/wtfffmpeg_videos` |
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `PORT` | Port for the application | 8080 |

### Local Mode Features

- **No Google Cloud required** - Works completely offline
- **Direct downloads** - Videos served directly from the Flask application
- **Automatic cleanup** - Videos older than 24 hours are automatically deleted
- **Same API** - Compatible with existing Chrome extension and web interface

### Using the Chrome Extension

1. Install the Chrome extension from the `chrome-extension/` directory
2. Start the local server: `python app.py`
3. Open the extension and verify the server URL (http://localhost:8080)
4. Upload files and create videos as normal

### API Endpoints

- `GET /` - Web interface
- `POST /` - Create video (supports both form and multipart uploads)
- `GET /download/<job_id>/<filename>` - Download video (local mode only)
- `GET /_health` - Health check
- `GET /_config` - Configuration status

### Testing Local Mode

```bash
# Check if server is running in local mode
curl http://localhost:8080/_config

# Create a video via API
curl -X POST \
  -F "image=@your_image.png" \
  -F "audio=@your_audio.mp3" \
  -F "resolution=720p" \
  http://localhost:8080/
```

### Troubleshooting

**FFmpeg not found:**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

**Permission errors:**
- Ensure the `LOCAL_STORAGE_DIR` is writable
- Check file permissions on uploaded content

**Videos not downloading:**
- Check that the job ID in the URL is valid
- Ensure videos haven't been cleaned up (24-hour limit)

## Switching Between Modes

The application automatically switches modes based on configuration:

**Force Local Mode:**
```bash
# Ensure CLOUD_STORAGE_BUCKET is not set
unset CLOUD_STORAGE_BUCKET
python app.py
```

**Use Cloud Mode:**
```bash
export CLOUD_STORAGE_BUCKET="your-bucket-name"
# Install google-cloud-storage if not already installed
pip install google-cloud-storage
python app.py
```

## Chrome Extension Setup

See [chrome-extension/README.md](chrome-extension/README.md) for detailed Chrome extension installation and usage instructions.