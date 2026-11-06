from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError
from models import Post
import parsers, logging

BrowserLogger = logging.getLogger("__BrowserClient__")

class BrowserClient:
    def __init__(self, headless: bool = False):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=headless)
        self._context = self._browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
                )
        self._page = self._context.new_page()
        logging.info("BrowserClient initialized")


    def fetch_posts(self, url , max_posts: int = 1500) -> list[Post]:
        self._page.goto("https://reddit.com", wait_until="domcontentloaded")
        self._page.wait_for_timeout(500)
        self._page.goto(url, wait_until="domcontentloaded")
        self._page.wait_for_selector("shreddit-post", timeout=10000)
        self._page.wait_for_timeout(500)
        BrowserLogger.info(f"Loaded page: {url}, fetching posts from feed..")
        
        self._anti_page_block(url)

        posts: dict[str, Post] = {}   
        stale_count = 0
        max_stale = 30

        while len(posts) < max_posts and stale_count < max_stale:
            # get posts on screen
            posts_on_screen = self._page.eval_on_selector_all(
                "shreddit-post",
                """elements => elements.map(el => ({
                    id: el.id,
                    permalink: el.getAttribute('permalink') || '',
                    title: el.getAttribute('title') || '',
                    author: el.getAttribute('author') || '',
                    created: el.getAttribute('created') || '',
                    comments_count: el.getAttribute('comment-count') || '',
                    upvotes: el.getAttribute('score') || '',
                    upvote_ratio: el.getAttribute('upvote-ratio') || '',
                }))""",
            )

            new_count = 0

            for post in posts_on_screen:
                post_id = post["id"]
                if not post_id or post_id in posts:
                    continue

                posts[post_id] = Post(
                    id=post_id,
                    url=f"https://reddit.com{post['permalink']}",
                    title=post['title'],
                    author=post['author'],
                    created=post['created'],
                    comments_count=int(post['comments_count']),
                    upvotes=int(post['upvotes']),
                    upvote_ratio=float(post['upvote_ratio']),
                )
                new_count += 1

            # chexk if new posts are being found
            if new_count == 0:
                stale_count += 1
            else:
                stale_count = 0

            self._page.mouse.wheel(0, 2000)
            self._page.wait_for_timeout(100)

        return list(posts.values())[:max_posts]

    def fetch_search_posts(self, subreddit: str, url: str) -> list[Post]:
        selector = 'search-telemetry-tracker[data-testid="search-sdui-post"]'
        self._page.goto("https://reddit.com/", wait_until="domcontentloaded")
        self._page.wait_for_timeout(500)
        self._page.goto(f"https://reddit.com/r/{subreddit}/", wait_until="domcontentloaded")
        self._page.wait_for_timeout(500)
        self._page.goto(url, wait_until="domcontentloaded")
        self._page.wait_for_selector(selector, timeout=10000)
        self._page.wait_for_timeout(500)

        BrowserLogger.info(f"loaded search page {url}, fetching posts..")

        self._anti_page_block(url)

        # scroll until the number of posts deosnt grow anymore
        last_count = 0
        stale_count = 0
        max_stale = 30

        while stale_count < max_stale:
            self._page.mouse.wheel(0, 2000)
            self._page.wait_for_timeout(100)

            count = self._page.locator(selector).count()
            if count == last_count:
                stale_count += 1
            else:
                stale_count = 0
                last_count = count

        # extract posts
        posts_on_page = self._page.eval_on_selector_all(
            selector,
            """elements => elements.map(el => {
                const ctx = JSON.parse(el.getAttribute('data-faceplate-tracking-context') || '{}');
                const numbers = el.querySelectorAll('faceplate-number');
                const link = el.querySelector('a[data-testid="post-title"]');
                const timeago = el.querySelector('faceplate-timeago');
                return {
                    id: el.getAttribute('data-thingid') || '',
                    permalink: link ? link.getAttribute('href') : '',
                    title: ctx.post?.title || '',
                    author: ctx.profile?.name || '',
                    created: timeago ? timeago.getAttribute('ts') : '',
                    upvotes: numbers[0] ? numbers[0].getAttribute('number') : '0',
                    comments_count: numbers[1] ? numbers[1].getAttribute('number') : '0',
                    upvote_ratio: '0',
                };
            })""",
        )

        return [
            Post(
                id=post["id"],
                url=f"https://reddit.com{post['permalink']}",
                title=post["title"],
                author=post["author"],
                created=post["created"],
                comments_count=int(post["comments_count"]),
                upvotes=int(post["upvotes"]),
                upvote_ratio=float(post["upvote_ratio"]),
            )
            for post in posts_on_page
            if post["id"]
        ]

    def fetch_post(self, post: Post) -> Post:
        BrowserLogger.info(f"fetch_post called for post ID: {post.id} with URL: {post.url}")
        self._page.goto(post.url, wait_until="domcontentloaded")
        self._page.wait_for_selector("shreddit-post", timeout=10000)

        self._anti_page_block(post.url)


        #load target number of comments in the html
        self._load_comments_to_html(target_comments=500)

        BrowserLogger.info(f"Page loaded for URL: {post.url}")

        #parse the content and comments and return the updated post
        new_post = parsers.parse_content_and_comments(self._page.content())
 
        
        BrowserLogger.info(f"Content and comments parsed for post ID: {post.id}")

        return new_post
    
    def _anti_page_block(self, url, timeout: int = 5000, attempts: int = 3):
        for attempt in range(attempts):
            button = self._page.get_by_role("button", name="Get Started", exact=True).first

            if not button.is_visible():
                return  

            BrowserLogger.warning(f"Page blocked (attempt {attempt + 1}/{attempts})")
            self._browser.close()
            self._browser = self._playwright.chromium.launch(headless=False)
            self._page = self._context.new_page()
            self._page.goto("https://reddit.com", wait_until="domcontentloaded")
            self._page.wait_for_timeout(500)
            self._page.goto(url, wait_until="domcontentloaded")
            self._page.wait_for_selector("shreddit-post", timeout=timeout)

        if self._page.get_by_role("button", name="Get Started", exact=True).first.is_visible():
            raise Exception("Page blocked")

    def _load_comments_to_html(self, target_comments: int = 0):
        button = self._page.get_by_role("button", name="View more comments", exact=True).first
        comments = self._page.locator("shreddit-comment")

        misses = 0
        while comments.count() < target_comments and misses < 2:
            old_count = comments.count()

            if button.is_visible():
                button.click()
            else:
                self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            self._wait_for_new_comments(old_count, timeout=1500)

            if comments.count() > old_count:
                misses = 0
            else:
                misses += 1

    def _wait_for_new_comments(self, old_count: int, timeout: int = 3000) -> bool:
        try:
            self._page.wait_for_function(
                "(n) => document.querySelectorAll('shreddit-comment').length > n",
                arg=old_count,
                timeout=timeout,
            )
            return True
        except TimeoutError:
            return False

    def close(self):
        self._browser.close()
        self._playwright.stop()
        BrowserLogger.info("BrowserClient closed.")




