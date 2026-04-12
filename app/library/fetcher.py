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


class FetchService:
    def __init__(self, config: Config, db: PostsDb) -> None:
        self.config = config
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def run_once(self) -> int:
        timeout = aiohttp.ClientTimeout(total=15)
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
        try:
            self.logger.info("Fetching %s", source.id)
            return await parser.get_posts(session)
        except Exception:
            self.logger.exception("Error while fetching source %s", source.id)
            return []
