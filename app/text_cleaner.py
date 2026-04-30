"""
Очистка текста субтитров.

Задача:
- убрать лишние пробелы
- убрать пустые строки
- привести текст к более аккуратному виду
"""

from __future__ import annotations

import re


def clean_subtitle_text(text: str) -> str:
    """
    Очищает текст одной реплики субтитров.

    Args:
        text: Исходный текст

    Returns:
        Очищенный текст
    """
    if not text:
        return ""

    # Normalize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove leading/trailing spaces from each line
    lines = [line.strip() for line in text.split("\n")]

    # Remove completely empty lines
    lines = [line for line in lines if line]

    # Join back into a single line, without preserving old line breaks yet
    text = " ".join(lines)

    # Collapse repeated spaces
    text = re.sub(r"\s+", " ", text)

    # Remove space before punctuation
    text = re.sub(r"\s+([,.!?:;])", r"\1", text)

    return text.strip()