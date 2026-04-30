"""
Local AI reviewer for subtitle translations.

This module uses Ollama to improve translated subtitles locally.
No cloud API is used.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:3b"


def review_translation_with_llm(
    source_text: str,
    translated_text: str,
    target_lang: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Rewrite a subtitle translation to make it more natural.

    Args:
        source_text: Original Russian subtitle text.
        translated_text: Raw machine translation.
        target_lang: Target language code: "fi" or "en".
        model: Local Ollama model name.

    Returns:
        Improved translation, or original translated text if review fails.
    """
    if not translated_text.strip():
        return translated_text

    language_name = {
        "en": "English",
        "fi": "Finnish",
    }.get(target_lang, target_lang)

    prompt = f"""
You are a professional subtitle translator.

Task:
Rewrite the translation so it sounds natural in {language_name}.
Preserve the meaning of the Russian source.
Do not explain anything.
Do not add notes.
Do not include quotes.
Return only the final subtitle text.

Rules:
- Keep names unchanged unless they have a standard form.
- Translate idioms by meaning, not word by word.
- Make the subtitle short and easy to read.
- Avoid literal translation.
- Preserve tone and emotion.

Russian source:
{source_text}

Raw translation:
{translated_text}

Final {language_name} subtitle:
""".strip()

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        request = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))

        result = data.get("response", "").strip()

        if not result:
            return translated_text

        return result

    except (urllib.error.URLError, TimeoutError, Exception):
        return translated_text