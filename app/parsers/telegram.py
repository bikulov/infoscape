import aiohttp
import asyncio

from asyncio.log import logger
from datetime import datetime
from typing import Generator
from bs4 import BeautifulSoup

from library import Post


def cleanup_text(text):
    lines = []

    for line in text.splitlines():
        if fixed_line := " ".join(line.strip().split()):
            lines.append(fixed_line)

    return "\n".join(lines)


class TelegramParser:
    def __init__(self, source_id: str, link: str):
        self.source_id = source_id
        self.link = link

    def parse_html(self, content: str) -> Generator[Post, None, None]:
        soup = BeautifulSoup(content, "html.parser")

        for div in soup.find_all("div", "tgme_widget_message_wrap"):
            try:
                for br in div.find_all("br"):
                    br.replace_with("\n")

                dt = cleanup_text(
                    div.find("a", "tgme_widget_message_date").find("time").get("datetime")
                )
                timestamp = int(datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S%z").timestamp())
                text = cleanup_text(
                    div.find("div", "tgme_widget_message_text").get_text(" ")
                )
                heading = text.splitlines()[0]
                link = cleanup_text(div.find("a", "tgme_widget_message_date").get("href"))

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
