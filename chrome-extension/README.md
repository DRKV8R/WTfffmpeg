# WTfffmpeg Chrome Extension

A Chrome extension that allows you to create videos from images and audio files using a local WTfffmpeg server, without requiring Google Cloud dependencies.

## Features

- **Local Processing**: Works with a local Flask server without Google Cloud Storage
- **Simple Interface**: Easy-to-use popup interface for file selection
- **Flexible Server**: Can connect to any local WTfffmpeg server instance
- **Direct Downloads**: Generated videos are served directly from the local server

## Installation

1. Clone or download this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top right
4. Click "Load unpacked" and select the `chrome-extension` folder
5. The extension will appear in your Chrome toolbar

## Usage

1. Start your local WTfffmpeg server:
   ```bash
   cd /path/to/WTfffmpeg
   python app.py
   ```

2. Click the WTfffmpeg extension icon in Chrome
3. Verify the server URL (default: http://localhost:8080)
4. Select an image file and an audio file
5. Choose your desired resolution (720p or 1080p)
6. Click "Create Video"
7. Download your generated video when ready

## Requirements

- Local WTfffmpeg server running (see main README for setup)
- Chrome browser with extension support
- FFmpeg installed on the server machine

## Server Configuration

The extension works with the WTfffmpeg Flask server in "local mode" - when the `CLOUD_STORAGE_BUCKET` environment variable is not set, the server will automatically operate in local mode and serve videos directly.

## Icons

The extension currently uses placeholder icons. You can replace the icons in the `icons/` folder with:
- icon16.png (16x16 pixels)
- icon32.png (32x32 pixels)  
- icon48.png (48x48 pixels)
- icon128.png (128x128 pixels)