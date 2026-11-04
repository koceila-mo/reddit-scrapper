from random import random
import logging, time
from browser import BrowserClient
from storage import SqliteStorage
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError
from playwright._impl._errors import TargetClosedError

scraper_logger = logging.getLogger("__Scraper__")

def scrape_feed(browser: BrowserClient, store: SqliteStorage, url: str, max_posts: int = 100) -> int:
    try:
        posts = browser.fetch_posts(url, max_posts)
    except TimeoutError:
        scraper_logger.error(f"Timeout while scraping feed: {url}")
        return 0
    except PlaywrightError as e:
        scraper_logger.error(f"Playwright error while scraping feed: {url} error: {e}")
        return 0
    
    store.save_posts(posts)
    scraper_logger.info(f"Scraped {len(posts)} posts from {url}")
    return len(posts)
    
        

def scrape_details(browser: BrowserClient, store: SqliteStorage, limit: int = 50) -> int:
    done = 0
    skipped = 0
    unfetched_posts = store.get_unfetched_posts(limit)

    for post in unfetched_posts:
        try:
            browser.fetch_post(post)
        except TimeoutError:
            skipped += 1
            scraper_logger.warning(f"Timeout while fetching details for post: {post.id} Post skipped")
            continue
        except TargetClosedError:
            scraper_logger.error(f"Browser closed while fetching")
            raise
        except PlaywrightError as e:
            skipped += 1
            scraper_logger.warning(f"Playwright error while fetching {post.id}: {e} Post skipped" )
            continue
        except Exception as e:
            skipped += 1
            scraper_logger.warning(f"Error while fetching {post.id}: {e} Post skipped")
            continue
    
        store.save_post_details(post)
        done += 1
        time.sleep(3)
    
    scraper_logger.info(f"Details: fetched={done} skipped={skipped} from={len(unfetched_posts)}")
    return done


