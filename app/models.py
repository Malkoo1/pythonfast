from typing import Optional

from pydantic import BaseModel, HttpUrl


class YouTubeURL(BaseModel):
    url: str


class VideoURL(BaseModel):
    url: str


class URLRequest(BaseModel):
    url: str


class YouTubeTranscriptRequest(BaseModel):
    url: str
    language: Optional[str] = "en"
    prefer_manual: Optional[bool] = True
    return_available: Optional[bool] = True
