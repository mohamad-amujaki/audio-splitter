from __future__ import annotations

import threading
from pathlib import Path

try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
except (ImportError, ModuleNotFoundError) as exc:
    raise SystemExit(
        "Versi desktop membutuhkan Tkinter. "
        "Di macOS dengan Homebrew, instal paket python-tk yang sesuai versi Python Anda, "
        "misalnya: brew install python-tk@3.14"
    ) from exc

from desktop_controller import DesktopSplitRequest, run_desktop_split
from folder_picker import FolderPickerError, pick_output_directory
from messages import desktop_ffmpeg_missing_message
from splitter import OUTPUT_FORMAT_ORIGINAL, SplitterError, ffmpeg_available, supported_audio_filetypes
from ui_options import OUTPUT_FORMAT_OPTIONS, SEGMENT_OPTIONS


class AudioSplitterApp(ctk.CTk):
    """Aplikasi desktop untuk memilih file, folder output, dan memotong audio secara lokal."""

    def __init__(self) -> None:
        super().__init__()

        self.title("Pemotong Audio")
        self.geometry("760x640")
        self.minsize(640, 560)

        self.input_path: str | None = None
        self.output_dir: str | None = None
        self.segment_minutes = ctk.IntVar(value=SEGMENT_OPTIONS[0])
        self.output_format = ctk.StringVar(value=OUTPUT_FORMAT_ORIGINAL)
        self.is_processing = False

        self._build_layout()
        self._check_prerequisites()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(9, weight=1)

        header = ctk.CTkLabel(
            self,
            text="Pemotong Audio",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        header.grid(row=0, column=0, padx=24, pady=(24, 8), sticky="w")

        caption = ctk.CTkLabel(
            self,
            text="File diproses sepenuhnya di komputer Anda. Tidak ada unggahan ke layanan eksternal.",
            wraplength=700,
            justify="left",
        )
        caption.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")

        file_frame = ctk.CTkFrame(self)
        file_frame.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(file_frame, text="File input").grid(
            row=0, column=0, columnspan=2, padx=16, pady=(16, 8), sticky="w"
        )
        self.input_label = ctk.CTkLabel(
            file_frame,
            text="Belum ada file dipilih.",
            anchor="w",
            justify="left",
            wraplength=520,
        )
        self.input_label.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="ew")
        self.pick_file_button = ctk.CTkButton(
            file_frame,
            text="Pilih file…",
            command=self._pick_input_file,
            width=140,
        )
        self.pick_file_button.grid(row=1, column=1, padx=16, pady=(0, 16), sticky="e")

        duration_frame = ctk.CTkFrame(self)
        duration_frame.grid(row=3, column=0, padx=24, pady=(0, 12), sticky="ew")

        ctk.CTkLabel(duration_frame, text="Durasi setiap potongan").grid(
            row=0, column=0, padx=16, pady=(16, 8), sticky="w"
        )
        duration_options = ctk.CTkFrame(duration_frame, fg_color="transparent")
        duration_options.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="w")
        for index, minutes in enumerate(SEGMENT_OPTIONS):
            ctk.CTkRadioButton(
                duration_options,
                text=f"{minutes} menit",
                variable=self.segment_minutes,
                value=minutes,
            ).grid(row=0, column=index, padx=(0, 16), sticky="w")

        format_frame = ctk.CTkFrame(self)
        format_frame.grid(row=4, column=0, padx=24, pady=(0, 12), sticky="ew")

        ctk.CTkLabel(format_frame, text="Format hasil").grid(
            row=0, column=0, padx=16, pady=(16, 8), sticky="w"
        )
        format_options = ctk.CTkFrame(format_frame, fg_color="transparent")
        format_options.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="w")
        for index, (value, label) in enumerate(OUTPUT_FORMAT_OPTIONS):
            ctk.CTkRadioButton(
                format_options,
                text=label,
                variable=self.output_format,
                value=value,
            ).grid(row=0, column=index, padx=(0, 16), sticky="w")

        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=5, column=0, padx=24, pady=(0, 12), sticky="ew")
        output_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(output_frame, text="Folder output").grid(
            row=0, column=0, columnspan=2, padx=16, pady=(16, 8), sticky="w"
        )
        self.output_label = ctk.CTkLabel(
            output_frame,
            text="Belum ada folder dipilih.",
            anchor="w",
            justify="left",
            wraplength=520,
        )
        self.output_label.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="ew")
        self.pick_output_button = ctk.CTkButton(
            output_frame,
            text="Pilih folder…",
            command=self._pick_output_folder,
            width=140,
        )
        self.pick_output_button.grid(row=1, column=1, padx=16, pady=(0, 16), sticky="e")

        info = ctk.CTkLabel(
            self,
            text=(
                "Hasil disimpan di subfolder bernama file di dalam folder output yang dipilih. "
                "Mode -c copy memotong tanpa re-encode; titik potong bisa sedikit "
                "menyimpang dari durasi yang dipilih."
            ),
            wraplength=700,
            justify="left",
        )
        info.grid(row=6, column=0, padx=24, pady=(0, 12), sticky="w")

        self.process_button = ctk.CTkButton(
            self,
            text="Potong audio",
            command=self._start_processing,
            height=42,
        )
        self.process_button.grid(row=7, column=0, padx=24, pady=(0, 12), sticky="ew")

        self.status_label = ctk.CTkLabel(self, text="", anchor="w", justify="left", wraplength=700)
        self.status_label.grid(row=8, column=0, padx=24, pady=(0, 24), sticky="w")

    def _check_prerequisites(self) -> None:
        if ffmpeg_available():
            return

        self._set_status(desktop_ffmpeg_missing_message(), is_error=True)
        self._set_controls_enabled(False)

    def _set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.pick_file_button.configure(state=state)
        self.pick_output_button.configure(state=state)
        self.process_button.configure(state=state)

    def _pick_input_file(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self,
            title="Pilih file audio",
            filetypes=supported_audio_filetypes(),
        )
        if not selected:
            return

        self.input_path = selected
        self.input_label.configure(text=selected)

    def _pick_output_folder(self) -> None:
        try:
            selected = pick_output_directory("Pilih folder output")
        except FolderPickerError as exc:
            messagebox.showerror("Folder output", str(exc), parent=self)
            return

        if not selected:
            return

        self.output_dir = selected
        self.output_label.configure(text=selected)

    def _set_status(self, message: str, *, is_error: bool = False) -> None:
        color = "#d9534f" if is_error else None
        self.status_label.configure(text=message, text_color=color)

    def _start_processing(self) -> None:
        if self.is_processing:
            return

        if not self.input_path:
            self._set_status("Pilih file audio terlebih dahulu.", is_error=True)
            return
        if not self.output_dir:
            self._set_status("Pilih folder output terlebih dahulu.", is_error=True)
            return

        self.is_processing = True
        self._set_controls_enabled(False)
        self._set_status("Memproses audio…")

        request = DesktopSplitRequest(
            input_path=Path(self.input_path),
            output_dir=Path(self.output_dir),
            segment_minutes=self.segment_minutes.get(),
            output_format=self.output_format.get(),
            source_name=Path(self.input_path).name,
        )

        def worker() -> None:
            try:
                message = run_desktop_split(request)
            except SplitterError as exc:
                self.after(0, lambda: self._finish_processing_error(str(exc)))
            else:
                self.after(0, lambda: self._finish_processing_success(message))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_processing_error(self, message: str) -> None:
        self.is_processing = False
        self._set_controls_enabled(True)
        self._set_status(message, is_error=True)

    def _finish_processing_success(self, message: str) -> None:
        self.is_processing = False
        self._set_controls_enabled(True)
        self._set_status(message)


def main() -> None:
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    app = AudioSplitterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
