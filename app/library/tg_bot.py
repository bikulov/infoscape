from dataclasses import dataclass
import os
import json
from typing import Dict, Optional
import aiohttp

from .auth import Auth

TG_TOKEN = os.environ["TG_TOKEN"]
TG_API_URL = "https://api.telegram.org"


@dataclass
class TgBotCommand:
    update_id: int
    chat_id: int
    text: str

    @staticmethod
    def parse(update: Dict) -> Optional["TgBotCommand"]:
        update_id = update.get("update_id")
        chat_id = update.get("message", {}).get("chat", {}).get("id")
        text = update.get("message", {}).get("text").strip("/")

        bot_command = False
        for entity in update.get("message", {}).get("entities", []):
            if entity.get("type") == "bot_command":
                bot_command = True

        if bot_command and update_id and chat_id and text:
            return TgBotCommand(update_id, chat_id, text)


class TgBot:
    def __init__(self, site_host: str, url: str = TG_API_URL, token: str = TG_TOKEN):
        self.api_url = url
        self.token = token
        self.offset = 0
        self.commands = [
            {"command": "link", "description": "Return link with token"}
        ]
        self.auth = Auth()
        self.site_host = site_host

    async def init_bot(self) -> bool:
        status = False
        async with aiohttp.ClientSession(f"{self.api_url}") as session:
            async with session.post(f"/bot{self.token}/setMyCommands?commands={json.dumps(self.commands)}") as response:
                if not await response.json():
                    raise Exception("Error setting commands")

            async with session.post(f"/bot{self.token}/setWebhook?url={self.site_host}/tg-webhook") as response:
                if not await response.json():
                    raise Exception("Error setting webhook")

        return status

    async def send_message(self, chat_id: int, text: str) -> bool:
        async with aiohttp.ClientSession(f"{self.api_url}") as session:
            async with session.get(f"/bot{self.token}/sendMessage?chat_id={chat_id}&text={text}") as response:
                if _ := await response.json():
                    return True

                return False

    async def process_update(self, update: Dict) -> None:
        if command := TgBotCommand.parse(update):
            if command.text == "link":
                token = self.auth.get_token(lifetime=12 * 3600)
                text = f"https://{self.site_host}/set-token?value={token}"
            else:
                text = "Unknown command, maybe you need /link?"
            await self.send_message(command.chat_id, text)

    async def get_updates(self) -> None:
        async with aiohttp.ClientSession(f"{self.api_url}") as session:
            async with session.get(f"/bot{self.token}/getUpdates?offset={self.offset}") as response:
                if updates := await response.json():
                    for update in updates["result"]:
                        await self.process_update(update)

                        self.offset = max(self.offset, update["update_id"] + 1)
