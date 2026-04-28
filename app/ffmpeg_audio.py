"""
Работа с ffmpeg для извлечения аудио из видео.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def check_ffmpeg() -> bool:
    """
    Проверяет, установлен ли ffmpeg в системе.

    Returns:
        True если ffmpeg доступен, False иначе
    """
    return shutil.which("ffmpeg") is not None


def extract_audio_to_wav(input_video_path: Path, output_wav_path: Path) -> None:
    """
    Извлекает аудио из видео в WAV-формат.

    Параметры:
    - mono
    - 16 kHz
    - PCM 16-bit
    - лёгкое шумоподавление

    Args:
        input_video_path: Путь к видеофайлу
        output_wav_path: Куда сохранить .wav

    Raises:
        RuntimeError: если ffmpeg не установлен
        RuntimeError: если ffmpeg завершился с ошибкой
    """
    if not check_ffmpeg():
        raise RuntimeError(
            "ffmpeg не найден в системе. Пожалуйста, установите ffmpeg "
            "и добавьте его в PATH (https://ffmpeg.org/download.html)"
        )

    output_wav_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-af",
        "afftdn",
        str(output_wav_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Ошибка ffmpeg при извлечении аудио.\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )