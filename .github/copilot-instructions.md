# Copilot instructions (yt-downloader)

## Big picture
- Single-process FastAPI backend that also serves a vanilla JS UI.
- API + WebSocket live in [app/main.py](../app/main.py) (CORS enabled, `/` serves `static/index.html`, `/static/*` is mounted).
- Download engine lives in [app/downloader.py](../app/downloader.py): wraps `yt-dlp`, writes finished media to `downloads/`, tracks progress/status in-memory.
- UI is static files ([static/index.html](../static/index.html), [static/app.js](../static/app.js), [static/style.css](../static/style.css)) and talks to the API on the same origin (`window.location.origin`).

## Run / debug
- Quick start (Windows): `run.bat` (creates `.venv/`, installs deps, runs `uvicorn app.main:app ...`).
- Quick start (Linux/macOS): `./run.sh`.
- Manual:
  - Create/activate venv, then `pip install -r requirements.txt`
  - Run: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Runtime config comes from `.env` via `python-dotenv` (at import time in [app/main.py](../app/main.py)).
- External dependency: `ffmpeg` must be installed and on `PATH` for `yt-dlp` merging.
- Ngrok note: the ngrok connect + “startup banner” runs only when executing [app/main.py](../app/main.py) as a script (`python -m app.main`). When using `uvicorn app.main:app` (including `run.sh`/`run.bat`), that block does not run.

## Request / data flow
- `POST /api/info` with `{ "url": "..." }` → `YouTubeDownloader.get_video_info()` returns either:
  - playlist summary (`is_playlist: true`, `video_count`, no formats), or
  - single-video metadata + up to 10 unique `height`-based format options.
- `POST /api/download` with `{url, quality, is_playlist}` → returns a UUID `download_id` and starts a background task (`asyncio.create_task`).
- WebSocket `GET /ws/{download_id}` → server pushes JSON status updates (`downloading`, `processing`, `completed`, `failed`) to the UI.
- File management: `GET /api/downloads` lists files, `GET /api/download-file/{filename}` streams a specific file.

## Project conventions / gotchas
- Keep request/response contracts in sync across [app/models.py](../app/models.py) and the frontend handling in [static/app.js](../static/app.js).
- Download status is process-local (`YouTubeDownloader.active_downloads`); restarting the server loses active statuses.
- Quality strings are user-facing values like `"1080p"` / `"best"` and are mapped in `YouTubeDownloader._get_format_string()`; selection prefers H.264 (`vcodec^=avc1`) + AAC/m4a for compatibility.
- Output naming uses yt-dlp `outtmpl: %(title)s.%(ext)s` into `downloads/`; be careful if changing naming/sanitization (Windows filename constraints).
- Progress updates come from a `yt-dlp` progress hook (runs in a worker thread) and are forwarded back to the main asyncio loop via `asyncio.run_coroutine_threadsafe`.

## Where to make changes
- API routes + WebSocket behavior: [app/main.py](../app/main.py)
- yt-dlp options, format selection, progress hook, file listing/filtering: [app/downloader.py](../app/downloader.py)
- Pydantic schemas: [app/models.py](../app/models.py)
- UI behavior and endpoint wiring: [static/app.js](../static/app.js)
