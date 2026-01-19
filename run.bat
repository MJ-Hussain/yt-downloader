@echo off
echo Starting YouTube Downloader...

REM Check if virtual environment exists
if not exist ".venv\" (
    echo Virtual environment not found. Creating one...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000
