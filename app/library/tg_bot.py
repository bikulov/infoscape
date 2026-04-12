from dataclasses import dataclass
import json
from typing import Any, Dict, Mapping, Optional
from urllib.parse import urlsplit

import aiohttp

from .auth import Auth

TG_API_URL = "https://api.telegram.org"


@dataclass(frozen=True)
class TgBotCommand:
    update_id: int
    chat_id: int
    text: str

    @staticmethod
    def parse(update: Mapping[str, Any]) -> Optional["TgBotCommand"]:
        update_id = update.get("update_id")
        message = update.get("message")
        if not isinstance(message, Mapping):
            return None

        chat = message.get("chat", {})
        text = message.get("text")
        entities = message.get("entities", [])
        chat_id = chat.get("id") if isinstance(chat, Mapping) else None
        if not isinstance(update_id, int) or not isinstance(chat_id, int):
            return None
        if not isinstance(text, str):
            return None

        bot_command = False
        for entity in entities:
            if (
                isinstance(entity, Mapping)
                and entity.get("type") == "bot_command"
                and entity.get("offset", 0) == 0
            ):
                bot_command = True

        command_text = text.split()[0].lstrip("/")
        if bot_command and command_text:
            return TgBotCommand(update_id, chat_id, command_text)
        return None


class TgBot:
    def __init__(
        self,
        site_host: str,
        token: str,
        auth: Auth,
        url: str = TG_API_URL,
    ) -> None:
        self.api_url = url
        self.token = token
        self.offset = 0
        self.commands = [{"command": "link", "description": "Return link with token"}]
        self.auth = auth
        self.site_host = self._normalize_site_host(site_host)
        self.session: Optional[aiohttp.ClientSession] = None

    async def start(self) -> None:
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=15)
            self.session = aiohttp.ClientSession(
                base_url=self.api_url,
                timeout=timeout,
            )

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()
            self.session = None

    async def init_bot(self) -> bool:
        await self._request(
            "POST",
            f"/bot{self.token}/setMyCommands",
            params={"commands": json.dumps(self.commands, ensure_ascii=False)},
        )
        await self._request(
            "POST",
            f"/bot{self.token}/setWebhook",
            params={"url": f"{self.site_host}/tg-webhook"},
        )
        return True

    async def send_message(self, chat_id: int, text: str) -> bool:
        await self._request(
            "POST",
            f"/bot{self.token}/sendMessage",
            params={"chat_id": chat_id, "text": text},
        )
        return True

    async def process_update(self, update: Mapping[str, Any]) -> None:
        if command := TgBotCommand.parse(update):
            if command.text == "link":
                try:
                    token = self.auth.get_token(lifetime=12 * 3600)
                    text = f"{self.site_host}/set-token?value={token}"
                except RuntimeError:
                    text = "Auth is not configured on the server."
            else:
                text = "Unknown command, maybe you need /link?"
            await self.send_message(command.chat_id, text)

    async def get_updates(self) -> None:
        updates = await self._request(
            "GET",
            f"/bot{self.token}/getUpdates",
            params={"offset": self.offset},
        )
        for update in updates.get("result", []):
            if not isinstance(update, Mapping):
                continue
            await self.process_update(update)
            update_id = update.get("update_id")
            if isinstance(update_id, int):
                self.offset = max(self.offset, update_id + 1)

    async def _request(
        self, method: str, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if self.session is None:
            raise RuntimeError("Telegram bot session is not started")

        async with self.session.request(method, path, params=params) as response:
            response.raise_for_status()
            payload = await response.json()

        if not payload.get("ok"):
            raise RuntimeError(
                payload.get("description", "Telegram API request failed")
            )
        return payload

    @staticmethod
    def _normalize_site_host(site_host: str) -> str:
        parsed = urlsplit(site_host)
        if parsed.scheme:
            return site_host.rstrip("/")
        return f"https://{site_host.rstrip('/')}"
