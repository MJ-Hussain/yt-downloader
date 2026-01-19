# Copilot instructions (yt-downloader)

## Big picture
- This is a single-process FastAPI backend serving a static vanilla JS UI.
- Backend: [app/main.py](app/main.py) wires routes + WebSocket and uses an in-memory `YouTubeDownloader` instance.
- Downloader: [app/downloader.py](app/downloader.py) wraps `yt-dlp` and writes finished media to `downloads/`.
- Frontend: [static/index.html](static/index.html), [static/app.js](static/app.js), [static/style.css](static/style.css) call the API and subscribe to progress updates.

## Run / debug (Linux)
- Quick start: `./run.sh` (creates `.venv/`, installs deps, runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`).
- Manual:
  - `python3 -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
  - `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Runtime config is in [.env](.env) and loaded via `python-dotenv` (PORT/HOST/NGROK_AUTHTOKEN).
- External dependency: `ffmpeg` must be installed for `yt-dlp` merging.

## Request/data flow
- UI calls `POST /api/info` → `YouTubeDownloader.get_video_info(url)` returns either a playlist summary or video formats.
- UI calls `POST /api/download` → server spawns `asyncio.create_task(downloader.download(...))` and returns a UUID `download_id`.
- UI opens `WebSocket /ws/{download_id}` and updates progress bars from JSON messages.
- UI lists files via `GET /api/downloads` and downloads via `GET /api/download-file/{filename}`.

## Project conventions / gotchas
- Keep Pydantic contracts in sync: when changing payloads, update both [app/models.py](app/models.py) and the frontend parsing in [static/app.js](static/app.js).
- Download progress is process-local (`YouTubeDownloader.active_downloads`); restarting the server loses active statuses.
- Quality selection is mapped in `YouTubeDownloader._get_format_string(quality)`; frontend sends values like `"1080p"` or `"best"`.
- Downloads are named by title (`outtmpl: %(title)s.%(ext)s`) and stored under `downloads/`.
- Ngrok note: the ngrok startup/printing lives under `if __name__ == "__main__":` in [app/main.py](app/main.py). When you run via `uvicorn app.main:app` (as `run.sh` does), that block does not execute.

## Where to make changes
- API routes / WebSocket behavior: [app/main.py](app/main.py)
- yt-dlp options, format filtering, file listing: [app/downloader.py](app/downloader.py)
- Request/response schemas: [app/models.py](app/models.py)
- UI behavior and endpoint wiring: [static/app.js](static/app.js)
