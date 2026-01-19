from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import asyncio
from typing import Dict
import uuid

from app.models import (
    VideoInfoRequest,
    VideoInfo,
    DownloadRequest,
    DownloadResponse,
    DownloadStatus,
    FileInfo
)
from app.downloader import YouTubeDownloader

# Load environment variables
load_dotenv()

app = FastAPI(title="YouTube Downloader API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize downloader
downloader = YouTubeDownloader()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, download_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[download_id] = websocket

    def disconnect(self, download_id: str):
        if download_id in self.active_connections:
            del self.active_connections[download_id]

    async def send_update(self, download_id: str, data: dict):
        if download_id in self.active_connections:
            try:
                await self.active_connections[download_id].send_json(data)
            except:
                self.disconnect(download_id)


manager = ConnectionManager()


@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")


@app.post("/api/info", response_model=VideoInfo)
async def get_video_info(request: VideoInfoRequest):
    """Get information about a video or playlist"""
    try:
        info = downloader.get_video_info(request.url)
        return VideoInfo(**info)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/download", response_model=DownloadResponse)
async def start_download(request: DownloadRequest):
    """Start downloading a video or playlist"""
    download_id = str(uuid.uuid4())

    async def progress_callback(status_update):
        await manager.send_update(download_id, status_update)

    # Start download in background
    asyncio.create_task(
        downloader.download(
            url=request.url,
            download_id=download_id,
            quality=request.quality,
            is_playlist=request.is_playlist,
            progress_callback=progress_callback
        )
    )

    return DownloadResponse(
        download_id=download_id,
        status="started",
        message="Download started successfully"
    )


@app.get("/api/status/{download_id}", response_model=DownloadStatus)
async def get_download_status(download_id: str):
    """Get the current status of a download"""
    status = downloader.get_download_status(download_id)

    if not status:
        raise HTTPException(status_code=404, detail="Download not found")

    return DownloadStatus(
        download_id=download_id,
        status=status.get('status', 'unknown'),
        progress=status.get('progress', 0),
        speed=status.get('speed'),
        eta=status.get('eta'),
        filename=status.get('filename'),
        error=status.get('error')
    )


@app.websocket("/ws/{download_id}")
async def websocket_endpoint(websocket: WebSocket, download_id: str):
    """WebSocket endpoint for real-time download progress"""
    await manager.connect(download_id, websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(download_id)


@app.get("/api/downloads")
async def list_downloads():
    """List all downloaded files"""
    files = downloader.get_downloaded_files()
    return [
        FileInfo(
            name=f['name'],
            size=f['size'],
            modified=datetime.fromtimestamp(f['modified']).isoformat()
        )
        for f in files
    ]


@app.get("/api/download-file/{filename}")
async def download_file(filename: str):
    """Download a file to the user's device"""
    file_path = Path("downloads") / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 8000))
    HOST = os.getenv("HOST", "0.0.0.0")

    print("\n" + "="*60)
    print("🎬 YouTube Downloader Server Starting...")
    print("="*60)

    # Try to start ngrok if token is available
    ngrok_token = os.getenv("NGROK_AUTHTOKEN")
    if ngrok_token:
        try:
            from pyngrok import ngrok, conf
            conf.get_default().auth_token = ngrok_token
            public_url = ngrok.connect(PORT)
            print(f"\n🌍 Public URL (ngrok): {public_url}")
        except Exception as e:
            print(f"\n⚠️  Failed to start ngrok: {e}")
            print("Continuing with local access only...")
    else:
        print("\n💡 Tip: Add NGROK_AUTHTOKEN to .env for public access")

    # Get local IP
    import socket
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
        print(f"\n📍 Local Network: http://{local_ip}:{PORT}")
    except:
        pass

    print(f"📍 Localhost: http://localhost:{PORT}")
    print("\n" + "="*60 + "\n")

    uvicorn.run(app, host=HOST, port=PORT)
