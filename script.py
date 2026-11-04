import logging

from browser import BrowserClient
from storage import SqliteStorage
from scraper import scrape_feed, scrape_details

SUBREDDIT_URL = "https://www.reddit.com/r/python"
DB_PATH = "Python.db"
FEED_LIMIT = 20
DETAILS_LIMIT = 10000

logging.basicConfig(
    level=logging.INFO,
    filename="log.log",
    filemode="w",
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("__script__")


def main():
    browser = BrowserClient(headless=False)
    store = SqliteStorage(DB_PATH)
    try:
        scrape_feed(browser, store, SUBREDDIT_URL, FEED_LIMIT)
        scrape_details(browser, store, DETAILS_LIMIT)
    except Exception:
        logger.critical("Scraping failed")
        raise
    finally:
        store.close()
        browser.close()


if __name__ == "__main__":
    main()