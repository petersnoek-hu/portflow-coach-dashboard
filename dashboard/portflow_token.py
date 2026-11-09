"""The Portflow bearer token: reading its expiry, and keeping it in .env.

The token is a secret. It is only stored in .env (see CLAUDE.md) and never
shown in the browser, in logs or in error messages.
"""

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ENV_KEY = "PORTFLOW_BEARER_TOKEN"


def decode_payload(token: str) -> dict | None:
    """Return the (unverified) JWT payload, or None if this is not a JWT."""
    parts = token.strip().split(".")
    if len(parts) != 3:
        return None
    try:
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def expires_at(token: str) -> datetime | None:
    """Expiry time (UTC) from the 'exp' claim, or None if unknown."""
    payload = decode_payload(token) or {}
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)):
        return None
    return datetime.fromtimestamp(exp, tz=timezone.utc)


class TokenStore:
    """Reads and writes PORTFLOW_BEARER_TOKEN in a .env file, keeping other lines."""

    def __init__(self, env_path: Path | str):
        self.path = Path(env_path)

    def _lines(self) -> list[str]:
        return self.path.read_text(encoding="utf-8").splitlines() if self.path.exists() else []

    def read(self) -> str | None:
        for line in self._lines():
            key, sep, value = line.partition("=")
            if sep and key.strip().removeprefix("export ").strip() == ENV_KEY:
                return value.strip().strip("'\"") or None
        return None

    def save(self, token: str) -> None:
        lines = [line for line in self._lines() if not self._is_token_line(line)]
        lines.append(f"{ENV_KEY}={token}")
        self._write(lines)

    def delete(self) -> None:
        if self.path.exists():
            self._write([line for line in self._lines() if not self._is_token_line(line)])

    @staticmethod
    def _is_token_line(line: str) -> bool:
        key, sep, _ = line.partition("=")
        return bool(sep) and key.strip().removeprefix("export ").strip() == ENV_KEY

    def _write(self, lines: list[str]) -> None:
        self.path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        os.chmod(self.path, 0o600)  # readable for the user only
