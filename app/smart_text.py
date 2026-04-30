from __future__ import annotations

from app.glossary import GLOSSARY
from app.idioms import IDIOMS


def normalize_text(text: str) -> str:
    """
    Normalize text for dictionary lookup.
    """
    return text.strip().lower().replace("ё", "е")


def get_direct_idiom_translation(text: str, target_lang: str) -> str | None:
    """
    Return a direct idiom translation if the whole subtitle matches
    a known idiom or colloquial expression.
    """
    normalized = normalize_text(text)

    for source_text, translations in IDIOMS.items():
        if normalize_text(source_text) == normalized:
            return translations.get(target_lang)

    return None


def apply_glossary(text: str, target_lang: str) -> str:
    """
    Preserve or normalize known names and terms before translation.
    """
    result = text

    for source_text, translations in GLOSSARY.items():
        replacement = translations.get(target_lang)
        if replacement:
            result = result.replace(source_text, replacement)

    return result


def preprocess_source_text(text: str, target_lang: str) -> str:
    """
    Prepare Russian source text before machine translation.

    Important:
    Do not replace Russian idioms with Finnish/English here.
    Direct idiom translations are handled separately in the pipeline.
    """
    return apply_glossary(text, target_lang)