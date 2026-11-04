from bs4 import BeautifulSoup
from models import Post
from models import Comment



def parse_posts(html: str) -> list[Post]:
    soup = BeautifulSoup(html, 'html.parser')
    posts = []

    for post in soup.find_all("shreddit-post"):
        post_id = post.get('id', '')
        if not post_id:
            continue

        posts.append(Post(
            post_id,
            post.get('post-title', ''),
            f"https://reddit.com{post.get('permalink', '')}",
            post.get('author', ''),
            post.get('created-timestamp', ''),
            int(post.get('comment-count', 0)),
            int(post.get('score', 0)),
            float(post.get('upvote-ratio', 0))
        ))

    return posts

def parse_content_and_comments(html: str) -> tuple[str, list[Comment]]:

    soup = BeautifulSoup(html, 'html.parser')
        
    # Extracting the content of the post
    pid = soup.find("shreddit-post").get('id', '')
    body = soup.find("div", attrs={"property": "schema:articleBody"})
    content = body.get_text("\n", strip=True) if body else ""

    # Extracting the comments
    comments = []
    for comment in soup.find_all("shreddit-comment", attrs={"depth": "0"}):

        #get the text of the comment
        cid = comment.get('thingid', '')
        comment_body = comment.find("div", attrs={"id": f"{cid}-comment-rtjson-content"})
        text = comment_body.get_text("\n", strip=True) if comment_body else ""

        #appending the comment
        comments.append(Comment(
            id=cid,
            post_id=pid,
            author=comment.get('author', ''),
            upvotes=int(comment.get('score', 0)),
            created=comment.get('created', ''),
            text=text
        ))

    return content, comments
                               



