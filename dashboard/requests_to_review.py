"""Te beoordelen (spec 030): the open review requests sent to the user, oldest first.

The requests are stored by the fetch round (portflow_fetch.Fetcher._save_requests); the skills
of a request come from the stored self-evaluations with the same review_request_id. Labels are
Dutch: they are shown to the user.
"""

import sqlite3
from datetime import date, datetime, timezone

from .portflow_connection import initials
from .skills import SKILLS

OPEN_STATUSES = ("not_started", "in_progress")   # F1


def _local_day(value: str) -> date | None:
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return moment.astimezone().date() if moment.tzinfo else moment.date()


def _moment(value: str | None) -> datetime | None:
    """An ISO timestamp from Portflow or the fetch round, as an aware datetime (None if unknown)."""
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _behind(created_at: str | None, fetched_at: str | None) -> bool:
    """Spec 041, F9, F10: the student was not fetched since this request was sent in."""
    fetched = _moment(fetched_at)
    if fetched is None:
        return True
    created = _moment(created_at)
    return created is not None and created > fetched


def students_behind(conn: sqlite3.Connection) -> list[int]:
    """Spec 041, F9: the students in the dashboard with an open request to the user that was sent in
    after their last fetch, oldest request first."""
    result = []
    for r in conn.execute(
            "SELECT s.id, s.fetched_at, rr.created_at FROM received_requests rr "
            "JOIN students s ON s.portflow_user_id = rr.student_portflow_id AND s.is_demo = 0 "
            "WHERE rr.status IN (?, ?) ORDER BY rr.created_at", OPEN_STATUSES):
        if r["id"] not in result and _behind(r["created_at"], r["fetched_at"]):
            result.append(r["id"])
    return result


# Spec 041, F10: why a request shows no skills.
NO_SKILLS = {
    "not_fetched": ("nog niet opgehaald", "De student is sinds dit verzoek nog niet opgehaald. Klik op Verversen."),
    "no_self": ("geen zelfevaluatie", "De student heeft bij dit verzoek in Portflow geen zelfevaluatie per vaardigheid "
                "ingevuld. Open het verzoek in Portflow om te zien wat er wel in staat."),
}


def no_skills_reason(conn: sqlite3.Connection, student_portflow_id: int | None, created_at: str | None) -> str | None:
    """Spec 041, F10: 'not_fetched', 'no_self', or None when the student is not in the dashboard."""
    row = conn.execute("SELECT fetched_at FROM students WHERE portflow_user_id = ? AND is_demo = 0",
                       (student_portflow_id,)).fetchone() if student_portflow_id is not None else None
    if row is None:
        return None
    return "not_fetched" if _behind(created_at, row["fetched_at"]) else "no_self"


def waiting_text(days: int) -> str:
    """F1: 'vandaag', '1 dag', '5 dagen'."""
    if days <= 0:
        return "vandaag"
    return "1 dag" if days == 1 else f"{days} dagen"


def open_count(conn: sqlite3.Connection) -> int:
    """F6: the number for the menu."""
    return conn.execute("SELECT COUNT(*) FROM received_requests WHERE status IN (?, ?)", OPEN_STATUSES).fetchone()[0]


def open_requests(conn: sqlite3.Connection, today: date) -> list[dict]:
    """F1-F4: one dict per open request, the one waiting longest first."""
    names = {r["portflow_user_id"]: r["name"] for r in conn.execute(
        "SELECT portflow_user_id, name FROM students WHERE portflow_user_id IS NOT NULL")}
    skills: dict[int, set[str]] = {}
    for r in conn.execute("SELECT DISTINCT review_request_id, skill FROM evaluations "
                          "WHERE kind = 'self' AND review_request_id IN "
                          "(SELECT review_request_id FROM received_requests)"):
        skills.setdefault(r["review_request_id"], set()).add(r["skill"])
    result = []
    for r in conn.execute("SELECT * FROM received_requests WHERE status IN (?, ?)", OPEN_STATUSES):
        name = names.get(r["student_portflow_id"]) or r["student_name"] or "Onbekende student"
        found = skills.get(r["review_request_id"], set())
        day = _local_day(r["created_at"])
        result.append({
            "id": r["review_request_id"],
            "student": name,
            "initials": initials(name),
            "followed": r["student_portflow_id"] in names,
            "title": r["title"] or "Evaluatieverzoek",
            "skills": [s for s in SKILLS if s in found],
            # spec 041, F10: why there are no skills ("–" for a student who is not in the dashboard)
            "no_skills": None if found else NO_SKILLS.get(no_skills_reason(conn, r["student_portflow_id"], r["created_at"])),
            "full_assessment": found >= set(SKILLS),          # F4
            "submitted": day,
            "waiting": waiting_text((today - day).days) if day else "",
            "sort": r["created_at"] or "~",
        })
    return sorted(result, key=lambda r: (r["sort"], r["id"]))   # F2: oldest first
