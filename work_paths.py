from __future__ import annotations

import shutil
import time
from pathlib import Path

from models import SplitJobResult

# Folder kerja sementara untuk upload dan output staging di mode browser.
WORK_ROOT = Path(".work")
UPLOAD_DIR = WORK_ROOT / "uploads"
TEMP_OUTPUT_DIR = WORK_ROOT / "output"
WORK_RETENTION_SECONDS = 6 * 60 * 60


def ensure_work_dirs() -> None:
    """Pastikan folder kerja sementara tersedia sebelum pemrosesan."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _path_within_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _delete_path(path: Path) -> None:
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        return

    try:
        if resolved.is_dir():
            shutil.rmtree(resolved, ignore_errors=True)
        elif resolved.is_file():
            resolved.unlink(missing_ok=True)
    except OSError:
        return


def cleanup_server_staging(*, input_path: Path, result: SplitJobResult | None = None) -> None:
    """Hapus file input dan hasil staging di server setelah hasil ada di folder lokal pengguna."""
    ensure_work_dirs()
    upload_root = UPLOAD_DIR.resolve()
    temp_root = TEMP_OUTPUT_DIR.resolve()

    resolved_input = input_path.expanduser().resolve()
    if _path_within_root(resolved_input, upload_root):
        _delete_path(resolved_input)

    if result is None:
        return

    staging_directories: set[Path] = set()
    for output_path in result.output_paths:
        resolved_output = output_path.expanduser().resolve()
        if not _path_within_root(resolved_output, temp_root):
            continue
        staging_directories.add(resolved_output.parent)
        _delete_path(resolved_output)

    for directory in sorted(staging_directories, key=lambda path: len(path.parts), reverse=True):
        if directory.exists() and _path_within_root(directory, temp_root):
            _delete_path(directory)


def cleanup_work_dirs(*, max_age_seconds: int = WORK_RETENTION_SECONDS) -> None:
    """Hapus artefak lama di folder kerja agar disk tidak terus terisi."""
    ensure_work_dirs()
    cutoff = time.time() - max_age_seconds
    for work_dir in (UPLOAD_DIR, TEMP_OUTPUT_DIR):
        for path in work_dir.iterdir():
            try:
                modified_at = path.stat().st_mtime
            except OSError:
                continue
            if modified_at >= cutoff:
                continue
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
