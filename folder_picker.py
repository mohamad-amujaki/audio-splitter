from __future__ import annotations

import shutil
import subprocess
import sys
from functools import lru_cache


class FolderPickerError(Exception):
    """Dipakai saat dialog folder native tidak dapat dibuka."""


def pick_output_directory(
    prompt: str = "Pilih folder output",
    *,
    prefer_tkinter: bool = True,
) -> str | None:
    """Buka dialog folder; desktop memakai Tkinter, web memakai dialog platform."""
    if prefer_tkinter:
        try:
            import tkinter as tk
            from tkinter import filedialog
        except ImportError:
            pass
        else:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            selected = filedialog.askdirectory(title=prompt, parent=root)
            root.destroy()
            return selected or None

    return _pick_output_directory_with_platform_handlers(prompt)


def pick_output_directory_for_web(prompt: str = "Pilih folder output") -> str | None:
    """Alias aman untuk Streamlit agar tidak memakai Tkinter di thread worker."""
    return pick_output_directory(prompt, prefer_tkinter=False)


def _pick_output_directory_with_platform_handlers(prompt: str) -> str | None:
    """Delegasikan pemilihan folder ke handler khusus platform."""
    if sys.platform == "darwin":
        return _pick_with_macos(prompt)
    if sys.platform == "win32":
        return _pick_with_windows(prompt)
    return _pick_with_linux(prompt)


@lru_cache(maxsize=1)
def folder_picker_available() -> bool:
    """Deteksi sekali per proses apakah dialog folder native tersedia di server."""
    if sys.platform == "darwin":
        return shutil.which("osascript") is not None
    if sys.platform == "win32":
        return True
    return shutil.which("zenity") is not None or shutil.which("kdialog") is not None


def _pick_with_macos(prompt: str) -> str | None:
    """Pilih folder di macOS melalui AppleScript."""
    if shutil.which("osascript") is None:
        raise FolderPickerError("Perintah osascript tidak ditemukan di macOS.")

    escaped_prompt = prompt.replace("\\", "\\\\").replace('"', '\\"')
    script = f'POSIX path of (choose folder with prompt "{escaped_prompt}")'
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    selected = result.stdout.strip()
    return selected or None


def _pick_with_windows(prompt: str) -> str | None:
    """Pilih folder di Windows melalui FolderBrowserDialog PowerShell."""
    escaped_prompt = prompt.replace("'", "''")
    command = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
        f"$dialog.Description = '{escaped_prompt}'; "
        "if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { "
        "Write-Output $dialog.SelectedPath "
        "}"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    selected = result.stdout.strip()
    return selected or None


def _pick_with_linux(prompt: str) -> str | None:
    """Pilih folder di Linux melalui zenity atau kdialog."""
    if shutil.which("zenity") is not None:
        result = subprocess.run(
            ["zenity", "--file-selection", "--directory", f"--title={prompt}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        selected = result.stdout.strip()
        return selected or None

    if shutil.which("kdialog") is not None:
        result = subprocess.run(
            ["kdialog", "--getexistingdirectory", ".", "--title", prompt],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        selected = result.stdout.strip()
        return selected or None

    raise FolderPickerError(
        "Dialog folder tidak tersedia. Instal zenity atau kdialog di Linux ini."
    )
