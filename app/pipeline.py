from pathlib import Path
import tempfile

import srt

from app.ffmpeg_audio import extract_audio_to_wav
from app.line_breaker import format_subtitle_lines
from app.srt_io import (
    build_srt_subtitles_from_segments,
    load_srt_file,
    save_srt_file,
)
from app.text_cleaner import clean_subtitle_text
from app.smart_text import preprocess_source_text
from app.postprocess import postprocess_target_text
from app.suspicious_detector import add_suspicious_candidate, looks_suspicious
from app.transcriber import transcribe_audio_to_segments
from app.translator import translate_text


VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".webm"}


def process_text(text: str) -> str:
    text = clean_subtitle_text(text)
    text = format_subtitle_lines(text, max_line_length=42, max_lines=2)
    return text


def build_output_srt_path(input_path: Path, out_lang: str) -> Path:
    if input_path.suffix.lower() == ".srt":
        stem = input_path.stem
        parts = stem.split(".")

        if len(parts) >= 2 and len(parts[-1]) == 2:
            base_name = ".".join(parts[:-1])
        else:
            base_name = stem

        return input_path.with_name(f"{base_name}.{out_lang}.srt")

    return input_path.with_suffix(f".{out_lang}.srt")


def translate_srt(input_path: Path, output_path: Path, target_lang: str = "fi") -> None:
    subtitles = load_srt_file(input_path)

    new_subs = []

    for sub in subtitles:
        source_text = sub.content

        # Сначала подготавливаем русский текст:
        # - идиомы
        # - имена
        source_text = preprocess_source_text(source_text, target_lang=target_lang)

        text = translate_text(source_text, target_lang=target_lang)

        # Постобработка под язык результата
        text = postprocess_target_text(text, target_lang=target_lang)

        # Проверка на подозрительные переводы
        reasons = looks_suspicious(source_text, text, target_lang)
        add_suspicious_candidate(
            source_text=source_text,
            translated_text=text,
            target_lang=target_lang,
            reasons=reasons,
        )

        # Финальная чистка и переносы
        text = process_text(text)

        new_subs.append(
            srt.Subtitle(
                index=sub.index,
                start=sub.start,
                end=sub.end,
                content=text,
                proprietary=sub.proprietary,
            )
        )

    save_srt_file(output_path, new_subs)

def video_to_subs(video_path: Path, target_lang: str = "fi") -> None:
    # Use system temp directory for cross-platform compatibility
    temp_dir = Path(tempfile.gettempdir()) / "rustrans"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_wav = temp_dir / f"{video_path.stem}.wav"

    ru_srt = video_path.with_suffix(".ru.srt")
    target_srt = build_output_srt_path(video_path, target_lang)

    print(f"Processing video: {video_path.name}")
    print("Extracting audio...")
    extract_audio_to_wav(video_path, temp_wav)

    print("Transcribing...")
    segments = transcribe_audio_to_segments(str(temp_wav))

    subtitles = build_srt_subtitles_from_segments(segments)
    save_srt_file(ru_srt, subtitles)

    print(f"Translating to {target_lang}...")
    translate_srt(ru_srt, target_srt, target_lang=target_lang)

    print("Done:", target_srt)


def process_video_folder(folder_path: Path, target_lang: str = "fi") -> None:
    """
    Обрабатывает все видеофайлы в папке.

    Для каждого видео создаёт:
    - .ru.srt
    - .<target_lang>.srt

    Уже готовые .<target_lang>.srt не пересоздаёт.
    """
    video_files = sorted(
        path for path in folder_path.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )

    if not video_files:
        raise RuntimeError("В папке не найдено видеофайлов.")

    print(f"Found videos: {len(video_files)}")

    for index, video_path in enumerate(video_files, start=1):
        target_srt = build_output_srt_path(video_path, target_lang)

        print("\n" + "=" * 60)
        print(f"[{index}/{len(video_files)}] {video_path.name}")

        if target_srt.exists():
            print(f"Skipping, already exists: {target_srt.name}")
            continue

        video_to_subs(video_path, target_lang=target_lang)

    print("\nAll done.")