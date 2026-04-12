from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import yaml


@dataclass(frozen=True)
class SourceConfig:
    allowed_parsers = ("telegram",)
    title: str
    id: str
    parser: str
    link: str
    pages: Tuple[str, ...] = ()
    hidden: bool = False

    def __post_init__(self) -> None:
        if self.parser not in self.allowed_parsers:
            raise ValueError(f"Unsupported parser: {self.parser}")

        normalized_pages = tuple(dict.fromkeys(self.pages))
        object.__setattr__(self, "pages", normalized_pages)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceConfig":
        raw_pages = data.get("pages") or []
        return cls(
            title=data["title"],
            id=data["id"],
            parser=data["parser"],
            link=data["link"],
            pages=tuple(raw_pages),
            hidden=bool(data.get("hidden", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "id": self.id,
            "parser": self.parser,
            "link": self.link,
            "pages": list(self.pages),
            "hidden": self.hidden,
        }


@dataclass(frozen=True)
class PageConfig:
    title: str
    slug: str
    sources: Tuple[SourceConfig, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slug": self.slug,
            "sources": [source.to_dict() for source in self.sources],
        }


class Config:
    def __init__(
        self,
        title: str,
        hostname: str,
        keywords: Iterable[str],
        sources: Iterable[SourceConfig],
    ) -> None:
        self.title = title
        self.hostname = hostname
        self.keywords = tuple(dict.fromkeys(keywords))
        self.sources = tuple(
            sorted(sources, key=lambda source: source.title.casefold())
        )
        self.pages = self._build_pages(self.sources)
        self._validate_unique_source_ids()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        sources = [SourceConfig.from_dict(source) for source in data["sources"]]
        return cls(
            title=data["title"],
            hostname=data["hostname"],
            keywords=data.get("keywords", ()),
            sources=sources,
        )

    @classmethod
    def from_file_factory(cls, filename: str) -> "Config":
        return cls.from_file(filename)

    @classmethod
    def from_file(cls, filename: str) -> "Config":
        with Path(filename).open(encoding="utf-8") as file_handle:
            config = yaml.safe_load(file_handle) or {}
        return cls.from_dict(config)

    def _build_pages(self, sources: Iterable[SourceConfig]) -> Dict[str, PageConfig]:
        page_sources: Dict[str, List[SourceConfig]] = {}
        for source in sources:
            for page_slug in source.pages:
                page_sources.setdefault(page_slug, []).append(source)

        pages: Dict[str, PageConfig] = {}
        for page_slug, grouped_sources in sorted(page_sources.items()):
            pages[page_slug] = PageConfig(
                title=page_slug,
                slug=page_slug,
                sources=tuple(
                    sorted(grouped_sources, key=lambda source: source.title.casefold())
                ),
            )
        return pages

    def _validate_unique_source_ids(self) -> None:
        seen = set()
        for source in self.sources:
            if source.id in seen:
                raise ValueError(f"Duplicate source id: {source.id}")
            seen.add(source.id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "hostname": self.hostname,
            "keywords": list(self.keywords),
            "sources": [s.to_dict() for s in self.sources],
        }
