from __future__ import annotations

import streamlit as st

from browser_folder import render_browser_folder_manager
from folder_picker import FolderPickerError, pick_output_directory_for_web
from messages import (
    browser_folder_hint,
    ffmpeg_missing_message,
    info_message_mp3_format,
    info_message_original_format,
    no_folder_selected_caption,
    processing_spinner_label,
    upload_required_message,
)
from output_destination import create_web_output_destination, uses_native_folder_picker
from splitter import OUTPUT_FORMAT_MP3, SplitterError, ffmpeg_available
from ui_options import (
    OUTPUT_FORMAT_LABELS,
    SEGMENT_OPTIONS,
    SUPPORTED_AUDIO_LABEL,
    SUPPORTED_AUDIO_TYPES,
    segment_label,
)
from web_seo import configure_streamlit_page, inject_meta_tags, inject_responsive_styles, render_page_header
from web_state import WebSessionState, save_uploaded_file
from web_workflow import (
    complete_split,
    handle_browser_save_result,
    render_split_success_message,
    run_split_job,
)
from work_paths import cleanup_work_dirs


def render_browser_folder_section() -> None:
    """Render komponen folder browser dan sinkronkan status penyimpanan."""
    component_result = render_browser_folder_manager(
        WebSessionState.get_pending_browser_files(),
        key="browser_folder_manager",
    )
    WebSessionState.sync_browser_folder_result(component_result)
    if handle_browser_save_result(component_result):
        st.rerun()


def main() -> None:
    """Bangun halaman Streamlit untuk upload, pemilihan folder, dan pemotongan audio."""
    configure_streamlit_page()
    WebSessionState.init()
    inject_meta_tags()
    inject_responsive_styles()
    cleanup_work_dirs()

    native_folder_picker = uses_native_folder_picker()
    render_page_header()

    if not ffmpeg_available():
        st.error(ffmpeg_missing_message())
        st.stop()

    uploaded_file = st.file_uploader(
        f"Unggah file audio ({SUPPORTED_AUDIO_LABEL})",
        type=SUPPORTED_AUDIO_TYPES,
        key=f"audio_upload_{WebSessionState.get_upload_widget_key()}",
    )
    segment_minutes = st.radio(
        "Durasi setiap potongan",
        options=SEGMENT_OPTIONS,
        format_func=segment_label,
        horizontal=True,
    )
    output_format = st.radio(
        "Format hasil",
        options=list(OUTPUT_FORMAT_LABELS),
        format_func=OUTPUT_FORMAT_LABELS.get,
        horizontal=True,
    )

    st.subheader("Folder output")
    if native_folder_picker:
        if st.button("Pilih folder lokal…", use_container_width=True):
            try:
                selected_directory = pick_output_directory_for_web()
            except FolderPickerError as exc:
                st.error(str(exc))
            else:
                if selected_directory:
                    WebSessionState.set_output_dir(selected_directory)

        if WebSessionState.get_output_dir():
            st.caption(f"Folder terpilih: `{WebSessionState.get_output_dir()}`")
        else:
            st.caption(no_folder_selected_caption())
    else:
        st.caption(browser_folder_hint())
        render_browser_folder_section()

    st.info(
        info_message_mp3_format()
        if output_format == OUTPUT_FORMAT_MP3
        else info_message_original_format()
    )

    if st.button("Potong audio", type="primary", use_container_width=True):
        if uploaded_file is None:
            st.error(upload_required_message())
            st.stop()

        destination = create_web_output_destination(
            native_picker_available=native_folder_picker,
            native_output_dir=WebSessionState.get_output_dir(),
            browser_output_folder=WebSessionState.get_browser_output_folder(),
        )

        try:
            input_path = save_uploaded_file(uploaded_file)
            with st.spinner(processing_spinner_label()):
                result = run_split_job(
                    input_path=input_path,
                    destination=destination,
                    segment_minutes=segment_minutes,
                    output_format=output_format,
                    source_name=uploaded_file.name,
                )
        except SplitterError as exc:
            st.error(str(exc))
        else:
            if complete_split(result=result, destination=destination):
                st.rerun()

    render_split_success_message()


if __name__ == "__main__":
    main()
