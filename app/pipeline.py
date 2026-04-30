"""
Subtitle processing pipeline for RusTrans.

This module contains the application backend:
- SRT translation
- video transcription
- batch processing for season folders

The GUI should call these functions instead of implementing processing logic.
"""

from __future__ import annotations

from pathlib import Path

import srt

from app.ffmpeg_audio import extract_audio_to_wav
from app.line_breaker import format_subtitle_lines
from app.postprocess import postprocess_target_text
from app.smart_text import preprocess_source_text
from app.srt_io import (
    build_srt_subtitles_from_segments,
    load_srt_file,
    save_srt_file,
)
from app.suspicious_detector import add_suspicious_candidate, looks_suspicious
from app.text_cleaner import clean_subtitle_text
from app.transcriber import transcribe_audio_to_segments
from app.translator import translate_text


VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".webm"}
SUPPORTED_TARGET_LANGUAGES = {"fi", "en"}

DEFAULT_MAX_LINE_LENGTH = 42
DEFAULT_MAX_LINES = 2


def validate_target_language(target_lang: str) -> None:
    """
    Validate that the requested target language is supported.

    Args:
        target_lang: Target language code.

    Raises:
        ValueError: If the language is not supported.
    """
    if target_lang not in SUPPORTED_TARGET_LANGUAGES:
        supported = ", ".join(sorted(SUPPORTED_TARGET_LANGUAGES))
        raise ValueError(f"Unsupported target language: {target_lang}. Supported: {supported}")


def process_text(text: str) -> str:
    """
    Clean and format translated subtitle text.

    Args:
        text: Raw translated text.

    Returns:
        Subtitle text formatted for readability.
    """
    text = clean_subtitle_text(text)
    text = format_subtitle_lines(
        text,
        max_line_length=DEFAULT_MAX_LINE_LENGTH,
        max_lines=DEFAULT_MAX_LINES,
    )
    return text


def build_output_srt_path(input_path: Path, out_lang: str) -> Path:
    """
    Build output subtitle path for a target language.

    Examples:
        episode.mkv -> episode.fi.srt
        episode.ru.srt -> episode.fi.srt
        movie.srt -> movie.fi.srt

    Args:
        input_path: Source video or subtitle path.
        out_lang: Target language code.

    Returns:
        Output SRT path.
    """
    validate_target_language(out_lang)

    if input_path.suffix.lower() == ".srt":
        stem = input_path.stem
        parts = stem.split(".")

        if len(parts) >= 2 and len(parts[-1]) == 2:
            base_name = ".".join(parts[:-1])
        else:
            base_name = stem

        return input_path.with_name(f"{base_name}.{out_lang}.srt")

    return input_path.with_suffix(f".{out_lang}.srt")


def build_temp_wav_path(video_path: Path) -> Path:
    """
    Build temporary WAV path for a video file.

    Args:
        video_path: Input video path.

    Returns:
        Temporary WAV path.
    """
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir / f"{video_path.stem}.wav"


def build_ru_srt_path(video_path: Path) -> Path:
    """
    Build Russian draft subtitle path for a video file.

    Args:
        video_path: Input video path.

    Returns:
        Russian SRT path.
    """
    return video_path.with_suffix(".ru.srt")


def translate_srt(input_path: Path, output_path: Path, target_lang: str = "fi") -> None:
    """
    Translate a Russian SRT file into the selected target language.

    The translation pipeline:
    1. Load Russian SRT.
    2. Apply idiom and glossary preprocessing.
    3. Translate text.
    4. Apply target-language postprocessing.
    5. Store suspicious translation candidates.
    6. Format subtitles for readability.
    7. Save output SRT.

    Args:
        input_path: Russian SRT input path.
        output_path: Translated SRT output path.
        target_lang: Target language code.
    """
    validate_target_language(target_lang)

    subtitles = load_srt_file(input_path)
    translated_subtitles: list[srt.Subtitle] = []

    for subtitle in subtitles:
        source_text = subtitle.content

        prepared_source = preprocess_source_text(
            source_text,
            target_lang=target_lang,
        )

        translated_text = translate_text(
            prepared_source,
            target_lang=target_lang,
        )

        translated_text = postprocess_target_text(
            translated_text,
            target_lang=target_lang,
        )

        reasons = looks_suspicious(
            source_text=source_text,
            translated_text=translated_text,
            target_lang=target_lang,
        )

        add_suspicious_candidate(
            source_text=source_text,
            translated_text=translated_text,
            target_lang=target_lang,
            reasons=reasons,
        )

        final_text = process_text(translated_text)

        translated_subtitles.append(
            srt.Subtitle(
                index=subtitle.index,
                start=subtitle.start,
                end=subtitle.end,
                content=final_text,
                proprietary=subtitle.proprietary,
            )
        )

    save_srt_file(output_path, translated_subtitles)


