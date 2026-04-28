# RusTrans - Offline Subtitle Generator

A desktop application for generating English or Finnish subtitles from Russian SRT files or video files, using local AI models (no internet required).

## Features

- Translate Russian SRT subtitles to English (offline)
- Translate Russian SRT subtitles to Finnish (offline)
- Extract audio from video and transcribe speech (Russian)
- 100% offline - no API calls or internet needed
- Clean, modern GUI interface
- CLI support for batch processing

## Tech Stack

- **Translation**: Argos Translate (offline ML)
- **Transcription**: Faster Whisper (local Whisper)
- **GUI**: CustomTkinter
- **Packaging**: PyInstaller

## Installation

1. Clone the repository
2. Create virtual environment: `python -m venv .venv`
3. Activate: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Install language models:
   - Argos: `argospm install translate-ru_to_en` (Russian → English)
   - Argos: `argospm install translate-ru_to_fi` (Russian → Finnish)
   - Whisper: Models auto-download on first use

## Usage

### GUI

```bash
python gui.py
```

### CLI

```bash
# Translate SRT file
python main.py --input subtitles.ru.srt

# Process video (extract audio + transcribe + save as .ru.srt)
python main.py --input video.mkv

# Process folder with SRT files
python main.py --input /path/to/folder
```

## Requirements

- Python 3.10+
- ffmpeg (must be in PATH) - [Download](https://ffmpeg.org/download.html)

## License

MIT