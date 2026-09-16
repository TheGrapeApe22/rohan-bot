import asyncio
import ipaddress
import json
import socket
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright


class InvalidUrlError(ValueError):
    pass

class PageTooLargeError(ValueError):
    pass


class HttpStatusError(RuntimeError):
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
        cls,
        headless: bool = True,
        max_page_bytes: int = 5_000_000,
        navigation_timeout_ms: int = 15_000,
    ) -> "ChromiumSession":
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context(java_script_enabled=False)
        context.set_default_navigation_timeout(navigation_timeout_ms)
        return cls(playwright, browser, context, max_page_bytes)

    async def get_page(self, url: str) -> Page:
        """Navigate in this Chromium session and return a new page."""
        await self._validate_url(url)
        page = await self.context.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        return page

    async def _validate_url(self, url: str) -> None:
        if not isinstance(url, str) or len(url) > 2_048:
            raise InvalidUrlError("URL must be a string no longer than 2,048 characters.")

        try:
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            port = parsed_url.port
        except ValueError as error:
            raise InvalidUrlError("URL is malformed.") from error

        if (
            parsed_url.scheme not in {"http", "https"}
            or not hostname
            or parsed_url.username
            or parsed_url.password
            or port not in {None, 80, 443}
        ):
            raise InvalidUrlError("URL must be an absolute HTTP or HTTPS URL.")

        try:
            addresses = {
                info[4][0]
                for info in await asyncio.get_running_loop().getaddrinfo(
                    hostname, None, type=socket.SOCK_STREAM
                )
            }
        except socket.gaierror as error:
            raise InvalidUrlError("URL hostname could not be resolved.") from error

        if not addresses or any(
            not ipaddress.ip_address(address).is_global for address in addresses
        ):
            raise InvalidUrlError("URL must resolve only to public IP addresses.")

    async def _get_limited_content(self, url: str) -> str:
        page = await self.context.new_page()
        blocked_url: str | None = None

        async def block_non_document_resources(route) -> None:
            nonlocal blocked_url
            if route.request.resource_type == "document":
                try:
                    await self._validate_url(route.request.url)
                except InvalidUrlError:
                    blocked_url = route.request.url
                    await route.abort()
                else:
                    await route.continue_()
            else:
                await route.abort()

        await page.route("**/*", block_non_document_resources)

        try:
            # "commit" returns as soon as response headers arrive, before the
            # document is fully downloaded and parsed.
            response = await page.goto(url, wait_until="commit")

            if response is None:
                raise HttpStatusError("Page did not return an HTTP response.")
            if response.status != 200:
                raise HttpStatusError(f"Page returned HTTP {response.status}: {url}")
            
            content_length = response.headers.get("content-length")
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
        except Exception as error:
            if blocked_url:
                raise InvalidUrlError(
                    f"Navigation to unsafe URL was blocked: {blocked_url}"
                ) from error
            raise
        finally:
            await page.close()

    async def get_metadata(self, url: str) -> dict[str, str | None]:
        await self._validate_url(url)
        html = await self._get_limited_content(url)
        soup = BeautifulSoup(html, "html.parser")

        title = soup.find("meta", property="og:title")
        html_title = soup.find("title")
        title_text = (
            title.get("content")
            if title
            else html_title.get_text(strip=True) if html_title else None
        )
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
            await self._validate_url(oembed_url)
            if urlparse(oembed_url).hostname != urlparse(url).hostname:
                raise InvalidUrlError("Cross-host oEmbed URLs are not allowed.")
            oembed_html = await self._get_limited_content(oembed_url)
            oembed_data = json.loads(BeautifulSoup(oembed_html, "html.parser").get_text())
            author_name = oembed_data.get("author_name")
            provider_name = oembed_data.get("provider_name")

        return {
            "title": title_text if title_text else None,
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

    # url = input('enter url: ')
    url = 'https://excelwithchess.com/schools/homework/'

    async with await ChromiumSession.create() as session:
        print(await session.get_metadata(url))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
