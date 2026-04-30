"""
Subtitle processing pipeline for RusTrans.

This module contains the backend logic:
- SRT translation
- video transcription
- subtitle generation
- batch folder processing
"""

from __future__ import annotations

from pathlib import Path

import srt

from app.ffmpeg_audio import extract_audio_to_wav
from app.line_breaker import format_subtitle_lines
from app.llm_reviewer import review_translation_with_llm
from app.postprocess import postprocess_target_text
from app.smart_text import get_direct_idiom_translation, preprocess_source_text
from app.srt_io import (
    build_srt_subtitles_from_segments,
    load_srt_file,
    save_srt_file,
)
from app.text_cleaner import clean_subtitle_text
from app.transcriber import transcribe_audio_to_segments
from app.translator import translate_text


VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".webm"}
SUPPORTED_TARGET_LANGUAGES = {"fi", "en"}
SUPPORTED_QUALITY_PRESETS = {"fast", "balanced", "best"}


def validate_target_language(target_lang: str) -> None:
    """
    Validate target language.
    """
    if target_lang not in SUPPORTED_TARGET_LANGUAGES:
        raise ValueError(f"Unsupported target language: {target_lang}")


def validate_quality(quality: str) -> None:
    """
    Validate transcription quality preset.
    """
    if quality not in SUPPORTED_QUALITY_PRESETS:
        raise ValueError(f"Unsupported quality preset: {quality}")


def process_text(text: str) -> str:
    """
    Clean and format subtitle text.
    """
    text = clean_subtitle_text(text)
    return format_subtitle_lines(text, max_line_length=42, max_lines=2)


def build_output_srt_path(input_path: Path, out_lang: str) -> Path:
    """
    Build translated subtitle output path.
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
    Build temporary WAV path and ensure tmp folder exists.
    """
    temp_dir = Path("tmp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir / f"{video_path.stem}.wav"


def build_ru_srt_path(video_path: Path) -> Path:
    """
    Build Russian draft SRT path.
    """
    return video_path.with_suffix(".ru.srt")


def translate_srt(input_path: Path, output_path: Path, target_lang: str = "fi") -> None:
    """
    Translate Russian SRT into Finnish or English.
    """
    validate_target_language(target_lang)

    subtitles = load_srt_file(input_path)
    translated_subtitles: list[srt.Subtitle] = []

    for subtitle in subtitles:
        source_text = subtitle.content.strip()

        if not source_text:
            continue

        direct_translation = get_direct_idiom_translation(
            source_text,
            target_lang=target_lang,
        )

        if direct_translation:
            translated_text = direct_translation
        else:
            prepared_source = preprocess_source_text(
                source_text,
                target_lang=target_lang,
            )

            translated_text = translate_text(
                prepared_source,
                target_lang=target_lang,
            )

            translated_text = review_translation_with_llm(
                source_text=source_text,
                translated_text=translated_text,
                target_lang=target_lang,
            )

        translated_text = postprocess_target_text(
            translated_text,
            target_lang=target_lang,
        )

        final_text = process_text(translated_text)

        if not final_text:
            final_text = source_text

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


def transcribe_video_to_ru_srt(video_path: Path, quality: str = "balanced") -> Path:
    """
    Generate Russian SRT from a video file.

    Args:
        video_path: Source video file.
        quality: Transcription quality preset: fast, balanced, best.

    Returns:
        Path to generated Russian SRT file.
    """
    validate_quality(quality)

    temp_wav_path = build_temp_wav_path(video_path)
    ru_srt_path = build_ru_srt_path(video_path)

    extract_audio_to_wav(video_path, temp_wav_path)

    segments = transcribe_audio_to_segments(
        str(temp_wav_path),
        quality=quality,
    )

    if not segments:
        raise RuntimeError(f"No speech segments detected in: {video_path.name}")

    subtitles = build_srt_subtitles_from_segments(segments)
    save_srt_file(ru_srt_path, subtitles)

    return ru_srt_path


def video_to_subs(
    video_path: Path,
    target_lang: str = "fi",
    quality: str = "balanced",
) -> Path:
    """
    Generate translated subtitles from a video file.
    """
    validate_target_language(target_lang)
    validate_quality(quality)

    ru_srt_path = transcribe_video_to_ru_srt(video_path, quality=quality)
    target_srt_path = build_output_srt_path(video_path, target_lang)

    translate_srt(
        input_path=ru_srt_path,
        output_path=target_srt_path,
        target_lang=target_lang,
    )

    return target_srt_path


def find_video_files(folder_path: Path) -> list[Path]:
    """
    Find supported video files in folder.
    """
    return sorted(
        path
        for path in folder_path.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )


def process_video_folder(
    folder_path: Path,
    target_lang: str = "fi",
    quality: str = "balanced",
) -> None:
    """
    Process all supported video files in a folder.
    """
    validate_target_language(target_lang)
    validate_quality(quality)

    video_files = find_video_files(folder_path)

    if not video_files:
        raise RuntimeError("No supported video files found in selected folder.")

    for video_path in video_files:
        target_srt_path = build_output_srt_path(video_path, target_lang)

        if target_srt_path.exists():
            continue

        video_to_subs(
            video_path,
            target_lang=target_lang,
            quality=quality,
        )