from __future__ import annotations

import shutil
import subprocess
import sys


class FolderPickerError(Exception):
    """Raised when no folder picker can be opened on this system."""


def pick_output_directory(prompt: str = "Pilih folder output") -> str | None:
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
    """Use platform dialogs via subprocess; safe from Streamlit worker threads."""
    return _pick_output_directory_with_platform_handlers(prompt)


def _pick_output_directory_with_platform_handlers(prompt: str) -> str | None:
    if sys.platform == "darwin":
        return _pick_with_macos(prompt)
    if sys.platform == "win32":
        return _pick_with_windows(prompt)
    return _pick_with_linux(prompt)


def folder_picker_available() -> bool:
    if sys.platform == "darwin":
        return shutil.which("osascript") is not None
    if sys.platform == "win32":
        return True
    return shutil.which("zenity") is not None or shutil.which("kdialog") is not None


def _pick_with_macos(prompt: str) -> str | None:
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
