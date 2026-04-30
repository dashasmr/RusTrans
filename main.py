"""
CLI для локальной генерации финских субтитров.

Что умеет эта версия:
1. Принимает путь к одному файлу или к папке
2. Если это .srt-файл:
   - читает субтитры
   - переводит
   - чистит текст
   - делает переносы строк
   - сохраняет *.fi.srt
3. Если это папка:
   - находит все .srt
   - пропускает уже готовые *.fi.srt
   - обрабатывает каждый файл по очереди
4. Если это видео:
   - извлекает аудио через ffmpeg
   - распознаёт русскую речь
   - сохраняет черновой русский .srt

Пока перевод видео-ветки в финский ещё не подключён.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

import srt

from app.ffmpeg_audio import extract_audio_to_wav
from app.line_breaker import format_subtitle_lines
from app.srt_io import (
    build_srt_subtitles_from_segments,
    load_srt_file,
    save_srt_file,
)
from app.text_cleaner import clean_subtitle_text
from app.transcriber import transcribe_audio_to_segments
from app.translator import translate_text


VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".webm"}
SRT_EXTENSIONS = {".srt"}


def parse_args() -> argparse.Namespace:
    """Разбор аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Локальный генератор финских субтитров из русского SRT или видео."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Путь к входному файлу или папке",
    )
    parser.add_argument(
        "--out-lang",
        default="fi",
        help="Код языка результата. Для MVP поддерживается fi",
    )
    return parser.parse_args()


def detect_input_type(input_path: Path) -> str:
    """Определяет тип входного пути."""
    if input_path.is_dir():
        return "directory"

    suffix = input_path.suffix.lower()

    if suffix in SRT_EXTENSIONS:
        return "srt"

    if suffix in VIDEO_EXTENSIONS:
        return "video"

    raise ValueError(f"Неподдерживаемый формат файла: {suffix}")


def build_output_srt_path(input_path: Path, out_lang: str) -> Path:
    """
    Строит путь выходного файла.

    Примеры:
    - episode.mkv     -> episode.fi.srt
    - episode.mp4     -> episode.fi.srt
    - episode.ru.srt  -> episode.fi.srt
    - film.srt        -> film.fi.srt
    """
    suffix = input_path.suffix.lower()

    if suffix == ".srt":
        stem = input_path.stem
        parts = stem.split(".")

        if len(parts) >= 2 and len(parts[-1]) == 2:
            base_name = ".".join(parts[:-1])
        else:
            base_name = stem

        return input_path.with_name(f"{base_name}.{out_lang}.srt")

    return input_path.with_suffix(f".{out_lang}.srt")


def build_temp_wav_path(input_path: Path) -> Path:
    """
    Строит путь для временного WAV-файла.

    Пример:
    - episode.mkv -> system temp/episode.wav
    """
    temp_dir = Path(tempfile.gettempdir()) / "rustrans"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir / f"{input_path.stem}.wav"


def is_already_translated_srt(path: Path, out_lang: str) -> bool:
    """
    Проверяет, похож ли файл на уже готовый перевод.

    Примеры:
    - episode.fi.srt -> True
    - movie.ru.srt   -> False
    - movie.srt      -> False
    """
    if path.suffix.lower() != ".srt":
        return False

    return path.stem.lower().endswith(f".{out_lang.lower()}")


def preview_subtitles(subtitles: list[srt.Subtitle], title: str) -> None:
    """Печатает краткий предпросмотр первых субтитров."""
    print(f"\n{title}")
    print(f"Найдено субтитров: {len(subtitles)}")

    for subtitle in subtitles[:3]:
        print("-" * 40)
        print(f"#{subtitle.index}")
        print(f"{subtitle.start} --> {subtitle.end}")
        print(subtitle.content)


def process_translated_text(text: str) -> str:
    """
    Финальная обработка текста субтитров:
    - чистка
    - переносы строк
    """
    text = clean_subtitle_text(text)
    text = format_subtitle_lines(text, max_line_length=42, max_lines=2)
    return text


def translate_subtitles(
    subtitles: list[srt.Subtitle],
    target_lang: str,
) -> list[srt.Subtitle]:
    """
    Создаёт новый список субтитров с переведённым текстом.
    """
    translated_subtitles: list[srt.Subtitle] = []

    for subtitle in subtitles:
        translated_text = translate_text(subtitle.content, target_lang=target_lang)
        translated_text = process_translated_text(translated_text)

        translated_subtitle = srt.Subtitle(
            index=subtitle.index,
            start=subtitle.start,
            end=subtitle.end,
            content=translated_text,
            proprietary=subtitle.proprietary,
        )
        translated_subtitles.append(translated_subtitle)

    return translated_subtitles


