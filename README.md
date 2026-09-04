# The Polite Scraper (FlyRank A9)

## Target classification

- **Site:** https://books.toscrape.com
- **Why this site:** toscrape.com explicitly describes it as a scraping sandbox —
  a fictional bookstore built specifically for people to practice and validate
  scraping techniques on. It requires no JavaScript and its data is paginated
  in the open.
- **Scope:** Only the first 3 catalogue pages (up to 60 books). No other pages,
  no other sites.
- **Data collected:** title, product URL, price, availability, star rating,
  description, source page, and fetch timestamp — for each of those 60 books.
- **robots.txt result:** Requested `https://books.toscrape.com/robots.txt` once
  on [date] — it returned a 404. No robots file found. (A missing file is not
  permission by itself — permission comes from the site's own description of
  itself as a sandbox built for this purpose.)
- **Why this is appropriate:** The site exists for exactly this purpose, the
  scope is small and fixed (3 pages), and no login, paywall, or personal data
  is involved.

I will not reuse this code on another site without checking its rules and
terms first.