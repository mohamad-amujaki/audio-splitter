from __future__ import annotations

from splitter import (
    ALLOWED_SEGMENT_MINUTES,
    OUTPUT_FORMAT_MP3,
    OUTPUT_FORMAT_ORIGINAL,
    supported_upload_types,
)

# Durasi potongan yang ditampilkan di web dan desktop.
SEGMENT_OPTIONS = tuple(sorted(ALLOWED_SEGMENT_MINUTES))

# Label format output yang dipakai bersama oleh semua UI.
OUTPUT_FORMAT_OPTIONS = (
    (OUTPUT_FORMAT_ORIGINAL, "Pertahankan format asal"),
    (OUTPUT_FORMAT_MP3, "Konversi ke .mp3"),
)
OUTPUT_FORMAT_LABELS = dict(OUTPUT_FORMAT_OPTIONS)

# Metadata upload Streamlit.
SUPPORTED_AUDIO_TYPES = supported_upload_types()
SUPPORTED_AUDIO_LABEL = ", ".join(f".{extension}" for extension in SUPPORTED_AUDIO_TYPES)


def output_format_label(output_format: str) -> str:
    """Kembalikan label manusia untuk kode format output."""
    return OUTPUT_FORMAT_LABELS[output_format]


def segment_label(minutes: int) -> str:
    """Format label durasi potongan untuk radio button."""
    return f"{minutes} menit"
