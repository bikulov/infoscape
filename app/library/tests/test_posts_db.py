from library.posts_db import Post, PostsDb


def test_select_supports_multiple_sources(tmp_path) -> None:
    db = PostsDb(str(tmp_path / "posts.sqlite"))
    try:
        db.add_many(
            [
                Post("a", "https://a/1", 10, "A1", "hello"),
                Post("b", "https://b/1", 20, "B1", "world"),
                Post("a", "https://a/2", 30, "A2", "python"),
            ]
        )

        posts = db.select(["a", "b"], limit=3)

        assert [post.link for post in posts] == [
            "https://a/2",
            "https://b/1",
            "https://a/1",
        ]
    finally:
        db.close()


def test_select_grouped_limits_each_source(tmp_path) -> None:
    db = PostsDb(str(tmp_path / "posts.sqlite"))
    try:
        db.add_many(
            [
                Post("a", "https://a/1", 10, "A1", "hello"),
                Post("a", "https://a/2", 30, "A2", "hello"),
                Post("b", "https://b/1", 20, "B1", "hello"),
            ]
        )

        grouped_posts = db.select_grouped(["a", "b"], limit=1)

        assert [post.link for post in grouped_posts["a"]] == ["https://a/2"]
        assert [post.link for post in grouped_posts["b"]] == ["https://b/1"]
    finally:
        db.close()


def test_select_keyword_searches_heading_and_text(tmp_path) -> None:
    db = PostsDb(str(tmp_path / "posts.sqlite"))
    try:
        db.add_many(
            [
                Post("a", "https://a/1", 10, "Alpha", "plain text"),
                Post("b", "https://b/1", 20, "No match", "Contains Python"),
            ]
        )

        posts = db.select_keyword("python")

        assert [post.link for post in posts] == ["https://b/1"]
    finally:
        db.close()
