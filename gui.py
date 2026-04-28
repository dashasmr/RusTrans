from __future__ import annotations

import os
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


class RusTransApp:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title("RusTrans")
        self.root.geometry("860x620")
        self.root.minsize(760, 560)

        self.selected_path: Path | None = None

        self.path_var = ctk.StringVar()
        self.mode_var = ctk.StringVar(value="auto")
        self.lang_var = ctk.StringVar(value="fi")
        self.status_var = ctk.StringVar(value="Ready")

        self._build_ui()

    def _build_ui(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self.root, corner_radius=16)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(5, weight=1)

        title_label = ctk.CTkLabel(
            main_frame,
            text="RusTrans",
            font=ctk.CTkFont(size=26, weight="bold"),
        )
        title_label.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Offline subtitle generator for Finnish and English",
            font=ctk.CTkFont(size=14),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        path_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        path_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        path_frame.grid_columnconfigure(0, weight=1)

        self.path_entry = ctk.CTkEntry(
            path_frame,
            textvariable=self.path_var,
            height=38,
            placeholder_text="Select a video or Russian SRT file...",
        )
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(12, 8), pady=12)

        browse_button = ctk.CTkButton(
            path_frame,
            text="Browse file",
            command=self.select_file,
            width=110,
            height=38,
        )
        browse_button.grid(row=0, column=1, padx=(0, 8), pady=12)

        browse_folder_button = ctk.CTkButton(
            path_frame,
            text="Browse folder",
            command=self.select_folder,
            width=120,
            height=38,
        )
        browse_folder_button.grid(row=0, column=2, padx=(0, 12), pady=12)

        options_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        options_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))
        options_frame.grid_columnconfigure((0, 1), weight=1)

        mode_frame = ctk.CTkFrame(options_frame, corner_radius=12)
        mode_frame.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)

        mode_title = ctk.CTkLabel(
            mode_frame,
            text="Mode",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        mode_title.pack(anchor="w", padx=12, pady=(12, 8))

        ctk.CTkRadioButton(
            mode_frame,
            text="Auto",
            variable=self.mode_var,
            value="auto",
        ).pack(anchor="w", padx=12, pady=4)

        ctk.CTkRadioButton(
            mode_frame,
            text="Video → RU SRT → target SRT",
            variable=self.mode_var,
            value="video",
        ).pack(anchor="w", padx=12, pady=4)

        ctk.CTkRadioButton(
            mode_frame,
            text="RU SRT → target SRT",
            variable=self.mode_var,
            value="srt",
        ).pack(anchor="w", padx=12, pady=(4, 12))

        lang_frame = ctk.CTkFrame(options_frame, corner_radius=12)
        lang_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)

        lang_title = ctk.CTkLabel(
            lang_frame,
            text="Target language",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        lang_title.pack(anchor="w", padx=12, pady=(12, 8))

        self.lang_menu = ctk.CTkOptionMenu(
            lang_frame,
            values=["fi", "en"],
            variable=self.lang_var,
            width=140,
        )
        self.lang_menu.pack(anchor="w", padx=12, pady=(0, 12))

        button_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        button_frame.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 12))
        button_frame.grid_columnconfigure(4, weight=1)

        self.start_button = ctk.CTkButton(
            button_frame,
            text="Start",
            command=self.start_processing,
            width=120,
            height=40,
        )
        self.start_button.grid(row=0, column=0, padx=(12, 8), pady=12)

        clear_button = ctk.CTkButton(
            button_frame,
            text="Clear log",
            command=self.clear_log,
            width=120,
            height=40,
        )
        clear_button.grid(row=0, column=1, padx=8, pady=12)

        open_output_btn = ctk.CTkButton(
            button_frame,
            text="Open output",
            command=self.open_output_folder,
            width=130,
            height=40,
        )
        open_output_btn.grid(row=0, column=2, padx=8, pady=12)

        open_candidates_btn = ctk.CTkButton(
            button_frame,
            text="Open candidates",
            command=self.open_candidates_file,
            width=150,
            height=40,
        )
        open_candidates_btn.grid(row=0, column=3, padx=8, pady=12)

        self.status_label = ctk.CTkLabel(
            button_frame,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.status_label.grid(row=0, column=4, sticky="e", padx=(8, 12), pady=12)

        log_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        log_frame.grid(row=5, column=0, sticky="nsew", padx=16, pady=(0, 16))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        log_title = ctk.CTkLabel(
            log_frame,
            text="Log",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        log_title.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

        self.log_text = ctk.CTkTextbox(log_frame, corner_radius=10)
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def select_file(self) -> None:
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
        self.log(f"Selected: {self.selected_path}")

    def select_folder(self) -> None:
        folder_path = filedialog.askdirectory(
            title="Select season folder",
        )

        if not folder_path:
            return

        self.selected_path = Path(folder_path)
        self.path_var.set(str(self.selected_path))
        self.log(f"Selected folder: {self.selected_path}")

    def clear_log(self) -> None:
        self.log_text.delete("1.0", "end")

    def log(self, message: str) -> None:
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.root.update_idletasks()

    def open_output_folder(self) -> None:
        if not self.selected_path:
            return

        folder = self.selected_path.parent

        try:
            os.startfile(folder)
        except Exception as e:
            self.log(f"Cannot open folder: {e}")

    def open_candidates_file(self) -> None:
        path = Path("data/idiom_candidates.json")

        if not path.exists():
            self.log("Candidates file not found yet.")
            return

        try:
            os.startfile(path)
        except Exception as e:
            self.log(f"Cannot open candidates file: {e}")

    def start_processing(self) -> None:
        path_text = self.path_var.get().strip()

        if not path_text:
            messagebox.showerror("Error", "Please select a file first.")
            return

        input_path = Path(path_text)

        if not input_path.exists():
            messagebox.showerror("Error", f"Path not found:\n{input_path}")
            return

        self.start_button.configure(state="disabled")
        self.status_var.set("Processing...")
        self.log("Starting...")

        worker = threading.Thread(
            target=self._run_processing,
            args=(input_path,),
            daemon=True,
        )
        worker.start()

    def _run_processing(self, input_path: Path) -> None:
        try:
            mode = self.mode_var.get()
            target_lang = self.lang_var.get()

            self.log(f"Target language: {target_lang}")

            if input_path.is_dir():
                self.log("Folder mode: processing season folder")
                process_video_folder(input_path, target_lang=target_lang)

            else:
                if mode == "auto":
                    if input_path.suffix.lower() == ".srt":
                        self._process_srt(input_path, target_lang)
                    else:
                        self._process_video(input_path, target_lang)

                elif mode == "srt":
                    self._process_srt(input_path, target_lang)

                elif mode == "video":
                    self._process_video(input_path, target_lang)

            self.log("Done.")
            self.status_var.set("Done")
            messagebox.showinfo("Success", "Processing completed.")

        except Exception as error:
            self.log(f"Error: {error}")
            self.status_var.set("Error")
            messagebox.showerror("Error", str(error))

        finally:
            self.start_button.configure(state="normal")

    def _process_srt(self, input_path: Path, target_lang: str) -> None:
        output_path = build_output_srt_path(input_path, target_lang)
        self.log(f"Input SRT: {input_path}")
        self.log(f"Output {target_lang.upper()} SRT: {output_path}")
        translate_srt(input_path, output_path, target_lang=target_lang)

    def _process_video(self, input_path: Path, target_lang: str) -> None:
        self.log(f"Input video: {input_path}")
        self.log(f"Mode: video -> ru.srt -> {target_lang}.srt")
        video_to_subs(input_path, target_lang=target_lang)


def main() -> None:
    root = ctk.CTk()
    app = RusTransApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()