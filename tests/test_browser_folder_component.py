from __future__ import annotations

import unittest
from pathlib import Path

from browser_folder import component_definition, render_browser_folder_manager
from models import BrowserFolderResult
from streamlit.util import AttributeDictionary


class BrowserFolderComponentTests(unittest.TestCase):
    def test_component_definition_uses_v2(self) -> None:
        definition = component_definition()
        self.assertTrue(definition["uses_v2"])
        self.assertEqual(definition["name"], "browser_folder_manager")
        self.assertTrue(Path(definition["frontend_dir"]).joinpath("folder-component-v2.js").is_file())

    def test_browser_folder_result_parses_component_result(self) -> None:
        result = BrowserFolderResult.from_component_value(
            AttributeDictionary(
                {
                    "name": "Music",
                    "selected": True,
                    "saved": 2,
                    "error": None,
                }
            )
        )
        assert result is not None
        self.assertEqual(result.name, "Music")
        self.assertTrue(result.selected)
        self.assertEqual(result.saved, 2)
        self.assertIsNone(result.error)

    def test_render_wrapper_exposes_callable(self) -> None:
        self.assertTrue(callable(render_browser_folder_manager))


if __name__ == "__main__":
    unittest.main()
