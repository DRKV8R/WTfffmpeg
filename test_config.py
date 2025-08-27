#!/usr/bin/env python3
"""
Simple test script to verify WTfffmpeg configuration endpoints and error handling.
This test validates the fixes for the service configuration error issue.
"""

import os
import sys
import io
from werkzeug.datastructures import FileStorage

# Add the current directory to Python path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_without_env_vars():
    """Test application behavior without environment variables."""
    print("=== Testing without environment variables ===")

    # Remove any existing env vars for this test
    old_bucket = os.environ.pop("CLOUD_STORAGE_BUCKET", None)
    old_secret = os.environ.pop("SECRET_KEY", None)

    try:
        # Import app after clearing environment
        import importlib

        if "app" in sys.modules:
            importlib.reload(sys.modules["app"])
        import app

        with app.app.test_client() as client:
            # Test health endpoint (should always work)
            response = client.get("/_health")
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "healthy"
            print("✓ Health endpoint works without env vars")

            # Test config endpoint (should show issues)
            response = client.get("/_config")
            assert (
                response.status_code == 503
            )  # Service unavailable due to missing config
            data = response.get_json()
            assert not data["ready_for_video_creation"]
            assert not data["configuration"]["cloud_storage_bucket_configured"]
            assert len(data["issues"]) > 0
            print("✓ Config endpoint correctly identifies missing bucket")

            # Test video creation (should fail with better error message)
            image_file = FileStorage(
                stream=io.BytesIO(b"fake image data"),
                filename="test.jpg",
                content_type="image/jpeg",
            )
            audio_file = FileStorage(
                stream=io.BytesIO(b"fake audio data"),
                filename="test.mp3",
                content_type="audio/mp3",
            )

            response = client.post(
                "/",
                data={"image": image_file, "audio": audio_file, "resolution": "720p"},
                content_type="multipart/form-data",
            )

            assert response.status_code == 500
            error_text = response.get_data(as_text=True)
            assert (
                "CLOUD_STORAGE_BUCKET environment variable not configured" in error_text
            )
            print("✓ Video creation fails with detailed error message")

    finally:
        # Restore environment variables
        if old_bucket:
            os.environ["CLOUD_STORAGE_BUCKET"] = old_bucket
        if old_secret:
            os.environ["SECRET_KEY"] = old_secret


def test_with_env_vars():
    """Test application behavior with proper environment variables."""
    print("\n=== Testing with environment variables ===")

    # Set proper environment variables
    os.environ["CLOUD_STORAGE_BUCKET"] = "yt-v8dr-wtfffmpeg-videos"
    os.environ["SECRET_KEY"] = "yt-v8dr-secret-2024-production"

    try:
        # Import app after setting environment
        import importlib

        if "app" in sys.modules:
            importlib.reload(sys.modules["app"])
        import app

        with app.app.test_client() as client:
            # Test health endpoint
            response = client.get("/_health")
            assert response.status_code == 200
            print("✓ Health endpoint works with env vars")

            # Test config endpoint
            response = client.get("/_config")
            assert response.status_code == 200  # Should be OK now
            data = response.get_json()
            assert data["ready_for_video_creation"]
            assert data["configuration"]["cloud_storage_bucket_configured"]
            assert (
                data["configuration"]["cloud_storage_bucket_value"]
                == "yt-v8dr-wtfffmpeg-videos"
            )
            assert data["configuration"]["secret_key_configured"]
            assert len(data["issues"]) == 0
            print("✓ Config endpoint shows proper configuration")

    finally:
        # Clean up environment variables
        os.environ.pop("CLOUD_STORAGE_BUCKET", None)
        os.environ.pop("SECRET_KEY", None)


def main():
    """Run all tests."""
    print("WTfffmpeg Configuration Tests")
    print("=" * 40)

    try:
        test_without_env_vars()
        test_with_env_vars()
        print("\n🎉 All tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
