from library.settings import DISABLED_TG_TOKEN, Settings


def test_placeholder_env_values_are_treated_as_missing() -> None:
    settings = Settings(
        config_path="config.yaml",
        db_path="data.sqlite",
        auth_secret=Settings._normalize_env_value("<random_string>"),
        tg_token=Settings._normalize_env_value("<telegram_token>"),
    )

    assert settings.auth_secret == ""
    assert settings.tg_token == ""
    assert settings.auth_enabled is False
    assert settings.bot_enabled is False


def test_test_token_keeps_bot_disabled() -> None:
    settings = Settings(
        config_path="config.yaml",
        db_path="data.sqlite",
        auth_secret="secret",
        tg_token=DISABLED_TG_TOKEN,
    )

    assert settings.auth_enabled is True
    assert settings.bot_enabled is False
