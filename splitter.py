from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Literal

ALLOWED_SEGMENT_MINUTES = frozenset({10, 20, 30})
ALLOWED_AUDIO_EXTENSIONS = frozenset(
    {
        ".m4a",
        ".mp3",
        ".wav",
        ".aac",
        ".ogg",
        ".flac",
        ".opus",
        ".wma",
        ".m4b",
        ".aiff",
        ".aif",
    }
)
OUTPUT_FORMAT_ORIGINAL = "original"
OUTPUT_FORMAT_MP3 = "mp3"
OutputFormat = Literal["original", "mp3"]


class SplitterError(Exception):
    """Raised when audio splitting cannot proceed."""


def resolve_ffmpeg() -> str | None:
    for environment_key in ("FFMPEG_BINARY", "FFMPEG_PATH"):
        configured = os.environ.get(environment_key)
        if configured:
            configured_path = Path(configured).expanduser()
            if configured_path.is_file():
                return str(configured_path)

    located = shutil.which("ffmpeg")
    if located:
        return located

    try:
        import imageio_ffmpeg
    except ImportError:
        return None

    bundled = imageio_ffmpeg.get_ffmpeg_exe()
    if bundled and Path(bundled).is_file():
        return bundled
    return None


def ffmpeg_available() -> bool:
    return resolve_ffmpeg() is not None


def ensure_ffmpeg() -> str:
    resolved = resolve_ffmpeg()
    if not resolved:
        raise SplitterError(
            "ffmpeg tidak ditemukan di server. "
            "Untuk Streamlit Community Cloud, pastikan file packages.txt berisi ffmpeg "
            "lalu deploy ulang aplikasi."
        )
    return resolved


def ensure_output_dir(output_dir: Path) -> Path:
    resolved = output_dir.expanduser().resolve()
    if resolved.exists():
        if not resolved.is_dir():
            raise SplitterError(f"Path output bukan folder: {resolved}")
    else:
        resolved.mkdir(parents=True, exist_ok=True)

    if not resolved.is_dir():
        raise SplitterError(f"Folder output tidak valid: {resolved}")

    test_file = resolved / ".write_test"
    try:
        test_file.write_text("", encoding="utf-8")
        test_file.unlink()
    except OSError as exc:
        raise SplitterError(f"Folder output tidak dapat ditulis: {resolved}") from exc

    return resolved


def _segment_seconds(segment_minutes: int) -> int:
    if segment_minutes not in ALLOWED_SEGMENT_MINUTES:
        allowed = ", ".join(str(value) for value in sorted(ALLOWED_SEGMENT_MINUTES))
        raise SplitterError(f"Durasi potong tidak didukung. Pilih salah satu: {allowed} menit.")
    return segment_minutes * 60


def supported_upload_types() -> tuple[str, ...]:
    return tuple(sorted(extension.lstrip(".") for extension in ALLOWED_AUDIO_EXTENSIONS))


def supported_audio_filetypes() -> list[tuple[str, str]]:
    extensions = " ".join(f"*{extension}" for extension in sorted(ALLOWED_AUDIO_EXTENSIONS))
    return [("Berkas audio didukung", extensions), ("Semua file", "*.*")]


def _validate_output_format(output_format: str) -> OutputFormat:
    if output_format not in {OUTPUT_FORMAT_ORIGINAL, OUTPUT_FORMAT_MP3}:
        raise SplitterError("Format output tidak didukung. Pilih format asal atau .mp3.")
    return output_format


def _output_extension(input_extension: str, output_format: OutputFormat) -> str:
    if output_format == OUTPUT_FORMAT_MP3:
        return ".mp3"
    return input_extension


def _codec_args(input_extension: str, output_format: OutputFormat) -> list[str]:
    if output_format == OUTPUT_FORMAT_ORIGINAL:
        return ["-c", "copy"]
    if input_extension == ".mp3":
        return ["-c", "copy"]
    return ["-c:a", "libmp3lame", "-q:a", "2"]


def _validate_audio_extension(path: Path) -> str:
    extension = path.suffix.lower()
    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_AUDIO_EXTENSIONS))
        raise SplitterError(
            f"Format audio tidak didukung: {extension or '(tanpa ekstensi)'}. "
            f"Format yang didukung: {allowed}."
        )
    return extension


def _rename_segments_to_one_based(output_dir: Path, stem: str, extension: str) -> list[Path]:
    zero_based_paths = sorted(
        output_dir.glob(f"{stem}_*{extension}"),
        key=lambda path: int(path.stem.rsplit("_", maxsplit=1)[-1]),
    )
    if not zero_based_paths:
        raise SplitterError("ffmpeg selesai tetapi tidak menghasilkan file potongan.")

    one_based_paths: list[Path] = []
    for index in range(len(zero_based_paths) - 1, -1, -1):
        source = zero_based_paths[index]
        target = output_dir / f"{stem}_{index + 1}{extension}"
        if target.exists() and target != source:
            raise SplitterError(f"File output sudah ada: {target.name}")
        source.rename(target)
        one_based_paths.append(target)

    one_based_paths.reverse()
    return one_based_paths


def split_audio(
    input_path: Path,
    output_dir: Path,
    segment_minutes: int,
    output_format: OutputFormat = OUTPUT_FORMAT_ORIGINAL,
) -> list[Path]:
    ffmpeg_executable = ensure_ffmpeg()
    validated_output_format = _validate_output_format(output_format)

    resolved_input = input_path.expanduser().resolve()
    if not resolved_input.is_file():
        raise SplitterError(f"File input tidak ditemukan: {resolved_input}")
    input_extension = _validate_audio_extension(resolved_input)
    if resolved_input.stat().st_size == 0:
        raise SplitterError("File input kosong.")

    resolved_output = ensure_output_dir(output_dir)
    segment_seconds = _segment_seconds(segment_minutes)
    stem = resolved_input.stem
    resolved_output = ensure_output_dir(resolved_output / stem)
    output_extension = _output_extension(input_extension, validated_output_format)
    first_output = resolved_output / f"{stem}_1{output_extension}"
    if first_output.exists():
        raise SplitterError(
            f"File output sudah ada: {first_output.name}. Pilih folder lain atau hapus file tersebut."
        )

    segment_pattern = resolved_output / f"{stem}_%d{output_extension}"
    command = [
        ffmpeg_executable,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(resolved_input),
        "-map",
        "0",
        *_codec_args(input_extension, validated_output_format),
        "-f",
        "segment",
        "-segment_time",
        str(segment_seconds),
        "-reset_timestamps",
        "1",
        str(segment_pattern),
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        message = stderr or "ffmpeg gagal memproses file."
        raise SplitterError(message) from exc

    return _rename_segments_to_one_based(resolved_output, stem, output_extension)


def split_m4a(
    input_path: Path,
    output_dir: Path,
    segment_minutes: int,
    output_format: OutputFormat = OUTPUT_FORMAT_ORIGINAL,
) -> list[Path]:
    return split_audio(input_path, output_dir, segment_minutes, output_format)
