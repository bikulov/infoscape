import argparse
import sys

import pytest

import main


def test_fetch_cli_does_not_require_serve_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    async def fake_fetch(args: argparse.Namespace) -> None:
        nonlocal called
        called = args.daemonize == 0

    monkeypatch.setattr(main, "fetch", fake_fetch)
    monkeypatch.setattr(sys, "argv", ["infoscape", "fetch", "--daemonize", "0"])

    main.main()

    assert called is True


def test_reload_cannot_be_combined_with_multiple_workers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["infoscape", "serve", "--reload", "--workers", "2"],
    )

    with pytest.raises(SystemExit) as exc_info:
        main.main()

    assert exc_info.value.code == 2
