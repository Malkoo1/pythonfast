import os
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .exceptions import AudioExtractionError, InvalidFileTypeError, InvalidVideoURLError
from .models import URLRequest, VideoURL, YouTubeTranscriptRequest, YouTubeURL
from .text_extractor import extract_text_from_file
from .utils import (
    cleanup_files,
    download_video_from_url,
    extract_audio_from_video_file,
    validate_file_type,
    validate_video_url,
)
from .web_text_extractor import extract_text_from_url
from .youtube_transcript import YouTubeTranscriptService

app = FastAPI(
    title="Video to Audio Extractor API",
    description="API for extracting audio from video files or YouTube URLs",
    version="1.0.0",
)

# Ensure temp directory exists
UPLOAD_DIR = "uploads"
TEMP_DIR = "temp"
Path(UPLOAD_DIR).mkdir(exist_ok=True)
Path(TEMP_DIR).mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="uploads"), name="static")


@app.post("/youtube/transcript")
async def get_youtube_transcript(request: YouTubeTranscriptRequest):
    """
    Robust YouTube transcript endpoint

    Returns:
    - Success with transcript if available
    - Detailed error message if no transcript found
    - List of available transcripts when requested
    """
    try:
        service = YouTubeTranscriptService()
        video_id = service.get_video_id(request.url)
        video_metadata = service.get_video_metadata(video_id)

        if not video_metadata["is_available"]:
            raise HTTPException(
                status_code=404, detail="Video is unavailable or private"
            )

        transcript, is_auto, language, error = service.fetch_transcript(
            video_id, request.language, request.prefer_manual
        )

        response = {
            "status": "success" if transcript else "no_transcript",
            "video_id": video_id,
            "language": language,
            "is_auto_generated": is_auto,
        }

        if transcript:
            response.update(
                {
                    "transcript": transcript,
                    "text": " ".join([t["text"] for t in transcript]),
                }
            )
        else:
            response["message"] = error or "No transcript available"

        if request.return_available:
            response["available_transcripts"] = service.get_available_transcripts(
                video_id
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/extract-website-text")
async def extract_website_text(request: URLRequest):
    """
    Extract clean text from a website URL

    Parameters:
    - url: Website URL (e.g., "https://example.com" or "example.com")

    Returns:
    - JSON with extracted text, title, and metadata
    """
    try:
        result = extract_text_from_url(request.url)
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.post("/extract-text")
async def extract_text(
    request: Request,
    file: Optional[UploadFile] = File(None),
    file_url: Optional[str] = Form(None),
):
    """Extract text from uploaded file or file URL"""
    try:
        temp_file_path = None
        try:
            if file:
                # Handle file upload
                temp_file_path = os.path.join(TEMP_DIR, file.filename)
                with open(temp_file_path, "wb") as buffer:
                    buffer.write(await file.read())
            elif file_url:
                # Handle file URL download
                validate_video_url(file_url)  # Reuse our URL validator
                temp_file_path = os.path.join(TEMP_DIR, f"temp_{uuid.uuid4().hex}")
                download_video_from_url(file_url, temp_file_path)
            else:
                raise HTTPException(
                    status_code=400, detail="Either file or file_url must be provided"
                )

            # Extract text from the file
            result = extract_text_from_file(temp_file_path)

            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "text": result["text"],
                    "file_type": result["file_type"],
                    "character_count": len(result["text"]),
                },
            )
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                cleanup_files([temp_file_path])

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction error: {str(e)}")


@app.post("/extract-audio/upload")
async def extract_audio_from_upload(
    request: Request,
    file: Optional[UploadFile] = File(None),
    video_url: Optional[str] = Form(None),
):
    """Extract audio from uploaded video file or video URL"""
    try:
        if file:
            # Handle file upload
            validate_file_type(file.filename)
            temp_video_path = os.path.join(TEMP_DIR, file.filename)

            # Save uploaded file temporarily
            with open(temp_video_path, "wb") as buffer:
                buffer.write(await file.read())

            # Generate unique filename for audio
            audio_filename = f"audio_{uuid.uuid4().hex}.mp3"
            output_audio_path = os.path.join(UPLOAD_DIR, audio_filename)

            # Extract audio
            extract_audio_from_video_file(temp_video_path, output_audio_path)

            # Clean up temporary video file
            cleanup_files([temp_video_path])

        elif video_url:
            # Handle video URL
            validate_video_url(video_url)

            # Generate unique filenames
            temp_video_path = os.path.join(TEMP_DIR, f"temp_{uuid.uuid4().hex}.mp4")
            audio_filename = f"audio_{uuid.uuid4().hex}.mp3"
            output_audio_path = os.path.join(UPLOAD_DIR, audio_filename)

            # Download video
            download_video_from_url(video_url, temp_video_path)

            # Extract audio
            extract_audio_from_video_file(temp_video_path, output_audio_path)

            # Clean up temporary video file
            cleanup_files([temp_video_path])

        else:
            raise HTTPException(
                status_code=400, detail="Either file or video_url must be provided"
            )

        # Return JSON response with audio URL
        base_url = str(request.base_url)
        audio_url = urljoin(base_url, f"static/{audio_filename}")
        audio_url = f"/uploads/{audio_filename}"
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Audio extracted successfully",
                "audio_url": audio_url,
                "filename": audio_filename,
            },
        )

    except InvalidFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidVideoURLError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AudioExtractionError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/extract-audio/youtube")
async def extract_audio_from_youtube(youtube_url: YouTubeURL):
    """Extract audio from YouTube video"""
    try:
        # Download YouTube video
        video_path = download_youtube_video(youtube_url.url, TEMP_DIR)

        # Extract audio
        audio_path = extract_audio_from_video_file(video_path)

        # Return the audio file
        return FileResponse(
            audio_path, media_type="audio/mpeg", filename=Path(audio_path).name
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Clean up temporary files
        if "video_path" in locals():
            cleanup_files([video_path])


@app.get("/uploads/{filename}")
async def get_audio_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/")
async def root():
    return {"message": "Video to Audio Extractor API is running"}
