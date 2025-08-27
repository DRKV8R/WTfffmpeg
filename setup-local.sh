#!/bin/bash

# WTfffmpeg Local Mode Setup Script
# This script sets up WTfffmpeg to run in local mode without Google Cloud dependencies

set -e

echo "🎬 WTfffmpeg Local Mode Setup"
echo "=============================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if FFmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg is required but not installed."
    echo "To install FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: Download from https://ffmpeg.org/"
    exit 1
fi

echo "✅ FFmpeg found: $(ffmpeg -version | head -1)"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements-local.txt

echo "🚀 Setup complete!"
echo ""
echo "To start the server:"
echo "  python3 app.py"
echo ""
echo "Then visit: http://localhost:8080"
echo ""
echo "To use the Chrome extension:"
echo "  1. Open Chrome and go to chrome://extensions/"
echo "  2. Enable 'Developer mode'"
echo "  3. Click 'Load unpacked' and select the 'chrome-extension' folder"
echo "  4. Start the server with 'python3 app.py'"
echo "  5. Click the extension icon to create videos"