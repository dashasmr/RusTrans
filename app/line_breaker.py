"""
Переносы строк для субтитров.

Цель:
- не делать слишком длинные строки
- сделать текст удобнее для чтения в Kodi
"""

from __future__ import annotations

import textwrap


def format_subtitle_lines(
    text: str,
    max_line_length: int = 42,
    max_lines: int = 2,
) -> str:
    """
    Форматирует текст субтитра в 1-2 строки.

    Args:
        text: Текст субтитра
        max_line_length: Максимальная длина одной строки
        max_lines: Максимум строк в субтитре

    Returns:
        Отформатированный текст
    """
    if not text:
        return ""

    wrapped_lines = textwrap.wrap(
        text,
        width=max_line_length,
        break_long_words=True,
        break_on_hyphens=False,
    )

    # Если строк слишком много, схлопываем хвост в последнюю строку
    if len(wrapped_lines) > max_lines:
        head = wrapped_lines[: max_lines - 1]
        tail = " ".join(wrapped_lines[max_lines - 1 :])
        wrapped_lines = head + [tail]

    # Центрируем каждую строку для лучшего вида
    centered_lines = []
    for line in wrapped_lines:
        centered_lines.append(line.center(max_line_length))

    return "\n".join(centered_lines)