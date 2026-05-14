from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from models import BrowserFolderResult
from persistence import encode_files_json

_FRONTEND_DIR = Path(__file__).resolve().parent / "browser_folder_frontend"
_COMPONENT_HTML = """
<div class="audio-folder-picker">
  <button id="pick-folder" type="button" aria-describedby="folder-status">
    Pilih folder lokal…
  </button>
  <p id="folder-status" role="status" aria-live="polite">Belum ada folder dipilih.</p>
</div>
"""
_COMPONENT_JS = (_FRONTEND_DIR / "folder-component-v2.js").read_text(encoding="utf-8")

_BROWSER_FOLDER_COMPONENT = st.components.v2.component(
    "browser_folder_manager",
    html=_COMPONENT_HTML,
    js=_COMPONENT_JS,
    isolate_styles=False,
)


def _noop_callback() -> None:
    return None


def render_browser_folder_manager(
    files_to_save: list[dict[str, str]] | None = None,
    *,
    key: str = "browser_folder_manager",
) -> BrowserFolderResult | None:
    """Render komponen folder browser CCv2 dan kembalikan status folder atau hasil simpan."""
    result = _BROWSER_FOLDER_COMPONENT(
        key=key,
        data={"files_json": encode_files_json(files_to_save)},
        on_name_change=_noop_callback,
        on_selected_change=_noop_callback,
        on_saved_change=_noop_callback,
        on_error_change=_noop_callback,
    )
    return BrowserFolderResult.from_component_value(result)


def component_definition() -> dict[str, Any]:
    """Metadata ringkas untuk pengujian registrasi komponen."""
    return {
        "name": "browser_folder_manager",
        "frontend_dir": str(_FRONTEND_DIR),
        "uses_v2": True,
    }
