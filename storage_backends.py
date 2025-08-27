"""
Storage backend abstraction for WTfffmpeg.
Supports Google Cloud Storage and MEGA.nz storage options.
"""

import os
import logging
from abc import ABC, abstractmethod
from google.cloud import storage as gcs


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str) -> str:
        """Upload a file and return a download URL."""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the storage backend is properly configured."""
        pass
    
    @abstractmethod
    def get_config_info(self) -> dict:
        """Get configuration information for debugging."""
        pass


class GoogleCloudStorageBackend(StorageBackend):
    """Google Cloud Storage backend."""
    
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = None
        
    def upload_file(self, local_path: str, remote_path: str) -> str:
        """Upload file to Google Cloud Storage and return signed URL."""
        if not self.is_configured():
            raise ValueError("Google Cloud Storage not properly configured")
            
        if not self.client:
            self.client = gcs.Client()
            
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(remote_path)
        blob.upload_from_filename(local_path)
        
        # Generate signed URL valid for 15 minutes
        download_url = blob.generate_signed_url(version='v4', expiration=900)
        return download_url
    
    def is_configured(self) -> bool:
        """Check if Google Cloud Storage is configured."""
        return bool(self.bucket_name)
    
    def get_config_info(self) -> dict:
        """Get configuration info for Google Cloud Storage."""
        return {
            'type': 'google_cloud_storage',
            'bucket_name': self.bucket_name,
            'configured': self.is_configured()
        }


class MegaStorageBackend(StorageBackend):
    """MEGA.nz storage backend."""
    
    def __init__(self, folder_url: str = None, email: str = None, password: str = None):
        self.folder_url = folder_url or "https://mega.nz/folder/ZNxmCARJ#aI_69FDOlhmRuQWDriHaUw"
        self.email = email
        self.password = password
    
    def upload_file(self, local_path: str, remote_path: str) -> str:
        """Upload file to MEGA.nz and return download URL."""
        # TODO: Implement MEGA.nz upload functionality
        # For now, this is a placeholder that raises an error
        raise NotImplementedError(
            "MEGA.nz storage is configured but not yet fully implemented. "
            f"Reference folder: {self.folder_url}. "
            "Please use Google Cloud Storage for now."
        )
    
    def is_configured(self) -> bool:
        """Check if MEGA storage is configured."""
        return bool(self.folder_url)
    
    def get_config_info(self) -> dict:
        """Get configuration info for MEGA storage."""
        return {
            'type': 'mega_storage',
            'folder_url': self.folder_url,
            'email_configured': bool(self.email),
            'password_configured': bool(self.password),
            'configured': self.is_configured(),
            'status': 'not_implemented'
        }


def get_storage_backend() -> StorageBackend:
    """
    Get the configured storage backend based on environment variables.
    
    Environment variables:
    - STORAGE_TYPE: 'gcs' (default) or 'mega'
    - CLOUD_STORAGE_BUCKET: For Google Cloud Storage
    - MEGA_FOLDER_URL: For MEGA.nz folder URL
    - MEGA_EMAIL: For MEGA.nz account email
    - MEGA_PASSWORD: For MEGA.nz account password
    """
    storage_type = os.environ.get('STORAGE_TYPE', 'gcs').lower()
    
    if storage_type == 'mega':
        folder_url = os.environ.get('MEGA_FOLDER_URL')
        email = os.environ.get('MEGA_EMAIL')
        password = os.environ.get('MEGA_PASSWORD')
        return MegaStorageBackend(folder_url, email, password)
    
    else:  # Default to Google Cloud Storage
        bucket_name = os.environ.get('CLOUD_STORAGE_BUCKET')
        return GoogleCloudStorageBackend(bucket_name)