import unittest
from web_utils import LinkHandler


class TestLinkHandler(unittest.TestCase):
    def setUp(self):
        self.handler = LinkHandler()

    def test_extract_shortcode_instagram(self):
        test_cases = [
            ("https://www.instagram.com/p/BsOGulcndj-/", "BsOGulcndj-"),
            ("https://instagram.com/reel/CuZ7YF8oQJZ/", "CuZ7YF8oQJZ"),
            ("http://www.instagram.com/p/ABC123/", "ABC123"),
            ("https://instagram.com/p/AbC-123_xYz/?param=value", "AbC-123_xYz"),
        ]

        for url, expected in test_cases:
            with self.subTest(url=url):
                self.assertEqual(self.handler.extract_shortcode(url), expected)

    def test_extract_shortcode_tiktok(self):
        test_cases = [
            ("https://vm.tiktok.com/ZMebxCR7T/", "ZMebxCR7T"),
            (
                "http://www.tiktok.com/@user123/video/1234567890123456789",
                "1234567890123456789",
            ),
            (
                "https://tiktok.com/@user.name/video/9876543210987654321/",
                "9876543210987654321",
            ),
        ]

        for url, expected in test_cases:
            with self.subTest(url=url):
                self.assertEqual(self.handler.extract_shortcode(url), expected)

    def test_extract_shortcode_invalid(self):
        invalid_urls = [
            "https://www.google.com",
            "not a url",
            "https://www.instagram.com/username/",
            "https://www.reddit.com/r/subreddit/",
            "https://tiktok.com/@username/",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertIsNone(self.handler.extract_shortcode(url))


if __name__ == "__main__":
    unittest.main()
