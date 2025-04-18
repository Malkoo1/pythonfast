# Video to Audio Extractor API

This API allows you to extract audio from video files or YouTube URLs.

## Endpoints

- `POST /extract-audio/upload` - Upload a video file to extract audio
- `POST /extract-audio/youtube` - Provide a YouTube URL to extract audio

## Running the API

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   uvicorn app.main:app
