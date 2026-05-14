from __future__ import annotations

import unittest

from web_seo import (
    PAGE_DESCRIPTION,
    PAGE_INTRO_MARKDOWN,
    PAGE_KEYWORDS,
    PAGE_TITLE,
    build_seo_meta_data,
)


class WebSeoTests(unittest.TestCase):
    def test_page_title_contains_primary_keywords(self) -> None:
        self.assertIn("Pemotong Audio", PAGE_TITLE)
        self.assertIn("MP3", PAGE_TITLE)

    def test_seo_copy_is_descriptive(self) -> None:
        self.assertGreater(len(PAGE_INTRO_MARKDOWN), 40)
        self.assertGreater(len(PAGE_DESCRIPTION), 40)
        self.assertIn("MP3", PAGE_INTRO_MARKDOWN)
        self.assertIn("folder output lokal", PAGE_DESCRIPTION)

    def test_build_seo_meta_data_contains_expected_fields(self) -> None:
        meta = build_seo_meta_data()
        self.assertEqual(meta["description"], PAGE_DESCRIPTION)
        self.assertEqual(meta["keywords"], PAGE_KEYWORDS)
        self.assertEqual(meta["og_title"], PAGE_TITLE)
        self.assertEqual(meta["twitter_description"], PAGE_DESCRIPTION)
        self.assertEqual(meta["robots"], "index, follow")


if __name__ == "__main__":
    unittest.main()
