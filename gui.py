"""
RusTrans desktop application.

This module contains only the GUI layer.
All subtitle processing logic is delegated to the app.pipeline module.
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
import tkinter.messagebox as messagebox
from tkinter import filedialog

import customtkinter as ctk

from app.pipeline import (
    build_output_srt_path,
    process_video_folder,
    translate_srt,
    video_to_subs,
)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


LANGUAGE_LABELS = {
    "Finnish": "fi",
    "English": "en",
}

MODE_LABELS = {
    "Auto": "auto",
    "Video → subtitles": "video",
    "Russian SRT → subtitles": "srt",
}


class RusTransApp:
    """
    Main desktop application window for RusTrans.

    The UI allows users to select a video, SRT file, or a season folder,
    then generate translated subtitles in Finnish or English.
    """

    def __init__(self, root: ctk.CTk) -> None:
        """
        Initialize application state and build the UI.
        """
        self.root = root
        self.root.title("RusTrans")
        self.root.geometry("940x660")
        self.root.minsize(820, 600)

        self.selected_path: Path | None = None

        self.path_var = ctk.StringVar()
        self.mode_var = ctk.StringVar(value="Auto")
        self.lang_var = ctk.StringVar(value="Finnish")
        self.status_var = ctk.StringVar(value="Ready")

        self._build_ui()

    def _build_ui(self) -> None:
        """
        Build all UI components.
        """
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        main = ctk.CTkFrame(self.root, corner_radius=22)
        main.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(5, weight=1)

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(22, 12))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="RusTrans",
            font=ctk.CTkFont(size=34, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Offline Russian subtitle generator and translator",
            font=ctk.CTkFont(size=15),
            text_color="#AAB2C0",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.status_badge = ctk.CTkLabel(
            header,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=18,
            fg_color="#1F6AA5",
            text_color="white",
            width=120,
            height=34,
        )
        self.status_badge.grid(row=0, column=1, rowspan=2, sticky="e")

        input_card = ctk.CTkFrame(main, corner_radius=18)
        input_card.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 14))
        input_card.grid_columnconfigure(0, weight=1)

        input_title = ctk.CTkLabel(
            input_card,
            text="Input",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        input_title.grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(14, 6))

        self.path_entry = ctk.CTkEntry(
            input_card,
            textvariable=self.path_var,
            height=42,
            placeholder_text="Choose a video, Russian SRT, or a season folder...",
        )
        self.path_entry.grid(row=1, column=0, sticky="ew", padx=(16, 8), pady=(0, 16))

        file_button = ctk.CTkButton(
            input_card,
            text="Browse file",
            command=self.select_file,
            width=120,
            height=42,
        )
        file_button.grid(row=1, column=1, padx=(0, 8), pady=(0, 16))

        folder_button = ctk.CTkButton(
            input_card,
            text="Browse folder",
            command=self.select_folder,
            width=130,
            height=42,
        )
        folder_button.grid(row=1, column=2, padx=(0, 16), pady=(0, 16))

        options = ctk.CTkFrame(main, corner_radius=18)
        options.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 14))
        options.grid_columnconfigure((0, 1, 2), weight=1)

        mode_card = ctk.CTkFrame(options, corner_radius=16)
        mode_card.grid(row=0, column=0, sticky="nsew", padx=(14, 7), pady=14)

        mode_title = ctk.CTkLabel(
            mode_card,
            text="Mode",
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        mode_title.pack(anchor="w", padx=14, pady=(14, 8))

        self.mode_menu = ctk.CTkOptionMenu(
            mode_card,
            values=list(MODE_LABELS.keys()),
            variable=self.mode_var,
            width=210,
            height=36,
        )
        self.mode_menu.pack(anchor="w", padx=14, pady=(0, 14))

        lang_card = ctk.CTkFrame(options, corner_radius=16)
        lang_card.grid(row=0, column=1, sticky="nsew", padx=7, pady=14)

        lang_title = ctk.CTkLabel(
            lang_card,
            text="Target language",
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        lang_title.pack(anchor="w", padx=14, pady=(14, 8))

        self.lang_menu = ctk.CTkOptionMenu(
            lang_card,
            values=list(LANGUAGE_LABELS.keys()),
            variable=self.lang_var,
            width=180,
            height=36,
        )
        self.lang_menu.pack(anchor="w", padx=14, pady=(0, 14))

        info_card = ctk.CTkFrame(options, corner_radius=16)
        info_card.grid(row=0, column=2, sticky="nsew", padx=(7, 14), pady=14)

        info_title = ctk.CTkLabel(
            info_card,
            text="Output",
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        info_title.pack(anchor="w", padx=14, pady=(14, 8))

        info_text = ctk.CTkLabel(
            info_card,
            text="Creates .ru.srt and .fi/.en.srt next to the source file.",
            wraplength=240,
            justify="left",
            text_color="#AAB2C0",
        )
        info_text.pack(anchor="w", padx=14, pady=(0, 14))

        actions = ctk.CTkFrame(main, corner_radius=18)
        actions.grid(row=3, column=0, sticky="ew", padx=22, pady=(0, 14))
        actions.grid_columnconfigure(5, weight=1)

        self.start_button = ctk.CTkButton(
            actions,
            text="Start",
            command=self.start_processing,
            width=130,
            height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.start_button.grid(row=0, column=0, padx=(14, 8), pady=14)

        clear_button = ctk.CTkButton(
            actions,
            text="Clear log",
            command=self.clear_log,
            width=120,
            height=44,
            fg_color="#3B3F4A",
            hover_color="#4A4F5C",
        )
        clear_button.grid(row=0, column=1, padx=8, pady=14)

        output_button = ctk.CTkButton(
            actions,
            text="Open output",
            command=self.open_output_folder,
            width=130,
            height=44,
            fg_color="#3B3F4A",
            hover_color="#4A4F5C",
        )
        output_button.grid(row=0, column=2, padx=8, pady=14)

        candidates_button = ctk.CTkButton(
            actions,
            text="Open candidates",
            command=self.open_candidates_file,
            width=150,
            height=44,
            fg_color="#3B3F4A",
            hover_color="#4A4F5C",
        )
        candidates_button.grid(row=0, column=3, padx=8, pady=14)

        kodi_note = ctk.CTkLabel(
            actions,
            text="Kodi tip: keep video and .srt in the same folder",
            text_color="#AAB2C0",
        )
        kodi_note.grid(row=0, column=5, sticky="e", padx=(8, 14), pady=14)

        log_card = ctk.CTkFrame(main, corner_radius=18)
        log_card.grid(row=5, column=0, sticky="nsew", padx=22, pady=(0, 22))
        log_card.grid_columnconfigure(0, weight=1)
        log_card.grid_rowconfigure(1, weight=1)

        log_title = ctk.CTkLabel(
            log_card,
            text="Log",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        log_title.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        self.log_text = ctk.CTkTextbox(
            log_card,
            corner_radius=14,
            font=ctk.CTkFont(size=13),
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        self.log("RusTrans is ready.")

    def select_file(self) -> None:
        """
        Open a file picker and store the selected input file.

        Supported inputs:
        - video files
        - Russian SRT subtitle files
        """
        file_path = filedialog.askopenfilename(
            title="Select video or Russian SRT",
            filetypes=[
                ("Video and subtitles", "*.mkv *.mp4 *.avi *.mov *.webm *.srt"),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            return

        self.selected_path = Path(file_path)
        self.path_var.set(str(self.selected_path))
        self.log(f"Selected file: {self.selected_path}")

    def select_folder(self) -> None:
        """
        Open a folder picker and store the selected season folder.

        Folder mode is used for batch processing multiple video files.
        """
        folder_path = filedialog.askdirectory(title="Select season folder")

        if not folder_path:
            return

        self.selected_path = Path(folder_path)
        self.path_var.set(str(self.selected_path))
        self.log(f"Selected folder: {self.selected_path}")

    def clear_log(self) -> None:
        """
        Clear all messages from the log panel.
        """
        self.log_text.delete("1.0", "end")

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Append a log message to the UI log panel.

        Args:
            message: Message to display.
            level: Log level label, for example INFO, WARNING, ERROR.
        """
        self.log_text.insert("end", f"[{level}] {message}\n")
        self.log_text.see("end")
        self.root.update_idletasks()

    def set_status(self, status: str) -> None:
        """
        Update the status badge text and color.
        """
        self.status_var.set(status)

        if status == "Ready":
            self.status_badge.configure(fg_color="#1F6AA5")
        elif status == "Processing":
            self.status_badge.configure(fg_color="#C77D00")
        elif status == "Done":
            self.status_badge.configure(fg_color="#2D8A4E")
        elif status == "Error":
            self.status_badge.configure(fg_color="#B83232")

    def open_output_folder(self) -> None:
        """
        Open the folder where generated subtitle files are stored.
        """
        if not self.selected_path:
            self.log("No file or folder selected.", level="WARNING")
            return

        folder = self.selected_path if self.selected_path.is_dir() else self.selected_path.parent

        try:
            os.startfile(folder)
        except Exception as error:
            self.log(f"Cannot open output folder: {error}", level="ERROR")

    def open_candidates_file(self) -> None:
        """
        Open the JSON file containing suspicious translation candidates.
        """
        # Use same path resolution as suspicious_detector
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(__file__).parent
        
        path = base_dir / "data" / "idiom_candidates.json"

        if not path.exists():
            self.log("Candidates file not found yet.", level="WARNING")
            return

        try:
            os.startfile(path)
        except Exception as error:
            self.log(f"Cannot open candidates file: {error}", level="ERROR")

    def start_processing(self) -> None:
        """
        Validate input and start processing in a background thread.

        A worker thread is used to keep the GUI responsive while
        transcription and translation are running.
        """
        path_text = self.path_var.get().strip()

        if not path_text:
            messagebox.showerror("Error", "Please select a file or folder first.")
            return

        input_path = Path(path_text)

        if not input_path.exists():
            messagebox.showerror("Error", f"Path not found:\n{input_path}")
            return

        self.start_button.configure(state="disabled")
        self.set_status("Processing")
        self.log("")
        self.log("Starting processing...")

        worker = threading.Thread(
            target=self._run_processing,
            args=(input_path,),
            daemon=True,
        )
        worker.start()

    def _run_processing(self, input_path: Path) -> None:
        """
        Run selected processing pipeline.

        The method supports:
        - single video file
        - single Russian SRT file
        - season folder with multiple video files
        """
        try:
            target_lang = LANGUAGE_LABELS[self.lang_var.get()]
            mode = MODE_LABELS[self.mode_var.get()]

            self.log(f"Target language: {target_lang}")
            self.log(f"Processing mode: {mode}")

            if input_path.is_dir():
                self.log("Season folder mode enabled.")
                process_video_folder(input_path, target_lang=target_lang)

            elif mode == "auto":
                if input_path.suffix.lower() == ".srt":
                    self._process_srt(input_path, target_lang)
                else:
                    self._process_video(input_path, target_lang)

            elif mode == "srt":
                self._process_srt(input_path, target_lang)

            elif mode == "video":
                self._process_video(input_path, target_lang)

            self.log("Processing completed successfully.")
            self.set_status("Done")
            messagebox.showinfo("Success", "Processing completed.")

        except Exception as error:
            self.log(f"Processing failed: {error}", level="ERROR")
            self.set_status("Error")
            messagebox.showerror("Error", str(error))

        finally:
            self.start_button.configure(state="normal")

    def _process_srt(self, input_path: Path, target_lang: str) -> None:
        """
        Translate an existing Russian SRT file into the selected target language.
        """
        output_path = build_output_srt_path(input_path, target_lang)

        self.log(f"Input SRT: {input_path}")
        self.log(f"Output SRT: {output_path}")

        translate_srt(input_path, output_path, target_lang=target_lang)

    def _process_video(self, input_path: Path, target_lang: str) -> None:
        """
        Generate Russian subtitles from a video and translate them
        into the selected target language.
        """
        self.log(f"Input video: {input_path}")
        self.log(f"Creating subtitles: ru + {target_lang}")

        video_to_subs(input_path, target_lang=target_lang)


def main() -> None:
    """
    Application entry point.
    """
    root = ctk.CTk()
    RusTransApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()