# Reddit Scraper

Playwright scraper that saves Reddit posts, their body text, and comments (top-level and replies) to SQLite.
No API key or login required.

It runs as a command-line tool, either directly with Python or inside Docker.

## Commands

| Command | What it does |
|---|---|
| `feed` | Scrape one subreddit's feed and store post metadata |
| `search` | Scrape a subreddit's search results and store post metadata |
| `details` | Fetch body text and comments for stored posts that don't have them yet |

Scraping is two-phase: `feed` / `search` collect the posts, then `details` visits each post to fetch its content and comments. `details` only processes posts that are still missing content, so it is safe to stop and rerun.

Global options go **before** the command:

| Option | Description |
|---|---|
| `--db PATH` | Path to the SQLite database (default: `Data.db`, or the `DB_PATH` environment variable) |
| `--headless` | Run the browser without a window (always on in Docker) |

Command options:

| Command | Options |
|---|---|
| `feed` | `subreddit`, `--sort {new,hot,top,rising}`, `--period {hour,day,week,month,year,all}`, `--limit N` |
| `search` | `subreddit`, `query`, `--sort {relevance,hot,top,new,comments}`, `--period {hour,day,week,month,year,all}` |
| `details` | `--limit N` |

Run `python main.py --help` or `python main.py <command> --help` for the full list.

## Run with Docker (recommended)

Requires Docker Engine with the Compose plugin (or Docker Desktop).

```bash
# 1. Build the image (first build downloads the Playwright base image, over 1 GB)
docker compose build

# 2. Run commands. Everything after "scraper" is passed to the CLI
docker compose run --rm scraper feed python --limit 100
docker compose run --rm scraper search python scraping --sort top
docker compose run --rm scraper details --limit 100
```

Data is saved to `./data/` on your machine (the folder is mounted into the container), so it survives after the container is removed.

Running several commands in order:

```bash
docker compose run --rm scraper feed men --limit 1000 \
  && docker compose run --rm scraper feed women --limit 1000 \
  && docker compose run --rm scraper details --limit 500
```

Running in the background (for example on a server):

```bash
docker compose run -d --name scraper-details scraper details --limit 5000
docker logs -f scraper-details       # watch progress (Ctrl+C stops watching only)
docker stop scraper-details          # graceful stop
```

After changing any Python file, rebuild with `docker compose build`.

## Run without Docker

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

```bash
python main.py feed python --limit 100
python main.py search python scraping --sort top
python main.py details --limit 100
python main.py --headless details --limit 100     # no browser window
```

By default the database is `Data.db` in the current folder. Change it with `--db` or the `DB_PATH` environment variable.

## Project layout

```
.
├── main.py             CLI entry point
├── browser.py          Playwright browser wrapper
├── scraper.py          feed / search / details scraping logic
├── parsers.py          HTML and data parsing
├── models.py           data classes
├── storage.py          SQLite storage
├── requirements.txt
├── Dockerfile          builds the image (Python, Chromium, dependencies, code)
├── compose.yaml        how to run the image (volumes, environment, flags)
├── .dockerignore
└── data/               output: database and logs (created at runtime, not committed)
```

## Output

Everything is written to the `data/` folder when using Docker.

- `Data.db` contains the `posts` and `comments` tables.
- `log.log` is the run log. Logs also print to the console, so `docker logs` works.

Post pages are fetched with a 3-7 second pause between each call.

## Updating Playwright

The Playwright version appears in two places and **must match**:

1. `requirements.txt`: `playwright==X.Y.Z`
2. `Dockerfile`: `FROM mcr.microsoft.com/playwright/python:vX.Y.Z-<ubuntu-release>`

The base image ships with the matching browser. If they differ, you'll get an `executable doesn't exist` error. Change both, then run `docker compose build`.

## Troubleshooting

| Problem | Likely cause |
|---|---|
| `Cannot connect to the Docker daemon` | Docker isn't running. Start the service or Docker Desktop |
| `Temporary failure in name resolution` while building | DNS problem. Add `"dns": ["8.8.8.8", "1.1.1.1"]` to `/etc/docker/daemon.json` and restart Docker |
| `executable doesn't exist at ...chromium` | Playwright version mismatch (see above) |
| `unable to open database file` | `data/` isn't mounted, or `DB_PATH` is wrong. Check with `docker compose config` |
| `Permission denied` writing to `data/` on Fedora/RHEL | SELinux. Use `./data:/data:z` in `compose.yaml` |
| Rate limit banner / no posts loading | Reddit is throttling the IP. The scraper waits and retries, but datacenter IPs are limited much harder than home connections |

## Notes

- Public pages only.
- Reddit search and listing pages stop at roughly 1,000 results per query. To collect more, split the work across sorts, time periods, and queries; posts are deduplicated by ID.
- This is a simple scraper that will break at larger scale, and Reddit's page structure changes often.
- Automated scraping may go against Reddit's terms of service. Use responsibly.