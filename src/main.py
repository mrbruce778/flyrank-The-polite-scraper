"""FlyRank A9 — Stage 1: fetch once, cache once."""

from pathlib import Path
import requests

CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/YOUR_USERNAME/YOUR_REPO)"
TIMEOUT_SECONDS = 10

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_FILE = CACHE_DIR / "catalogue-page-1.html"


def fetch_page(url: str) -> str:
    """Politely fetch a page: honest user-agent, timeout, status check."""
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)

    if response.status_code != 200:
        raise RuntimeError(f"Fetch failed: status {response.status_code} for {url}")

    return response.text


def get_catalogue_page_1() -> str:
    """Return page 1 HTML — from cache if we already have it, else fetch it."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if CACHE_FILE.exists():
        html = CACHE_FILE.read_text(encoding="utf-8")
        print(f"CACHE HIT: {CACHE_FILE.name} ({len(html)} bytes)")
        return html

    html = fetch_page(CATALOGUE_URL)
    CACHE_FILE.write_text(html, encoding="utf-8")
    print(f"FETCH: {CATALOGUE_URL} -> {CACHE_FILE.name} ({len(html)} bytes)")
    return html


def main() -> None:
    get_catalogue_page_1()


if __name__ == "__main__":
    main()