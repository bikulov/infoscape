import pytz
from datetime import datetime
from typing import List
from collections import namedtuple


from .posts_db import Post


RenderedPost = namedtuple("RenderedPost", ["date", "link", "summary", "html"])


class PostRenderer:
    @staticmethod
    def format_date(timestamp: int) -> str:
        utc_dt = datetime.fromtimestamp(timestamp, pytz.utc)
        msk = pytz.timezone("Europe/Moscow")
        local_dt = utc_dt.astimezone(msk)
        date = local_dt.strftime("%H:%M")
        if local_dt.date() != datetime.today().date():
            date = local_dt.strftime("%m.%d")
        return date

    def __call__(self, post: Post):
        date = self.format_date(post.timestamp)

        text = post.text.splitlines()
        html = "<br>".join(text)

        return RenderedPost(
            date=date,
            link=post.link,
            summary=post.heading,
            html=html
        )


RenderedSource = namedtuple("RenderedSource", ["heading", "link", "posts"])

class SourceRenderer:
    def __call__(self, heading: str, link: str, posts: List[Post]) -> None:
        post_renderer = PostRenderer()

        return RenderedSource(
            heading=heading,
            link=link,
            posts=[post_renderer(p) for p in posts],
        )
