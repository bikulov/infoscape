import asyncio
import logging
from pathlib import Path
from typing import Any, cast

import aiohttp
import pytest
from library.config import Config, SourceConfig
from library.fetcher import FETCH_ATTEMPTS, FetchService
from library.posts_db import Post, PostsDb
import library.fetcher as fetcher_module


def make_service(tmp_path: Path) -> tuple[FetchService, SourceConfig]:
    source = SourceConfig(
        title="Source",
        id="source",
        parser="telegram",
        link="https://example.com/source",
    )
    config = Config(
        title="Infoscape",
        hostname="example.com",
        keywords=(),
        sources=[source],
    )
    db = PostsDb(str(tmp_path / "posts.sqlite"))
    return FetchService(config, db), source


def test_fetch_source_retries_timeout_and_recovers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    service, source = make_service(tmp_path)
    attempts = 0
    expected_posts = [
        Post(
            source_id=source.id,
            link="https://example.com/post",
            timestamp=1,
            heading="Heading",
            text="Body",
        )
    ]

    class FlakyParser:
        def __init__(self, source_id: str, link: str) -> None:
            self.source_id = source_id
            self.link = link

        async def get_posts(self, session: Any) -> list[Post]:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise asyncio.TimeoutError
            return expected_posts

    async def fake_sleep(delay: float) -> None:
        return None

    monkeypatch.setitem(fetcher_module.PARSERS, source.parser, FlakyParser)
    monkeypatch.setattr(fetcher_module.asyncio, "sleep", fake_sleep)
    caplog.set_level(logging.WARNING)

    posts = asyncio.run(
        service._fetch_source(cast(aiohttp.ClientSession, object()), source)
    )

    assert posts == expected_posts
    assert attempts == 2
    assert "Retrying source source after attempt 1/3" in caplog.text


def test_fetch_source_returns_empty_after_repeated_timeouts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    service, source = make_service(tmp_path)
    attempts = 0

    class TimeoutParser:
        def __init__(self, source_id: str, link: str) -> None:
            self.source_id = source_id
            self.link = link

        async def get_posts(self, session: Any) -> list[Post]:
            nonlocal attempts
            attempts += 1
            raise asyncio.TimeoutError

    async def fake_sleep(delay: float) -> None:
        return None

    monkeypatch.setitem(fetcher_module.PARSERS, source.parser, TimeoutParser)
    monkeypatch.setattr(fetcher_module.asyncio, "sleep", fake_sleep)
    caplog.set_level(logging.WARNING)

    posts = asyncio.run(
        service._fetch_source(cast(aiohttp.ClientSession, object()), source)
    )

    assert posts == []
    assert attempts == FETCH_ATTEMPTS
    assert "Failed to fetch source source after 3 attempts" in caplog.text
    assert "request timed out after 15s" in caplog.text
