import yt_dlp
import os
import asyncio
from typing import Dict, Callable, Optional, List
from pathlib import Path


class YouTubeDownloader:
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.active_downloads: Dict[str, dict] = {}

    def get_video_info(self, url: str) -> dict:
        """Get video or playlist information without downloading"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)

                # Check if it's a playlist
                is_playlist = 'entries' in info

                if is_playlist:
                    return {
                        'title': info.get('title', 'Playlist'),
                        'is_playlist': True,
                        'video_count': len(list(info['entries'])),
                        'uploader': info.get('uploader', 'Unknown'),
                        'thumbnail': info.get('thumbnail'),
                        'formats': []
                    }
                else:
                    # Extract available formats
                    formats = []
                    seen_resolutions = set()

                    if 'formats' in info:
                        for fmt in info['formats']:
                            resolution = fmt.get('resolution', 'Unknown')
                            height = fmt.get('height')

                            # Only include video formats with audio or combined formats
                            if height and height >= 360:
                                res_label = f"{height}p"
                                if res_label not in seen_resolutions:
                                    formats.append({
                                        'format_id': fmt['format_id'],
                                        'resolution': res_label,
                                        'ext': fmt.get('ext', 'mp4'),
                                        'filesize': fmt.get('filesize')
                                    })
                                    seen_resolutions.add(res_label)

                    # Sort by resolution (descending)
                    formats.sort(key=lambda x: int(x['resolution'].replace('p', '')), reverse=True)

                    return {
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration'),
                        'thumbnail': info.get('thumbnail'),
                        'uploader': info.get('uploader', 'Unknown'),
                        'is_playlist': False,
                        'formats': formats[:10]  # Limit to top 10 formats
                    }
            except Exception as e:
                raise Exception(f"Failed to extract video info: {str(e)}")

    def _get_format_string(self, quality: str) -> str:
        """Convert quality string to yt-dlp format string"""
        quality_map = {
            '2160p': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
            '1440p': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            'best': 'bestvideo+bestaudio/best',
        }
        return quality_map.get(quality, 'bestvideo+bestaudio/best')

    async def download(
        self,
        url: str,
        download_id: str,
        quality: str = "best",
        is_playlist: bool = False,
        progress_callback: Optional[Callable] = None
    ):
        """Download video or playlist asynchronously"""
        # Get the current event loop to use in the thread
        loop = asyncio.get_event_loop()

        def progress_hook(d):
            if progress_callback:
                status_update = {
                    'download_id': download_id,
                    'status': 'downloading',
                    'progress': 0,
                    'speed': None,
                    'eta': None,
                    'filename': None
                }

                if d['status'] == 'downloading':
                    # Calculate progress percentage
                    if 'total_bytes' in d:
                        progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    elif 'total_bytes_estimate' in d:
                        progress = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                    else:
                        progress = 0

                    status_update['progress'] = round(progress, 2)
                    status_update['speed'] = d.get('_speed_str', 'N/A')
                    status_update['eta'] = d.get('_eta_str', 'N/A')
                    status_update['filename'] = os.path.basename(d.get('filename', ''))

                elif d['status'] == 'finished':
                    status_update['status'] = 'processing'
                    status_update['progress'] = 100
                    status_update['filename'] = os.path.basename(d.get('filename', ''))

                # Schedule the coroutine in the main event loop from this thread
                asyncio.run_coroutine_threadsafe(progress_callback(status_update), loop)

        ydl_opts = {
            'format': self._get_format_string(quality),
            'outtmpl': str(self.download_dir / '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'merge_output_format': 'mp4',
            'postprocessor_args': ['-c:v', 'copy', '-c:a', 'aac'],
        }

        if not is_playlist:
            ydl_opts['noplaylist'] = True

        try:
            # Update status
            self.active_downloads[download_id] = {
                'status': 'starting',
                'progress': 0
            }

            # Run download in executor to avoid blocking
            await loop.run_in_executor(
                None,
                self._download_sync,
                url,
                ydl_opts
            )

            # Update final status
            self.active_downloads[download_id] = {
                'status': 'completed',
                'progress': 100
            }

            if progress_callback:
                await progress_callback({
                    'download_id': download_id,
                    'status': 'completed',
                    'progress': 100
                })

        except Exception as e:
            self.active_downloads[download_id] = {
                'status': 'failed',
                'error': str(e)
            }
            if progress_callback:
                await progress_callback({
                    'download_id': download_id,
                    'status': 'failed',
                    'error': str(e),
                    'progress': 0
                })
            raise

    def _download_sync(self, url: str, ydl_opts: dict):
        """Synchronous download function to run in executor"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def get_download_status(self, download_id: str) -> Optional[dict]:
        """Get current status of a download"""
        return self.active_downloads.get(download_id)

    def get_downloaded_files(self) -> List[dict]:
        """Get list of all downloaded files"""
        files = []
        for file_path in self.download_dir.iterdir():
            if file_path.is_file():
                # Skip temporary files (.part, .ytdl, etc.)
                if file_path.suffix in ['.part', '.ytdl', '.temp']:
                    continue
                # Skip individual stream files (f123.mp4, f456.webm, etc.)
                if file_path.stem.endswith(tuple(f'.f{i}' for i in range(1000))):
                    continue
                # Skip hidden files
                if file_path.name.startswith('.'):
                    continue

                stat = file_path.stat()
                files.append({
                    'name': file_path.name,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
        return sorted(files, key=lambda x: x['modified'], reverse=True)
