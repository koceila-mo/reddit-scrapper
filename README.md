# Reddit Scraper Demo

Playwright scraper demo that saves Reddit posts, their body text and top-level comments and replies to SQLite.
No API key or login required.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Use

Edit the settings in `script.py` (`DB_PATH`, `FEED_LIMIT`, `DETAILS_LIMIT`, and the
`scrape_feed` / `scrape_search` calls), then:

```bash
python script.py
```

## Output

- `data.db` contains `posts` and `comments` tables.
- `log.log` overwritten on each run

Post pages are fetched with a 3–7 second pause between each call

## Notes

- Public pages only; top-level comments and replies
- This is a simple demo that will break at larger scale, still working on rate limiting

