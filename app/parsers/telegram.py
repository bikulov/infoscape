import logging
from datetime import datetime
from typing import Generator, List, Optional

import aiohttp
from bs4 import BeautifulSoup, Tag

from library import Post


logger = logging.getLogger(__name__)


def extract_text(node: Tag) -> list[str]:
    for br in node.find_all("br"):
        br.replace_with("\n")

    text = node.get_text(" ")

    lines = []
    for line in text.splitlines():
        if fixed_line := " ".join(line.replace("\u200b", "").strip().split()):
            lines.append(fixed_line)

    return lines


class TelegramParserException(Exception):
    pass


class TelegramParser:
    def __init__(self, source_id: str, link: str) -> None:
        self.source_id = source_id
        self.link = link

    @staticmethod
    def get_image_url(tgme_widget: Tag) -> Optional[str]:
        if image_a := tgme_widget.find("a", class_="tgme_widget_message_photo_wrap"):
            style = image_a.get("style")
            if not isinstance(style, str):
                return None
            for s in style.split(";"):
                if s.startswith("background-image"):
                    return s[len("background-image:url('") : -2]
        return None

    @staticmethod
    def get_timestamp(tgme_widget: Tag) -> int:
        if a_date := tgme_widget.find("a", class_="tgme_widget_message_date"):
            time_tag = a_date.find("time")
            if time_tag:
                dt = time_tag.get("datetime")
                if isinstance(dt, str):
                    return int(datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S%z").timestamp())

        raise TelegramParserException("Could not parse timestamp")

    @staticmethod
    def get_link(tgme_widget: Tag) -> str:
        if a_date := tgme_widget.find("a", class_="tgme_widget_message_date"):
            href = a_date.get("href")
            if isinstance(href, str):
                return href

        raise TelegramParserException("Could not parse link")

    @staticmethod
    def get_body(tgme_widget: Tag) -> Optional[str]:
        messages = []
        for div_text in tgme_widget.find_all("div", class_="tgme_widget_message_text"):
            messages.append(extract_text(div_text))

        if messages:
            posts = []
            line_prefix = ""
            for lines in messages[::-1]:
                posts.append("\n".join(f"{line_prefix}{line}" for line in lines))
                line_prefix = ">" + line_prefix if line_prefix else "> "

            return "\n\n".join(posts)
        return None

    def parse_html(self, content: str) -> Generator[Post, None, None]:
        soup = BeautifulSoup(content, "html.parser")

        for div in soup.find_all("div", class_="tgme_widget_message_wrap"):
            try:
                timestamp = self.get_timestamp(div)
                link = self.get_link(div)
                text = ""
                heading = ""

                if body := self.get_body(div):
                    text = body
                    for line in body.splitlines():
                        #  try to find better heading (not single tag on the line)
                        if not heading or (
                            heading.startswith("#") and len(heading.split()) < 3
                        ):
                            heading = line
                        else:
                            break

                image_url = self.get_image_url(div)

                yield Post(
                    self.source_id,
                    link,
                    timestamp,
                    heading,
                    text,
                    image_url=image_url,
                )
            except TelegramParserException:
                logger.warning("Could not parse telegram widget for %s", self.source_id)

    async def get_posts(
        self, session: Optional[aiohttp.ClientSession] = None
    ) -> List[Post]:
        if session is not None:
            return await self._get_posts(session)

        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as owned_session:
            return await self._get_posts(owned_session)

    async def _get_posts(self, session: aiohttp.ClientSession) -> List[Post]:
        async with session.get(self.link) as response:
            response.raise_for_status()
            html = await response.text()

        return list(self.parse_html(html))
