# Testing WTfffmpeg in GitHub Codespaces

This document provides step-by-step instructions for testing WTfffmpeg using GitHub Codespaces.

## Quick Start

1. **Open in Codespaces**
   - Go to the [WTfffmpeg repository](https://github.com/DRKV8R/WTfffmpeg)
   - Click the green "Code" button
   - Select "Codespaces" tab
   - Click "Create codespace on main"

2. **Wait for Environment Setup**
   - Codespaces will automatically install Python 3.11 and dependencies
   - FFmpeg will be installed during the setup process
   - This takes about 2-3 minutes on first launch

3. **Verify Environment**
   ```bash
   python3 test_codespaces.py
   ```
   This should show all tests passing.

4. **Start the Development Server**
   ```bash
   ./dev-server.sh
   ```

5. **Access the Application**
   - VS Code will show a notification about port 8080 being forwarded
   - Click "Open in Browser" to access the WTfffmpeg interface
   - You can now upload images and audio files to test video creation

## What's Included

The Codespaces environment provides:

- **Python 3.11** with Flask and Google Cloud libraries
- **FFmpeg** for video processing  
- **Pre-configured environment variables** for testing
- **VS Code extensions** for Python development
- **Automatic port forwarding** for web app access

## Testing Scenarios

### Basic Functionality Test
1. Start the dev server: `./dev-server.sh`
2. Open the forwarded port in your browser
3. The app should load with the upload interface

### Configuration Test
```bash
python3 test_config.py
```
This validates the app's configuration endpoints and error handling.

### Environment Test  
```bash
python3 test_codespaces.py
```
This verifies all required dependencies and tools are available.

## Limitations in Codespaces

- **No Google Cloud Storage**: Videos won't actually be stored in the cloud
- **Local testing only**: This is for development and testing the interface
- **No persistent storage**: Files are temporary and will be lost when Codespaces stops

## Troubleshooting

### Port Not Forwarding
If port 8080 doesn't automatically forward:
1. Go to the "Ports" tab in VS Code
2. Click "Forward a Port"
3. Enter `8080`
4. Set visibility to "Public" if needed

### FFmpeg Not Found
If you see FFmpeg errors:
1. The installation might still be running
2. Check the terminal for ongoing installation messages
3. Restart the dev server once installation completes

### Dependencies Missing
If Python imports fail:
1. Run: `pip install --user -r requirements.txt`
2. Wait for installation to complete
3. Restart the dev server

## For Production Deployment

Codespaces is only for development and testing. For production deployment, see:
- [Cloud Run Deployment Guide](README_DEPLOY.md)
- [Main README](README.md)

The production deployment includes real Google Cloud Storage integration and proper scaling.