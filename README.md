# The Polite Scraper (FlyRank A9)

A small, polite scraping pipeline for Books to Scrape — fetches the first 3
catalogue pages, visits all 60 book pages, and produces clean, validated JSON.

## Target classification

- **Site:** https://books.toscrape.com
- **Why this site:** toscrape.com describes it as a scraping sandbox — a
  fictional bookstore built specifically for people to practice and validate
  scraping techniques on. It requires no JavaScript.
- **Scope:** Only the first 3 catalogue pages (60 books total). No other
  pages, no other sites.
- **Data collected:** title, product URL, price, availability, star rating,
  description, source page, and fetch timestamp.
- **robots.txt result:** Requested `https://books.toscrape.com/robots.txt`
  once — it returned a 404. No robots file found. (A missing file is not
  permission by itself — permission comes from the site's own description
  of itself as a sandbox built for this purpose.)

I will not reuse this code on another site without checking its rules and
terms first.

## How to run

```bash
git clone <your-repo-url>
cd scraper
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

Output appears in `output/books.json`, `output/errors.json`, and
`output/run-report.json`.

## Record schema

| Field                | Type          | Notes                          |
|-----------------------|---------------|---------------------------------|
| title                | string        |                                  |
| product_url          | string (URL)  | canonical identity of the record|
| price_gbp            | number        | parsed from price_text          |
| price_text           | string        | original raw text, e.g. "£51.77"|
| availability_text    | string        |                                  |
| rating_text          | string \| null|                                  |
| description          | string \| null| null when the page has none     |
| source_page          | string (URL)  |                                  |
| fetched_at           | string (ISO8601) |                               |

## Politeness rules

- Identifying user-agent: `FlyRankInternshipA9/1.0 (+<repo-link>)`
- 10-second timeout on every request
- 500ms delay between real (non-cached) requests
- Status code checked before any parsing
- All pages cached locally in `cache/` after first fetch — reruns during
  development never hit the live site again
- Retries once on timeout/5xx only; never retries 404 or 403

## Sample run report

```json
<{
  "start_time": "2026-09-04T23:23:42.391225+00:00",
  "duration_seconds": 1.68,
  "pages_fetched": 0,
  "cache_hits": 0,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1
}>
```
## Why this assignment needed no browser

The book data (title, price, availability, description) is already present
in the HTML the server sends on first request — nothing is loaded
dynamically via JavaScript, so a browser would only add cost (memory, CPU,
and time) with no benefit here.
## Ethics note

This scraper only touches a site explicitly built and offered for scraping
practice. In general: prefer an official API when one exists, never bypass
logins/paywalls/blocks, and collect only the data you actually need.

## Known limitation

<write one honest limitation here — e.g. "price parsing assumes GBP and a
single numeric value; it would break on multi-currency or range prices"
or "retry logic is a single fixed retry, not exponential backoff">