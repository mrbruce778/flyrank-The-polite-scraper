"""FlyRank A9 — Stage 2: discover all three catalogue pages."""

import time
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime, timezone
import hashlib
import requests
import json
import re
from pydantic import BaseModel, HttpUrl, ValidationError
from bs4 import BeautifulSoup
MAX_CATALOGUE_PAGES = 3
BASE_CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/YOUR_USERNAME/YOUR_REPO)"
TIMEOUT_SECONDS = 10
REQUEST_DELAY_SECONDS = 0.5
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"

class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_gbp: float
    price_text: str
    availability_text: str
    rating_text: str | None
    description: str | None
    source_page: HttpUrl
    fetched_at: str

def cache_filename_for(url: str) -> Path:
    """Build a stable cache filename for a catalogue page URL."""
    # e.g. .../catalogue/page-2.html -> catalogue-page-2.html
    name = url.rstrip("/").split("/")[-1]
    return CACHE_DIR / f"catalogue-{name}"

def cache_filename_for_detail_page(url: str) -> Path:
    """Build a stable cache filename for a book detail page URL."""
    slug = url.rstrip("/").split("/")[-2]  # e.g. 'a-light-in-the-attic_1000'
    return CACHE_DIR / f"book-{slug}.html"

def fetch_page(url: str) -> str:
    """Politely fetch a page: honest user-agent, timeout, status check."""
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)

    if response.status_code != 200:
        raise RuntimeError(f"Fetch failed: status {response.status_code} for {url}")

    return response.text


def get_page(url: str, cache_path_fn=cache_filename_for) -> str:
    """Return page HTML from cache if present, else fetch, cache, and delay."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = cache_path_fn(url)

    if cache_file.exists():
        html = cache_file.read_text(encoding="utf-8")
        print(f"CACHE HIT: {cache_file.name} ({len(html)} bytes)")
        return html

    html = fetch_page(url)
    cache_file.write_text(html, encoding="utf-8")
    print(f"FETCH: {url} -> {cache_file.name} ({len(html)} bytes)")
    time.sleep(REQUEST_DELAY_SECONDS)
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
def extract_book_record(html: str, product_url: str, source_page: str) -> dict:
    """Pull the 8 raw fields out of a single book detail page."""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("div.product_main h1").get_text(strip=True)

    price_text = soup.select_one("p.price_color").get_text(strip=True)

    availability_text = soup.select_one("p.availability").get_text(strip=True)

    # Rating is stored as a CSS class, e.g. class="star-rating Three"
    rating_tag = soup.select_one("p.star-rating")
    rating_classes = rating_tag.get("class", []) if rating_tag else []
    rating_text = next((c for c in rating_classes if c != "star-rating"), None)

    # Not every book has a description
    description_tag = soup.select_one("#product_description ~ p")
    description = description_tag.get_text(strip=True) if description_tag else None

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
def parse_price_gbp(price_text: str) -> float:
    """Turn '£51.77' into 51.77. Raises ValueError if no number is found."""
    match = re.search(r"[\d.]+", price_text)
    if not match:
        raise ValueError(f"Could not parse a number out of price_text: {price_text!r}")
    return float(match.group())


def clean_and_validate_records(raw_records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Normalize raw records, validate against the schema, split good vs bad."""
    valid_records: list[dict] = []
    invalid_records: list[dict] = []
    seen_urls: set[str] = set()

    for raw in raw_records:
        try:
            price_gbp = parse_price_gbp(raw["price_text"])

            candidate = {**raw, "price_gbp": price_gbp}
            validated = BookRecord(**candidate)

            canonical_url = str(validated.product_url)
            if canonical_url in seen_urls:
                continue  # duplicate — skip silently, canonical URL already stored
            seen_urls.add(canonical_url)

            # model_dump with str URLs so json.dump doesn't choke on HttpUrl objects
            record_dict = json.loads(validated.model_dump_json())
            valid_records.append(record_dict)

        except (ValidationError, ValueError, KeyError) as exc:
            invalid_records.append({"record": raw, "reason": str(exc)})

    return valid_records, invalid_records


def store_records(valid_records: list[dict], invalid_records: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    books_path = OUTPUT_DIR / "books.json"
    errors_path = OUTPUT_DIR / "errors.json"

    books_path.write_text(json.dumps(valid_records, indent=2), encoding="utf-8")
    errors_path.write_text(json.dumps(invalid_records, indent=2), encoding="utf-8")

    print(f"stored: valid={len(valid_records)} invalid={len(invalid_records)}")

def extract_all_book_records(book_urls: list[str]) -> list[dict]:
    """Fetch every book detail page and extract its raw record."""
    records = []
    for url in book_urls:
        html = get_page(url, cache_path_fn=cache_filename_for_detail_page)
        record = extract_book_record(html, product_url=url, source_page=BASE_CATALOGUE_URL)
        records.append(record)

    print(f"detail_pages={len(records)}")
    return records

def main() -> None:
    book_urls = discover_all_book_urls()
    raw_records = extract_all_book_records(book_urls)
    valid_records, invalid_records = clean_and_validate_records(raw_records)
    store_records(valid_records, invalid_records)


if __name__ == "__main__":
    main()