"""Feedbackvragen en reacties (spec 035): the feedback requests of a student on his evidence, the
replies to them, key figures, two rows for the evidence timeline and the side panel.

The comments are fetched together with the evidence (evidence.fetch_for_student)."""

import sqlite3
from datetime import date, timedelta

from .evidence import KINDS, _local_day, plain_text
from .progress import name_key

ROLES = {"medestudent": "medestudent", "coach": "coach", "gildemeester": "gildemeester",
         "zelf": "de student zelf", "overig": "overig"}


def _staff(conn: sqlite3.Connection) -> dict[str, str]:
    roles = {}
    for row in conn.execute("SELECT name, is_coach, is_guild_master FROM staff"):
        roles[name_key(row["name"])] = "gildemeester" if row["is_guild_master"] else ("coach" if row["is_coach"] else "overig")
    return roles


def role_of(comment: dict, own_id: int | None, staff: dict[str, str]) -> str:
    """F3: the role of whoever wrote a comment: the lists Coaches and Gildemeesters first, then Portflow."""
    if own_id is not None and comment["author_id"] == own_id:
        return "zelf"
    if name_key(comment["author_name"]) in staff:
        return staff[name_key(comment["author_name"])]
    portflow_role = (comment["author_role"] or "").casefold()
    if portflow_role == "student":
        return "medestudent"
    if portflow_role in ("coach", "teacher", "assessor"):
        return "coach"
    return "overig"


REQUEST, REMARK = "feedback_request", "comment"   # spec 043: a feedback request, or a remark (opmerking)
LABELS = {REQUEST: "feedbackvraag", REMARK: "opmerking"}
STAFF_ROLES = ("coach", "gildemeester")


def _threads(conn: sqlite3.Connection, student_id: int, kind: str, start: date | None = None,
             end: date | None = None) -> list[dict]:
    """Top-level comments of one kind (feedback requests or, spec 043, remarks), each with its replies
    (oldest first) and roles. With `start` and `end` only the ones written in that period."""
    own = conn.execute("SELECT portflow_user_id FROM students WHERE id = ?", (student_id,)).fetchone()
    own_id = own[0] if own else None
    staff = _staff(conn)
    comments = [dict(r) for r in conn.execute(
        "SELECT * FROM evidence_comments WHERE student_id = ? ORDER BY created_at, comment_id", (student_id,))]
    replies: dict[int, list[dict]] = {}
    for c in comments:
        c["day"] = _local_day(c["created_at"])
        c["role"] = role_of(c, own_id, staff)
        if c["parent_id"] is not None:
            replies.setdefault(c["parent_id"], []).append(c)
    result = []
    for c in comments:
        if c["parent_id"] is not None or c["kind"] != kind:
            continue
        if start is not None and not (c["day"] and start <= c["day"] <= end):
            continue
        c["replies"] = replies.get(c["comment_id"], [])
        c["from_others"] = [r for r in c["replies"] if r["role"] != "zelf"]
        result.append(c)
    return result


def _requests(conn: sqlite3.Connection, student_id: int, start: date, end: date) -> list[dict]:
    """The feedback requests asked in the period, each with its replies (oldest first) and roles."""
    return _threads(conn, student_id, REQUEST, start, end)


def _remarks(conn: sqlite3.Connection, student_id: int, start: date | None = None, end: date | None = None) -> list[dict]:
    """Spec 043: the remarks (opmerkingen) on evidence, with their replies; with a period only those
    written in it (open question 1: the side panel shows all of them)."""
    return _threads(conn, student_id, REMARK, start, end)


def summary(conn: sqlite3.Connection, student_id: int, start: date, end: date) -> dict:
    """F2: the key figures of the requests asked in the period; replies by the student himself do not count."""
    requests = _requests(conn, student_id, start, end)
    answered = [r for r in requests if r["from_others"]]
    replies = [reply for r in requests for reply in r["from_others"]]
    people = {reply["author_id"] or reply["author_name"] for reply in replies}
    waits = [(r["from_others"][0]["day"] - r["day"]).days for r in answered if r["from_others"][0]["day"]]
    staff_remarks = [r for r in _remarks(conn, student_id, start, end) if r["role"] in STAFF_ROLES]   # spec 043, F6
    return {"requests": len(requests), "answered": len(answered), "replies": len(replies), "people": len(people),
            "first_reply_days": round(sum(waits) / len(waits), 1) if waits else None,
            "staff_remarks": len(staff_remarks)}


