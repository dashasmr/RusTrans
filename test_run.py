from pathlib import Path
from app.pipeline import video_to_subs

video_to_subs(Path("./ljod3.avi"), target_lang="en")