import yaml
from typing import List, Dict, Optional


class SourceConfig:
    allowed_parsers = ("telegram",)

    def __init__(
        self,
        title: str, id: str, parser: str, link: str,
        pages: Optional[List] = None, hidden: bool = False
    ) -> None:
        self.title = title  # Link title
        self.id = id  # Internal unique news source name
        self.link = link  # Link where to get news from
        self.parser = parser  # Parser kind
        self.pages = pages or []
        self.hidden = hidden

        assert self.parser in self.allowed_parsers

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "id": self.id,
            "parser": self.parser,
            "link": self.link,
        }


class PageConfig:
    def __init__(self, title: str, slug: str, sources: List[SourceConfig]) -> None:
        self.title = title
        self.slug = slug
        self.sources = sources

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "slug": self.slug,
            "sources": self.sources,
        }


class Config:
    def __init__(self, title: str, hostname: str, keywords: List[str], sources: List[dict]) -> None:
        self.title = title
        self.hostname = hostname
        self.keywords = keywords
        self.sources = [SourceConfig(**s) for s in sources]
        self.sources.sort(key=lambda s: s.title)

        self.pages: Dict[str, PageConfig] = {}
        for source in self.sources:
            for page in source.pages:
                if page not in self.pages:
                    self.pages[page] = PageConfig(page, page, [])
                self.pages[page].sources.append(source)

        for page in self.pages:
            self.pages[page].sources.sort(key=lambda s: s.title)

        # TODO: check config integrity

    @staticmethod
    def from_file_factory(filename: str) -> 'Config':
        with open(filename) as fin:
            config = yaml.safe_load(fin)
            return Config(**config)

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "sources": [s.to_dict() for s in self.sources],
        }
