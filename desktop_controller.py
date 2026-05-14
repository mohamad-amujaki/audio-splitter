from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from messages import build_desktop_success_message
from models import SplitJobResult
from persistence import split_result_from_paths
from splitter import OutputFormat, SplitterError, split_audio


@dataclass(frozen=True)
class DesktopSplitRequest:
    """Parameter pemotongan yang dikirim dari UI desktop ke worker thread."""
    input_path: Path
    output_dir: Path
    segment_minutes: int
    output_format: OutputFormat
    source_name: str


def execute_split(request: DesktopSplitRequest) -> SplitJobResult:
    """Jalankan pemotongan ffmpeg di thread worker desktop."""
    output_paths = split_audio(
        input_path=request.input_path,
        output_dir=request.output_dir,
        segment_minutes=request.segment_minutes,
        output_format=request.output_format,
    )
    return split_result_from_paths(
        source_name=request.source_name,
        segment_minutes=request.segment_minutes,
        output_format=request.output_format,
        output_paths=output_paths,
    )


def build_success_message(result: SplitJobResult, destination_label: str) -> str:
    """Susun pesan sukses desktop dengan format yang selaras dengan web."""
    return build_desktop_success_message(
        source_name=result.source_name,
        file_count=result.file_count,
        segment_minutes=result.segment_minutes,
        output_format=result.output_format,
        output_subfolder=result.output_subfolder,
        destination_label=destination_label,
    )


def run_desktop_split(request: DesktopSplitRequest) -> str:
    """Jalankan pemotongan dan kembalikan pesan sukses atau lempar SplitterError."""
    result = execute_split(request)
    return build_success_message(result, str(request.output_dir))
