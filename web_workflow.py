from __future__ import annotations

from pathlib import Path

import streamlit as st

from messages import build_split_success_message
from models import BrowserFolderResult, SplitJobResult, WebSplitPhase
from output_destination import OutputDestination
from persistence import split_result_from_paths
from splitter import OutputFormat, SplitterError, split_audio
from web_state import WebSessionState
from work_paths import cleanup_work_dirs


def record_split_success(result: SplitJobResult, destination_label: str) -> None:
    """Simpan pesan sukses dan reset widget upload."""
    WebSessionState.set_last_split_success(
        build_split_success_message(
            source_name=result.source_name,
            file_count=result.file_count,
            segment_minutes=result.segment_minutes,
            output_format=result.output_format,
            output_subfolder=result.output_subfolder,
            destination_label=destination_label,
        )
    )
    WebSessionState.clear_completed_split_info()
    WebSessionState.set_split_phase(WebSplitPhase.DONE)
    WebSessionState.reset_upload_widget()
    cleanup_work_dirs()


def run_split_job(
    *,
    input_path: Path,
    destination: OutputDestination,
    segment_minutes: int,
    output_format: OutputFormat,
    source_name: str,
) -> SplitJobResult:
    """Jalankan pemotongan ffmpeg ke folder yang disiapkan strategi output."""
    destination.validate_ready()
    output_paths = split_audio(
        input_path=input_path,
        output_dir=destination.processing_output_dir(),
        segment_minutes=segment_minutes,
        output_format=output_format,
    )
    return split_result_from_paths(
        source_name=source_name,
        segment_minutes=segment_minutes,
        output_format=output_format,
        output_paths=output_paths,
    )


def complete_split(
    *,
    result: SplitJobResult,
    destination: OutputDestination,
) -> bool:
    """Selesaikan penyimpanan hasil; kembalikan True bila Streamlit perlu rerun."""
    if destination.finalize(result):
        WebSessionState.set_split_phase(WebSplitPhase.SAVING)
        return True

    record_split_success(result, destination.destination_label())
    return True


def handle_browser_save_result(result: BrowserFolderResult | None) -> bool:
    """Proses callback penyimpanan browser; kembalikan True bila rerun diperlukan."""
    if result is None or not WebSessionState.get_pending_browser_files():
        return False

    if result.error:
        WebSessionState.set_split_phase(WebSplitPhase.ERROR)
        st.error(result.error)
        return False

    if result.saved <= 0:
        return False

    split_result = WebSessionState.get_completed_split_info()
    if split_result is None:
        return False

    WebSessionState.clear_pending_browser_files()
    destination_label = WebSessionState.get_browser_output_folder() or "folder lokal yang dipilih"
    record_split_success(split_result, destination_label)
    return True


def render_split_success_message() -> None:
    """Tampilkan ringkasan sukses terakhir di bawah tombol utama."""
    success_message = WebSessionState.get_last_split_success()
    if success_message:
        st.success(success_message)
