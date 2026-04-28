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

    # Нормализуем переводы строк
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Убираем пробелы по краям каждой строки
    lines = [line.strip() for line in text.split("\n")]

    # Убираем полностью пустые строки
    lines = [line for line in lines if line]

    # Собираем обратно в одну строку, пока без сохранения старых переносов
    text = " ".join(lines)

    # Сжимаем повторяющиеся пробелы
    text = re.sub(r"\s+", " ", text)

    # Убираем пробел перед знаками препинания
    text = re.sub(r"\s+([,.!?:;])", r"\1", text)

    return text.strip()