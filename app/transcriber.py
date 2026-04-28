"""
Распознавание речи через faster-whisper.
"""

from __future__ import annotations

from dataclasses import dataclass

from faster_whisper import WhisperModel


@dataclass
class TranscribedSegment:
    """Один распознанный сегмент."""
    start: float
    end: float
    text: str


def transcribe_audio_to_segments(
    audio_path: str,
    model_size: str = "medium",
    language: str = "ru",
) -> list[TranscribedSegment]:
    """
    Распознаёт аудио и возвращает список сегментов.
    """
    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
    )

    segments, info = model.transcribe(
        audio_path,
        language=language,
        vad_filter=True,
    )

    result: list[TranscribedSegment] = []

    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue

        result.append(
            TranscribedSegment(
                start=float(segment.start),
                end=float(segment.end),
                text=text,
            )
        )

    return result