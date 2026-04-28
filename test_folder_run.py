from pathlib import Path
from app.pipeline import process_video_folder

process_video_folder(Path("Season 1"), target_lang="fi")