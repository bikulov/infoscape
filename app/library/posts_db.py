from pathlib import Path
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence


@dataclass(frozen=True)
class Post:
    source_id: str
    link: str
    timestamp: int
    heading: str
    text: str
    image_url: Optional[str] = None


class PostsDb:
    def __init__(self, filename: str = "data/production.sqlite") -> None:
        db_path = Path(filename)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                source_id   TEXT,
                link        TEXT,
                timestamp   INT,
                heading     TEXT,
                text        TEXT,
                image_url   TEXT,
                PRIMARY KEY (source_id, link)
            );
            """
        )
        self._ensure_column("image_url", "TEXT")
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_posts_source_timestamp
            ON posts (source_id, timestamp DESC)
            """
        )

    def add(self, post: Post) -> None:
        self.add_many([post])

    def add_many(self, posts: Sequence[Post]) -> int:
        if not posts:
            return 0

        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO posts (source_id, link, timestamp, heading, text, image_url)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id, link) DO UPDATE SET
                    timestamp = excluded.timestamp,
                    heading = excluded.heading,
                    text = excluded.text,
                    image_url = excluded.image_url
                """,
                [
                    (
                        post.source_id,
                        post.link,
                        post.timestamp,
                        post.heading,
                        post.text,
                        post.image_url,
                    )
                    for post in posts
                ],
            )

        return len(posts)

    def select(self, source_ids: Sequence[str], limit: int = 10) -> List[Post]:
        if not source_ids or limit <= 0:
            return []

        placeholders = ", ".join("?" for _ in source_ids)
        query = f"""
            SELECT source_id, link, timestamp, heading, text, image_url
            FROM posts
            WHERE source_id IN ({placeholders})
            ORDER BY timestamp DESC
            LIMIT ?
        """
        rows = self.conn.execute(query, [*source_ids, limit]).fetchall()
        return [self._row_to_post(row) for row in rows]

    def select_grouped(
        self, source_ids: Sequence[str], limit: int = 10
    ) -> Dict[str, List[Post]]:
        grouped_posts: Dict[str, List[Post]] = {
            source_id: [] for source_id in source_ids
        }
        if not source_ids or limit <= 0:
            return grouped_posts

        placeholders = ", ".join("?" for _ in source_ids)
        query = f"""
            SELECT source_id, link, timestamp, heading, text, image_url
            FROM (
                SELECT
                    source_id,
                    link,
                    timestamp,
                    heading,
                    text,
                    image_url,
                    ROW_NUMBER() OVER (
                        PARTITION BY source_id
                        ORDER BY timestamp DESC
                    ) AS row_number
                FROM posts
                WHERE source_id IN ({placeholders})
            )
            WHERE row_number <= ?
            ORDER BY source_id, timestamp DESC
        """
        rows = self.conn.execute(query, [*source_ids, limit]).fetchall()
        for row in rows:
            post = self._row_to_post(row)
            grouped_posts[post.source_id].append(post)
        return grouped_posts

    def select_keyword(self, word: str, limit: int = 100) -> List[Post]:
        if not word or limit <= 0:
            return []

        like_pattern = f"%{word}%"
        rows = self.conn.execute(
            """
            SELECT source_id, link, timestamp, heading, text, image_url
            FROM posts
            WHERE heading LIKE ? COLLATE NOCASE
               OR text LIKE ? COLLATE NOCASE
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (like_pattern, like_pattern, limit),
        ).fetchall()
        return [self._row_to_post(row) for row in rows]

    def close(self) -> None:
        self.conn.close()

    def _ensure_column(self, column_name: str, column_type: str) -> None:
        columns = {
            row["name"]
            for row in self.conn.execute("PRAGMA table_info(posts)").fetchall()
        }
        if column_name not in columns:
            self.conn.execute(
                f"ALTER TABLE posts ADD COLUMN {column_name} {column_type}"
            )

    @staticmethod
    def _row_to_post(row: sqlite3.Row) -> Post:
        return Post(
            source_id=row["source_id"],
            link=row["link"],
            timestamp=int(row["timestamp"]),
            heading=row["heading"],
            text=row["text"],
            image_url=row["image_url"],
        )
