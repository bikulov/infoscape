from dataclasses import dataclass
import sqlite3
from typing import List


@dataclass
class Post:
    source_id: str
    link: str
    timestamp: int
    heading: str
    text: str


class PostsDb:
    def __init__(self, filename: str = "data/production.sqlite"):
        self.conn = sqlite3.connect(filename)

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                source_id   TEXT,
                link        TEXT,
                timestamp   INT,
                heading     TEXT,
                text        TEXT,
                PRIMARY KEY (source_id, link)
            );
            """
        )

    def add(self, post: Post):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO posts (source_id, link, timestamp, heading, text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (post.source_id, post.link, post.timestamp, post.heading, post.text),
        )
        self.conn.commit()

    def select(self, source_ids: List[str], limit: int = 10) -> List[Post]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT source_id, link, timestamp, heading, text
            FROM posts
            WHERE source_id IN (?) ORDER BY timestamp DESC
            LIMIT ?
            """,
            (", ".join(source_ids), limit),
        )

        result = []
        for row in cursor.fetchmany(limit):
            source_id, link, timestamp, heading, text = row
            timestamp = int(timestamp)
            result.append(Post(source_id, link, timestamp, heading, text))

        return result


if __name__ == "__main__":
    db = PostsDb("data/testing.sqlite")
    db.add(
        Post(
            "mask", "http://yandex.ru/1", 200000000, "Тестовая запись", "abc\nddf"
        )
    )

    for a in db.select(["mask"], 4):
        print(a)
