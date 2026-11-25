"""Evaluatie voorbereiden (spec 039): everything about one review request on one page.

Uses what Verversen and the evidence fetch already stored: received_requests (with the student's
note), evaluations (self-evaluations and assessments with their texts), evidence_items and
evidence_comments. No Portflow calls here. Labels are Dutch: they are shown to the user.
"""

import re
import sqlite3
from datetime import date

from . import lef
from .evaluation_panel import _role, _staff
from .evidence import KINDS, _local_day, _nl, safe_html
from .feedback import _requests as feedback_requests
from .requests_to_review import OPEN_STATUSES, open_requests, waiting_text
from .skills import CATEGORY, NAMES, PRODUCT_SKILLS, SKILLS

_SPAN = re.compile(r"<span\b[^>]*>", re.IGNORECASE)
_DATA_ID = re.compile(r'data-id="(\d+)"')


def mentioned_ids(text: str | None) -> set[int]:
    """F8: the ids of the evidence a text mentions ("@name")."""
    ids = set()
    for tag in _SPAN.findall(text or ""):
        if 'data-mention-type="evidence"' in tag:
            match = _DATA_ID.search(tag)
            if match:
                ids.add(int(match.group(1)))
    return ids


def _day(value: str | None) -> date | None:
    try:
        return date.fromisoformat((value or "")[:10])
    except ValueError:
        return None


def _level(value) -> int | None:
    return int(value) if isinstance(value, str) and value.isdigit() else None


def student_of(conn: sqlite3.Connection, request_id: int) -> tuple[sqlite3.Row | None, int | None]:
    """The stored request to the user (or None) and the id of the student in the dashboard (or None)."""
    received = conn.execute("SELECT * FROM received_requests WHERE review_request_id = ?", (request_id,)).fetchone()
    row = conn.execute("SELECT student_id FROM evaluations WHERE review_request_id = ? LIMIT 1", (request_id,)).fetchone()
    if row:
        return received, row["student_id"]
    if received and received["student_portflow_id"] is not None:
        student = conn.execute("SELECT id FROM students WHERE portflow_user_id = ?", (received["student_portflow_id"],)).fetchone()
        return received, student["id"] if student else None
    return received, None


def build(conn: sqlite3.Connection, request_id: int, today: date, start: date, end: date, mention=None) -> dict | None:
    """F1-F13 without the shared parts (progress row, timelines): the request, its skills and per
    skill the self-evaluation, LEF texts, earlier evaluations, evidence and feedback requests.
    mention: (evidence id, label) -> link address, for mentions in texts (F6). None: no such request."""
    received, student_id = student_of(conn, request_id)
    rows = [dict(r) for r in conn.execute("SELECT * FROM evaluations WHERE review_request_id = ? ORDER BY date, id",
                                          (request_id,))]
    if received is None and not rows:
        return None
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone() if student_id else None
    selfs = [r for r in rows if r["kind"] == "self"]
    submitted = _local_day(received["created_at"]) if received and received["created_at"] else None
    submitted = submitted or _day(min((r["date"] for r in selfs or rows if r["date"]), default=""))
    status = (received["status"] if received else None) or next((r["review_request_status"] for r in rows), None)
    note = received["note"] if received else None
    mentioned = mentioned_ids(note)
    for r in selfs:
        mentioned |= mentioned_ids(r["text"])

    request = {
        "id": request_id,
        "title": (received["title"] if received else "") or next((r["review_request_title"] for r in rows
                                                                   if r["review_request_title"]), "") or "Evaluatieverzoek",
        "student": (student["name"] if student else "") or (received["student_name"] if received else "") or "Onbekende student",
        "student_id": student_id,
        "submitted": f"{submitted.day}-{submitted.month}-{submitted.year}" if submitted else "",
        "waiting": waiting_text((today - submitted).days) if submitted else "",
        "to_me": bool(received) and received["status"] in OPEN_STATUSES,
        "open": status not in ("scored", "denied"),
        "note_known": received is not None,                                   # F5: only requests to the user
        "note_fetched": received is not None and note is not None,            # not yet after the update
        "note": safe_html(note, mention) if note and re.sub(r"<[^>]+>|\s", "", note) else "",
    }

    codes = [c for c in SKILLS if any(r["skill"] == c for r in rows)]
    skills = [_skill(conn, student_id, code, rows, request_id, start, end, mentioned, mention) for code in codes] \
        if student_id else []

    # F13: previous / next in Te beoordelen (oldest first)
    queue = [r["id"] for r in open_requests(conn, today)]
    previous = following = None
    if request_id in queue:
        i = queue.index(request_id)
        previous = queue[i - 1] if i > 0 else None
        following = queue[i + 1] if i + 1 < len(queue) else None

    no_skills = None
    if not codes and received is not None:   # spec 041, F10
        from .requests_to_review import NO_SKILLS, no_skills_reason
        no_skills = NO_SKILLS.get(no_skills_reason(conn, received["student_portflow_id"], received["created_at"]))
    return {"request": request, "skills": skills, "codes": codes, "full_assessment": bool(codes) and set(codes) >= set(SKILLS),
            "no_skills": no_skills,
            "previous": previous, "next": following, "queue_position": (queue.index(request_id) + 1, len(queue))
            if request_id in queue else None}


