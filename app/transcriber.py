"""
Speech recognition module for RusTrans.

This module wraps faster-whisper and provides quality presets:
- fast
- balanced
- best
"""

from __future__ import annotations

from dataclasses import dataclass

from faster_whisper import WhisperModel


QUALITY_PRESETS = {
    "fast": {
        "model_size": "small",
        "beam_size": 3,
        "vad_filter": True,
    },
    "balanced": {
        "model_size": "medium",
        "beam_size": 5,
        "vad_filter": True,
    },
    "best": {
        "model_size": "medium",
        "beam_size": 8,
        "vad_filter": True,
    },
}


@dataclass
class TranscribedSegment:
    """
    A single recognized speech segment.
    """

    start: float
    end: float
    text: str


def get_quality_config(quality: str) -> dict:
    """
    Return faster-whisper settings for selected quality preset.
    """
    if quality not in QUALITY_PRESETS:
        raise ValueError(f"Unsupported quality preset: {quality}")

    return QUALITY_PRESETS[quality]


def transcribe_audio_to_segments(
    audio_path: str,
    quality: str = "balanced",
    language: str = "ru",
) -> list[TranscribedSegment]:
    """
    Transcribe Russian speech from audio into timestamped text segments.

    Args:
        audio_path: Path to extracted WAV audio.
        quality: One of: fast, balanced, best.
        language: Spoken language code.

    Returns:
        List of timestamped speech segments.
    """
    config = get_quality_config(quality)

    model = WhisperModel(
        config["model_size"],
        device="cpu",
        compute_type="int8",
    )

    segments, info = model.transcribe(
        audio_path,
        language=language,
        vad_filter=config["vad_filter"],
        beam_size=config["beam_size"],
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