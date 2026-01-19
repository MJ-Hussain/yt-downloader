#!/bin/bash

echo "Starting YouTube Downloader..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000
