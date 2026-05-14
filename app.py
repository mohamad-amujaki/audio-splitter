from __future__ import annotations

from pathlib import Path

import streamlit as st

from browser_folder import render_browser_folder_picker, render_browser_folder_save
from folder_picker import FolderPickerError, folder_picker_available, pick_output_directory_for_web
from splitter import (
    OUTPUT_FORMAT_MP3,
    OUTPUT_FORMAT_ORIGINAL,
    SplitterError,
    ffmpeg_available,
    split_audio,
    supported_upload_types,
)

UPLOAD_DIR = Path(".work/uploads")
TEMP_OUTPUT_DIR = Path(".work/output")
SEGMENT_OPTIONS = (10, 20, 30)
OUTPUT_FORMAT_OPTIONS = (
    (OUTPUT_FORMAT_ORIGINAL, "Pertahankan format asal"),
    (OUTPUT_FORMAT_MP3, "Konversi ke .mp3"),
)
SUPPORTED_AUDIO_TYPES = supported_upload_types()
SUPPORTED_AUDIO_LABEL = ", ".join(f".{extension}" for extension in SUPPORTED_AUDIO_TYPES)


def init_session_state() -> None:
    if "output_dir" not in st.session_state:
        st.session_state.output_dir = ""
    if "browser_output_folder" not in st.session_state:
        st.session_state.browser_output_folder = ""


def sync_browser_folder_selection() -> None:
    selected_folder = st.query_params.get("selected_folder")
    if not selected_folder:
        return

    st.session_state.browser_output_folder = selected_folder
    if "selected_folder" in st.query_params:
        del st.query_params["selected_folder"]


def uses_native_folder_picker() -> bool:
    return folder_picker_available()


def resolve_output_dir() -> Path:
    output_dir = st.session_state.output_dir.strip()
    if output_dir:
        return Path(output_dir)
    raise SplitterError("Pilih folder output di komputer Anda terlebih dahulu.")


def save_uploaded_file(uploaded_file) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination = UPLOAD_DIR / uploaded_file.name
    destination.write_bytes(uploaded_file.getbuffer())
    return destination


def main() -> None:
    st.set_page_config(page_title="Pemotong Audio", page_icon="🎧", layout="centered")
    init_session_state()
    sync_browser_folder_selection()

    st.title("Pemotong Audio")
    st.caption(
        "Hasil disimpan ke folder lokal di komputer Anda. Pilih folder output sebelum memotong audio."
    )

    if not ffmpeg_available():
        st.error(
            "ffmpeg tidak ditemukan di server. "
            "Untuk Streamlit Community Cloud, pastikan file packages.txt berisi ffmpeg "
            "lalu deploy ulang aplikasi."
        )
        st.stop()

    uploaded_file = st.file_uploader(
        f"Unggah file audio ({SUPPORTED_AUDIO_LABEL})",
        type=list(SUPPORTED_AUDIO_TYPES),
    )
    segment_minutes = st.radio(
        "Durasi setiap potongan",
        options=SEGMENT_OPTIONS,
        format_func=lambda minutes: f"{minutes} menit",
        horizontal=True,
    )
    output_format = st.radio(
        "Format hasil",
        options=[value for value, _ in OUTPUT_FORMAT_OPTIONS],
        format_func=lambda value: dict(OUTPUT_FORMAT_OPTIONS)[value],
        horizontal=True,
    )

    st.subheader("Folder output")
    if uses_native_folder_picker():
        if st.button("Pilih folder lokal…", use_container_width=True):
            try:
                selected_directory = pick_output_directory_for_web()
            except FolderPickerError as exc:
                st.error(str(exc))
            else:
                if selected_directory:
                    st.session_state.output_dir = selected_directory

        if st.session_state.output_dir:
            st.caption(f"Folder terpilih: `{st.session_state.output_dir}`")
        else:
            st.caption("Belum ada folder dipilih.")
    else:
        st.caption(
            "Gunakan tombol di bawah untuk memilih folder lokal di komputer Anda. "
            "Fitur ini membutuhkan browser berbasis Chromium."
        )
        render_browser_folder_picker()
        if st.session_state.browser_output_folder:
            st.caption(f"Folder lokal terpilih: `{st.session_state.browser_output_folder}`")
            st.caption("Browser hanya menampilkan nama folder, bukan path lengkap.")
        else:
            st.caption("Belum ada folder dipilih.")

    info_message = (
        "Hasil disimpan di subfolder bernama file di dalam folder output yang dipilih. "
        "Format asal memakai mode `-c copy` tanpa re-encode; titik potong bisa sedikit "
        "menyimpang dari durasi yang dipilih."
    )
    if output_format == OUTPUT_FORMAT_MP3:
        info_message = (
            "Hasil disimpan di subfolder bernama file di dalam folder output yang dipilih. "
            "Konversi ke .mp3 memakai re-encode dan bisa lebih lama daripada format asal."
        )
    st.info(info_message)

    if st.button("Potong audio", type="primary", use_container_width=True):
        if uploaded_file is None:
            st.error("Unggah file audio terlebih dahulu.")
            st.stop()

        try:
            input_path = save_uploaded_file(uploaded_file)
            if uses_native_folder_picker():
                output_dir = resolve_output_dir()
            else:
                output_dir = TEMP_OUTPUT_DIR

            with st.spinner("Memproses audio…"):
                output_paths = split_audio(
                    input_path=input_path,
                    output_dir=output_dir,
                    segment_minutes=segment_minutes,
                    output_format=output_format,
                )
        except SplitterError as exc:
            st.error(str(exc))
        else:
            if uses_native_folder_picker():
                st.success(
                    f"Selesai. {len(output_paths)} file disimpan di folder lokal yang dipilih."
                )
            else:
                render_browser_folder_save(output_paths, TEMP_OUTPUT_DIR)
                folder_name = st.session_state.browser_output_folder
                if folder_name:
                    message = (
                        f"Selesai. {len(output_paths)} file disimpan ke folder lokal "
                        f"`{folder_name}`."
                    )
                else:
                    message = (
                        f"Selesai. {len(output_paths)} file disimpan ke folder lokal yang dipilih."
                    )
                st.success(message)


if __name__ == "__main__":
    main()
