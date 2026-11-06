import logging
from browser import BrowserClient
from storage import SqliteStorage
from scraper import scrape_feed, scrape_details, scrape_search


DB_PATH = "Posts.db"
FEED_LIMIT = 1000

DETAILS_LIMIT = 100

logging.basicConfig(
    level=logging.INFO,
    filename="log.log",
    filemode="w",
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
script_logger = logging.getLogger("__script__")


def main():
    browser = BrowserClient(headless=True)
    store = SqliteStorage(DB_PATH)
    print("Scraping started")
    try:
        #this scrapes posts from a subreddit feed and stores the posts' metadata, content and comments get fetched later on 
        scrape_feed(browser, store, "python", "new", "all", FEED_LIMIT)
        #this scrapes posts from a subreddit search and stores the posts' metadata, content and comments get fetched later on 
        scrape_search(browser, store, "python", "scraping", "relevance", "all")
        #this gets the posts that are still dont have content and comments from the database and fetches them one by one
        scrape_details(browser, store, DETAILS_LIMIT)

    except Exception:
        script_logger.critical("Scraping failed")
        raise
    finally:
        store.close()
        browser.close()


if __name__ == "__main__":
    main()