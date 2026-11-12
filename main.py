import logging, os, signal, argparse, sys

from browser import BrowserClient
from storage import SqliteStorage
from scraper import scrape_feed, scrape_details, scrape_search

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/data/log.log", mode="a"),
    ],
)
script_logger = logging.getLogger("__script__")

def init_parser():
    parser = argparse.ArgumentParser( prog="main.py", description="Reddit scraper")

    #global
    parser.add_argument("--db", default=os.environ.get("DB_PATH", "data/Data.db"), help="Path to the database file",)
    parser.add_argument("--headless", action="store_true", help="Run the browser in headless mode, must set when running in docker",)

    
    #subcommends
    subcommands = parser.add_subparsers(dest="command", required=True)
    
    feed = subcommands.add_parser("feed", help="Scrape a subreddit feed")
    feed.add_argument("subreddit", nargs="+", help="Subreddit to scrape",)
    feed.add_argument("--sort", nargs="+", default=["new"], choices=["new", "hot", "top", "rising"],)
    feed.add_argument("--period", nargs="+", default=["all"], choices=["hour", "day", "week", "month", "year", "all"],)
    feed.add_argument("--limit", type=int, default=1000)

    search = subcommands.add_parser("search", help="scrape a subreddit search")
    search.add_argument("subreddit")
    search.add_argument("query")
    search.add_argument("--sort", default="relevance", choices=["relevance", "hot", "top", "new", "comments"])
    search.add_argument("--period", default="all", choices=["hour", "day", "week", "month", "year", "all"])

    details = subcommands.add_parser("details", help="fetch content and comments for stored posts")
    details.add_argument("--limit", type=int, default=100)

    return parser



def main():
    args = init_parser().parse_args()
    
    browser = BrowserClient(headless=args.headless)
    store = SqliteStorage(args.db)
    script_logger.info(f"Scraping started: {args.command}")

    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(143))


    try:
        if args.command == "feed":
            scrape_feed(browser, store, args.subreddit, args.sort, args.period, args.limit)
        elif args.command == "search":
            scrape_search(browser, store, args.subreddit, args.query, args.sort, args.period)
        elif args.command == "details":
            scrape_details(browser, store, args.limit)
        return 0
    
    except KeyboardInterrupt:
        script_logger.warning("Interrupted by user")
        return 130

    except Exception:
        script_logger.critical("Scraping failed")
        raise
    
    finally:
        store.close()
        browser.close()


if __name__ == "__main__":
    sys.exit(main())