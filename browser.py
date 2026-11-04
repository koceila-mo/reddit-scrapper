from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PWTimeout
from models import Post
import parsers, logging

BrowserLogger = logging.getLogger("__BrowserClient__")

class BrowserClient:
    def __init__(self, headless: bool = False):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=headless)
        self._page = self._browser.new_page()
        logging.info("BrowserClient initialized.")


    def fetch_posts(self, url: str, MAX_POSTS: int = 1000, attempts: int = 3) -> list[Post]:
        BrowserLogger.info(f"fetch_posts called with url: {url} and MAX_POSTS: {MAX_POSTS}")

        #retry logic for loading the sub's page, avoids the Join Reddit popup and other issues
        for attempt in range(1, attempts + 1):
            try:
                self._page.goto(url, wait_until="domcontentloaded")
                self._page.wait_for_selector("shreddit-post", timeout=10000)
                break  # Exit the loop 
            except PWTimeout:
                BrowserLogger.error(f"timeout correctly loading {url} (attempt {attempt}/{attempts})")
                if attempt == attempts:
                    BrowserLogger.error(f"Failed to load {url} after {attempts} attempts.")            
                    raise
                else:
                    self._page.wait_for_timeout(2000 * attempt) # exponentiaal timeout

        BrowserLogger.info(f"Page loaded for URL: {url}")

        posts: dict[str, Post] = {}
        stale_count = 0

        while len(posts) < MAX_POSTS and stale_count < 10:
            new_posts = parsers.parse_posts(self._page.content())

            post_count = 0

            for post in new_posts:
                if post.id in posts:
                    continue

                posts[post.id] = post
                post_count += 1

            if post_count == 0:
                stale_count += 1
            else:
                stale_count = 0

            self._page.mouse.wheel(0, 3000)
            self._page.wait_for_timeout(2000)

        BrowserLogger.info(f"Found {len(posts)} new posts from {url}")
        return list(posts.values())[:MAX_POSTS]

    def fetch_post(self, post: Post) -> Post:
        BrowserLogger.info(f"fetch_post called for post ID: {post.id} with URL: {post.url}")

        self._page.goto(post.url, wait_until="domcontentloaded")
        self._page.wait_for_selector("shreddit-post", timeout=10000)

        BrowserLogger.info(f"Page loaded for URL: {post.url}")

        content, comments = parsers.parse_content_and_comments(self._page.content())

        post.content = content 
        post.comments = comments

        BrowserLogger.info(f"Content and comments parsed for post ID: {post.id}")

        return post

    def close(self):
        self._browser.close()
        self._playwright.stop()
        BrowserLogger.info("BrowserClient closed.")


