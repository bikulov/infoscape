from library.posts_db import Post
from library.source_renderer import SourceRenderer


def test_renderer_escapes_html_and_highlights_keywords() -> None:
    renderer = SourceRenderer(["Yandex"])
    source = renderer(
        heading="Source",
        link="https://example.com",
        posts=[
            Post(
                source_id="a",
                link="https://example.com/post",
                timestamp=1,
                heading='<script>alert("x")</script> Yandex',
                text="<b>unsafe</b>",
            )
        ],
    )

    rendered_post = source.posts[0]

    assert "<script>" not in rendered_post.summary
    assert "&lt;script&gt;" in rendered_post.summary
    assert "<mark>Yandex</mark>" in rendered_post.summary
    assert rendered_post.html == "&lt;b&gt;unsafe&lt;/b&gt;"


def test_renderer_renders_safe_image_tags() -> None:
    renderer = SourceRenderer([])
    source = renderer(
        heading="Source",
        link="https://example.com",
        posts=[
            Post(
                source_id="a",
                link="https://example.com/post",
                timestamp=1,
                heading="Heading",
                text="caption",
                image_url="https://cdn.example.com/image.jpg",
            )
        ],
    )

    assert (
        source.posts[0].html
        == 'caption<br><img src="https://cdn.example.com/image.jpg" alt="">'
    )
