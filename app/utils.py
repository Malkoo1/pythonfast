import os
import shutil
import uuid
from pathlib import Path
from typing import List

# import pytesseract
import requests
from moviepy.editor import VideoFileClip
from pytube import YouTube


def extract_audio_from_video_file(video_path: str, output_path: str) -> str:
    """Extract audio from video file and save to specified output path"""
    try:
        video = VideoFileClip(video_path)
        # Write audio file
        video.audio.write_audiofile(output_path)
        return output_path
    except Exception as e:
        raise AudioExtractionError(f"Failed to extract audio: {str(e)}")
    finally:
        if "video" in locals():
            video.close()


def download_video_from_url(url: str, output_path: str) -> str:
    """Download video from URL (YouTube or direct link)"""
    try:
        if "youtube.com" in url or "youtu.be" in url:
            # YouTube video
            yt = YouTube(url)

            # Get the highest resolution progressive stream
            stream = (
                yt.streams.filter(progressive=True, file_extension="mp4")
                .order_by("resolution")
                .desc()
                .first()
            )

            if not stream:
                raise ValueError("No suitable video stream found")

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Download the video
            return stream.download(
                output_path=os.path.dirname(output_path),
                filename=os.path.basename(output_path),
                skip_existing=False,
            )
        else:
            # Direct video URL
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            with requests.get(
                url, headers=headers, stream=True, timeout=10
            ) as response:
                response.raise_for_status()

                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive chunks
                            f.write(chunk)
            return output_path

    except Exception as e:
        raise ValueError(f"Video download failed: {str(e)}")


def validate_video_url(url: str) -> None:
    """Validate that the URL is a supported video URL"""
    if not url.startswith(("http://", "https://")):
        raise InvalidVideoURLError("Invalid URL format")
    # Add more validation as needed


def download_youtube_video(url: str, output_dir: str) -> str:
    """Download YouTube video and return local path"""
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension="mp4").first()

        if not stream:
            raise ValueError("No suitable video stream found")

        # Download the video
        output_path = stream.download(output_path=output_dir)
        return output_path
    except Exception as e:
        raise ValueError(f"YouTube download failed: {str(e)}")


def validate_file_type(filename: str) -> None:
    """Validate that the file is a supported video type"""
    allowed_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    file_ext = Path(filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise InvalidFileTypeError(
            f"File type {file_ext} not supported. Allowed types: {', '.join(allowed_extensions)}"
        )


def cleanup_files(file_paths: List[str]) -> None:
    """Clean up temporary files"""
    for path in file_paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"Error cleaning up file {path}: {e}")


# def setup_tesseract():
#     """Configure Tesseract OCR path if needed"""
#     try:
#         # On Windows, you might need to specify the Tesseract path
#         if os.name == "nt":
#             pytesseract.pytesseract.tesseract_cmd = (
#                 r"C:\Program Files\Tesseract-OCR\tesseract.exe"
#             )
#     except Exception as e:
#         print(f"Tesseract configuration warning: {str(e)}")
