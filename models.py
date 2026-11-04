from dataclasses import dataclass, field

@dataclass
class Post:
    id: str
    title: str
    url: str
    author: str
    created: str
    comments_count: int
    upvotes: int
    upvote_ratio: float
    content: str = ""
    comments: list['Comment'] = field(default_factory=list)
    
@dataclass
class Comment:
    id: str
    post_id: str
    text: str
    author: str
    upvotes: int
    created: str

