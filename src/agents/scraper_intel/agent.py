"""
Scraper-Intel Agent - Web Intelligence Gathering
Full implementation with Playwright for intelligent web scraping.
"""

import asyncio
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import Browser, Page, async_playwright

from src.agents.base import BaseAgent
from src.core import get_settings
from src.core.models import ScrapedContent


@dataclass
class ScrapeRequest:
    """Input for Scraper-Intel agent."""
    url: str
    depth: int = 2
    max_pages: int = 50
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=lambda: [
        r".*\.(jpg|jpeg|png|gif|svg|pdf|zip|exe)$",
        r".*/login.*",
        r".*/admin.*",
        r".*#.*",  # Fragment URLs
    ])
    wait_for_js: bool = True
    timeout_ms: int = 30000


class ScraperIntelAgent(BaseAgent[ScrapeRequest, list[ScrapedContent]]):
    """
    Web intelligence gathering agent using Playwright.

    Responsibilities:
    1. Navigate to target URL with full JS rendering
    2. Detect site structure (menu, sitemap, links)
    3. Extract clean content (text, tables, lists)
    4. Filter irrelevant content (navigation, footers, ads)
    5. Convert to clean Markdown
    """

    def __init__(self):
        super().__init__("scraper_intel")
        self.settings = get_settings()
        self.browser: Browser | None = None
        self.visited_urls: set[str] = set()
        self.base_domain: str = ""

    async def execute(self, input_data: ScrapeRequest) -> list[ScrapedContent]:
        """
        Execute web scraping operation.

        Algorithm:
        1. Initialize Playwright browser
        2. Start from root URL
        3. BFS through links up to max_depth
        4. Extract and clean content from each page
        5. Return list of scraped content
        """
        self.log.info(
            "scrape_started",
            url=input_data.url,
            depth=input_data.depth,
            max_pages=input_data.max_pages,
        )

        # Parse base domain for same-domain filtering
        parsed = urlparse(input_data.url)
        self.base_domain = parsed.netloc

        results: list[ScrapedContent] = []
        self.visited_urls.clear()

        async with async_playwright() as p:
            # Launch browser
            self.browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )

            try:
                # BFS queue: (url, depth)
                queue: list[tuple[str, int]] = [(input_data.url, 0)]

                while queue and len(results) < input_data.max_pages:
                    current_url, current_depth = queue.pop(0)

                    # Skip if already visited or too deep
                    if current_url in self.visited_urls:
                        continue
                    if current_depth > input_data.depth:
                        continue

                    # Check exclusion patterns
                    if self._should_exclude(current_url, input_data.exclude_patterns):
                        self.log.debug("url_excluded", url=current_url)
                        continue

                    self.visited_urls.add(current_url)

                    try:
                        # Scrape page
                        content, new_links = await self._scrape_page(
                            current_url,
                            input_data.wait_for_js,
                            input_data.timeout_ms,
                        )

                        if content:
                            results.append(content)
                            self.log.info(
                                "page_scraped",
                                url=current_url,
                                content_length=len(content.content),
                            )

                        # Add discovered links to queue
                        if current_depth < input_data.depth:
                            for link in new_links:
                                if link not in self.visited_urls:
                                    queue.append((link, current_depth + 1))

                    except Exception as e:
                        self.log.warning(
                            "scrape_page_failed",
                            url=current_url,
                            error=str(e),
                        )

            finally:
                await self.browser.close()

        self.log.info(
            "scrape_completed",
            pages_scraped=len(results),
            pages_discovered=len(self.visited_urls),
        )

        return results

    async def _scrape_page(
        self, url: str, wait_for_js: bool, timeout_ms: int
    ) -> tuple[ScrapedContent | None, list[str]]:
        """
        Scrape a single page.

        Returns:
            Tuple of (content, discovered_links)
        """
        if not self.browser:
            return None, []

        context = await self.browser.new_context(
            user_agent=self.settings.scraper_user_agent,
            viewport={"width": 1920, "height": 1080},
        )

        page = await context.new_page()
        discovered_links: list[str] = []

        try:
            # Navigate to page
            response = await page.goto(
                url,
                wait_until="networkidle" if wait_for_js else "domcontentloaded",
                timeout=timeout_ms,
            )

            if not response or response.status >= 400:
                self.log.warning("page_error", url=url, status=response.status if response else None)
                return None, []

            # Wait for dynamic content
            if wait_for_js:
                await asyncio.sleep(1)  # Extra wait for JS rendering

            # Get page content
            html = await page.content()
            title = await page.title()

            # Extract links for crawling
            discovered_links = await self._extract_links(page, url)

            # Parse and clean content
            content_md = self._html_to_markdown(html)
            content_hash = hashlib.md5(content_md.encode()).hexdigest()

            return ScrapedContent(
                url=url,
                title=title or "Untitled",
                content=content_md,
                content_hash=content_hash,
                scraped_at=datetime.utcnow(),
                metadata={
                    "status_code": response.status,
                    "content_type": response.headers.get("content-type", ""),
                },
            ), discovered_links

        except Exception as e:
            self.log.error("page_scrape_error", url=url, error=str(e))
            return None, []

        finally:
            await context.close()

    async def _extract_links(self, page: Page, base_url: str) -> list[str]:
        """Extract all valid links from page."""
        links: list[str] = []

        try:
            hrefs = await page.eval_on_selector_all(
                "a[href]",
                "elements => elements.map(e => e.href)"
            )

            for href in hrefs:
                if not href:
                    continue

                # Normalize URL
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)

                # Only same-domain links
                if parsed.netloc == self.base_domain:
                    # Remove fragment
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if parsed.query:
                        clean_url += f"?{parsed.query}"

                    links.append(clean_url)

        except Exception as e:
            self.log.warning("link_extraction_failed", error=str(e))

        return list(set(links))  # Deduplicate

    def _html_to_markdown(self, html: str) -> str:
        """
        Convert HTML to clean Markdown.
        Removes navigation, footers, scripts, styles.
        """
        soup = BeautifulSoup(html, "lxml")

        # Remove unwanted elements
        for tag in soup.find_all([
            "script", "style", "nav", "footer", "header",
            "aside", "noscript", "iframe", "form",
        ]):
            tag.decompose()

        # Remove elements by class/id patterns (common navigation/ads)
        for element in soup.find_all(
            class_=re.compile(r"(nav|menu|sidebar|footer|header|cookie|banner|ad)", re.I)
        ):
            element.decompose()

        for element in soup.find_all(
            id=re.compile(r"(nav|menu|sidebar|footer|header|cookie|banner|ad)", re.I)
        ):
            element.decompose()

        # Find main content (prefer <main>, <article>, or <div role="main">)
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find(attrs={"role": "main"})
            or soup.find("div", class_=re.compile(r"(content|main|body)", re.I))
            or soup.body
        )

        if not main_content:
            return ""

        # Convert to Markdown
        lines: list[str] = []
        self._element_to_markdown(main_content, lines)

        # Clean up
        text = "\n".join(lines)
        text = re.sub(r"\n{3,}", "\n\n", text)  # Max 2 newlines
        text = re.sub(r"[ \t]+", " ", text)  # Collapse spaces
        text = text.strip()

        return text

    def _element_to_markdown(self, element, lines: list[str], depth: int = 0):
        """Recursively convert element to Markdown lines."""
        if element.name is None:
            # Text node
            text = element.strip()
            if text:
                lines.append(text)
            return

        tag = element.name.lower()

        # Headings
        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag[1])
            text = element.get_text(strip=True)
            if text:
                lines.append(f"\n{'#' * level} {text}\n")
            return

        # Paragraphs
        if tag == "p":
            text = element.get_text(strip=True)
            if text:
                lines.append(f"\n{text}\n")
            return

        # Lists
        if tag == "ul":
            for li in element.find_all("li", recursive=False):
                text = li.get_text(strip=True)
                if text:
                    lines.append(f"- {text}")
            lines.append("")
            return

        if tag == "ol":
            for i, li in enumerate(element.find_all("li", recursive=False), 1):
                text = li.get_text(strip=True)
                if text:
                    lines.append(f"{i}. {text}")
            lines.append("")
            return

        # Tables
        if tag == "table":
            self._table_to_markdown(element, lines)
            return

        # Links (keep text, ignore href for now)
        if tag == "a":
            text = element.get_text(strip=True)
            if text:
                lines.append(text)
            return

        # Recurse for other elements
        for child in element.children:
            if hasattr(child, "name"):
                self._element_to_markdown(child, lines, depth + 1)
            elif isinstance(child, str) and child.strip():
                lines.append(child.strip())

    def _table_to_markdown(self, table, lines: list[str]):
        """Convert HTML table to Markdown table."""
        rows = table.find_all("tr")
        if not rows:
            return

        lines.append("")

        for i, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            cell_texts = [c.get_text(strip=True).replace("|", "\\|") for c in cells]
            lines.append("| " + " | ".join(cell_texts) + " |")

            # Add header separator after first row
            if i == 0:
                lines.append("| " + " | ".join(["---"] * len(cells)) + " |")

        lines.append("")

    def _should_exclude(self, url: str, patterns: list[str]) -> bool:
        """Check if URL matches any exclusion pattern."""
        for pattern in patterns:
            if re.match(pattern, url, re.I):
                return True
        return False

    def _build_system_prompt(self) -> str:
        return """
Jesteś agentem Scraper-Intel, specjalistą od zbierania danych ze stron WWW.
Twoje zadanie: pobrać pełną treść strony, uwzględniając dynamiczne elementy.
Pomiń: nawigację, stopki, reklamy, pliki cookie.
Zachowaj: artykuły, tabele, listy, formularze informacyjne.
Format wyjścia: czysty Markdown.
"""
