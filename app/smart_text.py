from __future__ import annotations

from app.glossary import GLOSSARY
from app.idioms import IDIOMS


def apply_idioms(text: str, target_lang: str) -> str:
    """
    Заменяет известные идиомы на смысловой вариант под нужный язык.
    """
    result = text

    for source_text, translations in IDIOMS.items():
        replacement = translations.get(target_lang)
        if replacement:
            result = result.replace(source_text, replacement)

    return result


def apply_glossary(text: str, target_lang: str) -> str:
    """
    Подменяет известные имена и термины на нужный вариант.
    """
    result = text

    for source_text, translations in GLOSSARY.items():
        replacement = translations.get(target_lang)
        if replacement:
            result = result.replace(source_text, replacement)

    return result


def preprocess_source_text(text: str, target_lang: str) -> str:
    """
    Подготовка текста до перевода.

    Сейчас:
    1. Идиомы
    2. Имена и термины
    """
    text = apply_idioms(text, target_lang)
    text = apply_glossary(text, target_lang)
    return text