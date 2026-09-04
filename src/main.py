"""FlyRank A9 — Stage 2: discover all three catalogue pages."""

import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
MAX_CATALOGUE_PAGES = 3
BASE_CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/YOUR_USERNAME/YOUR_REPO)"
TIMEOUT_SECONDS = 10
REQUEST_DELAY_SECONDS = 0.5

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"


def cache_filename_for(url: str) -> Path:
    """Build a stable cache filename for a catalogue page URL."""
    # e.g. .../catalogue/page-2.html -> catalogue-page-2.html
    name = url.rstrip("/").split("/")[-1]
    return CACHE_DIR / f"catalogue-{name}"


def fetch_page(url: str) -> str:
    """Politely fetch a page: honest user-agent, timeout, status check."""
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)

    if response.status_code != 200:
        raise RuntimeError(f"Fetch failed: status {response.status_code} for {url}")

    return response.text


def get_page(url: str) -> str:
    """Return page HTML from cache if present, else fetch, cache, and delay."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = cache_filename_for(url)

    if cache_file.exists():
        html = cache_file.read_text(encoding="utf-8")
        print(f"CACHE HIT: {cache_file.name} ({len(html)} bytes)")
        return html

    html = fetch_page(url)
    cache_file.write_text(html, encoding="utf-8")
    print(f"FETCH: {url} -> {cache_file.name} ({len(html)} bytes)")
    time.sleep(REQUEST_DELAY_SECONDS)  # only real requests get delayed
    return html


def extract_book_links(html: str, page_url: str) -> list[str]:
    """Return absolute URLs for every book listed on a catalogue page."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for article in soup.select("article.product_pod"):
        a_tag = article.select_one("h3 a")
        if a_tag and a_tag.get("href"):
            absolute_url = urljoin(page_url, a_tag["href"])
            links.append(absolute_url)
    return links


def find_next_page_url(html: str, page_url: str) -> str | None:
    """Return the absolute URL of the 'next' catalogue page, or None."""
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.select_one("li.next a")
    if next_link and next_link.get("href"):
        return urljoin(page_url, next_link["href"])
    return None


def discover_all_book_urls() -> list[str]:
    """Walk the catalogue pages via 'next' links and collect unique book URLs."""
    all_links: list[str] = []
    current_url: str | None = BASE_CATALOGUE_URL
    pages_visited = 0

    while current_url and pages_visited < MAX_CATALOGUE_PAGES:
        html = get_page(current_url)
        all_links.extend(extract_book_links(html, current_url))
        pages_visited += 1
        current_url = find_next_page_url(html, current_url)

    unique_links = list(dict.fromkeys(all_links))  # de-dupe, preserve order

    print(
        f"catalogue_pages={pages_visited} "
        f"discovered={len(all_links)} "
        f"unique_urls={len(unique_links)}"
    )
    return unique_links


def main() -> None:
    discover_all_book_urls()


if __name__ == "__main__":
    main()