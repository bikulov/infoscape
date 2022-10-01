import jwt
import os
import time
import logging

from typing import Optional

AUTH_SECRET = os.environ["AUTH_SECRET"]


class Auth:
    def __init__(self, secret: str = AUTH_SECRET):
        self.secret = secret
        self.algorithm = "HS256"

    def get_token(self, lifetime: int = 3600) -> str:
        payload = {
            "valid-til": int(time.time()) + lifetime
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def check_token(self, token: Optional[str]) -> bool:
        if not token:
            return False

        try:
            decoded = jwt.decode(token, self.secret, algorithms=[self.algorithm])

            if decoded["valid-til"] > time.time():
                return True
        except Exception:
            logging.error("Invalid token")

        return False
