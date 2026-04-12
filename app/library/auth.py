import logging
import time
from typing import Optional

import jwt


logger = logging.getLogger(__name__)


class Auth:
    def __init__(self, secret: str = "") -> None:
        self.secret = secret
        self.algorithm = "HS256"

    def get_token(self, lifetime: int = 3600) -> str:
        if not self.secret:
            raise RuntimeError("AUTH_SECRET is not configured")

        expires_at = int(time.time()) + lifetime
        payload = {"exp": expires_at, "valid-til": expires_at}
        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        if isinstance(token, bytes):
            return token.decode("utf-8")
        return token

    def check_token(self, token: Optional[str]) -> bool:
        if not token or not self.secret:
            return False

        try:
            decoded = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                options={"verify_exp": False},
            )
        except jwt.InvalidTokenError:
            logger.info("Invalid token")
            return False

        expires_at = decoded.get("exp", decoded.get("valid-til"))
        if isinstance(expires_at, (int, float)):
            return expires_at > time.time()
        return False
