from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from desktop_controller import DesktopSplitRequest, build_success_message
from folder_picker import folder_picker_available, pick_output_directory_for_web
from messages import build_split_success_message
from models import BrowserFolderResult, SplitJobResult, WebSplitPhase
from output_destination import (
    BrowserOutputDestination,
    NativeOutputDestination,
    create_web_output_destination,
)
from persistence import build_browser_files_payload, encode_files_json, split_result_from_paths
from splitter import (
    OUTPUT_FORMAT_MP3,
    OUTPUT_FORMAT_ORIGINAL,
    SplitterError,
    _output_extension,
    _segment_seconds,
    ffmpeg_available,
    supported_upload_types,
)
from ui_options import output_format_label
from work_paths import WORK_ROOT, cleanup_work_dirs, ensure_work_dirs


class SplitterHelperTests(unittest.TestCase):
    def test_supported_upload_types_sorted(self) -> None:
        self.assertEqual(supported_upload_types(), tuple(sorted(supported_upload_types())))

    def test_segment_seconds_accepts_allowed_values(self) -> None:
        self.assertEqual(_segment_seconds(10), 600)
        self.assertEqual(_segment_seconds(30), 1800)

    def test_segment_seconds_rejects_unknown_value(self) -> None:
        with self.assertRaises(SplitterError):
            _segment_seconds(15)

    def test_output_extension_for_mp3_mode(self) -> None:
        self.assertEqual(_output_extension(".m4a", OUTPUT_FORMAT_MP3), ".mp3")
        self.assertEqual(_output_extension(".m4a", OUTPUT_FORMAT_ORIGINAL), ".m4a")


class MessageTests(unittest.TestCase):
    def test_output_format_label(self) -> None:
        self.assertEqual(output_format_label(OUTPUT_FORMAT_ORIGINAL), "Pertahankan format asal")
        self.assertEqual(output_format_label(OUTPUT_FORMAT_MP3), "Konversi ke .mp3")

    def test_build_split_success_message_contains_key_details(self) -> None:
        message = build_split_success_message(
            source_name="lagu.m4a",
            file_count=3,
            segment_minutes=10,
            output_format=OUTPUT_FORMAT_ORIGINAL,
            output_subfolder="lagu",
            destination_label="/tmp/output",
        )
        self.assertIn("lagu.m4a", message)
        self.assertIn("3", message)
        self.assertIn("10 menit", message)
        self.assertIn("/tmp/output", message)


class BrowserPayloadTests(unittest.TestCase):
    def test_build_browser_files_payload_uses_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "lagu"
            nested.mkdir()
            output_file = nested / "lagu_1.m4a"
            output_file.write_bytes(b"audio")

            payload = build_browser_files_payload([output_file], root)

            self.assertEqual(len(payload), 1)
            self.assertEqual(payload[0]["relative_path"], "lagu/lagu_1.m4a")
            self.assertTrue(payload[0]["data"])

    def test_encode_files_json_is_compact(self) -> None:
        encoded = encode_files_json([{"relative_path": "a/b", "data": "Zg=="}])
        self.assertNotIn(" ", encoded)


class ModelTests(unittest.TestCase):
    def test_browser_folder_result_from_component_value(self) -> None:
        result = BrowserFolderResult.from_component_value(
            {"name": "Music", "selected": True, "saved": 2, "error": None}
        )
        assert result is not None
        self.assertEqual(result.name, "Music")
        self.assertEqual(result.saved, 2)

    def test_split_job_result_subfolder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "lagu"
            nested.mkdir()
            output_file = nested / "lagu_1.m4a"
            output_file.write_bytes(b"audio")
            result = split_result_from_paths(
                source_name="lagu.m4a",
                segment_minutes=10,
                output_format=OUTPUT_FORMAT_ORIGINAL,
                output_paths=[output_file],
            )
            self.assertEqual(result.output_subfolder, "lagu")
            self.assertEqual(result.file_count, 1)


class OutputDestinationTests(unittest.TestCase):
    def test_native_destination_requires_folder(self) -> None:
        destination = NativeOutputDestination("")
        with self.assertRaises(SplitterError):
            destination.validate_ready()

    def test_browser_destination_requires_folder_name(self) -> None:
        destination = BrowserOutputDestination("")
        with self.assertRaises(SplitterError):
            destination.validate_ready()

    def test_create_web_output_destination_prefers_native(self) -> None:
        destination = create_web_output_destination(
            native_picker_available=True,
            native_output_dir="/tmp/output",
            browser_output_folder="Music",
        )
        self.assertIsInstance(destination, NativeOutputDestination)


class RuntimeAvailabilityTests(unittest.TestCase):
    def test_folder_picker_available_is_cached(self) -> None:
        folder_picker_available.cache_clear()
        first = folder_picker_available()
        second = folder_picker_available()
        self.assertEqual(first, second)

    @patch("splitter.resolve_ffmpeg", return_value="/usr/bin/ffmpeg")
    def test_ffmpeg_available_uses_resolver(self, _mock_resolve) -> None:
        self.assertTrue(ffmpeg_available())

    def test_pick_output_directory_for_web_skips_tkinter(self) -> None:
        with patch(
            "folder_picker._pick_output_directory_with_platform_handlers",
            return_value="/tmp/output",
        ) as handler:
            selected = pick_output_directory_for_web()
        self.assertEqual(selected, "/tmp/output")
        handler.assert_called_once()


class WorkPathTests(unittest.TestCase):
    def test_cleanup_work_dirs_removes_old_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            upload_dir = work_root / "uploads"
            upload_dir.mkdir(parents=True)
            stale_file = upload_dir / "stale.m4a"
            stale_file.write_bytes(b"old")
            old_time = time.time() - (7 * 60 * 60)
            stale_file.touch(stale_file.stat().st_mtime)
            import os

            os.utime(stale_file, (old_time, old_time))

            with patch("work_paths.WORK_ROOT", work_root), patch(
                "work_paths.UPLOAD_DIR", upload_dir
            ), patch("work_paths.TEMP_OUTPUT_DIR", work_root / "output"):
                ensure_work_dirs()
                cleanup_work_dirs(max_age_seconds=60)

            self.assertFalse(stale_file.exists())


class DesktopControllerTests(unittest.TestCase):
    def test_build_success_message_uses_shared_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "lagu"
            nested.mkdir()
            output_file = nested / "lagu_1.m4a"
            output_file.write_bytes(b"audio")
            result = SplitJobResult.from_paths(
                source_name="lagu.m4a",
                segment_minutes=10,
                output_format=OUTPUT_FORMAT_ORIGINAL,
                output_paths=[output_file],
            )
            message = build_success_message(result, str(root))
            self.assertIn("lagu.m4a", message)
            self.assertIn("lagu/", message)


if __name__ == "__main__":
    unittest.main()
