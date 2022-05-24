import json
from typing import List


class SourceConfig:
    allowed_parsers = ("telegram",)

    def __init__(self, title: str, id: str, parser: str, link: str):
        self.title = title  # Link title
        self.id = id  # Internal unique news source name
        self.link = link  # Link where to get news from
        self.parser = parser  # Parser kind

        assert self.parser in self.allowed_parsers

    def to_dict(self):
        return {
            "title": self.title,
            "id": self.id,
            "parser": self.parser,
            "link": self.link,
        }


class PageConfig:
    def __init__(self, title: str, slug: str, sources: List[str]):
        self.title = title
        self.slug = slug
        self.sources = sources

    def to_dict(self):
        return {
            "title": self.title,
            "slug": self.slug,
            "sources": self.sources,
        }


class Config:
    def __init__(self, title: str, pages: List[dict], sources: List[dict]):
        self.title = title
        self.pages = {p["slug"]: PageConfig(**p) for p in pages}
        self.sources = {s["id"]: SourceConfig(**s) for s in sources}

        # TODO: check config integrity

    @staticmethod
    def from_file_factory(filename):
        with open(filename) as fin:
            config = json.load(fin)
            return Config(**config)

    def to_dict(self):
        return {
            "title": self.title,
            "pages": [p.to_dict() for p in self.pages.values()],
            "sources": [s.to_dict() for s in self.sources.values()],
        }


if __name__ == "__main__":
    app_config = Config.from_file_factory("config.json")

    print(json.dumps(app_config.to_dict(), indent=2, ensure_ascii=False))
