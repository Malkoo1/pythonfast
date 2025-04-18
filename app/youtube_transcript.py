from typing import Dict, List, Optional, Tuple, Union

from pytube import YouTube
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)


class YouTubeTranscriptService:
    @staticmethod
    def get_video_id(url: str) -> str:
        """Extract video ID from YouTube URL"""
        if "youtu.be" in url:
            return url.split("/")[-1]
        elif "youtube.com" in url:
            if "v=" in url:
                return url.split("v=")[1].split("&")[0]
            elif "youtu.be" in url:
                return url.split("/")[-1]
        return url

    @staticmethod
    def get_video_metadata(video_id: str) -> Dict:
        """Get YouTube video metadata"""
        try:
            yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            return {
                "is_available": True,
            }
        except Exception as e:
            return {"title": "Unknown", "is_available": False, "error": str(e)}

    @staticmethod
    def get_available_transcripts(video_id: str) -> List[Dict]:
        """Get list of available transcripts"""
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            return [
                {
                    "language": t.language,
                    "language_code": t.language_code,
                    "is_generated": t.is_generated,
                }
                for t in transcript_list
            ]
        except Exception:
            return []

    @staticmethod
    def fetch_transcript(
        video_id: str, language: str = "en", prefer_manual: bool = True
    ) -> Tuple[Optional[List[Dict]], bool, str, Optional[str]]:
        """
        Fetch transcript with comprehensive error handling

        Returns:
            tuple: (transcript, is_auto_generated, language_code, error_message)
        """
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            if prefer_manual:
                try:
                    transcript = transcript_list.find_manually_created_transcript(
                        [language]
                    )
                    return transcript.fetch(), False, language, None
                except:
                    try:
                        transcript = transcript_list.find_generated_transcript(
                            [language]
                        )
                        return transcript.fetch(), True, language, None
                    except:
                        pass

            for transcript in transcript_list:
                try:
                    return (
                        transcript.fetch(),
                        transcript.is_generated,
                        transcript.language_code,
                        None,
                    )
                except:
                    continue

            return None, False, language, "No suitable transcript found"

        except VideoUnavailable:
            return None, False, language, "Video is unavailable or private"
        except TranscriptsDisabled:
            return None, False, language, "Transcripts are disabled for this video"
        except NoTranscriptFound:
            return None, False, language, "No transcripts found for this video"
        except Exception as e:
            return None, False, language, f"Error fetching transcript: {str(e)}"
