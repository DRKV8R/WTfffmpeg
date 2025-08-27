#!/usr/bin/env python3
"""
Test script to validate GitHub Codespaces environment setup for WTfffmpeg.
This test ensures all required components are available for development.
"""

import os
import sys
import subprocess
import json

def test_python_dependencies():
    """Test that required Python packages are importable."""
    print("🐍 Testing Python dependencies...")
    
    required_packages = [
        'flask',
        'google.cloud.storage',
        'werkzeug'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError as e:
            print(f"  ❌ {package}: {e}")
            return False
    
    return True

def test_ffmpeg_availability():
    """Test that FFmpeg is available in the system."""
    print("🎬 Testing FFmpeg availability...")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"  ✓ FFmpeg available: {version_line}")
            return True
        else:
            print(f"  ❌ FFmpeg command failed: {result.stderr}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  ❌ FFmpeg not found: {e}")
        return False

def test_devcontainer_config():
    """Test that devcontainer configuration is valid."""
    print("📋 Testing devcontainer configuration...")
    
    config_path = '.devcontainer/devcontainer.json'
    if not os.path.exists(config_path):
        print(f"  ❌ {config_path} not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        required_keys = ['name', 'image', 'forwardPorts']
        for key in required_keys:
            if key not in config:
                print(f"  ❌ Missing required key: {key}")
                return False
            print(f"  ✓ {key}: {config[key]}")
        
        return True
    except json.JSONDecodeError as e:
        print(f"  ❌ Invalid JSON: {e}")
        return False

def test_dev_script():
    """Test that development script exists and is executable."""
    print("📜 Testing development script...")
    
    script_path = 'dev-server.sh'
    if not os.path.exists(script_path):
        print(f"  ❌ {script_path} not found")
        return False
    
    if not os.access(script_path, os.X_OK):
        print(f"  ❌ {script_path} is not executable")
        return False
    
    print(f"  ✓ {script_path} exists and is executable")
    return True

def test_app_health():
    """Test that the Flask app can import and basic health check works."""
    print("🏥 Testing application health...")
    
    try:
        # Set minimal environment for testing
        os.environ['CLOUD_STORAGE_BUCKET'] = 'test-bucket'
        os.environ['SECRET_KEY'] = 'test-key'
        
        # Import app
        import app
        
        # Test health endpoint
        with app.app.test_client() as client:
            response = client.get('/_health')
            if response.status_code == 200:
                print("  ✓ Health endpoint responding")
                return True
            else:
                print(f"  ❌ Health endpoint failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"  ❌ App health test failed: {e}")
        return False

def main():
    """Run all Codespaces environment tests."""
    print("🧪 WTfffmpeg Codespaces Environment Test")
    print("=" * 40)
    print()
    
    tests = [
        test_python_dependencies,
        test_ffmpeg_availability,
        test_devcontainer_config,
        test_dev_script,
        test_app_health
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append(False)
            print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("📊 Test Summary")
    print("=" * 20)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Codespaces environment is ready.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main())