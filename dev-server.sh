#!/bin/bash

# Development script for running WTfffmpeg locally in GitHub Codespaces
# This script sets up the environment and starts the Flask development server

set -e

echo "🚀 Starting WTfffmpeg Development Server"
echo "========================================"

# Set development environment variables
export CLOUD_STORAGE_BUCKET="dev-test-bucket"
export SECRET_KEY="dev-secret-key-for-testing-only"
export PORT=8080

echo "📋 Development Configuration:"
echo "  - CLOUD_STORAGE_BUCKET: $CLOUD_STORAGE_BUCKET"
echo "  - PORT: $PORT"
echo "  - SECRET_KEY: [SET]"
echo ""

# Check if dependencies are installed
echo "🔍 Checking dependencies..."
if ! python3 -c "import flask, google.cloud.storage" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install --user -r requirements.txt
else
    echo "✅ Dependencies are installed"
fi

# Check if ffmpeg is available
if command -v ffmpeg >/dev/null 2>&1; then
    echo "✅ ffmpeg is available"
else
    echo "⚠️  ffmpeg not found. Video processing may not work."
fi

echo ""
echo "🔧 Running configuration tests..."
python3 test_config.py
echo ""

echo "🌐 Starting Flask development server..."
echo "📱 The app will be available on port 8080"
echo "🔗 In Codespaces, VS Code will automatically forward this port"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask development server
python3 app.py