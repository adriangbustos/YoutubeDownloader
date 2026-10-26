# YouTube Downloader Pro

A modern, high-performance desktop application built with Python, CustomTkinter, and `yt-dlp` to download YouTube videos in up to 1080p Full HD, extract high-bitrate MP3 audio, and grab clean plain-text transcripts in batch queue mode.

![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- **Full HD (1080p) & Best Quality Downloads**: Automatic adaptive stream merging (`video + audio`) powered by FFmpeg.
- **Audio Extraction**: Single-click conversion to MP3 (192 kbps).
- **Clean Transcript Extractor**: Downloads video subtitles/transcripts exclusively in the speaker's original language, automatically cleans formatting/timestamps, and outputs a ready-to-read `.txt` file.
- **Batch Download Queue**: Paste multiple URLs (one per line) to process an entire queue unattended.
- **Custom Output Folder**: Select any export destination on your drive via native Windows dialogs.
- **Modern Dark/Light UI**: Built with CustomTkinter for sleek aesthetics and native system theme integration.
- **Standalone Build Support**: Can be run from source or compiled into a single `.exe` using PyInstaller.

---

## Directory Structure

```
YoutubeDownloader/
├── downloader.py          # Main application and UI code
├── iniciar.bat            # Windows 1-click venv bootstrapper & launcher
├── requirements.txt       # Python dependencies (customtkinter, yt-dlp)
├── icon.ico               # High-res multi-size application icon
├── .gitignore             # Comprehensive VCS exclusion rules
└── README.md              # Project documentation
```

---

## Prerequisites

1. **Python 3.10 or higher**: Ensure Python is added to your system `PATH`.
2. **FFmpeg & FFprobe**: Required for merging 1080p video streams and extracting audio. Place `ffmpeg.exe` and `ffprobe.exe` in the application directory or install them system-wide in `PATH`.

---

## Installation & Running

### Option 1: Quick Start (Windows)
Double-click `iniciar.bat`. It will automatically configure the virtual environment, install requirements, and start the app without opening a command prompt.

### Option 2: Manual Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/adriangbustos/YoutubeDownloader.git
   cd YoutubeDownloader
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On Windows (CMD):
   call venv\Scripts\activate.bat
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application:**
   ```bash
   python downloader.py
   ```

---

## Compiling to Standalone `.exe`

To package the application into a standalone Windows executable:

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --icon icon.ico --add-data "icon.ico;." --name YouTubeDownloader --collect-all customtkinter --collect-all yt_dlp downloader.py
```

The compiled binary will be placed inside the `dist/` directory.

---

## License

This project is licensed under the [MIT License](LICENSE).
