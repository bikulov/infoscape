import asyncio
from asyncio.log import logger
from datetime import datetime
from typing import Generator, Optional

import aiohttp
from bs4 import BeautifulSoup, ResultSet

from library import Post


def extract_text(bs_set: ResultSet):
    for br in bs_set.find_all("br"):
        br.replace_with("\n")

    text = bs_set.get_text(" ")

    lines = []
    for line in text.splitlines():
        if fixed_line := " ".join(line.strip().split()):
            lines.append(fixed_line)

    return lines


class TelegramParser:
    def __init__(self, source_id: str, link: str):
        self.source_id = source_id
        self.link = link

    @staticmethod
    def get_image_url(tgme_widget: ResultSet) -> Optional[str]:
        if image_a := tgme_widget.find("a", "tgme_widget_message_photo_wrap"):
            for s in image_a.get("style").split(";"):
                if s.startswith("background-image"):
                    return s[len("background-image:url('") : -2]

    @staticmethod
    def get_timestamp(tgme_widget: ResultSet) -> Optional[int]:
        if a_date := tgme_widget.find("a", "tgme_widget_message_date"):
            dt = a_date.find("time").get("datetime")
            return int(datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S%z").timestamp())

    @staticmethod
    def get_link(tgme_widget: ResultSet) -> Optional[str]:
        if a_date := tgme_widget.find("a", "tgme_widget_message_date"):
            return a_date.get("href")

    @staticmethod
    def get_body(tgme_widget: ResultSet) -> Optional[str]:
        messages = []
        for div_text in tgme_widget.find_all("div", "tgme_widget_message_text"):
            messages.append(extract_text(div_text))

        if messages:
            posts = []
            line_prefix = ""
            for lines in messages[::-1]:
                posts.append("\n".join(f"{line_prefix}{l}" for l in lines))
                line_prefix = ">" + line_prefix if line_prefix else "> "

            return "\n\n".join(posts)

    def parse_html(self, content: str) -> Generator[Post, None, None]:
        soup = BeautifulSoup(content, "html.parser")

        for div in soup.find_all("div", "tgme_widget_message_wrap"):
            try:
                timestamp = self.get_timestamp(div)
                link = self.get_link(div)
                text = self.source_id
                heading = text

                if body := self.get_body(div):
                    text = body
                    heading = text.splitlines()[0]

                if image_url := self.get_image_url(div):
                    text += f'\n<img src="{image_url}"></img>'

                yield Post(self.source_id, link, timestamp, heading, text)
            except:
                logger.error(f"Except while parsing {div}")

    async def get_posts(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.link) as response:
                html = await response.text()

                for a in self.parse_html(html):
                    yield a


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    addmeto = TelegramParser("addmeto", "https://t.me/s/addmeto")

    async def get_posts_sync():
        result = []
        async for p in addmeto.get_posts():
            result.append(p)
        return result

    for s in loop.run_until_complete(get_posts_sync()):
        print(s)
