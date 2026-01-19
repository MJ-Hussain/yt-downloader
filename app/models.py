from pydantic import BaseModel
from typing import List, Optional


class VideoInfoRequest(BaseModel):
    url: str


class FormatInfo(BaseModel):
    format_id: str
    resolution: str
    ext: str
    filesize: Optional[int] = None


class VideoInfo(BaseModel):
    title: str
    duration: Optional[int]
    thumbnail: Optional[str]
    uploader: Optional[str]
    is_playlist: bool
    video_count: Optional[int] = None
    formats: List[FormatInfo] = []


class DownloadRequest(BaseModel):
    url: str
    quality: str = "best"  # Can be: best, 1080p, 720p, 480p, 360p, etc.
    is_playlist: bool = False


class DownloadResponse(BaseModel):
    download_id: str
    status: str
    message: str


class DownloadStatus(BaseModel):
    download_id: str
    status: str  # starting, downloading, processing, completed, failed
    progress: float
    speed: Optional[str] = None
    eta: Optional[str] = None
    filename: Optional[str] = None
    error: Optional[str] = None


class FileInfo(BaseModel):
    name: str
    size: int
    modified: str