def _skill(conn, student_id: int, code: str, rows: list[dict], request_id: int, start: date, end: date,
           mentioned: set[int], mention) -> dict:
    staff = _staff(conn)
    own = [r for r in rows if r["skill"] == code]
    self_row = next((r for r in own if r["kind"] == "self"), None)
    assessed_here = [r for r in own if r["kind"] == "assessed"]
    earlier = [dict(r) for r in conn.execute(
        "SELECT * FROM evaluations WHERE student_id = ? AND skill = ? AND kind = 'assessed' "
        "AND (review_request_id IS NULL OR review_request_id != ?) ORDER BY date DESC, id DESC",
        (student_id, code, request_id))]
    levels = [lv for lv in (_level(r["level"]) for r in earlier) if lv is not None]
    current = max(levels) if levels else None
    claimed = _level(self_row["level"]) if self_row else None
    last_assessed = _day(earlier[0]["date"]) if earlier else None

    def show(r):
        return {"author": r["assessor"] or "Onbekend", "role": _role(r["assessor"], code, staff), "level": r["level"],
                "date": _nl(_day(r["date"])), "title": r["review_request_title"] or "",
                "text": safe_html(r["text"] or "", mention)}

    evidence, ids = [], []
    for item in conn.execute("SELECT * FROM evidence_items WHERE student_id = ? ORDER BY created_at DESC, evidence_id DESC",
                             (student_id,)):
        if code not in (item["skills"] or "").split(","):
            continue
        created, updated = _local_day(item["created_at"]), _local_day(item["updated_at"])
        if not any(d and start <= d <= end for d in (created, updated)):
            continue
        newest = max(d for d in (created, updated) if d)
        evidence.append({"id": item["evidence_id"], "name": item["name"] or "Bewijsstuk",
                         "kind": KINDS.get(item["kind"], item["kind"] or "onbekend"), "raw_kind": item["kind"] or "",
                         "collections": item["collections"] or "", "created": _nl(created),
                         "updated": _nl(updated) if updated and updated != created else "",
                         "new": bool(last_assessed and newest > last_assessed),     # F8
                         "mentioned": item["evidence_id"] in mentioned, "requests": 0, "replies": 0})
        ids.append(item["evidence_id"])

    by_evidence = {e["id"]: e for e in evidence}
    threads = []
    for r in feedback_requests(conn, student_id, start, end):   # F12
        item = by_evidence.get(r["evidence_id"])
        if item is None:
            continue
        item["requests"] += 1
        item["replies"] += len(r["from_others"])
        threads.append({"id": r["comment_id"], "evidence": item["name"], "author": r["author_name"] or "Onbekend",
                        "date": _nl(r["day"]), "replies": len(r["from_others"]),
                        "roles": sorted({reply["role"] for reply in r["from_others"]})})
    threads.reverse()   # newest first

    return {
        "code": code, "name": NAMES[code], "category": CATEGORY[code],
        "assessor": "gildemeester" if code in PRODUCT_SKILLS else "coach",
        "current": current, "claimed": claimed,
        "self_text": safe_html(self_row["text"] or "", mention) if self_row and self_row["text"] else "",
        "self_date": _nl(_day(self_row["date"])) if self_row else "",
        "assessed_here": [show(r) for r in assessed_here],
        "earlier": [show(r) for r in earlier],
        "last_assessed": _nl(last_assessed) if last_assessed else "",
        "lef_claimed": lef.level_text(code, claimed),
        "lef_current": lef.level_text(code, current) if current != claimed else None,
        "evidence": evidence, "threads": threads, "thread_ids": ",".join(str(t["id"]) for t in threads),
    }