def process_srt_file(
    input_path: Path,
    out_lang: str,
    show_preview: bool = True,
) -> bool:
    """
    Обрабатывает один SRT-файл.

    Returns:
        True, если обработка успешна, иначе False
    """
    output_path = build_output_srt_path(input_path, out_lang)

    print("\n" + "=" * 60)
    print(f"Обработка файла : {input_path}")
    print(f"Выходной файл   : {output_path}")

    try:
        subtitles = load_srt_file(input_path)
    except Exception as error:
        print(f"Ошибка чтения SRT: {error}")
        return False

    if show_preview:
        preview_subtitles(subtitles, title="Исходные субтитры")

    try:
        translated_subtitles = translate_subtitles(
            subtitles=subtitles,
            target_lang=out_lang,
        )
    except Exception as error:
        print(f"Ошибка перевода: {error}")
        return False

    try:
        save_srt_file(output_path, translated_subtitles)
    except Exception as error:
        print(f"Ошибка записи SRT: {error}")
        return False

    if show_preview:
        preview_subtitles(translated_subtitles, title="Переведённые субтитры")

    print(f"\nГотово: файл сохранён -> {output_path}")
    return True


def process_directory(directory_path: Path, out_lang: str) -> int:
    """
    Обрабатывает все подходящие .srt файлы в папке.

    Returns:
        Код возврата процесса
    """
    srt_files = sorted(directory_path.glob("*.srt"))
    srt_files = [
        path
        for path in srt_files
        if not is_already_translated_srt(path, out_lang=out_lang)
    ]

    if not srt_files:
        print("В папке не найдено подходящих .srt файлов для обработки.")
        return 1

    print(f"Найдено файлов для обработки: {len(srt_files)}")

    success_count = 0
    failed_count = 0

    for path in srt_files:
        ok = process_srt_file(path, out_lang=out_lang, show_preview=False)
        if ok:
            success_count += 1
        else:
            failed_count += 1

    print("\n" + "=" * 60)
    print("Итоги batch-обработки:")
    print(f"Успешно : {success_count}")
    print(f"Ошибки  : {failed_count}")

    return 0 if success_count > 0 else 1


def process_video_file(input_path: Path) -> int:
    """
    Обрабатывает видеофайл:
    - извлекает WAV
    - распознаёт речь
    - сохраняет черновой русский SRT
    """
    temp_wav_path = build_temp_wav_path(input_path)
    output_path = build_output_srt_path(input_path, "ru")

    print("Сценарий B: распознавание русской речи из видео + перевод в финский SRT")
    print(f"Временный WAV   : {temp_wav_path}")
    print(f"Черновой RU SRT : {output_path}")

    try:
        extract_audio_to_wav(input_path, temp_wav_path)
    except Exception as error:
        print(f"Ошибка извлечения аудио: {error}")
        return 1

    print("Аудио успешно извлечено.")

    try:
        segments = transcribe_audio_to_segments(
            audio_path=str(temp_wav_path),
            model_size="medium",
            language="ru",
        )
    except Exception as error:
        print(f"Ошибка распознавания речи: {error}")
        return 1

    if not segments:
        print("Распознавание завершилось, но сегменты не найдены.")
        return 1

    subtitles = build_srt_subtitles_from_segments(segments)

    try:
        save_srt_file(output_path, subtitles)
    except Exception as error:
        print(f"Ошибка записи чернового RU SRT: {error}")
        return 1

    preview_subtitles(subtitles, title="Черновые русские субтитры")
    
    print(f"\nГотово: черновой SRT сохранён -> {output_path}")

    # --- NEW: translate to Finnish ---
    print("\nПереводим в финский...")

    try:
        translated_subtitles = translate_subtitles(
            subtitles=subtitles,
            target_lang="fi",
        )
    except Exception as error:
        print(f"Ошибка перевода: {error}")
        return 1

    fi_output_path = build_output_srt_path(input_path, "fi")

    try:
        save_srt_file(fi_output_path, translated_subtitles)
    except Exception as error:
        print(f"Ошибка записи финского SRT: {error}")
        return 1

    print(f"Готово: финские субтитры -> {fi_output_path}")

    return 0


def main() -> int:
    """Точка входа программы."""
    args = parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Ошибка: путь не найден: {input_path}")
        return 1

    if args.out_lang != "fi":
        print("Ошибка: в этой минимальной версии поддерживается только --out-lang fi")
        return 1

    try:
        input_type = detect_input_type(input_path)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return 1

    print("=== fin-subs MVP ===")
    print(f"Входной путь : {input_path}")
    print(f"Тип входа    : {input_type}")

    if input_type == "directory":
        print("Batch-режим: обработка папки с SRT-файлами")
        return process_directory(input_path, out_lang=args.out_lang)

    if input_type == "srt":
        print("Сценарий A: перевод готового русского SRT в финский SRT")
        ok = process_srt_file(input_path, out_lang=args.out_lang, show_preview=True)
        return 0 if ok else 1

    if input_type == "video":
        return process_video_file(input_path)

    print("Неизвестный тип входа.")
    return 1


if __name__ == "__main__":
    sys.exit(main())