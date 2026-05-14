from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from splitter import OUTPUT_FORMAT_MP3, OUTPUT_FORMAT_ORIGINAL, SplitterError, ensure_ffmpeg, ffmpeg_available, split_audio


def create_sample_wav(path: Path, *, seconds: int = 5) -> None:
    """Buat file audio pendek untuk pengujian integrasi ffmpeg."""
    ffmpeg_executable = ensure_ffmpeg()
    command = [
        ffmpeg_executable,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono",
        "-t",
        str(seconds),
        str(path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)


@unittest.skipUnless(ffmpeg_available(), "ffmpeg tidak tersedia di lingkungan ini")
class SplitAudioIntegrationTests(unittest.TestCase):
    def test_split_short_audio_creates_one_based_segment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "sample.wav"
            output_dir = root / "output"
            create_sample_wav(input_path)

            output_paths = split_audio(
                input_path=input_path,
                output_dir=output_dir,
                segment_minutes=10,
                output_format=OUTPUT_FORMAT_ORIGINAL,
            )

            self.assertEqual(len(output_paths), 1)
            self.assertEqual(output_paths[0].name, "sample_1.wav")
            self.assertEqual(output_paths[0].parent.name, "sample")
            self.assertTrue(output_paths[0].stat().st_size > 0)

    def test_split_rejects_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "sample.wav"
            output_dir = root / "output"
            create_sample_wav(input_path)
            split_audio(
                input_path=input_path,
                output_dir=output_dir,
                segment_minutes=10,
                output_format=OUTPUT_FORMAT_ORIGINAL,
            )

            with self.assertRaises(SplitterError):
                split_audio(
                    input_path=input_path,
                    output_dir=output_dir,
                    segment_minutes=10,
                    output_format=OUTPUT_FORMAT_ORIGINAL,
                )

    def test_split_can_convert_to_mp3(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "sample.wav"
            output_dir = root / "output"
            create_sample_wav(input_path)

            output_paths = split_audio(
                input_path=input_path,
                output_dir=output_dir,
                segment_minutes=10,
                output_format=OUTPUT_FORMAT_MP3,
            )

            self.assertEqual(output_paths[0].suffix, ".mp3")


if __name__ == "__main__":
    unittest.main()