def rows(conn: sqlite3.Connection, student_id: int, start: date, end: date, skills: list[str] | None = None) -> list[dict]:
    """F3: the rows Feedbackvraag (a mark per day; open when one of them has no reply yet) and
    Reactie (a mark per day, coloured by role), positioned like the evidence dots. With `skills`
    (spec 039, F12): only feedback on evidence of those skills."""
    first = start - timedelta(days=start.weekday())
    span = ((end - first).days // 7 + 1) * 7
    left = lambda day: round(100 * ((day - first).days + 0.5) / span, 2)
    wanted = set(skills) if skills else None
    names, evidence_skills = {}, {}
    for r in conn.execute("SELECT evidence_id, name, skills FROM evidence_items WHERE student_id = ?", (student_id,)):
        names[r["evidence_id"]] = r["name"]
        evidence_skills[r["evidence_id"]] = {s for s in (r["skills"] or "").split(",") if s}
    asked: dict[date, dict] = {}
    answers: dict[date, dict] = {}
    for request in _requests(conn, student_id, start, end):
        if wanted is not None and not (evidence_skills.get(request["evidence_id"], set()) & wanted):
            continue
        mark = asked.setdefault(request["day"], {"ids": [], "open": False, "tips": []})
        mark["ids"].append(request["comment_id"])
        mark["open"] = mark["open"] or not request["from_others"]
        count = len(request["from_others"])
        mark["tips"].append(f"Feedbackvraag bij {names.get(request['evidence_id']) or 'een bewijsstuk'} · "
                            + (f"{count} reactie{'s' if count != 1 else ''}" if count else "nog geen reactie"))
        for reply in request["replies"]:
            if reply["day"] and start <= reply["day"] <= end:
                mark = answers.setdefault(reply["day"], {"ids": [], "roles": set(), "tips": []})
                if request["comment_id"] not in mark["ids"]:
                    mark["ids"].append(request["comment_id"])
                mark["roles"].add(reply["role"])
                mark["tips"].append(f"Reactie van {reply['author_name'] or 'onbekend'} ({ROLES[reply['role']]})")
    # Spec 043, F3: remarks by others than the student, and replies by others under a remark, in the
    # period, in the row Reactie; a click opens the remark in the side panel.
    for remark in _remarks(conn, student_id):
        if wanted is not None and not (evidence_skills.get(remark["evidence_id"], set()) & wanted):
            continue
        evidence = names.get(remark["evidence_id"]) or "een bewijsstuk"
        for message in [remark] + remark["replies"]:
            if message["role"] == "zelf" or not (message["day"] and start <= message["day"] <= end):
                continue
            mark = answers.setdefault(message["day"], {"ids": [], "roles": set(), "tips": []})
            if remark["comment_id"] not in mark["ids"]:
                mark["ids"].append(remark["comment_id"])
            mark["roles"].add(message["role"])
            what = "Opmerking" if message is remark else "Reactie op een opmerking"
            mark["tips"].append(f"{what} van {message['author_name'] or 'onbekend'} ({ROLES[message['role']]}) bij {evidence}")

    def marks(by_day: dict, kind) -> list[dict]:
        return [{"left": left(day), "count": len(m["tips"]), "ids": ",".join(map(str, m["ids"])),
                 "kind": kind(m), "tip": "\n".join(m["tips"])} for day, m in sorted(by_day.items())]

    return [{"code": "Feedbackvraag", "shape": "request",
             "marks": marks(asked, lambda m: "open" if m["open"] else "answered")},
            {"code": "Reactie", "shape": "reply",
             "marks": marks(answers, lambda m: next(iter(m["roles"])) if len(m["roles"]) == 1 else "gemengd")}]


def threads(conn: sqlite3.Connection, student_id: int, request_ids: list[int], start: date, end: date) -> list[dict]:
    """F4: for the side panel: per feedback request or (spec 043) remark the evidence, the message
    and the replies. The ids say which; they come from the page, so no period applies here."""
    wanted = set(request_ids)
    items = {r["evidence_id"]: dict(r) for r in conn.execute(
        "SELECT * FROM evidence_items WHERE student_id = ?", (student_id,))}
    result = []
    for message in _threads(conn, student_id, REQUEST) + _threads(conn, student_id, REMARK):
        if message["comment_id"] not in wanted:
            continue
        item = items.get(message["evidence_id"], {})
        result.append(dict(_thread(message), evidence_id=message["evidence_id"], evidence=item.get("name") or "Bewijsstuk",
                           raw_kind=item.get("kind") or "", kind=KINDS.get(item.get("kind"), item.get("kind") or ""),
                           skills=[s for s in (item.get("skills") or "").split(",") if s]))
    return result


def _thread(message: dict) -> dict:
    """A feedback request or remark with its replies, for the conversation in the side panel."""
    return {"label": LABELS.get(message["kind"], "opmerking"), "is_request": message["kind"] == REQUEST,
            "request": _show(message), "replies": [_show(reply) for reply in message["replies"]]}


def evidence_items(conn: sqlite3.Connection, student_id: int, evidence_ids: list[int], start: date, end: date) -> list[dict]:
    """Spec 037, F3: the evidence of a dot, each with the feedback requests and (spec 043, F2) the
    remarks on it, with their replies: all of them, also from outside the period (open question 1)."""
    requests_on: dict[int, list[dict]] = {}
    remarks_on: dict[int, list[dict]] = {}
    for request in _threads(conn, student_id, REQUEST):
        requests_on.setdefault(request["evidence_id"], []).append(_thread(request))
    for remark in _remarks(conn, student_id):
        remarks_on.setdefault(remark["evidence_id"], []).append(_thread(remark))
    result = []
    for evidence_id in dict.fromkeys(evidence_ids):
        item = conn.execute("SELECT * FROM evidence_items WHERE student_id = ? AND evidence_id = ?",
                            (student_id, evidence_id)).fetchone()
        if item is None:   # spec 039, F6: a mentioned piece of evidence that is not stored: fetched live
            result.append({"evidence_id": evidence_id, "evidence": "Bewijsstuk", "raw_kind": "", "kind": "",
                           "skills": [], "threads": [], "remarks": [], "live": True})
            continue
        result.append({
            "evidence_id": evidence_id, "evidence": item["name"] or "Bewijsstuk", "raw_kind": item["kind"] or "",
            "kind": KINDS.get(item["kind"], item["kind"] or ""),
            "skills": [s for s in (item["skills"] or "").split(",") if s],
            "threads": requests_on.get(evidence_id, []),
            "remarks": remarks_on.get(evidence_id, []),
        })
    return result


def _show(comment: dict) -> dict:
    day = comment["day"]
    return {"author": comment["author_name"] or "Onbekend", "role": ROLES[comment["role"]],
            "date": f"{day.day}-{day.month}-{day.year}" if day else "", "text": plain_text(comment["text"]),
            "version": f"V{comment['version']}" if comment.get("version") else ""}   # spec 043, F1
