from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from splitter import OutputFormat


class WebSplitPhase(StrEnum):
    """Fase alur pemotongan di aplikasi web Streamlit."""
    IDLE = "idle"
    PROCESSING = "processing"
    SAVING = "saving"
    DONE = "done"
    ERROR = "error"


@dataclass(frozen=True)
class SplitJobResult:
    """Ringkasan hasil pemotongan yang dipakai UI dan laporan sukses."""
    source_name: str
    segment_minutes: int
    output_format: OutputFormat
    output_paths: tuple[Path, ...]

    @property
    def file_count(self) -> int:
        return len(self.output_paths)

    @property
    def output_subfolder(self) -> str:
        if not self.output_paths:
            return ""
        return self.output_paths[0].parent.name

    @classmethod
    def from_paths(
        cls,
        *,
        source_name: str,
        segment_minutes: int,
        output_format: OutputFormat,
        output_paths: list[Path],
    ) -> SplitJobResult:
        return cls(
            source_name=source_name,
            segment_minutes=segment_minutes,
            output_format=output_format,
            output_paths=tuple(output_paths),
        )


@dataclass(frozen=True)
class SplitSuccessContext:
    """Data yang dibutuhkan untuk menyusun pesan sukses lintas platform."""
    source_name: str
    file_count: int
    segment_minutes: int
    output_format: OutputFormat
    output_subfolder: str
    destination_label: str


@dataclass(frozen=True)
class BrowserFolderResult:
    """Hasil callback komponen folder browser."""
    name: str
    selected: bool
    saved: int
    error: str | None

    @classmethod
    def from_component_value(cls, value: Any | None) -> BrowserFolderResult | None:
        if value is None:
            return None

        if isinstance(value, dict):
            payload = value
        elif hasattr(value, "get"):
            payload = {
                "name": value.get("name"),
                "selected": value.get("selected"),
                "saved": value.get("saved"),
                "error": value.get("error"),
            }
        else:
            payload = {
                "name": getattr(value, "name", ""),
                "selected": getattr(value, "selected", False),
                "saved": getattr(value, "saved", 0),
                "error": getattr(value, "error", None),
            }

        return cls(
            name=str(payload.get("name") or ""),
            selected=bool(payload.get("selected")),
            saved=int(payload.get("saved") or 0),
            error=str(payload["error"]) if payload.get("error") else None,
        )
