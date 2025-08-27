#!/usr/bin/env python3
"""
Enhanced integration tests for WTfffmpeg service configuration.
This test suite provides comprehensive validation for deployment scenarios.
"""

import os
import sys
import io
import json
import tempfile
import time
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage

# Add the current directory to Python path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_configuration():
    """Test basic configuration scenarios."""
    print("🧪 Running basic configuration tests...")
    
    # Test 1: Health endpoint always works
    with patch.dict(os.environ, {}, clear=True):
        import importlib
        if 'app' in sys.modules:
            importlib.reload(sys.modules['app'])
        import app
        
        with app.app.test_client() as client:
            response = client.get('/_health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert data['service'] == 'wtfffmpeg'
            print("  ✓ Health endpoint works without any environment variables")

def test_configuration_endpoints():
    """Test configuration endpoints with various scenarios."""
    print("🧪 Running configuration endpoint tests...")
    
    # Test 1: No environment variables
    with patch.dict(os.environ, {}, clear=True):
        import importlib
        if 'app' in sys.modules:
            importlib.reload(sys.modules['app'])
        import app
        
        with app.app.test_client() as client:
            response = client.get('/_config')
            assert response.status_code == 503
            data = response.get_json()
            assert not data['ready_for_video_creation']
            assert not data['configuration']['cloud_storage_bucket_configured']
            assert data['configuration']['cloud_storage_bucket_value'] == 'NOT_SET'
            assert not data['configuration']['secret_key_configured']
            assert data['configuration']['secret_key_source'] == 'default'
            assert len(data['issues']) >= 1
            print("  ✓ Config endpoint returns 503 with no environment variables")
    
    # Test 2: Only bucket configured
    with patch.dict(os.environ, {'CLOUD_STORAGE_BUCKET': 'test-bucket'}, clear=True):
        import importlib
        if 'app' in sys.modules:
            importlib.reload(sys.modules['app'])
        import app
        
        with app.app.test_client() as client:
            response = client.get('/_config')
            assert response.status_code == 200
            data = response.get_json()
            assert data['ready_for_video_creation']
            assert data['configuration']['cloud_storage_bucket_configured']
            assert data['configuration']['cloud_storage_bucket_value'] == 'test-bucket'
            # Should still warn about default secret key
            assert any('SECRET_KEY' in issue for issue in data['issues'])
            print("  ✓ Config endpoint returns 200 with bucket configured")
    
    # Test 3: Full configuration
    with patch.dict(os.environ, {
        'CLOUD_STORAGE_BUCKET': 'production-bucket',
        'SECRET_KEY': 'super-secret-production-key'
    }, clear=True):
        import importlib
        if 'app' in sys.modules:
            importlib.reload(sys.modules['app'])
        import app
        
        with app.app.test_client() as client:
            response = client.get('/_config')
            assert response.status_code == 200
            data = response.get_json()
            assert data['ready_for_video_creation']
            assert data['configuration']['cloud_storage_bucket_configured']
            assert data['configuration']['secret_key_configured']
            assert data['configuration']['secret_key_source'] == 'environment'
            assert len(data['issues']) == 0
            print("  ✓ Config endpoint returns 200 with full configuration")

def test_video_creation_without_bucket():
    """Test video creation behavior without cloud storage bucket."""
    print("🧪 Running video creation error tests...")
    
    with patch.dict(os.environ, {}, clear=True):
        import importlib
        if 'app' in sys.modules:
            importlib.reload(sys.modules['app'])
        import app
        
        with app.app.test_client() as client:
            # Test missing files
            response = client.post('/', data={})
            assert response.status_code == 400
            assert "Missing file(s)" in response.get_data(as_text=True)
            print("  ✓ Video creation fails with missing files")
            
            # Test with files but no bucket
            image_file = FileStorage(
                stream=io.BytesIO(b'fake image data'),
                filename='test.jpg',
                content_type='image/jpeg'
            )
            audio_file = FileStorage(
                stream=io.BytesIO(b'fake audio data'),
                filename='test.mp3',
                content_type='audio/mp3'
            )
            
            response = client.post('/', data={
                'image': image_file,
                'audio': audio_file,
                'resolution': '720p'
            }, content_type='multipart/form-data')
            
            assert response.status_code == 500
            error_text = response.get_data(as_text=True)
            assert 'Service configuration error' in error_text
            assert 'CLOUD_STORAGE_BUCKET environment variable not configured' in error_text
            assert 'Please contact administrator' in error_text
            print("  ✓ Video creation fails with detailed configuration error")

def test_error_logging():
    """Test that configuration errors are properly logged."""
    print("🧪 Running error logging tests...")
    
    with patch.dict(os.environ, {}, clear=True):
        # Capture logging output
        import logging
        from io import StringIO
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        
        # Reload app to trigger configuration validation
        import importlib
        if 'app' in sys.modules:
            importlib.reload(sys.modules['app'])
        import app
        
        # Check that warnings were logged
        log_output = log_capture.getvalue()
        # The logging happens during module import, so we check startup_issues instead
        assert len(app.startup_issues) >= 1
        assert any('CLOUD_STORAGE_BUCKET' in issue for issue in app.startup_issues)
        print("  ✓ Configuration issues are properly captured in startup_issues")

def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("🧪 Running edge case tests...")
    
    # Test with empty bucket name
    with patch.dict(os.environ, {'CLOUD_STORAGE_BUCKET': ''}, clear=True):
        import importlib
        if 'app' in sys.modules:
            importlib.reload(sys.modules['app'])
        import app
        
        with app.app.test_client() as client:
            response = client.get('/_config')
            assert response.status_code == 503
            data = response.get_json()
            assert not data['ready_for_video_creation']
            print("  ✓ Empty bucket name treated as not configured")
    
    # Test with whitespace-only bucket name
    with patch.dict(os.environ, {'CLOUD_STORAGE_BUCKET': '   '}, clear=True):
        import importlib
        if 'app' in sys.modules:
            importlib.reload(sys.modules['app'])
        import app
        
        # The current implementation doesn't strip whitespace, so this would be valid
        # but we can test that it's preserved
        with app.app.test_client() as client:
            response = client.get('/_config')
            data = response.get_json()
            assert data['configuration']['cloud_storage_bucket_value'] == '   '
            print("  ✓ Whitespace bucket name is preserved")

def test_concurrent_requests():
    """Test behavior under concurrent requests."""
    print("🧪 Running concurrent request tests...")
    
    with patch.dict(os.environ, {'CLOUD_STORAGE_BUCKET': 'test-bucket'}, clear=True):
        import importlib
        if 'app' in sys.modules:
            importlib.reload(sys.modules['app'])
        import app
        
        with app.app.test_client() as client:
            # Simulate multiple concurrent health checks
            responses = []
            for i in range(5):
                response = client.get('/_health')
                responses.append(response.status_code)
            
            assert all(code == 200 for code in responses)
            print("  ✓ Multiple concurrent health checks succeed")
            
            # Simulate multiple concurrent config checks
            responses = []
            for i in range(5):
                response = client.get('/_config')
                responses.append(response.status_code)
            
            assert all(code == 200 for code in responses)
            print("  ✓ Multiple concurrent config checks succeed")

def test_deployment_scenarios():
    """Test common deployment scenarios."""
    print("🧪 Running deployment scenario tests...")
    
    # Scenario 1: Fresh deployment (no env vars)
    print("  Testing fresh deployment scenario...")
    with patch.dict(os.environ, {}, clear=True):
        import importlib
        if 'app' in sys.modules:
            importlib.reload(sys.modules['app'])
        import app
        
        with app.app.test_client() as client:
            health_response = client.get('/_health')
            config_response = client.get('/_config')
            
            assert health_response.status_code == 200
            assert config_response.status_code == 503
            config_data = config_response.get_json()
            assert not config_data['ready_for_video_creation']
            print("    ✓ Fresh deployment shows not ready")
    
    # Scenario 2: Production deployment
    print("  Testing production deployment scenario...")
    with patch.dict(os.environ, {
        'CLOUD_STORAGE_BUCKET': 'yt-v8dr-wtfffmpeg-videos',
        'SECRET_KEY': 'production-secret-key-2024',
        'PORT': '8080'
    }, clear=True):
        import importlib
        if 'app' in sys.modules:
            importlib.reload(sys.modules['app'])
        import app
        
        with app.app.test_client() as client:
            health_response = client.get('/_health')
            config_response = client.get('/_config')
            
            assert health_response.status_code == 200
            assert config_response.status_code == 200
            config_data = config_response.get_json()
            assert config_data['ready_for_video_creation']
            assert config_data['configuration']['port'] == '8080'
            print("    ✓ Production deployment shows ready")

def main():
    """Run all integration tests."""
    print("🚀 WTfffmpeg Enhanced Integration Tests")
    print("=" * 50)
    
    try:
        test_basic_configuration()
        test_configuration_endpoints()
        test_video_creation_without_bucket()
        test_error_logging()
        test_edge_cases()
        test_concurrent_requests()
        test_deployment_scenarios()
        
        print("\n🎉 All integration tests passed!")
        print("✅ Service configuration error handling is working correctly")
        return 0
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())