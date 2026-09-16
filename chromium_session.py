import json
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright


class InvalidUrlError(ValueError):
    pass

class PageTooLargeError(ValueError):
    pass


class ChromiumSession:
    def __init__(
        self,
        playwright: Playwright,
        browser: Browser,
        context: BrowserContext,
        max_page_bytes: int,
    ):
        self.max_page_bytes = max_page_bytes
        self.playwright = playwright
        self.browser = browser
        self.context = context

    @classmethod
    async def create(
        cls, headless: bool = False, max_page_bytes: int = 5_000_000
    ) -> "ChromiumSession":
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context()
        return cls(playwright, browser, context, max_page_bytes)

    async def get_page(self, url: str) -> Page:
        """Navigate in this Chromium session and return a new page."""
        self._validate_url(url)
        page = await self.context.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        return page

    def _validate_url(self, url: str) -> None:
        parsed_url = urlparse(url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise InvalidUrlError("URL must be an absolute HTTP or HTTPS URL.")

    async def _get_limited_content(self, url: str) -> str:
        page = await self.context.new_page()

        async def block_non_document_resources(route) -> None:
            if route.request.resource_type == "document":
                await route.continue_()
            else:
                await route.abort()

        await page.route("**/*", block_non_document_resources)

        try:
            # "commit" returns as soon as response headers arrive, before the
            # document is fully downloaded and parsed.
            response = await page.goto(url, wait_until="commit")
            content_length = response.headers.get("content-length") if response else None
            if content_length:
                try:
                    declared_size = int(content_length)
                except ValueError as error:
                    raise PageTooLargeError("Page has an invalid Content-Length header.") from error

                if declared_size > self.max_page_bytes:
                    raise PageTooLargeError(
                        f"Page exceeds the {self.max_page_bytes:,}-byte limit."
                    )

            await page.wait_for_load_state("domcontentloaded")
            content = await page.content()
            if len(content.encode("utf-8")) > self.max_page_bytes:
                raise PageTooLargeError(
                    f"Page exceeds the {self.max_page_bytes:,}-byte limit."
                )

            return content
        finally:
            await page.close()

    async def get_metadata(self, url: str) -> dict[str, str | None]:
        self._validate_url(url)
        html = await self._get_limited_content(url)
        soup = BeautifulSoup(html, "html.parser")

        title = soup.find("meta", property="og:title")
        description = soup.find("meta", property="og:description")
        image = soup.find("meta", property="og:image")
        site_name = soup.find("meta", property="og:site_name")
        card = soup.find("meta", attrs={"property": "twitter:card"})
        if not card:
            card = soup.find("meta", attrs={"name": "twitter:card"})
        oembed = soup.find(
            "link",
            attrs={"rel": "alternate", "type": "application/json+oembed"},
        )

        oembed_url = urljoin(url, oembed["href"]) if oembed and oembed.get("href") else None
        author_name = None
        provider_name = None

        if oembed_url:
            self._validate_url(oembed_url)
            oembed_html = await self._get_limited_content(oembed_url)
            oembed_data = json.loads(BeautifulSoup(oembed_html, "html.parser").get_text())
            author_name = oembed_data.get("author_name")
            provider_name = oembed_data.get("provider_name")

        return {
            "title": title.get("content") if title else None,
            "description": description.get("content") if description else None,
            "image": image.get("content") if image else None,
            "site_name": site_name.get("content") if site_name else None,
            "card": card.get("content") if card else None,
            "oembed": oembed_url,
            "author_name": author_name,
            "provider_name": provider_name,
        }

    async def close(self) -> None:
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def __aenter__(self) -> "ChromiumSession":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()


async def main() -> None:
    url1 = "https://www.nytimes.com/2026/09/15/us/politics/trump-israel-bombs.html"
    url2 = "https://chsprospector.com/"
    url3 = "https://docs.google.com/spreadsheets/d/1l9prl692D_6PZLwiFYWFmzkBNQOoIL0Vg5v6HwuQMBA/edit?gid=0#gid=0"

    async with await ChromiumSession.create() as session:
        print(await session.get_metadata(url1))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
