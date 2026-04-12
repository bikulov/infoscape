from dataclasses import dataclass
from hashlib import blake2b
from html import escape
import re
from datetime import datetime
from typing import List, Optional, Pattern
from urllib.parse import urlsplit

import pytz

from .posts_db import Post


MOSCOW_TZ = pytz.timezone("Europe/Moscow")


@dataclass(frozen=True)
class RenderedPost:
    date: str
    is_fresh: bool
    link: str
    summary: str
    html: str
    id: str


@dataclass(frozen=True)
class RenderedSource:
    heading: str
    link: str
    posts: List[RenderedPost]


class PostRenderer:
    def __init__(self, keywords: List[str]) -> None:
        self.keywords = keywords
        escaped_keywords = [re.escape(keyword) for keyword in keywords if keyword]
        self.keyword_pattern: Optional[Pattern[str]] = None
        if escaped_keywords:
            self.keyword_pattern = re.compile("|".join(escaped_keywords), re.IGNORECASE)

    @staticmethod
    def get_msk_date(timestamp: int) -> datetime:
        utc_dt = datetime.fromtimestamp(timestamp, pytz.utc)
        return utc_dt.astimezone(MOSCOW_TZ)

    def __call__(self, post: Post) -> RenderedPost:
        local_dt = self.get_msk_date(post.timestamp)
        is_fresh = local_dt.date() == datetime.now(MOSCOW_TZ).date()

        date = local_dt.strftime("%m.%d")
        if is_fresh:
            date = local_dt.strftime("%H:%M")

        heading = self._highlight(post.heading)
        html = self._render_html(post)

        return RenderedPost(
            date=date,
            is_fresh=is_fresh,
            link=post.link,
            summary=heading,
            html=html,
            id=self._stable_id(post.link),
        )

    def _highlight(self, text: str) -> str:
        if self.keyword_pattern is None:
            return escape(text)

        parts = []
        offset = 0
        for match in self.keyword_pattern.finditer(text):
            parts.append(escape(text[offset : match.start()]))
            parts.append(f"<mark>{escape(match.group(0))}</mark>")
            offset = match.end()
        parts.append(escape(text[offset:]))
        return "".join(parts)

    def _render_html(self, post: Post) -> str:
        parts = []
        if post.text:
            parts.append("<br>".join(escape(line) for line in post.text.splitlines()))

        image_html = self._render_image(post.image_url)
        if image_html:
            if parts:
                parts.append(image_html)
            else:
                parts = [image_html]

        return "<br>".join(part for part in parts if part)

    @staticmethod
    def _render_image(image_url: Optional[str]) -> str:
        if not image_url:
            return ""

        parsed = urlsplit(image_url)
        if parsed.scheme not in {"http", "https"}:
            return ""

        return f'<img src="{escape(image_url, quote=True)}" alt="">'

    @staticmethod
    def _stable_id(value: str) -> str:
        return blake2b(value.encode("utf-8"), digest_size=8).hexdigest()


class SourceRenderer:
    def __init__(self, keywords: List[str]) -> None:
        self.post_renderer = PostRenderer(keywords)

    def __call__(self, heading: str, link: str, posts: List[Post]) -> RenderedSource:
        return RenderedSource(
            heading=heading,
            link=link,
            posts=[self.post_renderer(p) for p in posts],
        )
