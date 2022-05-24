import json
import os

import pytest
from bs4 import BeautifulSoup

from library import Post
from parsers.telegram import TelegramParser


def test_parse_html():
    path = os.path.dirname(__file__)

    with open(os.path.join(path, "tests_data", "page.html")) as fin:
        html = fin.read()

    canon_posts = []
    with open(os.path.join(path, "tests_data", "canon_posts.json")) as fin:
        for post_data in json.load(fin):
            canon_posts.append(Post(**post_data))

    parser = TelegramParser("infoscape_test", "https://t.me/s/infoscape_test")
    posts = list(parser.parse_html(html))

    assert posts == canon_posts


@pytest.mark.parametrize(
    "html, url",
    (
        (
            """<a class="tgme_widget_message_photo_wrap 123 45_67" href="#" style="width:794px;background-image:url('https://cdn4.telegram-cdn.org/file/JYf.jpg')">
                <div class="tgme_widget_message_photo" style="padding-top:48.110831234257%"></div>
            </a>""",
            "https://cdn4.telegram-cdn.org/file/JYf.jpg",
        ),
        ("""<div class="other_tag" href="#"></div>""", None),
    ),
)
def test_extract_image_url(html, url):
    assert TelegramParser.get_image_url(BeautifulSoup(html, "html.parser")) == url


@pytest.mark.parametrize(
    "html, timestamp",
    (
        (
            """<a class="tgme_widget_message_date" href="#"><time datetime="2022-05-24T19:08:13+00:00" class="time">22:08</time></a>""",
            1653419293,
        ),
        ("""<div class="other_tag" href="#"></div>""", None),
    ),
)
def test_get_timestamp(html, timestamp):
    assert TelegramParser.get_timestamp(BeautifulSoup(html, "html.parser")) == timestamp


@pytest.mark.parametrize(
    "html, link",
    (
        (
            """<a class="tgme_widget_message_date" href="https://t.me/infoscape_test/3"><time datetime="2022-05-24T19:08:13+00:00" class="time">22:08</time></a>""",
            "https://t.me/infoscape_test/3",
        ),
        ("""<a class="other_tag" href="https://t.me/infoscape_test/3"></a>""", None),
    ),
)
def test_get_link(html, link):
    assert TelegramParser.get_link(BeautifulSoup(html, "html.parser")) == link
