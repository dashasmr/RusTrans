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
    """
    text = path.read_text(encoding="utf-8-sig")
    subtitles = list(srt.parse(text))
    return subtitles


def save_srt_file(path: Path, subtitles: list[srt.Subtitle]) -> None:
    """
    Сохраняет список субтитров в SRT-файл.
    """
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