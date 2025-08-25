# Where Do My Videos Go? - WTfffmpeg Video Storage Guide

## 📹 Video Storage Overview

When you create a video with WTfffmpeg, here's exactly where your videos go and how you can access them:

## 🎯 Video Processing Workflow

1. **Upload**: You upload an image and audio file through the web interface
2. **Processing**: FFmpeg combines them into an MP4 video (720p or 1080p)
3. **Cloud Storage**: Your video is automatically uploaded to Google Cloud Storage
4. **Download**: You get a direct download link that works for 15 minutes

## 📂 Where Videos Are Stored

### Cloud Storage Location
- **Storage Service**: Google Cloud Storage
- **Bucket**: `yt-v8dr-wtfffmpeg-videos` (for the deployed instance)
- **File Path**: `{unique-job-id}/{video_output_filename}.mp4`
- **Format**: MP4 with H.264 video encoding and AAC audio

### Example Storage Path
```
gs://yt-v8dr-wtfffmpeg-videos/
└── a1b2c3d4-e5f6-7890-abcd-ef1234567890/
    └── video_output_myimage.mp4
```

## ⏰ Video Availability

### Download Window
- **Immediate Access**: After processing, you're redirected to a download URL
- **Download Link Duration**: 15 minutes (900 seconds)
- **Direct Download**: Click the link to download your video file

### Automatic Cleanup
- **Storage Duration**: Videos are automatically deleted after **24 hours**
- **Cost Optimization**: This keeps storage costs minimal
- **Important**: Download your video within 24 hours of creation

## 💡 How to Access Your Videos

### Immediate Download (Recommended)
1. After clicking "Create Video", wait for processing to complete
2. You'll be automatically redirected to a download link
3. Click to download your video file immediately
4. Save the video to your device within 15 minutes

### If You Miss the Download Window
- **Unfortunately**: There's no way to regenerate the download link
- **Solution**: Simply create the video again using the same image and audio files
- **Processing Time**: Usually takes less than a minute

## 🔒 Privacy & Security

- **Temporary URLs**: Download links are signed and expire after 15 minutes
- **Automatic Deletion**: All videos are automatically deleted after 24 hours
- **No Permanent Storage**: Videos are not permanently stored or accessible by others

## ❓ Frequently Asked Questions

**Q: Can I get my video again after 24 hours?**
A: No, videos are automatically deleted. You'll need to create it again.

**Q: Can I extend the download link expiration?**
A: No, download links are fixed at 15 minutes for security.

**Q: Where can I find old videos I created?**
A: Videos are not stored permanently. Each video creation is a one-time process.

**Q: Can I access videos from the Google Cloud Console?**
A: Technically yes if you have access to the project, but videos are automatically deleted after 24 hours anyway.

## 🚀 Best Practices

1. **Download Immediately**: Always download your video right after creation
2. **Save Locally**: Store videos on your device or cloud storage of choice
3. **Keep Source Files**: Save your original image and audio files for future re-creation
4. **Bookmark the Service**: For easy access when you need to create videos

## 🛠️ Technical Details

- **Processing Location**: Temporary files in `/tmp/{job-id}/` during processing
- **Upload Method**: Google Cloud Storage client library
- **URL Generation**: Signed URLs with v4 signing
- **Cleanup**: Automatic removal of temporary files after processing