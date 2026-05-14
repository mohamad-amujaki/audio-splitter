from __future__ import annotations

import unittest

from web_seo import PAGE_DESCRIPTION, PAGE_INTRO_MARKDOWN, PAGE_LEAD, PAGE_TITLE


class WebSeoTests(unittest.TestCase):
    def test_page_title_contains_primary_keywords(self) -> None:
        self.assertIn("Pemotong Audio", PAGE_TITLE)
        self.assertIn("MP3", PAGE_TITLE)

    def test_page_copy_is_descriptive(self) -> None:
        self.assertGreater(len(PAGE_LEAD), 40)
        self.assertGreater(len(PAGE_INTRO_MARKDOWN), 40)
        self.assertGreater(len(PAGE_DESCRIPTION), 40)
        self.assertIn("MP3", PAGE_INTRO_MARKDOWN)
        self.assertIn("folder output lokal", PAGE_DESCRIPTION)


if __name__ == "__main__":
    unittest.main()
