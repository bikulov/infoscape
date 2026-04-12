import os
from dataclasses import dataclass


DISABLED_TG_TOKEN = "na_for_test"


@dataclass(frozen=True)
class Settings:
    config_path: str
    db_path: str
    auth_secret: str = ""
    tg_token: str = ""

    @classmethod
    def from_env(
        cls,
        config_path: str = "config.yaml",
        db_path: str = "data/production.sqlite",
    ) -> "Settings":
        return cls(
            config_path=os.path.abspath(config_path),
            db_path=os.path.abspath(db_path),
            auth_secret=cls._normalize_env_value(os.getenv("AUTH_SECRET", "")),
            tg_token=cls._normalize_env_value(os.getenv("TG_TOKEN", "")),
        )

    @property
    def auth_enabled(self) -> bool:
        return bool(self.auth_secret)

    @property
    def bot_enabled(self) -> bool:
        return self.auth_enabled and self.tg_token not in {"", DISABLED_TG_TOKEN}

    @staticmethod
    def _normalize_env_value(value: str) -> str:
        normalized = value.strip()
        if not normalized:
            return ""
        if normalized.startswith("<") and normalized.endswith(">"):
            return ""
        return normalized
