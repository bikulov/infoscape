import argparse
import asyncio
import inspect
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Optional, Sequence, cast

import uvicorn
from fastapi import APIRouter, Cookie, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from library import Auth, Config, FetchService, PostsDb, Settings, SourceRenderer, TgBot
from library.config import SourceConfig


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"
POSTS_PER_WIDGET = 10
logger = logging.getLogger("infoscape")
router = APIRouter()


@dataclass
class RuntimeServices:
    config: Config
    db: PostsDb
    auth: Auth
    renderer: SourceRenderer
    templates: Environment
    tg_bot: Optional[TgBot]


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    resolved_settings = settings or Settings.from_env(
        config_path=os.getenv("INFOSCAPE_CONFIG", "config.yaml"),
        db_path=os.getenv("INFOSCAPE_DB_PATH", "data/production.sqlite"),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        runtime = build_runtime(resolved_settings)
        app.state.runtime = runtime

        if runtime.tg_bot is not None:
            await runtime.tg_bot.start()
            try:
                await runtime.tg_bot.init_bot()
            except Exception:
                logger.exception(
                    "Telegram bot initialization failed; continuing without bot"
                )
                await runtime.tg_bot.close()
                runtime.tg_bot = None
        elif resolved_settings.tg_token and not resolved_settings.auth_enabled:
            logger.warning(
                "Telegram bot disabled because AUTH_SECRET is not configured"
            )

        try:
            yield
        finally:
            if runtime.tg_bot is not None:
                await runtime.tg_bot.close()
            runtime.db.close()

    app = FastAPI(lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(router)
    return app


def build_runtime(settings: Settings) -> RuntimeServices:
    config = Config.from_file(settings.config_path)
    auth = Auth(settings.auth_secret)
    tg_bot = None
    if settings.bot_enabled:
        tg_bot = TgBot(site_host=config.hostname, token=settings.tg_token, auth=auth)

    return RuntimeServices(
        config=config,
        db=PostsDb(settings.db_path),
        auth=auth,
        renderer=SourceRenderer(list(config.keywords)),
        templates=Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(("html", "xml")),
        ),
        tg_bot=tg_bot,
    )


def get_runtime(request: Request) -> RuntimeServices:
    return cast(RuntimeServices, request.app.state.runtime)


@router.get("/healthz")
async def healthcheck() -> dict:
    return {"status": "ok"}


@router.get("/set-token")
async def set_token(request: Request, value: str) -> RedirectResponse:
    runtime = get_runtime(request)
    response = RedirectResponse("/")
    if runtime.auth.check_token(value):
        response.set_cookie(
            key="token",
            value=value,
            httponly=True,
            samesite="lax",
        )
    return response


@router.post("/tg-webhook")
async def tg_webhook(request: Request) -> str:
    runtime = get_runtime(request)
    if runtime.tg_bot is None:
        return ""

    data = await request.json()
    await runtime.tg_bot.process_update(data)
    return ""


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, token: Optional[str] = Cookie(default="")) -> str:
    runtime = get_runtime(request)
    return render_page(
        runtime=runtime,
        page_slug="/",
        sources=runtime.config.sources,
        token=token,
    )


@router.get("/p/{page_slug}", response_class=HTMLResponse)
async def get_page(
    request: Request, page_slug: str, token: Optional[str] = Cookie(default="")
) -> str:
    runtime = get_runtime(request)
    page = runtime.config.pages.get(page_slug)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")

    return render_page(
        runtime=runtime,
        page_slug=page_slug,
        sources=page.sources,
        token=token,
    )


def render_page(
    runtime: RuntimeServices,
    page_slug: str,
    sources: Sequence[SourceConfig],
    token: Optional[str],
) -> str:
    has_token = runtime.auth.check_token(token)
    visible_sources = [source for source in sources if not source.hidden or has_token]
    posts_by_source = runtime.db.select_grouped(
        [source.id for source in visible_sources],
        POSTS_PER_WIDGET,
    )
    widgets = [
        runtime.renderer(
            heading=source.title,
            link=source.link,
            posts=posts_by_source.get(source.id, []),
        )
        for source in visible_sources
    ]

    template = runtime.templates.get_template("index.html")
    return template.render(
        title=runtime.config.title,
        page_slug=page_slug,
        pages=runtime.config.pages.values(),
        widgets=widgets,
    )


async def fetch(args: argparse.Namespace) -> None:
    settings = Settings.from_env(config_path=args.config, db_path=args.db_path)
    runtime = build_runtime(settings)
    fetch_service = FetchService(runtime.config, runtime.db)

    try:
        while True:
            stored_posts = await fetch_service.run_once()
            logger.info("Stored %s posts", stored_posts)

            if args.daemonize <= 0:
                break

            logger.info("Sleeping %s seconds", args.daemonize)
            await asyncio.sleep(args.daemonize)
    finally:
        runtime.db.close()


def serve(args: argparse.Namespace) -> None:
    os.environ["INFOSCAPE_CONFIG"] = os.path.abspath(args.config)
    os.environ["INFOSCAPE_DB_PATH"] = os.path.abspath(args.db_path)
    uvicorn.run(
        "main:create_app",
        app_dir=str(BASE_DIR),
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level.lower(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="infoscape")
    parser.add_argument("--config", default="config.yaml", help="App configuration")
    parser.add_argument(
        "--db-path",
        default="data/production.sqlite",
        help="SQLite database location",
    )
    parser.add_argument("--log-level", default="INFO", help="Application log level")
    subparsers = parser.add_subparsers(help="mode")

    serve_parser = subparsers.add_parser("serve", help="serve news")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    serve_parser.add_argument("--port", type=int, default=8000, help="Bind port")
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable autoreload for development",
    )
    serve_parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes",
    )
    serve_parser.set_defaults(func=serve)

    fetch_parser = subparsers.add_parser("fetch", help="fetch news")
    fetch_parser.add_argument(
        "--daemonize",
        type=int,
        default=600,
        help="Run in a loop with the provided sleep interval in seconds",
    )
    fetch_parser.set_defaults(func=fetch)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.error("Please choose a mode: serve or fetch")
    if args.reload and args.workers != 1:
        parser.error("--reload cannot be combined with --workers > 1")

    logger.setLevel(getattr(logging, args.log_level.upper(), logging.INFO))
    result = args.func(args)
    if inspect.iscoroutine(result):
        asyncio.run(result)


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    main()
