# Reddit Scraper

Scrapes Reddit posts, bodies and comments into SQLite with Playwright. No API key or login.

## Usage

Docker:

```bash
docker compose build
docker compose run --rm scraper feed python --limit 100
docker compose run --rm scraper search python scraping --sort top
docker compose run --rm scraper details --limit 100
```

Local:

```bash
pip install -r requirements.txt
playwright install chromium
python main.py --headless feed python --limit 100
```

## Commands

- `feed <subreddit...>` — scrape one or more feeds. Options: `--sort` (`new` default, `hot`, `top`, `rising`), `--period` (`hour`, `day`, `week`, `month`, `year`, `all` — default `all`), `--limit` (default 1000).
- `search <subreddit> <query>` — scrape search results. Options: `--sort` (`relevance` default, `hot`, `top`, `new`, `comments`), `--period`.
- `details` — fetch body and comments for stored posts that don't have them. Option: `--limit` (default 100).

Scraping is two steps: `feed`/`search` collect posts, then `details` fills in content and comments. `details` skips already-fetched posts, so it's safe to stop and rerun.

Global options: `--db` (default `data/Data.db` or `DB_PATH`), `--headless`.

Data is stored in `./data/`.

## Notes

- Reddit caps listings at ~1000 posts per query.
- Rate limiting is still rough.
