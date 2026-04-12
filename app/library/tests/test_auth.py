import time

import jwt

from library.auth import Auth


TEST_SECRET = "0123456789abcdef0123456789abcdef"


def test_generated_token_is_valid() -> None:
    auth = Auth(TEST_SECRET)

    token = auth.get_token(lifetime=60)

    assert auth.check_token(token) is True


def test_legacy_token_is_still_valid() -> None:
    auth = Auth(TEST_SECRET)
    token = jwt.encode(
        {"valid-til": int(time.time()) + 60},
        TEST_SECRET,
        algorithm="HS256",
    )

    assert auth.check_token(token) is True


def test_expired_token_is_rejected() -> None:
    auth = Auth(TEST_SECRET)
    token = jwt.encode(
        {"valid-til": int(time.time()) - 1},
        TEST_SECRET,
        algorithm="HS256",
    )

    assert auth.check_token(token) is False
