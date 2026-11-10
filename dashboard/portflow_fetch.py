"""Fetching evaluations from Portflow and keeping a local copy (spec 005).

A fetch round runs in a background thread, started only with the "Verversen" button
(F5, F6). Pages read `status()`; the token never leaves the connection object.
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable

from . import db, portflow_api, portflow_link
from .skills import skill_for_goal_name

MAX_WORKERS = 8  # architectuur.md#verversen

S_LAST_FETCH = "fetch_last_finished"
S_LAST_FETCH_FAILED = "fetch_last_failed"   # JSON list of student names
S_UNLINKED = "fetch_unlinked"              # JSON list of names not linked to Portflow (spec 015, F4)

MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
          "augustus", "september", "oktober", "november", "december"]

# Fallbacks from the console app (API document §4.5 and §8); real responses use
# item.date and evaluation.reviewer.name (seen 2026-11-09).
DATE_KEYS = ["date", "submitted_at", "evaluated_at", "evaluation_date", "graded_at",
             "reviewed_at", "assessed_at", "created_at", "updated_at"]
ASSESSOR_KEYS = ["reviewer", "user", "author", "creator", "evaluator", "created_by"]


class Unauthorized(Exception):
    """Portflow answered 401: stop the round (F11)."""


# Reading one feedback item ------------------------------------------------------

def resolve_level(evaluation: dict) -> str | None:
    """`evaluation.level` points to `level_set[].id`; "Startniveau" becomes '0'."""
    level_id = evaluation.get("level")
    if level_id in (None, ""):
        return None
    for option in evaluation.get("level_set") or []:
        if str(option.get("id")) == str(level_id):
            label = str(option.get("label", "")).strip()
            return "0" if label.casefold() == "startniveau" else (label or None)
    return None


def resolve_date(item: dict) -> str:
    """ISO date (YYYY-MM-DD) of a feedback item, or '' if none is recognisable."""
    evaluation = item.get("evaluation") or {}
    for source in (item, evaluation):
        for key in DATE_KEYS:
            value = source.get(key)
            if isinstance(value, str) and len(value) >= 10 and value[4] == "-":
                return value[:10]
    return ""


def resolve_assessor(item: dict) -> str | None:
    evaluation = item.get("evaluation") or {}
    for source in (evaluation, item):
        for key in ASSESSOR_KEYS:
            person = source.get(key)
            if isinstance(person, dict) and isinstance(person.get("name"), str) and person["name"].strip():
                return " ".join(person["name"].split())
        for key in ("reviewer_name", "user_name", "author_name", "evaluator_name"):
            if isinstance(source.get(key), str) and source[key].strip():
                return " ".join(source[key].split())
    return None


def parse_feedback_item(item: dict, skill: str, request_statuses: dict[int, str]) -> dict | None:
    """One feedback item -> one row for the evaluations table (F2), or None if not relevant.

    Only evaluations on the skill itself count (`criterion_evaluation`); sub-criteria
    (professional tasks) are skipped. Comments and evidence are not kept.
    """
    if item.get("type") != "criterion_evaluation":
        return None
    evaluation = item.get("evaluation")
    if not isinstance(evaluation, dict):
        return None
    request_id = evaluation.get("review_request_id")
    scored = evaluation.get("review_request_scored")
    status = request_statuses.get(request_id) if request_id is not None else None
    if status is None:
        status = "scored" if scored is True else "not_scored"
    return {
        "skill": skill,
        "kind": "self" if item.get("role") == "self" else "assessed",
        "level": resolve_level(evaluation),
        "date": resolve_date(item),
        "assessor": None if item.get("role") == "self" else resolve_assessor(item),
        "review_request_id": request_id if isinstance(request_id, int) else None,
        "review_request_title": evaluation.get("review_request_title"),
        "review_request_status": status,
    }


# Formatting -----------------------------------------------------------------------

def updated_text(finished: datetime | None, now: datetime) -> str:
    """F8: 'Bijgewerkt om 14:32' today, 'Bijgewerkt op 8 november, 14:32' earlier."""
    if finished is None:
        return "Nog niet opgehaald"
    local, today = finished.astimezone(), now.astimezone()
    time = local.strftime("%H:%M")
    if local.date() == today.date():
        return f"Bijgewerkt om {time}"
    return f"Bijgewerkt op {local.day} {MONTHS[local.month - 1]}, {time}"


# The fetch round ----------------------------------------------------------------------

def _spawn(target: Callable[[], None]) -> None:
    threading.Thread(target=target, daemon=True).start()


class Fetcher:
    def __init__(self, database: str, connection, *, api=portflow_api, spawn=_spawn,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc), retry: dict | None = None):
        self.database = database
        self.connection = connection
        self.api = api
        self.spawn = spawn
        self.now = now
        self.retry = retry or {}
        self.running = False
        self.done = 0
        self.total = 0
        self._lock = threading.Lock()

    # Starting -------------------------------------------------------------

    def start(self) -> bool:
        """F6: start a round for all followed students; False if one is running or not connected."""
        token = self.connection.token
        if not token:
            return False
        with self._lock:
            if self.running:
                return False
            self.running, self.done, self.total = True, 0, 0
        self.spawn(lambda: self._run(token))
        return True

    # Status for the top bar -------------------------------------------------

    def status(self) -> dict:
        last = db.get_setting(self.database, S_LAST_FETCH)
        failed = json.loads(db.get_setting(self.database, S_LAST_FETCH_FAILED) or "[]")
        unlinked = json.loads(db.get_setting(self.database, S_UNLINKED) or "[]")
        if self.running:
            text = f"Ophalen… {self.done} van {self.total} studenten" if self.total else "Ophalen…"
        else:
            text = updated_text(datetime.fromisoformat(last) if last else None, self.now())
        return {
            "running": self.running,
            "text": text,
            "failed": failed,
            "unlinked": unlinked,
            "can_start": bool(self.connection.token) and not self.running,
            "last": last,
        }

    # Work ---------------------------------------------------------------------

    def _students(self) -> list[dict]:
        conn = db.connect(self.database)
        try:
            rows = conn.execute(
                "SELECT s.id, s.name, sp.portfolio_id FROM students s "
                "JOIN student_portfolios sp ON sp.student_id = s.id "
                "WHERE s.is_demo = 0 AND s.portflow_user_id IS NOT NULL ORDER BY s.name, sp.portfolio_id"
            ).fetchall()
        finally:
            conn.close()
        students: dict[int, dict] = {}
        for row in rows:
            students.setdefault(row["id"], {"id": row["id"], "name": row["name"], "portfolios": []})
            students[row["id"]]["portfolios"].append(row["portfolio_id"])
        return list(students.values())

    def _link(self, token: str) -> None:
        try:
            candidates = portflow_link.shared_students(self.api, token, use_cache=False)
        except portflow_link.Unauthorized:
            raise Unauthorized from None
        if candidates is None:
            return  # keep the existing links (F2)
        conn = db.connect(self.database)
        try:
            _, unresolved = portflow_link.auto_link(conn, candidates)
        finally:
            conn.close()
        db.set_setting(self.database, S_UNLINKED, json.dumps(unresolved))

    def _request_statuses(self, token: str) -> dict[int, str]:
        own = db.get_setting(self.database, "portflow_portfolio_id")
        if not own:
            return {}
        status, items = self.api.received_invitations(token, own, **self.retry)
        if status == 401:
            raise Unauthorized
        statuses = {}
        for item in items or []:
            if isinstance(item.get("review_request_id"), int) and isinstance(item.get("status"), str):
                statuses[item["review_request_id"]] = item["status"]
        return statuses

    def _fetch_student(self, token: str, student: dict, statuses: dict[int, str], pool) -> tuple[str, list]:
        """Returns ('ok', rows), ('no_access', []) or ('failed', [])."""
        rows, not_found, failed = [], 0, False
        for portfolio_id in student["portfolios"]:
            status, goal_list = self.api.goals(token, portfolio_id, **self.retry)
            if status == 401:
                raise Unauthorized
            if status == 404:
                not_found += 1
                continue
            if status != 200:
                failed = True
                continue
            skill_goals = [(g["id"], skill_for_goal_name(g.get("name"))) for g in goal_list or []]
            skill_goals = [(goal_id, skill) for goal_id, skill in skill_goals if skill]
            results = pool.map(
                lambda pair: (pair[1], self.api.feedback_items(token, portfolio_id, pair[0], **self.retry)),
                skill_goals,
            )
            for skill, (item_status, items) in results:
                if item_status == 401:
                    raise Unauthorized
                if item_status == 404:
                    continue  # this goal has no feedback items for the user
                if item_status != 200:
                    failed = True
                    continue
                for item in items or []:
                    row = parse_feedback_item(item, skill, statuses)
                    if row:
                        rows.append(row)
        if failed:
            return "failed", []
        if not_found == len(student["portfolios"]):
            return "no_access", []
        return "ok", rows

    def _save(self, student_id: int, outcome: str, rows: list) -> None:
        conn = db.connect(self.database)
        try:
            with conn:
                if outcome == "no_access":
                    conn.execute("UPDATE students SET has_access = 0 WHERE id = ?", (student_id,))
                elif outcome == "ok":
                    conn.execute("DELETE FROM evaluations WHERE student_id = ? AND is_demo = 0", (student_id,))
                    conn.executemany(
                        """INSERT INTO evaluations (student_id, skill, kind, level, date, assessor,
                               review_request_id, review_request_title, review_request_status)
                           VALUES (:student_id, :skill, :kind, :level, :date, :assessor,
                                   :review_request_id, :review_request_title, :review_request_status)""",
                        [dict(row, student_id=student_id) for row in rows],
                    )
                    conn.execute("UPDATE students SET has_access = 1, fetched_at = ? WHERE id = ?",
                                 (self.now().isoformat(), student_id))
        finally:
            conn.close()

    def _run(self, token: str) -> None:
        failed_names: list[str] = []
        completed = False
        try:
            self._link(token)  # spec 015, F2: link on name first, so new links are fetched too
            students = self._students()
            self.total = len(students)
            statuses = self._request_statuses(token)
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
                for student in students:
                    outcome, rows = self._fetch_student(token, student, statuses, pool)
                    if outcome == "failed":
                        failed_names.append(student["name"])  # keeps its old data (F4, F12)
                    else:
                        self._save(student["id"], outcome, rows)
                    self.done += 1
            completed = True
        except Unauthorized:
            self.connection.mark_unauthorized()  # F11: stop, keep everything
        except Exception:
            failed_names.append("(onverwachte fout)")
        finally:
            if completed:
                db.set_setting(self.database, S_LAST_FETCH, self.now().isoformat())
                db.set_setting(self.database, S_LAST_FETCH_FAILED, json.dumps(failed_names))
            with self._lock:
                self.running = False
