from dataclasses import dataclass
import os
import json
from typing import Dict, Optional
import aiohttp

from .auth import Auth

TG_TOKEN = os.environ["TG_TOKEN"]
TG_URL = "https://api.telegram.org"


@dataclass
class TgBotCommand:
    update_id: int
    chat_id: int
    text: str

    @staticmethod
    def parse(update: Dict) -> Optional["TgBotCommand"]:
        update_id = update.get("update_id")
        chat_id = update.get("message", {}).get("chat", {}).get("id")
        text = update.get("message", {}).get("text")

        bot_command = False
        for entity in update.get("message", {}).get("entities", []):
            if entity.get("type") == "bot_command":
                bot_command = True

        if bot_command and update_id and chat_id and text:
            return TgBotCommand(update_id, chat_id, text)


class TgBot:
    def __init__(self, site_host: str, url: str = TG_URL, token: str = TG_TOKEN):
        self.url = url
        self.token = token
        self.offset = 0
        self.commands = [
            {"command": "link", "description": "Return link with token"}
        ]
        self.auth = Auth()
        self.site_host = site_host

    async def set_commands(self) -> bool:
        async with aiohttp.ClientSession(f"{self.url}") as session:
            async with session.post(f"/bot{self.token}/setMyCommands?commands={json.dumps(self.commands)}") as response:
                if _ := await response.json():
                    return True

                return False

    async def send_message(self, chat_id: int, text: str) -> bool:
        async with aiohttp.ClientSession(f"{self.url}") as session:
            async with session.get(f"/bot{self.token}/sendMessage?chat_id={chat_id}&text={text}") as response:
                if _ := await response.json():
                    return True

                return False

    async def get_updates(self) -> None:
        async with aiohttp.ClientSession(f"{self.url}") as session:
            async with session.get(f"/bot{self.token}/getUpdates?offset={self.offset}") as response:
                if updates := await response.json():
                    for update in updates["result"]:
                        if command := TgBotCommand.parse(update):
                            token = self.auth.get_token()
                            link = f"https://{self.site_host}/set-token?value={token}"
                            await self.send_message(command.chat_id, link)

                        self.offset = max(self.offset, update["update_id"] + 1)
