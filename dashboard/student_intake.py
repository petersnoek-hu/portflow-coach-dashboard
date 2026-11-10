"""Logic for adding students (spec 004). Only 'Uit Portflow kiezen' is built so far;
the other three manners from docs/gegevensmodel.md#studenten-toevoegen will be added here later.
"""

import sqlite3

from .portflow_connection import initials


def group_shared_students(raw_items: list[dict]) -> list[dict]:
    """Group `/shares/shared-with-me` items by Portflow student (F6).

    Keeps only items where `inviter.current_role == "student"`. A student can share
    more than one portfolio (docs/gegevensmodel.md#student); those appear as separate
    items with the same `inviter.id` and are combined into one candidate here.
    """
    by_id: dict[int, dict] = {}
    order: list[int] = []
    for item in raw_items:
        inviter = item.get("inviter") or {}
        if inviter.get("current_role") != "student":
            continue
        user_id, name, portfolio_id = inviter.get("id"), inviter.get("name"), item.get("portfolio_id")
        if not isinstance(user_id, int) or not isinstance(name, str) or not name.strip():
            continue
        if user_id not in by_id:
            by_id[user_id] = {"portflow_user_id": user_id, "name": name.strip(), "portfolio_ids": []}
            order.append(user_id)
        if portfolio_id is not None and portfolio_id not in by_id[user_id]["portfolio_ids"]:
            by_id[user_id]["portfolio_ids"].append(portfolio_id)
    candidates = [by_id[user_id] for user_id in order]
    candidates.sort(key=lambda candidate: candidate["name"].casefold())
    for candidate in candidates:
        candidate["initials"] = initials(candidate["name"])
    return candidates


def tracked_portflow_ids(conn: sqlite3.Connection) -> set[int]:
    """Portflow user ids of students that are already followed (F10)."""
    return {
        row[0]
        for row in conn.execute("SELECT portflow_user_id FROM students WHERE portflow_user_id IS NOT NULL")
    }


def normalize_name(name: str) -> str:
    """Case- and whitespace-insensitive comparison key (docs/gegevensmodel.md#koppelen-aan-portflow)."""
    return " ".join(name.split()).casefold()


def unlinked_students_by_name(conn: sqlite3.Connection) -> dict[str, int]:
    """Students without a Portflow link yet, keyed by normalized name (F10): candidates for
    "Mogelijk al gevolgd (zelfde naam)" (added via Excel/plakken, before those manners exist).
    Demo students do not count (spec 004, F10). If more than one student shares a name,
    the one added first (lowest id) is used.
    """
    by_name: dict[str, int] = {}
    rows = conn.execute(
        "SELECT id, name FROM students WHERE portflow_user_id IS NULL AND is_demo = 0 ORDER BY id"
    ).fetchall()
    for row in rows:
        by_name.setdefault(normalize_name(row["name"]), row["id"])
    return by_name


def staff_id_by_name(conn: sqlite3.Connection, name: str | None) -> int | None:
    """Id in the managed staff list for a name (used for the "Ik ben hun coach" checkbox, F11)."""
    if not name:
        return None
    row = conn.execute("SELECT id FROM staff WHERE name = ?", (name,)).fetchone()
    return row[0] if row else None


def add_or_link_students_from_portflow(
    conn: sqlite3.Connection, candidates: list[dict], *, coach_id: int | None = None
) -> tuple[int, int]:
    """Add or link one student per candidate (F10, F11); returns (added, linked).

    A candidate whose name matches an existing student without a Portflow link is
    **linked** to that student (only the Portflow link and portfolios change). All
    other candidates are **added** as a new student: name and Portflow link only,
    with `coach_id` as coach if the "Ik ben hun coach" checkbox was on. Semester,
    squad, profile and guild master stay empty, so a new student falls under
    "Nog in te delen" until they are filled in (docs/gegevensmodel.md#student).
    """
    added = linked = 0
    with conn:
        name_matches = unlinked_students_by_name(conn)
        for candidate in candidates:
            existing_id = name_matches.get(normalize_name(candidate["name"]))
            if existing_id is not None:
                conn.execute(
                    "UPDATE students SET portflow_user_id = ? WHERE id = ?",
                    (candidate["portflow_user_id"], existing_id),
                )
                student_id = existing_id
                linked += 1
                del name_matches[normalize_name(candidate["name"])]  # do not reuse for another candidate
            else:
                cursor = conn.execute(
                    "INSERT INTO students (name, portflow_user_id, coach_id) VALUES (?, ?, ?)",
                    (candidate["name"], candidate["portflow_user_id"], coach_id),
                )
                student_id = cursor.lastrowid
                added += 1
            for portfolio_id in candidate["portfolio_ids"]:
                conn.execute(
                    "INSERT OR IGNORE INTO student_portfolios (student_id, portfolio_id) VALUES (?, ?)",
                    (student_id, portfolio_id),
                )
    return added, linked
