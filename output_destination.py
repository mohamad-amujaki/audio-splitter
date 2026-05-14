from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from folder_picker import folder_picker_available
from models import SplitJobResult
from work_paths import TEMP_OUTPUT_DIR


class OutputDestination(ABC):
    """Kontrak penyimpanan hasil potongan untuk web native maupun browser."""

    @abstractmethod
    def validate_ready(self) -> None:
        """Pastikan folder output siap dipakai sebelum pemotongan dimulai."""

    @abstractmethod
    def processing_output_dir(self) -> Path:
        """Folder tempat ffmpeg menulis hasil sementara atau final."""

    @abstractmethod
    def destination_label(self) -> str:
        """Label folder tujuan yang ditampilkan ke pengguna."""

    @abstractmethod
    def finalize(self, result: SplitJobResult) -> bool:
        """Selesaikan penyimpanan; kembalikan True bila UI perlu rerun."""


class NativeOutputDestination(OutputDestination):
    """Simpan langsung ke folder lokal yang dipilih lewat dialog server."""

    def __init__(self, output_dir: str) -> None:
        self._output_dir = output_dir.strip()

    def validate_ready(self) -> None:
        if not self._output_dir:
            from messages import native_output_required_message
            from splitter import SplitterError

            raise SplitterError(native_output_required_message())

    def processing_output_dir(self) -> Path:
        return Path(self._output_dir)

    def destination_label(self) -> str:
        return self._output_dir

    def finalize(self, result: SplitJobResult) -> bool:
        return False


class BrowserOutputDestination(OutputDestination):
    """Potong ke folder staging server lalu kirim hasil ke folder browser."""

    def __init__(self, browser_output_folder: str) -> None:
        self._browser_output_folder = browser_output_folder.strip()

    def validate_ready(self) -> None:
        if not self._browser_output_folder:
            from messages import browser_output_required_message
            from splitter import SplitterError

            raise SplitterError(browser_output_required_message())

    def processing_output_dir(self) -> Path:
        return TEMP_OUTPUT_DIR

    def destination_label(self) -> str:
        return self._browser_output_folder or "folder lokal yang dipilih"

    def finalize(self, result: SplitJobResult) -> bool:
        from persistence import build_browser_files_payload
        from web_state import WebSessionState

        WebSessionState.set_pending_browser_files(
            build_browser_files_payload(list(result.output_paths), TEMP_OUTPUT_DIR)
        )
        WebSessionState.set_completed_split_info(result)
        return True


def create_web_output_destination(
    *,
    native_picker_available: bool,
    native_output_dir: str,
    browser_output_folder: str,
) -> OutputDestination:
    """Pilih strategi output web berdasarkan ketersediaan dialog folder server."""
    if native_picker_available:
        return NativeOutputDestination(native_output_dir)
    return BrowserOutputDestination(browser_output_folder)


def uses_native_folder_picker() -> bool:
    """Wrapper agar UI tidak memanggil folder_picker langsung."""
    return folder_picker_available()
