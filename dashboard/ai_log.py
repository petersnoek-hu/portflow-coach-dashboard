"""Spec 042: the log of the AI advice. What the dashboard did to talk to Ollama (or Claude) and why it
did or did not work, kept in the local database (the last 500 lines) and shown in Instellingen.

Lines hold no names, no content of evaluations or evidence, no titles, no token and no key (F6):
callers only pass addresses, model names, numbers and error messages, which are cut short here.
Writing a line never raises (the advice goes on if the log cannot be written).
"""

import logging
import platform
from datetime import datetime, timezone

from . import db

KEEP = 500
MAX_TEXT = 300
TOPICS = ("Ollama", "Downloaden", "Proefvraag", "Advies", "Vervolgvraag", "Instellingen")


def _short(text: str) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT - 1] + "…"


def add(database: str, topic: str, ok: bool, text: str, detail: str = "", *, repeat: bool = False) -> None:
    """Write a line. With `repeat` (the check of Ollama on every page view) a line equal to the newest
    line of that topic only gets a new time and one more in its count."""
    try:
        conn = db.connect(database)
        try:
            now = datetime.now(timezone.utc).isoformat()
            text, detail = _short(text), _short(detail)
            with conn:
                last = conn.execute("SELECT id, ok, text, detail FROM ai_log WHERE topic = ? ORDER BY id DESC LIMIT 1",
                                    (topic,)).fetchone() if repeat else None
                newest = conn.execute("SELECT MAX(id) FROM ai_log").fetchone()[0]
                if last and last["id"] == newest and (bool(last["ok"]), last["text"], last["detail"]) == (ok, text, detail):
                    conn.execute("UPDATE ai_log SET at = ?, times = times + 1 WHERE id = ?", (now, last["id"]))
                else:
                    conn.execute("INSERT INTO ai_log (at, topic, ok, text, detail) VALUES (?, ?, ?, ?, ?)",
                                 (now, topic, int(bool(ok)), text, detail))
                    conn.execute("DELETE FROM ai_log WHERE id <= (SELECT MAX(id) FROM ai_log) - ?", (KEEP,))
        finally:
            conn.close()
    except Exception:   # never let the log break the advice
        logging.getLogger(__name__).exception("could not write the AI log")


def _local(at: str) -> str:
    moment = datetime.fromisoformat(at).astimezone()
    return f"{moment.day}-{moment.month} {moment:%H:%M:%S}"


def recent(conn, limit: int = KEEP) -> list[dict]:
    """F3: the lines, newest first."""
    return [{"time": _local(r["at"]), "topic": r["topic"], "ok": bool(r["ok"]), "text": r["text"],
             "detail": r["detail"], "times": r["times"]}
            for r in conn.execute("SELECT * FROM ai_log ORDER BY id DESC LIMIT ?", (limit,))]


def clear(database: str) -> None:
    conn = db.connect(database)
    try:
        with conn:
            conn.execute("DELETE FROM ai_log")
    finally:
        conn.close()


def as_text(rows: list[dict], version: str, ollama_version: str | None) -> str:
    """F4: the whole log as plain text, for the clipboard."""
    head = [f"Portflow coach dashboard {version}",
            f"Systeem: {platform.system()} {platform.release()} ({platform.machine()})",
            f"Ollama: {ollama_version or 'niet bereikbaar'}", ""]
    lines = [f"{r['time']}  {r['topic']:<12} {'OK ' if r['ok'] else 'FOUT'}  {r['text']}"
             + (f" [{r['detail']}]" if r["detail"] else "") + (f" ({r['times']}×)" if r["times"] > 1 else "")
             for r in rows]
    return "\n".join(head + (lines or ["(nog niets vastgelegd)"]))
