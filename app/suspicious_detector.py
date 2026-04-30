from __future__ import annotations

import json
import sys
from pathlib import Path


def _get_data_dir() -> Path:
    """
    Get the data directory path that works both in development and in packaged exe.
    
    Returns:
        Path to the data directory.
    """
    if getattr(sys, 'frozen', False):
        # Running as packaged exe
        base_dir = Path(sys._MEIPASS)
    else:
        # Running in development
        base_dir = Path(__file__).parent.parent
    
    return base_dir / "data"


CANDIDATES_FILE = _get_data_dir() / "idiom_candidates.json"


def looks_suspicious(source_text: str, translated_text: str, target_lang: str) -> list[str]:
    """
    Возвращает список причин, почему перевод выглядит подозрительно.
    """
    reasons: list[str] = []

    source_lower = source_text.strip().lower()
    translated_lower = translated_text.strip().lower()

    # Очень короткие разговорные фразы часто ломаются
    short_phrases = {
        "вот такие пироги",
        "да ну",
        "ну да",
        "ничего себе",
        "как бы не так",
        "вот оно как",
    }

    if source_lower in short_phrases:
        reasons.append("possible_idiom_or_colloquial_phrase")

    # Если перевод слишком длинный для короткой реплики
    if len(source_text.split()) <= 3 and len(translated_text.split()) >= 6:
        reasons.append("short_source_but_long_translation")

    # Если перевод вообще пустой
    if not translated_text.strip():
        reasons.append("empty_translation")

    # Если перевод совпал с оригиналом, но это не имя
    if source_lower == translated_lower and len(source_text.split()) > 1:
        reasons.append("translation_same_as_source")

    # Очень короткие эмоциональные реплики
    emotional_short = {
        "ага",
        "угу",
        "ну да",
        "да",
        "нет",
        "ладно",
        "понятно",
    }

    if source_lower in emotional_short:
        reasons.append("short_emotional_phrase")

    return reasons


def load_candidates() -> list[dict]:
    """
    Загружает уже найденные кандидаты.
    """
    if not CANDIDATES_FILE.exists():
        return []

    try:
        return json.loads(CANDIDATES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_candidates(candidates: list[dict]) -> None:
    """
    Сохраняет кандидаты в JSON.
    """
    CANDIDATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATES_FILE.write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_suspicious_candidate(
    source_text: str,
    translated_text: str,
    target_lang: str,
    reasons: list[str],
) -> None:
    """
    Добавляет подозрительную фразу в файл кандидатов.
    """
    if not reasons:
        return

    candidates = load_candidates()

    item = {
        "source_text": source_text,
        "translated_text": translated_text,
        "target_lang": target_lang,
        "reasons": reasons,
    }

    # Не добавляем точные дубликаты
    for existing in candidates:
        if (
            existing.get("source_text") == item["source_text"]
            and existing.get("translated_text") == item["translated_text"]
            and existing.get("target_lang") == item["target_lang"]
        ):
            return

    candidates.append(item)
    save_candidates(candidates)