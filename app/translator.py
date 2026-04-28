"""
Локальный переводчик через Argos Translate.

На этом шаге:
- пытаемся найти установленную языковую пару
- переводим одну строку текста
- если подходящей пары нет, даём понятную ошибку
"""

from __future__ import annotations

from dataclasses import dataclass

import argostranslate.package
import argostranslate.translate


@dataclass
class TranslationConfig:
    """Настройки перевода."""
    source_lang: str = "ru"
    target_lang: str = "fi"


def _find_installed_language(lang_code: str):
    """
    Ищет установленный язык Argos по коду языка.

    Args:
        lang_code: Например 'ru' или 'fi'

    Returns:
        Объект языка Argos или None
    """
    installed_languages = argostranslate.translate.get_installed_languages()

    for language in installed_languages:
        if language.code == lang_code:
            return language

    return None


def _get_translation(source_lang: str, target_lang: str):
    """
    Возвращает объект перевода для заданной языковой пары.

    Args:
        source_lang: Исходный язык, например 'ru'
        target_lang: Целевой язык, например 'fi'

    Returns:
        Объект перевода Argos

    Raises:
        RuntimeError: если нужная языковая пара не найдена
    """
    from_lang = _find_installed_language(source_lang)
    to_lang = _find_installed_language(target_lang)

    if from_lang is None:
        raise RuntimeError(
            f"Не найден установленный язык Argos: {source_lang}. "
            f"Нужно установить языковой пакет."
        )

    if to_lang is None:
        raise RuntimeError(
            f"Не найден установленный язык Argos: {target_lang}. "
            f"Нужно установить языковой пакет."
        )

    translation = from_lang.get_translation(to_lang)

    if translation is None:
        raise RuntimeError(
            f"Не найдена установленная языковая пара Argos: "
            f"{source_lang} -> {target_lang}"
        )

    return translation


def translate_text(text: str, target_lang: str = "fi", source_lang: str = "ru") -> str:
    """
    Переводит одну строку текста локально через Argos Translate.

    Args:
        text: Исходный текст
        target_lang: Язык перевода
        source_lang: Исходный язык

    Returns:
        Переведённый текст
    """
    text = text.strip()

    if not text:
        return ""

    if source_lang == "ru" and target_lang == "fi":
        # Перевод через английский: ru -> en -> fi
        try:
            translation_ru_en = _get_translation("ru", "en")
            text_en = translation_ru_en.translate(text)
            translation_en_fi = _get_translation("en", "fi")
            translated = translation_en_fi.translate(text_en)
        except RuntimeError:
            # Если нет пары, попробовать прямой перевод
            translation = _get_translation(source_lang, target_lang)
            translated = translation.translate(text)
    else:
        translation = _get_translation(source_lang, target_lang)
        translated = translation.translate(text)

    return translated