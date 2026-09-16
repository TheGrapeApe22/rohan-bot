import json
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import Page, Playwright, sync_playwright


class InvalidUrlError(ValueError):
    pass

class PageTooLargeError(ValueError):
    pass


class ChromiumSession:
    def __init__(self, headless: bool = False, max_page_bytes: int = 5_000_000):
        self.max_page_bytes = max_page_bytes
        self.playwright: Playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def get_page(self, url: str) -> Page:
        """Navigate and return the same page in this Chromium session."""
        self.page.goto(url, wait_until="domcontentloaded")
        return self.page

    def _validate_url(self, url: str) -> None:
        parsed_url = urlparse(url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise InvalidUrlError("URL must be an absolute HTTP or HTTPS URL.")

    def _get_limited_content(self, url: str) -> str:
        page = self.context.new_page()

        def block_non_document_resources(route) -> None:
            if route.request.resource_type == "document":
                route.continue_()
            else:
                route.abort()

        page.route("**/*", block_non_document_resources)

        try:
            # "commit" returns as soon as response headers arrive, before the
            # document is fully downloaded and parsed.
            response = page.goto(url, wait_until="commit")
            content_length = response.header_value("content-length") if response else None
            if content_length:
                try:
                    declared_size = int(content_length)
                except ValueError as error:
                    raise PageTooLargeError("Page has an invalid Content-Length header.") from error

                if declared_size > self.max_page_bytes:
                    raise PageTooLargeError(
                        f"Page exceeds the {self.max_page_bytes:,}-byte limit."
                    )

            page.wait_for_load_state("domcontentloaded")
            content = page.content()
            if len(content.encode("utf-8")) > self.max_page_bytes:
                raise PageTooLargeError(
                    f"Page exceeds the {self.max_page_bytes:,}-byte limit."
                )

            return content
        finally:
            page.close()

    def get_metadata(self, url: str) -> dict[str, str | None]:
        self._validate_url(url)
        html = self._get_limited_content(url)
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
            oembed_html = self._get_limited_content(oembed_url)
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

    def close(self) -> None:
        self.browser.close()
        self.playwright.stop()

    def __enter__(self) -> "ChromiumSession":
        return self

    def __exit__(self, *args) -> None:
        self.close()


if __name__ == "__main__":
    url1 = "https://www.nytimes.com/2026/09/15/us/politics/trump-israel-bombs.html"
    url2 = "https://chsprospector.com/"
    url3 = "https://docs.google.com/spreadsheets/d/1l9prl692D_6PZLwiFYWFmzkBNQOoIL0Vg5v6HwuQMBA/edit?gid=0#gid=0"

    with ChromiumSession() as session:
        print(session.get_metadata(url1))
