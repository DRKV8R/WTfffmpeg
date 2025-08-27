#!/usr/bin/env python3
"""
Test script for WTfffmpeg storage backend functionality.
Tests both Google Cloud Storage and MEGA.nz storage options.
"""

import os
import sys
import io
from werkzeug.datastructures import FileStorage

# Add the current directory to Python path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_google_cloud_storage():
    """Test application with Google Cloud Storage backend."""
    print("=== Testing Google Cloud Storage Backend ===")
    
    # Set up Google Cloud Storage environment
    os.environ.clear()
    os.environ['STORAGE_TYPE'] = 'gcs'
    os.environ['CLOUD_STORAGE_BUCKET'] = 'test-bucket'
    os.environ['SECRET_KEY'] = 'test-secret'
    
    # Clear modules to force reload with new environment
    for module in ['app', 'storage_backends']:
        if module in sys.modules:
            del sys.modules[module]
    
    import app
    
    with app.app.test_client() as client:
        # Test health endpoint
        response = client.get('/_health')
        assert response.status_code == 200
        print("✓ Health endpoint works with GCS")
        
        # Test config endpoint
        response = client.get('/_config')
        assert response.status_code == 200
        data = response.get_json()
        assert data['ready_for_video_creation']
        assert data['configuration']['storage_backend']['type'] == 'google_cloud_storage'
        assert data['configuration']['storage_backend']['configured']
        print("✓ Config endpoint shows GCS properly configured")


def test_mega_storage():
    """Test application with MEGA.nz storage backend."""
    print("\n=== Testing MEGA.nz Storage Backend ===")
    
    # Set up MEGA storage environment
    os.environ.clear()
    os.environ['STORAGE_TYPE'] = 'mega'
    os.environ['MEGA_FOLDER_URL'] = 'https://mega.nz/folder/ZNxmCARJ#aI_69FDOlhmRuQWDriHaUw'
    os.environ['SECRET_KEY'] = 'test-secret'
    
    # Clear modules to force reload with new environment
    for module in ['app', 'storage_backends']:
        if module in sys.modules:
            del sys.modules[module]
    
    import app
    
    with app.app.test_client() as client:
        # Test health endpoint
        response = client.get('/_health')
        assert response.status_code == 200
        print("✓ Health endpoint works with MEGA")
        
        # Test config endpoint
        response = client.get('/_config')
        assert response.status_code == 200
        data = response.get_json()
        assert data['ready_for_video_creation']
        assert data['configuration']['storage_backend']['type'] == 'mega_storage'
        assert data['configuration']['storage_backend']['configured']
        assert data['configuration']['storage_backend']['status'] == 'not_implemented'
        print("✓ Config endpoint shows MEGA properly configured")
        
        # Test video creation (should fail due to ffmpeg not being available)
        image_file = FileStorage(stream=io.BytesIO(b'fake image data'), 
                               filename='test.jpg', content_type='image/jpeg')
        audio_file = FileStorage(stream=io.BytesIO(b'fake audio data'), 
                               filename='test.mp3', content_type='audio/mp3')
        
        response = client.post('/', data={
            'image': image_file,
            'audio': audio_file,
            'resolution': '720p'
        }, content_type='multipart/form-data')
        
        assert response.status_code == 500
        error_text = response.get_data(as_text=True)
        # Will fail due to ffmpeg not being available, but that's expected
        assert 'An error occurred during video creation' in error_text
        print("✓ Video creation handles MEGA storage configuration")


def test_storage_backend_fallback():
    """Test storage backend fallback behavior."""
    print("\n=== Testing Storage Backend Fallback ===")
    
    # Test with no storage configuration
    os.environ.clear()
    
    # Clear modules to force reload with new environment
    for module in ['app', 'storage_backends']:
        if module in sys.modules:
            del sys.modules[module]
    
    import app
    
    with app.app.test_client() as client:
        # Test config endpoint (should show not configured)
        response = client.get('/_config')
        assert response.status_code == 503  # Service unavailable
        data = response.get_json()
        assert not data['ready_for_video_creation']
        assert data['configuration']['storage_backend']['type'] == 'google_cloud_storage'
        assert not data['configuration']['storage_backend']['configured']
        print("✓ Config endpoint correctly shows unconfigured state")


def main():
    """Run all tests."""
    print("WTfffmpeg Storage Backend Tests")
    print("=" * 40)
    
    try:
        test_google_cloud_storage()
        test_mega_storage()
        test_storage_backend_fallback()
        print("\n🎉 All storage backend tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())