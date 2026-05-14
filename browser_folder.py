from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_COMPONENT_PATH = Path(__file__).resolve().parent / "browser_folder_frontend"
_browser_folder_component = components.declare_component(
    "browser_folder_manager",
    path=str(_COMPONENT_PATH),
)


def render_browser_folder_manager(
    files_to_save: list[dict[str, str]] | None = None,
    *,
    key: str = "browser_folder_manager",
) -> dict[str, Any] | None:
    files_json = json.dumps(files_to_save or [])
    result = _browser_folder_component(files_json=files_json, key=key)
    if not isinstance(result, dict):
        return None
    return result


def build_browser_files_payload(output_paths: list[Path], output_root: Path) -> list[dict[str, str]]:
    resolved_root = output_root.expanduser().resolve()
    files_payload: list[dict[str, str]] = []
    for output_path in output_paths:
        resolved_output = output_path.expanduser().resolve()
        files_payload.append(
            {
                "relative_path": resolved_output.relative_to(resolved_root).as_posix(),
                "data": base64.b64encode(resolved_output.read_bytes()).decode("ascii"),
            }
        )
    return files_payload
