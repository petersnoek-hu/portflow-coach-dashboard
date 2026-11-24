"""Fetching evaluations from Portflow and keeping a local copy (spec 005).

A fetch round runs in a background thread, started with the "Verversen" button (F5, F6;
Shift+click for a full round, spec 042),
or by itself once after the very first connection (spec 019, F2). Every round adds the
students who shared their portfolio and are not in the dashboard yet (spec 019, F1, F3).
Pages read `status()`; the token never leaves the connection object.
"""

import hashlib
import json
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable

from . import db, portflow_api, portflow_link, staff, student_intake
from .progress import name_key
from .skills import skill_for_goal_name

MAX_WORKERS = 8  # architectuur.md#verversen

S_LAST_FETCH = "fetch_last_finished"
S_REQUESTS_FETCHED = "requests_last_fetched"   # spec 030, F5
S_LAST_FETCH_FAILED = "fetch_last_failed"   # JSON list of student names
S_LAST_CHANGED = "fetch_last_changed"      # spec 042, F4: students fetched fully ('' after Shift+click)

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
    (professional tasks) are skipped. The comment is kept since spec 037 (F1); evidence is not.
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
        "text": evaluation.get("comment") if isinstance(evaluation.get("comment"), str) else None,
    }


# Skipping unchanged students (spec 042) -----------------------------------------------

def reviews_signature(reviews: list[dict] | None) -> str | None:
    """Fingerprint of a portfolio's review list: the review ids with their `updated_at`.
    A review that is added, changed or removed changes it. None if the list is unusable (F2)."""
    if reviews is None:
        return None
    pairs = []
    for review in reviews:
        if not isinstance(review, dict) or not isinstance(review.get("id"), int):
            return None
        pairs.append([review["id"], str(review.get("updated_at") or "")])
    return hashlib.sha256(json.dumps(sorted(pairs)).encode()).hexdigest()


def is_unchanged(student: dict, signatures: dict[int, str | None]) -> bool:
    """F1, F2: skip a student only if it was fetched before and every portfolio's review list
    is known and equal to the one at its last full fetch."""
    if not student.get("fetched_at"):
        return False
    stored = student.get("signatures") or {}
    return all(signatures.get(pid) is not None and signatures.get(pid) == stored.get(pid)
               for pid in student["portfolios"])


# Formatting -----------------------------------------------------------------------

