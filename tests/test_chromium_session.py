import unittest
from unittest.mock import AsyncMock

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from utils.chromium_session import ChromiumSession, MetadataTimeoutError


class ChromiumSessionTimeoutTests(unittest.IsolatedAsyncioTestCase):
    async def test_navigation_timeout_closes_page_and_has_readable_error(self):
        page = AsyncMock()
        page.goto.side_effect = PlaywrightTimeoutError("Page.goto: Timeout 10000ms exceeded.")
        context = AsyncMock()
        context.new_page.return_value = page
        session = ChromiumSession(None, None, context, 5_000_000)

        with self.assertRaisesRegex(MetadataTimeoutError, "too long to load"):
            await session._get_limited_content("https://example.com")

        page.close.assert_awaited_once()

    async def test_optional_oembed_timeout_preserves_page_metadata(self):
        session = ChromiumSession(None, None, None, 5_000_000)
        session._validate_url = AsyncMock()
        session._get_limited_content = AsyncMock(side_effect=[
            '<html><head><title>Example</title>'
            '<meta property="og:description" content="Description">'
            '<link rel="alternate" type="application/json+oembed" href="/oembed">'
            '</head></html>',
            MetadataTimeoutError("The page took too long to load."),
        ])

        result = await session.get_metadata("https://example.com/article")

        self.assertEqual(result["title"], "Example")
        self.assertEqual(result["description"], "Description")
        self.assertIsNone(result["author"])
        self.assertIsNone(result["provider"])
        self.assertEqual(session._get_limited_content.await_count, 2)


if __name__ == "__main__":
    unittest.main()
