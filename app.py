from __future__ import annotations

from pathlib import Path

import streamlit as st

from browser_folder import build_browser_files_payload, render_browser_folder_manager
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
    if "pending_browser_files" not in st.session_state:
        st.session_state.pending_browser_files = []


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


def sync_browser_folder_state(component_result: dict | None) -> None:
    if not component_result:
        return

    folder_name = component_result.get("name")
    if component_result.get("selected") and folder_name:
        st.session_state.browser_output_folder = folder_name


def handle_browser_save_result(component_result: dict | None) -> None:
    if not component_result:
        return

    if component_result.get("error"):
        st.error(str(component_result["error"]))
        return

    saved_count = int(component_result.get("saved") or 0)
    if saved_count <= 0:
        return

    folder_name = st.session_state.browser_output_folder
    st.session_state.pending_browser_files = []
    if folder_name:
        st.success(
            f"Selesai. {saved_count} file disimpan ke folder lokal `{folder_name}`."
        )
    else:
        st.success(
            f"Selesai. {saved_count} file disimpan ke folder lokal yang dipilih."
        )


def render_browser_folder_section() -> None:
    component_result = render_browser_folder_manager(
        st.session_state.pending_browser_files,
        key="browser_folder_manager",
    )
    sync_browser_folder_state(component_result)
    handle_browser_save_result(component_result)

    if st.session_state.browser_output_folder:
        st.caption(f"Folder lokal terpilih: `{st.session_state.browser_output_folder}`")
        st.caption("Browser hanya menampilkan nama folder, bukan path lengkap.")
    else:
        st.caption("Belum ada folder dipilih.")


def main() -> None:
    st.set_page_config(page_title="Pemotong Audio", page_icon="🎧", layout="centered")
    init_session_state()

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
        render_browser_folder_section()

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

        if uses_native_folder_picker():
            if not st.session_state.output_dir.strip():
                st.error("Pilih folder output di komputer Anda terlebih dahulu.")
                st.stop()
        elif not st.session_state.browser_output_folder:
            st.error("Pilih folder output lokal terlebih dahulu.")
            st.stop()

        try:
            input_path = save_uploaded_file(uploaded_file)
            output_dir = resolve_output_dir() if uses_native_folder_picker() else TEMP_OUTPUT_DIR

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
                st.session_state.pending_browser_files = build_browser_files_payload(
                    output_paths,
                    TEMP_OUTPUT_DIR,
                )
                st.rerun()


if __name__ == "__main__":
    main()
