from dataclasses import dataclass, field

@dataclass
class Post:
    id: str
    title: str = ""
    url: str = ""
    author: str = ""
    created: str = ""
    comments_count: int = 0
    upvotes: int = 0
    upvote_ratio: float = 0.0
    content: str = None
    comments: list['Comment'] = field(default_factory=list) #just an empty list of objects
    
@dataclass
class Comment:
    id: str
    post_id: str
    text: str
    author: str
    upvotes: int
    depth: int
    created: str
    parent_id: str = ""

