import json, sqlite3, logging
from pathlib import Path
from dataclasses import asdict
from models import Post
from models import Comment

SqliteStorageLogger = logging.getLogger("__SqliteStorage__") 


class JsonlStorage:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)  # makes sure the folder exists and creates it if it doesnt
        self._seen = self._load_seen()
        self._file = open(self.path, 'a', encoding='utf-8')

    def _load_seen(self) -> set[str]:
        seen = set()

        if self.path.exists():
            with open(self.path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                         seen.add(json.loads(line)["id"])

        return seen
    
    def save(self, posts: list[Post]) -> int:
        saved_count = 0

        for post in posts:
            if post.id in self._seen:
                continue
            
            post_dict = asdict(post)

            # Turn the dictionary into a JSON string (one line of text)
            line = json.dumps(post_dict, ensure_ascii=False)

            # Write it to the file, ending with a newline so each post gets its own line
            self._file.write(line + "\n")

            # Remember this post's id so we don't save it again
            self._seen.add(post.id)
            saved_count += 1

        # Force Python to write everything to disk now, instead of keeping it in memory
        self._file.flush()

        # Tell the caller how many new posts were saved
        return saved_count
    
    def close(self):
        self._file.close()
        

class SqliteStorage:
    def __init__(self, path="posts.db"):
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                title TEXT,
                url TEXT,
                author TEXT,
                created TEXT,
                comments_count INTEGER,
                upvotes INTEGER,
                upvote_ratio REAL,
                content TEXT
            );

            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                post_id TEXT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
                text TEXT,
                author TEXT,
                upvotes INTEGER,
                created TEXT
            );
        """)
        SqliteStorageLogger.info("SqliteStorage initialized")

    #takes a list of posts and saves them or updates them if they exist (does not update the content or comments of the post)
    def save_posts(self, posts: list[Post]):
        for p in posts:
            self.conn.execute(
                """
                INSERT INTO posts (id, title, url, author, created, comments_count, upvotes, upvote_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    url = excluded.url,
                    author = excluded.author,
                    created = excluded.created,
                    comments_count = excluded.comments_count,
                    upvotes = excluded.upvotes,
                    upvote_ratio = excluded.upvote_ratio
                """,
                (p.id, p.title, p.url, p.author, p.created,
                p.comments_count, p.upvotes, p.upvote_ratio),
            )
        self.conn.commit()
        SqliteStorageLogger.info(f"Saved/updated {len(posts)} posts to the database")

    #takes the new post, uses its id to find it and update its content
    def save_post_details(self, post: Post):
        self.conn.execute(
            "UPDATE posts SET content = ? WHERE id = ?",
            (post.content, post.id),
        )

        for c in post.comments:
            self.conn.execute(
                """
                INSERT INTO comments (id, post_id, text, author, upvotes, created)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    text = excluded.text,
                    upvotes = excluded.upvotes
                """,
                (c.id, c.post_id, c.text, c.author, c.upvotes, c.created),
            )
        self.conn.commit()
        SqliteStorageLogger.info(f"Saved/updated content and {len(post.comments)} comments for post ID: {post.id}")

    def get_unfetched_posts(self, limit: int = 50) -> list[Post]:
        rows = self.conn.execute(
            """
            SELECT id, title, url, author, created, comments_count, upvotes, upvote_ratio
            FROM posts
            WHERE content IS NULL
            LIMIT ?
            """,
            (limit,)
        ).fetchall()
        
        posts = []
        for row in rows:
            posts.append(Post(
                id=row[0],
                title=row[1],
                url=row[2],
                author=row[3],
                created=row[4],
                comments_count=row[5],
                upvotes=row[6],
                upvote_ratio=row[7],
            ))
        return posts
    
    def get_comments_for_post(self, post_id: str) -> list[Comment]:
        rows = self.conn.execute(
            """
            SELECT id, post_id, text, author, upvotes, created
            FROM comments
            WHERE post_id = ?
            """,
            (post_id,)
        ).fetchall()
        
        comments = []
        for row in rows:
            comments.append(Comment(
                id=row[0],
                post_id=row[1],
                text=row[2],
                author=row[3],
                upvotes=row[4],
                created=row[5],
            ))
        return comments

    def close(self):
        self.conn.close()


    