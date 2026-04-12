import asyncio
import logging
from typing import Dict, List, Type

import aiohttp

from parsers import TelegramParser

from .config import Config, SourceConfig
from .posts_db import Post, PostsDb


PARSERS: Dict[str, Type[TelegramParser]] = {
    "telegram": TelegramParser,
}
FETCH_TIMEOUT_SECONDS = 15
FETCH_ATTEMPTS = 3


class FetchService:
    def __init__(self, config: Config, db: PostsDb) -> None:
        self.config = config
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def run_once(self) -> int:
        timeout = aiohttp.ClientTimeout(total=FETCH_TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [
                self._fetch_source(session, source) for source in self.config.sources
            ]
            fetched_sources = await asyncio.gather(*tasks)

        posts = [post for source_posts in fetched_sources for post in source_posts]
        return self.db.add_many(posts)

    async def _fetch_source(
        self, session: aiohttp.ClientSession, source: SourceConfig
    ) -> List[Post]:
        parser_class = PARSERS[source.parser]
        parser = parser_class(source.id, source.link)
        self.logger.info("Fetching %s", source.id)

        for attempt in range(1, FETCH_ATTEMPTS + 1):
            try:
                return await parser.get_posts(session)
            except (asyncio.TimeoutError, aiohttp.ClientError) as exc:
                if attempt == FETCH_ATTEMPTS:
                    self.logger.warning(
                        "Failed to fetch source %s after %s attempts: %s",
                        source.id,
                        FETCH_ATTEMPTS,
                        self._format_fetch_error(exc),
                    )
                    return []

                self.logger.warning(
                    "Retrying source %s after attempt %s/%s: %s",
                    source.id,
                    attempt,
                    FETCH_ATTEMPTS,
                    self._format_fetch_error(exc),
                )
                await asyncio.sleep(attempt)
            except Exception:
                self.logger.exception("Error while fetching source %s", source.id)
                return []

        return []

    @staticmethod
    def _format_fetch_error(exc: BaseException) -> str:
        if isinstance(exc, asyncio.TimeoutError):
            return f"request timed out after {FETCH_TIMEOUT_SECONDS}s"

        message = str(exc)
        return message or exc.__class__.__name__
