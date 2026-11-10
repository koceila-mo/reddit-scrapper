# Reddit Scraper

Scrapes Reddit posts, their body text and comments into SQLite using Playwright. No API key or login needed.

## Usage

```bash
docker compose build
docker compose run --rm scraper feed python --limit 100
docker compose run --rm scraper search python scraping --sort top
docker compose run --rm scraper details --limit 100
```

Scraping is two steps: `feed` and `search` collect posts, then `details` goes through each stored post and fetches its body and comments. `details` skips posts that already have content, so you can stop it and rerun.

## Commands

**`feed <subreddit>`**: scrape a subreddit's feed

- `--sort`: `new` (default), `hot`, `top`, `rising`
- `--period`: `hour`, `day`, `week`, `month`, `year`, `all` (default)
- `--limit`: max posts to collect, default 1000

**`search <subreddit> <query>`**: scrape the results of a search inside a subreddit

- `--sort`: `relevance` (default), `hot`, `top`, `new`, `comments`
- `--period`: same as `feed`

**`details`**: fetch body and comments for stored posts that don't have them yet

- `--limit`: how many posts to process, default 100

Global options go before the command:

- `--db`: path to the database file (default `Data.db`, or the `DB_PATH` env var)
- `--headless`: run without a browser window (Docker always does)

```bash
python main.py --headless feed men --sort top --period month --limit 500
```

Data ends up in `./data/`.

## Without Docker

```bash
pip install -r requirements.txt
playwright install chromium
python main.py feed python --limit 100
```

## Notes

- Reddit stops listings at around 1000 posts per query
- Will probably break at larger scale, still working on rate limiting
- The Playwright version in `requirements.txt` has to match the one in the `Dockerfile`
