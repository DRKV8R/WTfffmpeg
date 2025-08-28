#!/usr/bin/env python3

"""
Simple test script to verify WTfffmpeg local mode functionality
"""

import requests
import tempfile
import os
import sys
from PIL import Image
import io

def test_server_health(base_url="http://localhost:8080"):
    """Test if the server is running and healthy"""
    try:
        response = requests.get(f"{base_url}/_health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is healthy")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def test_config(base_url="http://localhost:8080"):
    """Test server configuration"""
    try:
        response = requests.get(f"{base_url}/_config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Server mode: {config.get('mode', 'unknown')}")
            print(f"✅ Ready for video creation: {config.get('ready_for_video_creation', False)}")
            return config.get('mode') == 'local'
        else:
            print(f"❌ Config check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Config check error: {e}")
        return False

def create_test_files():
    """Create test image and audio files"""
    # Create a simple test image
    img = Image.new('RGB', (640, 480), color='red')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # For audio, we'll use a simple text file (won't work for actual video creation, but tests the upload)
    audio_buffer = io.BytesIO(b"This is a test audio file placeholder")
    
    return img_buffer, audio_buffer

def main():
    print("🧪 WTfffmpeg Local Mode Test")
    print("============================")
    
    base_url = "http://localhost:8080"
    
    # Test 1: Server health
    if not test_server_health(base_url):
        print("\n❌ Server is not running. Please start it with: python3 app.py")
        sys.exit(1)
    
    # Test 2: Configuration
    if not test_config(base_url):
        print("\n❌ Server is not in local mode or not ready")
        sys.exit(1)
    
    print("\n✅ All tests passed! WTfffmpeg local mode is working correctly.")
    print("\nTo test video creation:")
    print("1. Visit http://localhost:8080")
    print("2. Upload an image and audio file")
    print("3. Click 'Create Video'")
    print("\nOr use the Chrome extension for a better experience!")

if __name__ == "__main__":
    try:
        import requests
        from PIL import Image
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install requests pillow")
        sys.exit(1)
    
    main()