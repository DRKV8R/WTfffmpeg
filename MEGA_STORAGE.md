# MEGA.nz Storage Configuration Guide

## Overview

WTfffmpeg now supports MEGA.nz as an alternative storage backend for videos. This guide explains how to configure and use MEGA.nz storage.

## Reference Folder

The MEGA.nz storage implementation references the folder:
**https://mega.nz/folder/ZNxmCARJ#aI_69FDOlhmRuQWDriHaUw**

## Configuration

To use MEGA.nz storage, set the following environment variables:

### Required Variables
```bash
export STORAGE_TYPE=mega
export MEGA_FOLDER_URL=https://mega.nz/folder/ZNxmCARJ#aI_69FDOlhmRuQWDriHaUw
```

### Optional Variables (for future authentication)
```bash
export MEGA_EMAIL=your-mega-account@example.com
export MEGA_PASSWORD=your-mega-password
```

## Current Status

🚧 **Implementation Status: In Progress**

The MEGA.nz storage backend is currently configured but not fully implemented. The system will:

1. ✅ Accept MEGA storage configuration
2. ✅ Validate MEGA storage settings  
3. ✅ Display MEGA storage information
4. ❌ Upload videos to MEGA.nz (not yet implemented)

When attempting to create videos with MEGA storage, you'll receive a message:
> "MEGA.nz storage is configured but not yet fully implemented. Reference folder: https://mega.nz/folder/ZNxmCARJ#aI_69FDOlhmRuQWDriHaUw. Please use Google Cloud Storage for now."

## Testing MEGA Configuration

You can test if MEGA storage is properly configured by visiting the config endpoint:

```bash
curl http://localhost:8080/_config
```

Look for the `storage_backend` section in the response:

```json
{
  "configuration": {
    "storage_backend": {
      "type": "mega_storage",
      "folder_url": "https://mega.nz/folder/ZNxmCARJ#aI_69FDOlhmRuQWDriHaUw",
      "configured": true,
      "status": "not_implemented"
    }
  }
}
```

## Fallback to Google Cloud Storage

To switch back to Google Cloud Storage:

```bash
export STORAGE_TYPE=gcs
export CLOUD_STORAGE_BUCKET=your-bucket-name
```

Or simply unset the STORAGE_TYPE (defaults to Google Cloud Storage):

```bash
unset STORAGE_TYPE
export CLOUD_STORAGE_BUCKET=your-bucket-name
```

## Future Implementation

The MEGA.nz storage implementation will be completed in future updates to include:

- Full MEGA.nz API integration
- File upload functionality  
- Download URL generation
- Authentication with MEGA accounts
- Error handling and retry logic

## Support

For questions about MEGA.nz storage configuration, please refer to:
- The main [README.md](README.md) for general configuration
- The [VIDEO_STORAGE.md](VIDEO_STORAGE.md) for storage details
- This repository's issues for bug reports and feature requests