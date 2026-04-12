from asyncio.log import logger
from datetime import datetime
from typing import AsyncGenerator, Generator, Optional

import aiohttp
from bs4 import BeautifulSoup, Tag

from library import Post


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

                if image_url := self.get_image_url(div):
                    text += f'\n<img src="{image_url}"></img>'

                yield Post(self.source_id, link, timestamp, heading, text)
            except TelegramParserException:
                logger.error(f"Except while parsing {div}")

    async def get_posts(self) -> AsyncGenerator[Post, None]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.link) as response:
                html = await response.text()

                for a in self.parse_html(html):
                    yield a
