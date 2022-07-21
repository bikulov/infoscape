import pytz
import re

from datetime import datetime
from typing import List
from collections import namedtuple


from .posts_db import Post


RenderedPost = namedtuple("RenderedPost", ["date", "link", "summary", "html"])
RenderedSource = namedtuple("RenderedSource", ["heading", "link", "posts"])


class PostRenderer:
    def __init__(self, keywords: List[str]) -> None:
        self.keywords = keywords

    @staticmethod
    def format_date(timestamp: int) -> str:
        utc_dt = datetime.fromtimestamp(timestamp, pytz.utc)
        msk = pytz.timezone("Europe/Moscow")
        local_dt = utc_dt.astimezone(msk)
        date = local_dt.strftime("%H:%M")
        if local_dt.date() != datetime.today().date():
            date = local_dt.strftime("%m.%d")
        return date

    def __call__(self, post: Post) -> RenderedPost:
        date = self.format_date(post.timestamp)

        heading = post.heading
        text = post.text

        for kw in self.keywords:
            heading = re.sub(kw, f"<mark>{kw}</mark>", heading, flags=re.IGNORECASE)

        html = "<br>".join(text.splitlines())

        return RenderedPost(
            date=date,
            link=post.link,
            summary=heading,
            html=html
        )


class SourceRenderer:
    def __init__(self, keywords: List[str]) -> None:
        self.post_renderer = PostRenderer(keywords)

    def __call__(self, heading: str, link: str, posts: List[Post]) -> RenderedSource:
        return RenderedSource(
            heading=heading,
            link=link,
            posts=[self.post_renderer(p) for p in posts],
        )
