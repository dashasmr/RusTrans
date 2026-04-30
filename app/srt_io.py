"""
Функции для чтения и записи SRT-файлов.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import srt


def load_srt_file(path: Path) -> list[srt.Subtitle]:
    """
    Загружает SRT-файл и возвращает список субтитров.
    
    Raises:
        ValueError: Если файл пустой или не содержит субтитров.
    """
    text = path.read_text(encoding="utf-8-sig")
    
    if not text.strip():
        raise ValueError(f"Empty subtitle file: {path.name}")
    
    subtitles = list(srt.parse(text))
    
    if not subtitles:
        raise ValueError(f"No subtitles found in: {path.name}")
    
    return subtitles


def save_srt_file(path: Path, subtitles: list[srt.Subtitle]) -> None:
    """
    Сохраняет список субтитров в SRT-файл.
    
    Args:
        path: Путь для сохранения.
        subtitles: Список субтитров.
        
    Raises:
        ValueError: Если список субтитров пустой.
    """
    if not subtitles:
        raise ValueError(f"Cannot save empty subtitles to: {path.name}")
    
    # Ensure output directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    srt_text = srt.compose(subtitles)
    path.write_text(srt_text, encoding="utf-8")


def build_srt_subtitles_from_segments(segments) -> list[srt.Subtitle]:
    """
    Преобразует список сегментов распознавания в список srt.Subtitle.
    """
    subtitles: list[srt.Subtitle] = []

    for index, segment in enumerate(segments, start=1):
        subtitle = srt.Subtitle(
            index=index,
            start=timedelta(seconds=segment.start),
            end=timedelta(seconds=segment.end),
            content=segment.text,
        )
        subtitles.append(subtitle)

    return subtitles