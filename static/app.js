// API Base URL
const API_BASE = window.location.origin;

// DOM Elements
const urlInput = document.getElementById('urlInput');
const fetchInfoBtn = document.getElementById('fetchInfoBtn');
const infoSection = document.getElementById('infoSection');
const thumbnail = document.getElementById('thumbnail');
const videoTitle = document.getElementById('videoTitle');
const uploader = document.getElementById('uploader');
const duration = document.getElementById('duration');
const playlistInfo = document.getElementById('playlistInfo');
const qualitySelect = document.getElementById('qualitySelect');
const downloadBtn = document.getElementById('downloadBtn');
const activeDownloads = document.getElementById('activeDownloads');
const activeDownloadsList = document.getElementById('activeDownloadsList');
const filesList = document.getElementById('filesList');
const refreshFilesBtn = document.getElementById('refreshFilesBtn');

// State
let currentVideoInfo = null;
let activeDownloadConnections = new Map();

// Event Listeners
fetchInfoBtn.addEventListener('click', fetchVideoInfo);
downloadBtn.addEventListener('click', startDownload);
refreshFilesBtn.addEventListener('click', loadDownloadedFiles);

urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        fetchVideoInfo();
    }
});

// Fetch video info
async function fetchVideoInfo() {
    const url = urlInput.value.trim();

    if (!url) {
        alert('Please enter a YouTube URL');
        return;
    }

    fetchInfoBtn.disabled = true;
    fetchInfoBtn.textContent = 'Loading...';

    try {
        const response = await fetch(`${API_BASE}/api/info`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to fetch video info');
        }

        currentVideoInfo = await response.json();
        displayVideoInfo(currentVideoInfo);
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        fetchInfoBtn.disabled = false;
        fetchInfoBtn.textContent = 'Get Info';
    }
}

// Display video info
function displayVideoInfo(info) {
    infoSection.classList.remove('hidden');

    // Set thumbnail
    if (info.thumbnail) {
        thumbnail.src = info.thumbnail;
        thumbnail.style.display = 'block';
    } else {
        thumbnail.style.display = 'none';
    }

    // Set title
    videoTitle.textContent = info.title;

    // Set uploader
    uploader.textContent = info.uploader || 'Unknown';

    // Set duration
    if (info.duration) {
        const minutes = Math.floor(info.duration / 60);
        const seconds = info.duration % 60;
        duration.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    } else {
        duration.textContent = '';
    }

    // Set playlist info
    if (info.is_playlist) {
        playlistInfo.textContent = `Playlist (${info.video_count} videos)`;
        playlistInfo.style.display = 'inline';
    } else {
        playlistInfo.style.display = 'none';
    }

    // Populate quality options
    qualitySelect.innerHTML = '<option value="best">Best Quality</option>';

    if (info.formats && info.formats.length > 0) {
        info.formats.forEach(format => {
            const option = document.createElement('option');
            option.value = format.resolution;
            option.textContent = format.resolution;
            qualitySelect.appendChild(option);
        });
    } else {
        // Add common quality options as fallback
        ['1080p', '720p', '480p', '360p'].forEach(quality => {
            const option = document.createElement('option');
            option.value = quality;
            option.textContent = quality;
            qualitySelect.appendChild(option);
        });
    }
}

// Start download
async function startDownload() {
    const url = urlInput.value.trim();
    const quality = qualitySelect.value;

    if (!currentVideoInfo) {
        alert('Please fetch video info first');
        return;
    }

    downloadBtn.disabled = true;
    downloadBtn.textContent = 'Starting...';

    try {
        const response = await fetch(`${API_BASE}/api/download`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url,
                quality,
                is_playlist: currentVideoInfo.is_playlist,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start download');
        }

        const result = await response.json();

        // Add to active downloads
        addActiveDownload(result.download_id, currentVideoInfo.title);

        // Connect WebSocket for real-time updates
        connectWebSocket(result.download_id);

        // Reset form
        urlInput.value = '';
        infoSection.classList.add('hidden');
        currentVideoInfo = null;

        alert('Download started! Check the Active Downloads section.');
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        downloadBtn.disabled = false;
        downloadBtn.textContent = 'Start Download';
    }
}

// Add active download to UI
function addActiveDownload(downloadId, title) {
    activeDownloads.classList.remove('hidden');

    const downloadItem = document.createElement('div');
    downloadItem.className = 'download-item';
    downloadItem.id = `download-${downloadId}`;

    downloadItem.innerHTML = `
        <div class="download-header">
            <div class="download-title">${title}</div>
            <div class="download-status status-downloading">Starting...</div>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: 0%"></div>
        </div>
        <div class="progress-info">
            <span class="progress-percent">0%</span>
            <span class="progress-speed"></span>
        </div>
    `;

    activeDownloadsList.appendChild(downloadItem);
}

// Connect WebSocket for real-time updates
function connectWebSocket(downloadId) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/${downloadId}`;

    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateDownloadProgress(downloadId, data);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
        activeDownloadConnections.delete(downloadId);
    };

    activeDownloadConnections.set(downloadId, ws);
}

// Update download progress
function updateDownloadProgress(downloadId, data) {
    const downloadItem = document.getElementById(`download-${downloadId}`);
    if (!downloadItem) return;

    const statusElement = downloadItem.querySelector('.download-status');
    const progressFill = downloadItem.querySelector('.progress-fill');
    const progressPercent = downloadItem.querySelector('.progress-percent');
    const progressSpeed = downloadItem.querySelector('.progress-speed');

    // Update status
    statusElement.className = `download-status status-${data.status}`;
    statusElement.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);

    // Update progress
    if (data.progress !== undefined) {
        progressFill.style.width = `${data.progress}%`;
        progressPercent.textContent = `${data.progress.toFixed(1)}%`;
    }

    // Update speed and ETA
    if (data.speed) {
        progressSpeed.textContent = `${data.speed} • ETA: ${data.eta || 'N/A'}`;
    }

    // If completed, refresh files list and remove from active after 3 seconds
    if (data.status === 'completed') {
        setTimeout(() => {
            downloadItem.remove();
            if (activeDownloadsList.children.length === 0) {
                activeDownloads.classList.add('hidden');
            }
            loadDownloadedFiles();
        }, 3000);
    }

    // If failed, keep it but close WebSocket
    if (data.status === 'failed') {
        const ws = activeDownloadConnections.get(downloadId);
        if (ws) {
            ws.close();
        }
        progressSpeed.textContent = data.error || 'Download failed';
    }
}

// Load downloaded files
async function loadDownloadedFiles() {
    try {
        const response = await fetch(`${API_BASE}/api/downloads`);
        const files = await response.json();

        if (files.length === 0) {
            filesList.innerHTML = '<p class="empty-message">No downloads yet</p>';
            return;
        }

        filesList.innerHTML = files.map(file => `
            <div class="file-item">
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-meta">
                        ${formatFileSize(file.size)} • ${new Date(file.modified).toLocaleString()}
                    </div>
                </div>
                <div class="file-actions">
                    <a href="${API_BASE}/api/download-file/${encodeURIComponent(file.name)}"
                       class="btn-download"
                       download="${file.name}">
                        Download
                    </a>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading files:', error);
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Load files on page load
loadDownloadedFiles();
