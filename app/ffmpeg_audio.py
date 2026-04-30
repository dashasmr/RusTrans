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
        # Extract a readable error message from ffmpeg output
        error_lines = []
        stderr_lower = result.stderr.lower()
        
        if "no such file" in stderr_lower or "cannot open" in stderr_lower:
            error_lines.append(f"Input file not found or cannot be read: {input_video_path.name}")
        elif "permission denied" in stderr_lower:
            error_lines.append("Permission denied. Check file access rights.")
        elif "invalid data found" in stderr_lower or "invalid data" in stderr_lower:
            error_lines.append(f"File format not supported or file is corrupted: {input_video_path.name}")
        elif "output file" in stderr_lower and "already exists" in stderr_lower:
            error_lines.append("Output file already exists and cannot be overwritten.")
        else:
            # Include first few lines of stderr for other errors
            stderr_lines = result.stderr.strip().split("\n")
            for line in stderr_lines[:5]:
                if line.strip():
                    error_lines.append(line.strip())
        
        error_msg = "ffmpeg error while extracting audio:\n"
        if error_lines:
            error_msg += "\n".join(f"  - {line}" for line in error_lines)
        else:
            error_msg += f"  Return code: {result.returncode}"
        
        raise RuntimeError(error_msg)