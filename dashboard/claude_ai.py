"""AI-advies met Claude via de API (spec 040, F13-F17), with the official Anthropic SDK.

The API key lives only in the local database (like the Portflow token): never in code, logs,
backups or the browser. Labels are Dutch: they are shown to the user.
"""

import json
import threading
from datetime import datetime, timezone

from . import db
from .progress import name_key
from .ollama import OllamaError as AdviceError   # one kind of error with a Dutch message for both services

def _sdk():
    """The Anthropic SDK, loaded only when Claude is really used: it is large, and loading it at
    start-up made the first start after an installation or update slow for everyone."""
    import anthropic
    return anthropic


MODEL = "claude-opus-5-5"
# Spec 040, F22: Claude is only offered to this Portflow user (who pays for and manages the key).
# Other users of this dashboard only get the local model. Compared case/accent-insensitively.
ALLOWED_USERS = {name_key("Peter Snoek")}
EFFORT = "high"
MAX_TOKENS = 16000
S_KEY = "ai_claude_api_key"
S_APPROVED = "ai_claude_approved"   # JSON {"date"}: the user confirmed the HU allows this (F13)
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def key(database: str) -> str | None:
    return db.get_setting(database, S_KEY) or None


def short(api_key: str | None) -> str:
    """F13: the key as shown: 'sk-ant-…1234'."""
    if not api_key:
        return ""
    return f"{api_key[:7]}…{api_key[-4:]}" if len(api_key) > 12 else "…"


def approved(database: str) -> str | None:
    """The date on which the user confirmed the HU allows Claude (F13), or None."""
    try:
        value = json.loads(db.get_setting(database, S_APPROVED) or "null")
    except ValueError:
        return None
    return value.get("date") if isinstance(value, dict) else None


def allowed(user_name: str | None) -> bool:
    """F22: whether Claude may be shown to this logged-in Portflow user."""
    return name_key(user_name) in ALLOWED_USERS


def ready(database: str) -> bool:
    return bool(key(database) and approved(database))


def save(database: str, api_key: str) -> None:
    db.set_setting(database, S_KEY, api_key.strip())
    moment = datetime.now(timezone.utc).astimezone()
    db.set_setting(database, S_APPROVED, json.dumps({"date": f"{moment.day}-{moment.month}-{moment.year}"}))


def remove(database: str) -> None:
    conn = db.connect(database)
    try:
        with conn:
            conn.execute("DELETE FROM settings WHERE key IN (?, ?)", (S_KEY, S_APPROVED))
    finally:
        conn.close()


def _client(api_key: str, timeout: float = 600) -> "anthropic.Anthropic":
    return _sdk().Anthropic(api_key=api_key, timeout=timeout, max_retries=2)


def _message(error: Exception) -> str:
    """A Dutch message for an API error (most specific first)."""
    if isinstance(error, _sdk().AuthenticationError):
        return "Anthropic accepteert deze API-sleutel niet. Controleer de sleutel."
    if isinstance(error, _sdk().PermissionDeniedError):
        return "Deze API-sleutel mag dit model niet gebruiken."
    if isinstance(error, _sdk().NotFoundError):
        return f"Het model {MODEL} is niet gevonden bij Anthropic."
    if isinstance(error, _sdk().RateLimitError):
        return "Te veel verzoeken of het tegoed is op. Probeer het later opnieuw of kijk in de Claude Console."
    if isinstance(error, _sdk().BadRequestError):
        return "Anthropic weigerde het verzoek (bijvoorbeeld te groot of geen tegoed)."
    if isinstance(error, _sdk().APIStatusError):
        return "Anthropic heeft een storing. Probeer het later opnieuw."
    if isinstance(error, _sdk().APIConnectionError):   # includes timeouts
        return "Geen verbinding met Anthropic. Controleer je internetverbinding."
    return "Er ging iets mis bij Anthropic."


def check_key(api_key: str) -> None:
    """F13: is the key accepted? Asks for the model's details, which costs nothing. Raises AdviceError."""
    try:
        _client(api_key, timeout=20).models.retrieve(MODEL)
    except _sdk().AnthropicError as error:
        raise AdviceError(_message(error)) from None


def chat(api_key: str, system: str, user: str, schema: dict | None, *, images: list[dict] = (),
         history: list[dict] = (), cancel: threading.Event | None = None, progress=None):
    """F16: a question with a fixed JSON answer; without a schema a free text answer (F21, with
    `history`: earlier user/assistant messages after the first). Streams, so it can be stopped (F4).
    images: [{'data': base64, 'mime': 'image/png'}]. Returns the parsed JSON or the text; raises AdviceError."""
    content = [{"type": "image", "source": {"type": "base64", "media_type": i["mime"], "data": i["data"]}}
               for i in images]
    content.append({"type": "text", "text": user})
    output_config = {"effort": EFFORT}
    if schema is not None:
        output_config["format"] = {"type": "json_schema", "schema": schema}
    try:
        with _client(api_key).beta.messages.stream(
            model=MODEL, max_tokens=MAX_TOKENS, system=system,
            betas=[FALLBACK_BETA], fallbacks="default",          # Anthropic retries a declined request itself
            output_config=output_config,
            messages=[{"role": "user", "content": content}, *history],
        ) as stream:
            written = ""
            for event in stream:
                if cancel is not None and cancel.is_set():
                    raise AdviceError("Gestopt.")
                delta = getattr(event, "delta", None) if getattr(event, "type", "") == "content_block_delta" else None
                written += getattr(delta, "text", None) or ""
                if progress:
                    progress(written)   # spec 040, F34, F35
            message = stream.get_final_message()
    except _sdk().AnthropicError as error:
        raise AdviceError(_message(error)) from None
    if message.stop_reason == "refusal":
        raise AdviceError("Claude wilde dit verzoek niet behandelen.")
    if message.stop_reason == "max_tokens":
        raise AdviceError("Het antwoord van Claude was te lang en is afgebroken. Probeer het opnieuw.")
    text = "".join(b.text for b in message.content if b.type == "text")
    if schema is None:
        return text.strip()
    try:
        return json.loads(text)
    except ValueError:
        raise AdviceError("Claude gaf geen geldig antwoord. Probeer het opnieuw.") from None
