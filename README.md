# 🎬 YouTube Downloader

A modern, web-based YouTube video and playlist downloader with custom quality selection and real-time progress tracking. Built with FastAPI and yt-dlp.

## ✨ Features

- 📹 **Download single videos** with custom quality selection
- 📑 **Download entire playlists** automatically
- 🎯 **Quality selection** (2160p, 1440p, 1080p, 720p, 480p, 360p, or best)
- 📊 **Real-time progress tracking** using WebSocket
- 🌐 **Web-based interface** - clean and responsive UI
- 🔗 **Public shareable links** via ngrok integration (optional)
- 📦 **File management** - view and download completed files
- 💻 **Cross-platform** - works on Windows, Linux, and macOS

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+**
- **ffmpeg** (required for merging video and audio streams)

### Installing ffmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
You need `ffmpeg` available on your `PATH` (required for merging video+audio streams).

#### Option A: Install via winget (recommended)
1. Open **PowerShell**.
2. Check winget is available:
  ```powershell
  winget --version
  ```
3. Install ffmpeg:
  ```powershell
  winget install --id Gyan.FFmpeg -e
  ```
4. Close the terminal and open a **new** PowerShell (PATH refresh).
5. Verify:
  ```powershell
  ffmpeg -version
  where.exe ffmpeg
  ```

#### Option B: Manual install (no package manager)
1. Download an ffmpeg build (e.g. “release essentials”) from:
  - https://www.gyan.dev/ffmpeg/builds/
2. Unzip it to a simple folder, for example:
  - `C:\ffmpeg\`
3. Locate the `bin` folder that contains `ffmpeg.exe` (typically `C:\ffmpeg\bin`).
4. Add it to PATH:
  - Press **Win + S** → search **Environment Variables**
  - Open **Edit the system environment variables**
  - Click **Environment Variables…**
  - Under **User variables** (or **System variables**), select **Path** → **Edit** → **New**
  - Add: `C:\ffmpeg\bin`
  - Click **OK** to close all dialogs
5. Close all terminals (and if needed VS Code) and open a new PowerShell.
6. Verify:
  ```powershell
  ffmpeg -version
  where.exe ffmpeg
  ```

#### Common gotcha
If you install ffmpeg while the server is already running, the running `uvicorn` process may not see the updated PATH. Stop the server (`Ctrl + C`) and restart `run.bat` after installing ffmpeg.

## 🚀 Installation

1. **Clone the repository:**
```bash
cd /home/mj-hussain/Git/yt-downloader
```

2. **Create a virtual environment:**
```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
Edit the `.env` file:
```env
PORT=8000
HOST=127.0.0.1
NGROK_AUTHTOKEN=your_ngrok_token_here  # Optional: for public access
```

> Tip: `127.0.0.1` (localhost) is local-only. If you want to access the app from another device on your WiFi/LAN, set `HOST=0.0.0.0`.

### Getting ngrok Auth Token (Optional)

For public shareable links:

1. Sign up at [ngrok.com](https://ngrok.com)
2. Get your auth token from the [dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)
3. Add it to `.env` file

## 🎯 Usage

### Starting the Server

**Linux/macOS:**
```bash
./run.sh
```

**Windows:**
```bash
run.bat
```

**Or manually:**
```bash
# Linux/macOS
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Windows
.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

> Want LAN access? Use `--host 0.0.0.0` and open `http://<your-ip>:8000` from other devices.

### Accessing the Application

> Note: `0.0.0.0` is a **bind address** (listen on all interfaces), not a URL you can open in a browser. If the server prints `0.0.0.0:8000`, open `http://localhost:8000` on the same machine, or `http://<your-ip>:8000` from another device.

After starting the server, you'll see:

```
🚀 YouTube Downloader Server Starting...
====================================================================

🌍 Public URL (ngrok): https://abc123.ngrok.io  # If ngrok is configured
📍 Local Network: http://192.168.1.100:8000
📍 Localhost: http://localhost:8000

====================================================================
```

- **Localhost**: Access from same machine
- **Local Network**: Share with devices on same WiFi
- **Public URL**: Share with anyone, anywhere (requires ngrok)

### Using the Application

1. **Paste a YouTube URL** (video or playlist)
2. **Click "Get Info"** to fetch video details
3. **Select quality** from the dropdown
4. **Click "Start Download"**
5. **Monitor progress** in real-time
6. **Download files** from the "Downloaded Files" section

## 📁 Project Structure

```
yt-downloader/
├── app/
│   ├── main.py           # FastAPI application & routes
│   ├── downloader.py     # yt-dlp integration
│   └── models.py         # Pydantic data models
├── static/
│   ├── index.html        # Web UI
│   ├── style.css         # Styling
│   └── app.js            # Frontend JavaScript
├── downloads/            # Downloaded videos (auto-created)
├── requirements.txt      # Python dependencies
├── .env                  # Configuration
└── README.md
```

## 🔧 API Endpoints

### `POST /api/info`
Get video or playlist information
```json
{
  "url": "https://youtube.com/watch?v=..."
}
```

### `POST /api/download`
Start a download
```json
{
  "url": "https://youtube.com/watch?v=...",
  "quality": "1080p",
  "is_playlist": false
}
```

### `GET /api/status/{download_id}`
Get download status

### `WebSocket /ws/{download_id}`
Real-time progress updates

### `GET /api/downloads`
List all downloaded files

### `GET /api/download-file/{filename}`
Download a file

## 🐛 Troubleshooting

### "yt-dlp: command not found"
Make sure you installed the requirements:
```bash
pip install -r requirements.txt
```

### "ffmpeg not found"
Install ffmpeg (see Prerequisites section)

### "Unable to extract video data"
- Check if the URL is valid
- Try updating yt-dlp: `pip install -U yt-dlp`
- Some videos may be region-restricted or age-restricted

### WebSocket connection issues
- Make sure you're accessing via the correct protocol (http/https)
- Check firewall settings if accessing from another device

### ngrok not working
- Verify your auth token is correct in `.env`
- Free ngrok accounts have session limits

## 🔒 Security Notes

- This application is intended for **personal use** and **legal downloads only**
- Respect copyright laws and YouTube's Terms of Service
- Downloads are stored locally in the `downloads/` folder
- When sharing via ngrok, anyone with the link can access your server

## 📝 License

MIT License - feel free to use this project for personal or educational purposes.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 💡 Tips

- **Playlist downloads**: Can take a while depending on the number of videos
- **Quality selection**: "Best" will download the highest available quality
- **Storage**: Downloaded videos are saved in the `downloads/` folder
- **Network access**: Share your local IP with others on the same WiFi network

## 🙏 Credits

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Tunneling via [ngrok](https://ngrok.com)

---

**Enjoy downloading!** 🎉
