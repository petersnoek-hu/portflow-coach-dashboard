"""Linking students to their shared Portflow portfolio (spec 015).

The shared list comes from `GET /shares/shared-with-me` (spec 004) and is kept in
memory for five minutes, so the edit page opens quickly.
"""

import sqlite3
import time

from . import student_intake
from .progress import name_key

CACHE_SECONDS = 5 * 60
_cache: dict = {"token": None, "at": 0.0, "candidates": None}


class Unauthorized(Exception):
    """Portflow answered 401."""


def shared_students(api, token: str, *, use_cache: bool = True) -> list[dict] | None:
    """Grouped shared Portflow students (name, portflow_user_id, portfolio_ids), or None on an error."""
    now = time.time()
    if use_cache and _cache["token"] == token and now - _cache["at"] < CACHE_SECONDS:
        return _cache["candidates"]
    status, items = api.shared_with_me(token)
    if status == 401:
        raise Unauthorized
    if status != 200:
        return None
    candidates = student_intake.group_shared_students(items or [])
    _cache.update(token=token, at=now, candidates=candidates)
    return candidates


def clear_cache() -> None:
    _cache.update(token=None, at=0.0, candidates=None)


def _set_portfolios(conn: sqlite3.Connection, student_id: int, portfolio_ids: list[int]) -> None:
    conn.executemany("INSERT OR IGNORE INTO student_portfolios (student_id, portfolio_id) VALUES (?, ?)",
                     [(student_id, pid) for pid in portfolio_ids])


def auto_link(conn: sqlite3.Connection, candidates: list[dict]) -> tuple[int, list[str]]:
    """F1, F2: link unlinked students on name; add newly shared portfolios to linked ones.
    Returns (number linked now, names still unlinked)."""
    by_key: dict[str, list[dict]] = {}
    for candidate in candidates:
        by_key.setdefault(name_key(candidate["name"]), []).append(candidate)
    by_id = {c["portflow_user_id"]: c for c in candidates}
    linked, unresolved = 0, []
    with conn:
        used = {r[0] for r in conn.execute("SELECT portflow_user_id FROM students WHERE portflow_user_id IS NOT NULL")}
        for row in conn.execute("SELECT id, portflow_user_id FROM students WHERE portflow_user_id IS NOT NULL").fetchall():
            if row[1] in by_id:
                _set_portfolios(conn, row[0], by_id[row[1]]["portfolio_ids"])
        for student in conn.execute("SELECT id, name FROM students WHERE portflow_user_id IS NULL AND is_demo = 0 "
                                    "ORDER BY name").fetchall():
            matches = [c for c in by_key.get(name_key(student[1]), []) if c["portflow_user_id"] not in used]
            if len(matches) != 1:
                unresolved.append(student[1])
                continue
            match = matches[0]
            conn.execute("UPDATE students SET portflow_user_id = ?, has_access = 1 WHERE id = ?",
                         (match["portflow_user_id"], student[0]))
            _set_portfolios(conn, student[0], match["portfolio_ids"])
            used.add(match["portflow_user_id"])
            linked += 1
    return linked, unresolved


def choices(conn: sqlite3.Connection, candidates: list[dict], student_id: int) -> list[dict]:
    """F5: shared students not linked to another student, by name."""
    taken = {r[0] for r in conn.execute(
        "SELECT portflow_user_id FROM students WHERE portflow_user_id IS NOT NULL AND id != ?", (student_id,))}
    return sorted((c for c in candidates if c["portflow_user_id"] not in taken), key=lambda c: c["name"].casefold())


def set_link(conn: sqlite3.Connection, student_id: int, candidate: dict | None) -> None:
    """F5: link to another Portflow student, or unlink (None). Old evaluations and portfolios go."""
    with conn:
        conn.execute("DELETE FROM evaluations WHERE student_id = ? AND is_demo = 0", (student_id,))
        conn.execute("DELETE FROM student_portfolios WHERE student_id = ?", (student_id,))
        if candidate is None:
            conn.execute("UPDATE students SET portflow_user_id = NULL, fetched_at = NULL WHERE id = ?", (student_id,))
        else:
            conn.execute("UPDATE students SET portflow_user_id = ?, has_access = 1, fetched_at = NULL WHERE id = ?",
                         (candidate["portflow_user_id"], student_id))
            _set_portfolios(conn, student_id, candidate["portfolio_ids"])
