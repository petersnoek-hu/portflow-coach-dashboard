"""The timeline of evaluations on the page Evaluaties (spec 029): per week of the semester
period the achieved and the handed-in, not yet assessed evaluations.

Which evaluations count is decided by progress.py (via overview.student_rows); this module
only puts them in weeks. Labels are Dutch: they are shown to the user.
"""

import math
import sqlite3
from datetime import date, timedelta

from .overview import WHO_DEFAULT, who_options
from .progress import panel_args
from .requests_to_review import OPEN_STATUSES, waiting_text
from .skills import CATEGORY, NAMES, SKILLS

S_WHO = "evaluations_who"   # F2: the choice of Evaluaties, apart from Overzicht
MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
          "augustus", "september", "oktober", "november", "december"]


def long_date(day: date) -> str:
    """'1 september 2026'."""
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _day(value: str) -> date | None:
    try:
        return date.fromisoformat((value or "")[:10])
    except ValueError:
        return None


def week_counts(rows: list[dict], start: date, end: date) -> list[dict]:
    """F1, F3, F3a: one entry per week (Monday to Sunday) from the week of `start` to the week of
    `end`. An evaluation counts in the week it was handed in; one without a date is left out."""
    first = start - timedelta(days=start.weekday())
    weeks = [{"number": i + 1, "monday": first + timedelta(weeks=i), "achieved": 0, "pending": 0}
             for i in range((end - first).days // 7 + 1)]

    def add(value: str, kind: str) -> None:
        day = _day(value)
        if day is not None and start <= day <= end:
            weeks[(day - first).days // 7][kind] += 1

    for row in rows:
        for cell in row["progress"].cells.values():
            for evaluation in cell.evaluations:
                add(evaluation.submitted or evaluation.date, "achieved")
            if cell.pending:   # a full assessment has no pending cells (voortgangsregels.md#openstaand)
                add(cell.pending.date, "pending")
    for week in weeks:
        week["sunday"] = week["monday"] + timedelta(days=6)
        week["total"] = week["achieved"] + week["pending"]
    return weeks


def scale(weeks: list[dict]) -> dict:
    """The vertical axis: a round top and at most about five steps; heights in percent."""
    highest = max((w["total"] for w in weeks), default=0)
    if highest == 0:
        return {"top": 0, "ticks": []}
    raw = highest / 5
    magnitude = 10 ** math.floor(math.log10(raw)) if raw >= 1 else 1
    step = next(m * magnitude for m in (1, 2, 5, 10) if m * magnitude >= raw)
    top = math.ceil(highest / step) * step
    for week in weeks:
        week["achieved_pct"] = round(100 * week["achieved"] / top, 2)
        week["pending_pct"] = round(100 * week["pending"] / top, 2)
    return {"top": top, "ticks": [{"value": v, "pct": round(100 * v / top, 2)} for v in range(0, top + 1, step)]}


# The choice "wie" (F2), remembered apart from Overzicht -----------------------------------------

def saved_who(conn: sqlite3.Connection, user_name: str | None = None) -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (S_WHO,)).fetchone()
    return row[0] if row and row[0] in dict(who_options(conn, user_name)) else WHO_DEFAULT


def save_who(conn: sqlite3.Connection, who: str, user_name: str | None = None) -> str:
    who = who if who in dict(who_options(conn, user_name)) else WHO_DEFAULT
    with conn:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (S_WHO, who))
    return who


# The compact progress table (spec 029, F7-F11) ----------------------------------------------------

def project_blocks(rows: list[dict]) -> list[list[dict]]:
    """F10: the students per project, in the order of the projects on Overzicht, without a project
    last; by name within a block. The template draws a thin line between blocks."""
    blocks: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (0, row["squad_sort"].casefold(), row["squad_id"]) if row["squad_id"] else (1, "", 0)
        blocks.setdefault(key, []).append(row)
    return [sorted(blocks[key], key=lambda r: r["name"].casefold()) for key in sorted(blocks)]


# One student (spec 032) ------------------------------------------------------------------------------

def _nl_date(day: date | None) -> str:
    return f"{day.day}-{day.month}-{day.year}" if day else "datum onbekend"


def student_weeks(row: dict, start: date, end: date) -> list[dict]:
    """F3: the weeks of the period with a block per evaluation: achieved first (in skill order),
    then handed in and not yet assessed. The same rules as week_counts (week of handing in)."""
    first = start - timedelta(days=start.weekday())
    weeks = [{"number": i + 1, "monday": first + timedelta(weeks=i), "achieved": [], "pending": []}
             for i in range((end - first).days // 7 + 1)]

    def week_of(value: str):
        day = _day(value)
        return weeks[(day - first).days // 7] if day is not None and start <= day <= end else None

    cells = row["progress"].cells
    for code in SKILLS:
        for evaluation in cells[code].evaluations:
            week = week_of(evaluation.submitted or evaluation.date)
            if week is not None:
                handed_in, assessed = _day(evaluation.submitted), _day(evaluation.date)
                tip = f"{NAMES[code]}: niveau {evaluation.level}, ingediend {_nl_date(handed_in)}"
                if assessed and assessed != handed_in:
                    tip += f", beoordeeld {_nl_date(assessed)}"
                if evaluation.assessor:
                    tip += f" door {evaluation.assessor}"
                week["achieved"].append({"code": code, "label": f"{code} {evaluation.level}",
                                         "category": CATEGORY[code], "tip": tip,
                                         "panel": panel_args([evaluation])})   # spec 037, F3
        pending = cells[code].pending
        if pending:
            week = week_of(pending.date)
            if week is not None:
                week["pending"].append({"code": code, "label": f"{code} ?", "category": "pending",
                                        "tip": f"{NAMES[code]}: ingediend {_nl_date(_day(pending.date))}, nog niet beoordeeld"
                                               + (f" ({pending.title})" if pending.title else ""),
                                        "panel": panel_args([], pending)})
    for week in weeks:
        week["sunday"] = week["monday"] + timedelta(days=6)
        week["blocks"] = week["achieved"] + week["pending"]
    return weeks


def student_open_requests(conn: sqlite3.Connection, row: dict, today: date) -> list[dict]:
    """F4: the open requests of the student, one per request, oldest first; "aan jou" for the ones
    sent to the user (spec 030)."""
    to_me = {r[0] for r in conn.execute(
        "SELECT review_request_id FROM received_requests WHERE status IN (?, ?)", OPEN_STATUSES)}
    grouped: dict = {}
    progress = row["progress"]
    for code in SKILLS:
        pending = progress.cells[code].pending
        if pending:
            key = pending.request_id if pending.request_id is not None else (pending.title, pending.date)
            item = grouped.setdefault(key, {"request_id": pending.request_id, "title": pending.title,
                                            "date": pending.date, "skills": [], "full_assessment": False})
            item["skills"].append(code)
    for full in progress.full_requests:
        grouped[full.request_id] = {"request_id": full.request_id, "title": full.title, "date": full.date,
                                    "skills": [], "full_assessment": True}
    result = []
    for item in grouped.values():
        day = _day(item["date"])
        result.append(dict(item, title=item["title"] or "Evaluatieverzoek", submitted=day,
                           submitted_text=_nl_date(day) if day else "",
                           waiting=waiting_text((today - day).days) if day else "",
                           to_me=item["request_id"] in to_me))
    return sorted(result, key=lambda r: (r["date"] or "~", r["title"]))


def student_assessed_requests(conn: sqlite3.Connection, student_id: int, start: date, end: date) -> list[dict]:
    """Spec 032, F7: the review requests of the student assessed in the period, newest assessment
    first; per skill the level, who and when. Assessments of an excluded assessor stay hidden
    (voortgangsregels.md#welke-evaluaties-tellen); one that does not count otherwise (no level, or
    the request not scored as a whole) is shown with "telt niet mee"."""
    from .portflow_connection import S_USER_NAME
    from .progress import _counts, normalize_name
    excluded = {r[0] for r in conn.execute("SELECT name_key FROM excluded_assessors")}
    me = normalize_name(next((r[0] for r in conn.execute("SELECT value FROM settings WHERE key = ?", (S_USER_NAME,))), ""))
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM evaluations WHERE student_id = ? AND review_request_id IS NOT NULL ORDER BY date, id", (student_id,))]
    submitted = {}
    for r in rows:
        if r["kind"] == "self" and r["date"]:
            submitted.setdefault(r["review_request_id"], r["date"])
    grouped: dict[int, dict] = {}
    for r in rows:
        if r["kind"] != "assessed" or r["skill"] not in SKILLS or normalize_name(r["assessor"]) in excluded:
            continue
        day = _day(r["date"] or "")
        if day is None or not start <= day <= end:
            continue
        item = grouped.setdefault(r["review_request_id"], {
            "request_id": r["review_request_id"], "title": r["review_request_title"] or "Evaluatieverzoek",
            "skills": {}, "assessed": day})
        item["assessed"] = max(item["assessed"], day)
        item["skills"][r["skill"]] = {
            "code": r["skill"], "level": r["level"] if r["level"] not in (None, "") else None,
            "assessor": r["assessor"] or "Onbekend", "by_me": bool(me) and normalize_name(r["assessor"]) == me,
            "counts": _counts(r, excluded, start, end)}
    result = []
    for item in grouped.values():
        skills = [item["skills"][c] for c in SKILLS if c in item["skills"]]
        sent = _day(submitted.get(item["request_id"]) or "")
        result.append({
            "request_id": item["request_id"], "title": item["title"], "skills": skills,
            "full_assessment": len(skills) == len(SKILLS),
            "assessors": list(dict.fromkeys(s["assessor"] for s in skills)),
            "by_me": any(s["by_me"] for s in skills),
            "assessed": item["assessed"], "assessed_text": _nl_date(item["assessed"]),
            "submitted_text": _nl_date(sent) if sent else ""})
    return sorted(result, key=lambda r: (r["assessed"], r["request_id"]), reverse=True)
