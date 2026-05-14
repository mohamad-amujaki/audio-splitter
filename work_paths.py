from __future__ import annotations

import shutil
import time
from pathlib import Path

# Folder kerja sementara untuk upload dan output staging di mode browser.
WORK_ROOT = Path(".work")
UPLOAD_DIR = WORK_ROOT / "uploads"
TEMP_OUTPUT_DIR = WORK_ROOT / "output"
WORK_RETENTION_SECONDS = 6 * 60 * 60


def ensure_work_dirs() -> None:
    """Pastikan folder kerja sementara tersedia sebelum pemrosesan."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
