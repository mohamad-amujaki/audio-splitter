from __future__ import annotations

import base64
import json
from pathlib import Path

from models import SplitJobResult
from splitter import OutputFormat


def build_browser_files_payload(output_paths: list[Path], output_root: Path) -> list[dict[str, str]]:
    """Siapkan payload base64 untuk disimpan ke folder lokal lewat File System Access API."""
    resolved_root = output_root.expanduser().resolve()
    files_payload: list[dict[str, str]] = []

    for output_path in sorted(output_paths):
        resolved_output = output_path.expanduser().resolve()
        file_bytes = resolved_output.read_bytes()
        files_payload.append(
            {
                "relative_path": resolved_output.relative_to(resolved_root).as_posix(),
                "data": base64.b64encode(file_bytes).decode("ascii"),
            }
        )

    return files_payload


def encode_files_json(files_to_save: list[dict[str, str]] | None) -> str:
    """Serialisasi payload file untuk komponen browser."""
    return json.dumps(files_to_save or [], separators=(",", ":"))


def split_result_from_paths(
    *,
    source_name: str,
    segment_minutes: int,
    output_format: OutputFormat,
    output_paths: list[Path],
) -> SplitJobResult:
    """Bangun model hasil potongan dari daftar path output ffmpeg."""
    return SplitJobResult.from_paths(
        source_name=source_name,
        segment_minutes=segment_minutes,
        output_format=output_format,
        output_paths=output_paths,
    )