def updated_text(finished: datetime | None, now: datetime) -> str:
    """F8: 'Bijgewerkt om 14:32' today, 'Bijgewerkt op 8 november, 14:32' earlier (spec 041, F8:
    without the number of students)."""
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
        self.round = ""                  # spec 039: which round, so a page reloads once per round
        self.fetched: set[int] = set()   # spec 039: the students done in this round
        self.skipped = 0                 # spec 042: students left alone in this round (unchanged)
        self.full = False                # spec 042, F3: Shift+click round
        self._lock = threading.Lock()

    # Starting -------------------------------------------------------------

    def start(self, student_ids: list[int] | None = None, *, screen: bool = False, full: bool = False) -> bool:
        """F6: start a round; False if one is running or not connected.
        Spec 041: with `screen` (a page that shows students) only `student_ids`, the students on
        the screen, are fetched (plus students added in this round). Without it (a page without
        students) every student that is not hidden, `student_ids` first (spec 019, F14).
        Spec 042: unchanged students are skipped unless `full` (Shift+click)."""
        token = self.connection.token
        if not token:
            return False
        with self._lock:
            if self.running:
                return False
            self.running, self.done, self.total = True, 0, 0
            self.round, self.fetched, self.skipped, self.full = uuid.uuid4().hex, set(), 0, full
        self.spawn(lambda: self._run(token, student_ids, screen, full))
        return True

    def start_first(self) -> bool:
        """Spec 019, F2: after the very first connection the first round starts by itself."""
        if db.get_setting(self.database, S_LAST_FETCH):
            return False
        return self.start()

    # Status for the top bar -------------------------------------------------

    def status(self) -> dict:
        last = db.get_setting(self.database, S_LAST_FETCH)
        failed = json.loads(db.get_setting(self.database, S_LAST_FETCH_FAILED) or "[]")
        if self.running:
            students = f"student{'' if self.total == 1 else 'en'}"
            text = (f"Ophalen… {self.done} van {self.total} {students}" if self.full
                    else f"Controleren… {self.done} van {self.total}") if self.total else "Ophalen…"   # spec 042, F4
        else:
            text = updated_text(datetime.fromisoformat(last) if last else None, self.now())
            changed = db.get_setting(self.database, S_LAST_CHANGED)
            if last and changed:
                text += " · niets nieuw" if changed == "0" else f" · {changed} nieuw"
        return {
            "running": self.running,
            "text": text,
            "failed": failed,
            "can_start": bool(self.connection.token) and not self.running,
            "last": last,
            "round": self.round,
            "fetched": sorted(self.fetched),
        }

    # Work ---------------------------------------------------------------------

    def _students(self, student_ids: list[int] | None = None) -> list[dict]:
        conn = db.connect(self.database)
        try:
            rows = conn.execute(
                "SELECT s.id, s.name, s.is_hidden, s.fetched_at, sp.portfolio_id, sp.reviews_signature FROM students s "
                "JOIN student_portfolios sp ON sp.student_id = s.id "
                "WHERE s.is_demo = 0 AND s.portflow_user_id IS NOT NULL ORDER BY s.name, sp.portfolio_id"
            ).fetchall()
        finally:
            conn.close()
        wanted = set(student_ids) if student_ids is not None else None
        students: dict[int, dict] = {}
        for row in rows:
            if (row["id"] not in wanted) if wanted is not None else row["is_hidden"]:
                continue   # spec 019, F14
            students.setdefault(row["id"], {"id": row["id"], "name": row["name"], "fetched_at": row["fetched_at"],
                                            "portfolios": [], "signatures": {}})
            students[row["id"]]["portfolios"].append(row["portfolio_id"])
            students[row["id"]]["signatures"][row["portfolio_id"]] = row["reviews_signature"]
        return list(students.values())

    def _student_ids(self) -> set[int]:
        conn = db.connect(self.database)
        try:
            return {row[0] for row in conn.execute("SELECT id FROM students")}
        finally:
            conn.close()

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
            # Spec 019, F1, F3: every shared student who is not in the dashboard yet is added
            # (a student with the same name and no link is linked instead, spec 004, F10).
            # A name that is still unresolved (spec 015, F4: more than one shared student with
            # that name) is not added; the user links it at Student bewerken.
            tracked = student_intake.tracked_portflow_ids(conn)
            waiting = {name_key(n) for n in unresolved}
            new = [c for c in candidates if c["portflow_user_id"] not in tracked and name_key(c["name"]) not in waiting]
            if new:
                student_intake.add_or_link_students_from_portflow(conn, new)
        finally:
            conn.close()

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
        if status == 200 and items is not None:
            self._save_requests(items)   # spec 030: a failed call keeps the previous list
        return statuses

    def _save_requests(self, items: list[dict]) -> None:
        """Spec 030: the review requests to the user, without the due date; since spec 039 with the
        student's note (HTML, shown safely on the evaluation page)."""
        rows = []
        for item in items:
            rid, status = item.get("review_request_id"), item.get("status")
            if not isinstance(rid, int) or not isinstance(status, str):
                continue
            requester = item.get("requester") if isinstance(item.get("requester"), dict) else {}
            rows.append({
                "review_request_id": rid,
                "title": str(item.get("review_request_title") or ""),
                "student_name": str(requester.get("name") or ""),
                "student_portflow_id": requester.get("id") if isinstance(requester.get("id"), int) else None,
                "portfolio_id": item.get("portfolio_id") if isinstance(item.get("portfolio_id"), int) else None,
                "status": status,
                "created_at": str(item.get("created_at") or ""),
                # "" when Portflow has no note (null): fetched, but nothing written; NULL = not fetched yet
                "note": item.get("review_request_note") if isinstance(item.get("review_request_note"), str) else "",
            })
        conn = db.connect(self.database)
        try:
            with conn:
                conn.execute("DELETE FROM received_requests")
                conn.executemany(
                    "INSERT OR REPLACE INTO received_requests (review_request_id, title, student_name, "
                    "student_portflow_id, portfolio_id, status, created_at, note) VALUES (:review_request_id, :title, "
                    ":student_name, :student_portflow_id, :portfolio_id, :status, :created_at, :note)", rows)
        finally:
            conn.close()
        db.set_setting(self.database, S_REQUESTS_FETCHED, self.now().isoformat())

    def _all_signatures(self, token: str, students: list[dict], pool) -> dict[int, dict[int, str | None]]:
        """Spec 042: the fingerprint of every portfolio's review list (None after an error, F2), for
        all students at once and in parallel, so unchanged students can be skipped right away."""
        def one(pair):
            student_id, portfolio_id = pair
            status, reviews = self.api.reviews(token, portfolio_id, **self.retry)
            if status == 401:
                raise Unauthorized
            return student_id, portfolio_id, reviews_signature(reviews) if status == 200 else None
        pairs = [(s["id"], pid) for s in students for pid in s["portfolios"]]
        result: dict[int, dict[int, str | None]] = {s["id"]: {} for s in students}
        for student_id, portfolio_id, signature in pool.map(one, pairs):
            result[student_id][portfolio_id] = signature
        return result

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

    def _save(self, student_id: int, outcome: str, rows: list,
              signatures: dict[int, str | None] | None = None) -> None:
        conn = db.connect(self.database)
        try:
            with conn:
                # Spec 042: the fingerprint belongs to this fetch; without a full fetch it is cleared,
                # so the next round fetches the student fully again.
                for portfolio_id, signature in (signatures or {}).items():
                    conn.execute("UPDATE student_portfolios SET reviews_signature = ? WHERE student_id = ? "
                                 "AND portfolio_id = ?", (signature if outcome == "ok" else None, student_id, portfolio_id))
                if outcome == "no_access":
                    conn.execute("UPDATE students SET has_access = 0 WHERE id = ?", (student_id,))
                elif outcome == "ok":
                    conn.execute("DELETE FROM evaluations WHERE student_id = ? AND is_demo = 0", (student_id,))
                    conn.executemany(
                        """INSERT INTO evaluations (student_id, skill, kind, level, date, assessor,
                               review_request_id, review_request_title, review_request_status, text)
                           VALUES (:student_id, :skill, :kind, :level, :date, :assessor,
                                   :review_request_id, :review_request_title, :review_request_status, :text)""",
                        [dict({"text": None}, **row, student_id=student_id) for row in rows],
                    )
                    conn.execute("UPDATE students SET has_access = 1, fetched_at = ? WHERE id = ?",
                                 (self.now().isoformat(), student_id))
        finally:
            conn.close()

    def _update_statuses(self, student_ids: list[int], statuses: dict[int, str]) -> None:
        """Spec 042, F5: skipped students still get the current status of requests to the user
        (a denied request does not change the review list). One statement for all of them that
        only touches rows whose status changed: one UPDATE per request and student took 25 s."""
        if not statuses or not student_ids:
            return
        conn = db.connect(self.database)
        try:
            with conn:
                conn.execute("CREATE TEMP TABLE IF NOT EXISTS new_status (rid INTEGER PRIMARY KEY, status TEXT)")
                conn.execute("CREATE TEMP TABLE IF NOT EXISTS skipped (id INTEGER PRIMARY KEY)")
                conn.executemany("INSERT OR REPLACE INTO new_status VALUES (?, ?)", statuses.items())
                conn.executemany("INSERT OR REPLACE INTO skipped VALUES (?)", [(i,) for i in student_ids])
                conn.execute(
                    "UPDATE evaluations SET review_request_status = new_status.status FROM new_status "
                    "WHERE evaluations.review_request_id = new_status.rid AND evaluations.is_demo = 0 "
                    "AND evaluations.student_id IN (SELECT id FROM skipped) "
                    "AND evaluations.review_request_status IS NOT new_status.status")
        finally:
            conn.close()

    def _add_assessors(self) -> None:
        """Spec 019, F11: assessors found in the evaluations join the list of coaches and guild masters."""
        conn = db.connect(self.database)
        try:
            staff.add_found_assessors(conn, getattr(self.connection, "user_name", None))
        finally:
            conn.close()

    def _run(self, token: str, student_ids: list[int] | None = None, screen: bool = False,
             full: bool = False) -> None:
        failed_names: list[str] = []
        completed = False
        first = not db.get_setting(self.database, S_LAST_FETCH)
        try:
            before = self._student_ids()
            self._link(token)  # spec 015, F2: link on name first, so new links are fetched too
            added = sorted(self._student_ids() - before)
            if screen and not first:
                # Spec 041, F1-F3, F5: only the students on the screen, then the ones added in this round.
                order = list(dict.fromkeys(list(student_ids or []) + added))
            else:
                # Spec 019, F2, F14, spec 041, F4, F6: every student that is not hidden (the first
                # round: everyone), the students sent along first, then the ones added in this round.
                rest = [s["id"] for s in self._students(None)]
                first_ids = [] if first else list(student_ids or [])
                order = list(dict.fromkeys(first_ids + added + rest))
            by_id = {s["id"]: s for s in self._students(order)}
            students = [by_id[i] for i in order if i in by_id]
            self.total = len(students)
            statuses = self._request_statuses(token)
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
                # Spec 042: first every review list (in parallel); only a changed student is
                # fetched fully, everyone with Shift+click (F3).
                all_signatures = self._all_signatures(token, students, pool)
                skipped_ids: list[int] = []
                for student in students:
                    signatures = all_signatures[student["id"]]
                    if not full and is_unchanged(student, signatures):
                        skipped_ids.append(student["id"])   # statuses updated after the loop (F5)
                        self.skipped += 1
                    else:
                        outcome, rows = self._fetch_student(token, student, statuses, pool)
                        if outcome == "failed":
                            failed_names.append(student["name"])  # keeps its old data (F4, F12)
                        else:
                            self._save(student["id"], outcome, rows, signatures)
                    self.fetched.add(student["id"])
                    self.done += 1
            self._update_statuses(skipped_ids, statuses)
            self._add_assessors()
            completed = True
        except Unauthorized:
            self.connection.mark_unauthorized()  # F11: stop, keep everything
        except Exception:
            failed_names.append("(onverwachte fout)")
        finally:
            if completed:
                db.set_setting(self.database, S_LAST_FETCH, self.now().isoformat())
                changed = self.done - self.skipped - len(failed_names)
                db.set_setting(self.database, S_LAST_CHANGED, "" if full else str(changed))
                db.set_setting(self.database, S_LAST_FETCH_FAILED, json.dumps(failed_names))
            with self._lock:
                self.running = False
