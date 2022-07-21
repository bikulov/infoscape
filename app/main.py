import argparse
import os
import asyncio
import logging
import time


import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, PackageLoader, select_autoescape

from library import Config, PostsDb, SourceRenderer
from parsers import TelegramParser, TelegramParserException

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

config = Config.from_file_factory("config.json")
logger = logging.getLogger("infoscape")
db = PostsDb()


env = Environment(loader=PackageLoader("main"), autoescape=select_autoescape())


async def fetch(args: argparse.Namespace) -> None:
    while True:
        for source in config.sources.values():
            logger.info(f"fetching {source.id}")
            if source.parser == "telegram":
                try:
                    parser = TelegramParser(source.id, source.link)
                    async for post in parser.get_posts():
                        db.add(post)
                except TelegramParserException:
                    logger.exception(f"Error while fetching source {source.id}")

        if args.daemonize > 0:
            logger.info(f"sleeping {args.daemonize} seconds")
            time.sleep(args.daemonize)
        else:
            break


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    source_renderer = SourceRenderer()
    template = env.get_template("index.html")

    widgets = []
    for s in config.sources.values():
        widgets.append(source_renderer(
            heading=s.title,
            link=s.link,
            posts=db.select([s.id], 10)
        ))

    return template.render(
        title=config.title,
        page_slug="/",
        pages=config.pages.values(),
        widgets=widgets,
    )


@app.get("/p/{page_slug}", response_class=HTMLResponse)
async def get_page(page_slug: str = "top") -> str:
    source_renderer = SourceRenderer()
    template = env.get_template("index.html")

    page = config.pages[page_slug]
    widgets = []
    for s in page.sources:
        widgets.append(source_renderer(
            heading=config.sources[s].title,
            link=config.sources[s].link,
            posts=db.select([s], 10)
        ))

    return template.render(
        title=config.title,
        page_slug=page_slug,
        pages=config.pages.values(),
        widgets=widgets,
    )


async def serve(args: argparse.Namespace) -> None:
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=3)


async def main() -> None:
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
