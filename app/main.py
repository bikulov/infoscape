from collections import namedtuple
from typing import List
import asyncio
import time
from datetime import datetime
import logging
import argparse
import uvicorn
import pytz
from jinja2 import Environment, PackageLoader, select_autoescape
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from parsers import TelegramParser
from library import Config, Post, PostsDb


app = FastAPI()
config = Config.from_file_factory("config.json")
logger = logging.getLogger("infoscape")
db = PostsDb()


env = Environment(loader=PackageLoader("main"), autoescape=select_autoescape())

RenderedPost = namedtuple("RenderedPost", ["date", "link", "summary", "html"])


class SourceRenderer:
    def __init__(self, heading: str, posts: List[Post]):
        self.heading = heading
        self.posts = posts

    @staticmethod
    def format_date(timestamp):
        utc_dt = datetime.fromtimestamp(int(timestamp), pytz.utc)
        msk = pytz.timezone("Europe/Moscow")
        local_dt = utc_dt.astimezone(msk)
        date = local_dt.strftime("%H:%M")
        if local_dt.date() != datetime.today().date():
            date = local_dt.strftime("%m.%d")
        return date
    
    def render_posts(self):
        for post in self.posts:
            date = self.format_date(post.timestamp)
            link = post.link

            text = post.text.splitlines()
            html = "<br>".join(text)
            summary = text[0]

            yield RenderedPost(date, link, summary, html)


async def fetch(args):
    while True:
        for source in config.sources.values():
            logger.info(f"fetching {source.id}")
            if source.parser == "telegram":
                try:
                    parser = TelegramParser(source.id, source.link)
                    async for Post in parser.get_posts():
                        db.add(Post)
                except:
                    logger.exception(f"Error while fetching source {source.id}")

        if args.daemonize > 0:
            logger.info(f"sleeping {args.daemonize} seconds")
            time.sleep(args.daemonize)
        else:
            break    


@app.get("/", response_class=HTMLResponse)
async def index():
    widgets = []
    for s in config.sources.values():
        posts = db.select([s.id], 10)
        widgets.append(SourceRenderer(s.title, posts))

    template = env.get_template("index.html")
  
    return template.render(title=config.title, page_slug="", pages=config.pages.values(), widgets=widgets)


@app.get("/p/{page_slug}", response_class=HTMLResponse)
async def get_page(page_slug: str = "top"):
    page = config.pages[page_slug]
    widgets = []
    for s in page.sources:
        posts = db.select([s], 10)
        widget_title = config.sources[s].title
        widgets.append(SourceRenderer(widget_title, posts))

    template = env.get_template("index.html")
  
    return template.render(title=config.title, page_slug=page_slug, pages=config.pages.values(), widgets=widgets)


async def serve(args):
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=3)


async def main():
    parser = argparse.ArgumentParser(prog="infoscape")
    parser.add_argument("--config", default="config.json", help="App configuration")
    subparsers = parser.add_subparsers(help="mode")

    serve_parser = subparsers.add_parser("serve", help="serve news")
    serve_parser.set_defaults(func=serve)

    fetch_parser = subparsers.add_parser("fetch", help="fetch news")
    fetch_parser.add_argument(
        "--daemonize",
        type=int,
        default=600,
        help="Run program in the infinite loop with specified seconds sleep",
    )
    fetch_parser.set_defaults(func=fetch)

    args = parser.parse_args()

    await args.func(args)


if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.INFO)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