def transcribe_video_to_ru_srt(video_path: Path) -> Path:
    """
    Generate Russian SRT subtitles from a video file.

    Args:
        video_path: Input video file.

    Returns:
        Path to generated Russian SRT file.
    """
    temp_wav_path = build_temp_wav_path(video_path)
    ru_srt_path = build_ru_srt_path(video_path)

    print(f"[INFO] Extracting audio: {video_path.name}")
    extract_audio_to_wav(video_path, temp_wav_path)

    print("[INFO] Transcribing Russian speech...")
    segments = transcribe_audio_to_segments(str(temp_wav_path))

    if not segments:
        raise RuntimeError(f"No speech segments were detected in: {video_path.name}")

    subtitles = build_srt_subtitles_from_segments(segments)
    save_srt_file(ru_srt_path, subtitles)

    return ru_srt_path


def video_to_subs(video_path: Path, target_lang: str = "fi") -> Path:
    """
    Generate translated subtitles from a video file.

    The pipeline creates:
    - Russian draft SRT
    - Translated target SRT

    Args:
        video_path: Input video path.
        target_lang: Target language code.

    Returns:
        Path to translated target SRT file.
    """
    validate_target_language(target_lang)

    target_srt_path = build_output_srt_path(video_path, target_lang)

    print(f"[INFO] Processing video: {video_path.name}")

    ru_srt_path = transcribe_video_to_ru_srt(video_path)

    print(f"[INFO] Translating to {target_lang}: {ru_srt_path.name}")
    translate_srt(
        input_path=ru_srt_path,
        output_path=target_srt_path,
        target_lang=target_lang,
    )

    print(f"[INFO] Done: {target_srt_path}")
    return target_srt_path


def find_video_files(folder_path: Path) -> list[Path]:
    """
    Find supported video files in a folder.

    Args:
        folder_path: Folder to scan.

    Returns:
        Sorted list of video files.
    """
    return sorted(
        path
        for path in folder_path.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )


def process_video_folder(folder_path: Path, target_lang: str = "fi") -> None:
    """
    Process a full season folder.

    For each video file, the pipeline creates:
    - .ru.srt
    - .fi.srt or .en.srt

    Existing translated subtitles are skipped.
    If one episode fails, processing continues with the next one.

    Args:
        folder_path: Folder containing video files.
        target_lang: Target language code.
    """
    validate_target_language(target_lang)

    video_files = find_video_files(folder_path)

    if not video_files:
        raise RuntimeError("No supported video files were found in the selected folder.")

    print(f"[INFO] Found videos: {len(video_files)}")

    success_count = 0
    skipped_count = 0
    failed_count = 0

    for index, video_path in enumerate(video_files, start=1):
        target_srt_path = build_output_srt_path(video_path, target_lang)

        print("=" * 60)
        print(f"[INFO] [{index}/{len(video_files)}] {video_path.name}")

        if target_srt_path.exists():
            print(f"[INFO] Skipping existing subtitle: {target_srt_path.name}")
            skipped_count += 1
            continue

        try:
            video_to_subs(video_path, target_lang=target_lang)
            success_count += 1
            print(f"[INFO] Success: {video_path.name}")
        except Exception as e:
            failed_count += 1
            print(f"[ERROR] Failed to process {video_path.name}: {e}")
            continue

    print("=" * 60)
    print(f"[INFO] Folder processing completed.")
    print(f"[INFO] Success: {success_count}, Skipped: {skipped_count}, Failed: {failed_count}")