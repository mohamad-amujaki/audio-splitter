from __future__ import annotations

from ui_options import output_format_label
from splitter import OutputFormat


def ffmpeg_missing_message() -> str:
    return (
        "ffmpeg tidak ditemukan di server. "
        "Untuk Streamlit Community Cloud, pastikan file packages.txt berisi ffmpeg "
        "lalu deploy ulang aplikasi."
    )


def desktop_ffmpeg_missing_message() -> str:
    return "ffmpeg tidak ditemukan di PATH. Instal ffmpeg terlebih dahulu."


def upload_required_message() -> str:
    return "Unggah file audio terlebih dahulu."


def native_output_required_message() -> str:
    return "Pilih folder output di komputer Anda terlebih dahulu."


def browser_output_required_message() -> str:
    return "Pilih folder output lokal terlebih dahulu."


def browser_folder_hint() -> str:
    return (
        "Pilih folder output lokal di komputer Anda melalui tombol di bawah. "
        "Fitur ini membutuhkan browser berbasis Chromium seperti Chrome atau Edge."
    )


def browser_folder_name_hint() -> str:
    return "Browser hanya menampilkan nama folder, bukan path lengkap."


def no_folder_selected_caption() -> str:
    return "Belum ada folder dipilih."


def processing_spinner_label() -> str:
    return "Memproses audio…"


def info_message_original_format() -> str:
    return (
        "Hasil disimpan di subfolder bernama file di dalam folder output yang dipilih. "
        "Format asal memakai mode salin stream tanpa re-encode, sehingga proses lebih cepat; "
        "titik potong bisa sedikit menyimpang dari durasi yang dipilih."
    )


def info_message_mp3_format() -> str:
    return (
        "Hasil disimpan di subfolder bernama file di dalam folder output yang dipilih. "
        "Konversi ke MP3 memakai re-encode dan bisa lebih lama daripada mempertahankan format asal."
    )


def build_split_success_message(
    *,
    source_name: str,
    file_count: int,
    segment_minutes: int,
    output_format: OutputFormat,
    output_subfolder: str,
    destination_label: str,
) -> str:
    format_label = output_format_label(output_format)
    return (
        f"**Potongan selesai.** File `{source_name}` dipecah menjadi **{file_count}** file "
        f"dengan durasi masing-masing **{segment_minutes} menit** ({format_label}).\n\n"
        f"Hasil disimpan di subfolder `{output_subfolder}/` di dalam folder output "
        f"`{destination_label}`."
    )


def build_desktop_success_message(
    *,
    source_name: str,
    file_count: int,
    segment_minutes: int,
    output_format: OutputFormat,
    output_subfolder: str,
    destination_label: str,
) -> str:
    format_label = output_format_label(output_format)
    return (
        f"Potongan selesai. File {source_name} dipecah menjadi {file_count} file "
        f"dengan durasi masing-masing {segment_minutes} menit ({format_label}). "
        f"Hasil disimpan di subfolder {output_subfolder}/ di dalam {destination_label}."
    )
