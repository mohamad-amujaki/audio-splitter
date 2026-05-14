from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from models import BrowserFolderResult, SplitJobResult, WebSplitPhase
from work_paths import UPLOAD_DIR, ensure_work_dirs


class WebSessionState:
    """Akses terpusat ke session state Streamlit untuk alur web."""

    @staticmethod
    def init() -> None:
        defaults: dict[str, Any] = {
            "output_dir": "",
            "browser_output_folder": "",
            "pending_browser_files": [],
            "upload_widget_key": 0,
            "completed_split_info": None,
            "last_split_success": None,
            "split_phase": WebSplitPhase.IDLE.value,
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def get_split_phase() -> WebSplitPhase:
        return WebSplitPhase(st.session_state.get("split_phase", WebSplitPhase.IDLE.value))

    @staticmethod
    def set_split_phase(phase: WebSplitPhase) -> None:
        st.session_state.split_phase = phase.value

    @staticmethod
    def get_output_dir() -> str:
        return str(st.session_state.output_dir)

    @staticmethod
    def set_output_dir(path: str) -> None:
        st.session_state.output_dir = path

    @staticmethod
    def get_browser_output_folder() -> str:
        return str(st.session_state.browser_output_folder)

    @staticmethod
    def set_browser_output_folder(folder_name: str) -> None:
        st.session_state.browser_output_folder = folder_name

    @staticmethod
    def get_pending_browser_files() -> list[dict[str, str]]:
        return list(st.session_state.pending_browser_files)

    @staticmethod
    def set_pending_browser_files(files: list[dict[str, str]]) -> None:
        st.session_state.pending_browser_files = files

    @staticmethod
    def clear_pending_browser_files() -> None:
        st.session_state.pending_browser_files = []

    @staticmethod
    def get_completed_split_info() -> SplitJobResult | None:
        value = st.session_state.completed_split_info
        return value if isinstance(value, SplitJobResult) else None

    @staticmethod
    def set_completed_split_info(result: SplitJobResult) -> None:
        st.session_state.completed_split_info = result

    @staticmethod
    def clear_completed_split_info() -> None:
        st.session_state.completed_split_info = None

    @staticmethod
    def get_last_split_success() -> str | None:
        return st.session_state.last_split_success

    @staticmethod
    def set_last_split_success(message: str) -> None:
        st.session_state.last_split_success = message

    @staticmethod
    def reset_upload_widget() -> None:
        st.session_state.upload_widget_key += 1

    @staticmethod
    def get_upload_widget_key() -> int:
        return int(st.session_state.upload_widget_key)

    @staticmethod
    def sync_browser_folder_result(result: BrowserFolderResult | None) -> None:
        if result and result.selected and result.name:
            WebSessionState.set_browser_output_folder(result.name)


def save_uploaded_file(uploaded_file) -> Path:
    """Tulis file upload Streamlit ke folder kerja lokal server."""
    ensure_work_dirs()
    destination = UPLOAD_DIR / uploaded_file.name
    destination.write_bytes(uploaded_file.getbuffer())
    return destination
