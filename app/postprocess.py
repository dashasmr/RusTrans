from __future__ import annotations

import re


def postprocess_english(text: str) -> str:
    """
    Делает английский текст чуть более естественным.
    Пока это простой rule-based слой.
    """
    text = text.strip()

    replacements = {
        "Yeah, right": "Yeah, right",
        "No way": "No way",
        "Wow": "Wow",
    }

    for source, target in replacements.items():
        text = text.replace(source, target)

    # Убираем двойные пробелы
    text = re.sub(r"\s+", " ", text)

    # Чуть нормализуем пунктуацию
    text = re.sub(r"\s+([,.!?:;])", r"\1", text)

    return text.strip()


def postprocess_finnish(text: str) -> str:
    """
    Делает финский текст чуть более естественным для чтения.
    Пока это простой rule-based слой.
    """
    text = text.strip()

    replacements = {
        "Oho": "Oho",
        "Sellaista se on": "Sellaista se on",
    }

    for source, target in replacements.items():
        text = text.replace(source, target)

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.!?:;])", r"\1", text)

    return text.strip()


def postprocess_target_text(text: str, target_lang: str) -> str:
    """
    Выбирает постобработку под язык результата.
    """
    if target_lang == "en":
        return postprocess_english(text)

    if target_lang == "fi":
        return postprocess_finnish(text)

    return text.strip()