"""Pages of the dashboard (spec 002 shell; specs 001, 004, 006 and 007)."""

import os
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

from urllib.parse import urlencode

from flask import Blueprint, abort, current_app, redirect, render_template, request, send_file, url_for

from . import (choices, columns as column_data, demo, guilds, overview as overview_data, portflow_link, projects, reset,
               requests_to_review, semesters as semester_data, staff, student_edit, student_intake, summary, timeline)
from . import ai_routes, db, evidence, evidence_files, feedback, hide_names, paths
from . import evaluation_panel as evaluation_panel_data
from . import evaluation_page as evaluation_page_data
from .db import get_db
from .portflow_fetch import S_REQUESTS_FETCHED, updated_text
from .portflow_connection import initials
from .skills import CATEGORY, NAMES as SKILL_NAMES, SKILLS
from .version import VERSION

bp = Blueprint("pages", __name__)

# Sidebar menu and page headers (spec 002, F5 and F8). Text is Dutch: it is shown to the user.
PAGES = [
    {"endpoint": "overview", "path": "/", "label": "Overzicht", "icon": "home",
     "title": "Overzicht",
     "placeholder": None},
    {"endpoint": "students", "path": "/studenten", "label": "Studenten", "icon": "users",
     "title": "Studenten",
     "placeholder": None,
     "show_add_student": True},
    {"endpoint": "evaluations", "path": "/evaluaties", "label": "Evaluaties", "icon": "clipboard",
     "title": "Evaluaties",
     "placeholder": None},
    {"endpoint": "squads", "path": "/projecten", "label": "Projecten", "icon": "folder",
     "title": "Projecten",
     "placeholder": None},
    {"endpoint": "coaches", "path": "/coaches", "label": "Coaches", "icon": "coach",
     "title": "Coaches",
     "placeholder": None},
    {"endpoint": "guild_masters", "path": "/gildemeesters", "label": "Gildemeesters", "icon": "guild",
     "title": "Gildemeesters",
     "placeholder": None},
    {"endpoint": "guilds", "path": "/gildes", "label": "Gildes", "icon": "flag",
     "title": "Gildes",
     "placeholder": None},
    {"endpoint": "columns", "path": "/kolommen", "label": "Kolommen", "icon": "columns",
     "title": "Kolommen",
     "placeholder": None},
    {"endpoint": "choice_lists", "path": "/keuzelijsten", "label": "Keuzelijsten", "icon": "list",
     "title": "Keuzelijsten",
     "placeholder": None},
    {"endpoint": "semesters", "path": "/semesters", "label": "Semesters", "icon": "calendar",
     "title": "Semesters",
     "placeholder": None},
    {"endpoint": "settings", "path": "/instellingen", "label": "Instellingen", "icon": "sliders",
     "title": "Instellingen",
     "placeholder": None},
]
# Spec 002, F17: the management pages sit in one collapsible group "Beheer", in this order.
MENU_ORDER = ["overview", "evaluations",
              "students", "semesters", "guilds", "guild_masters", "coaches", "squads", "columns",
              "choice_lists", "settings"]   # spec 018: no Beroepsrollen any more
MANAGEMENT = {"students", "semesters", "guilds", "guild_masters", "coaches", "squads", "columns", "choice_lists"}
PAGES.sort(key=lambda page: MENU_ORDER.index(page["endpoint"]))
for _page in PAGES:
    _page["group"] = "beheer" if _page["endpoint"] in MANAGEMENT else None
PAGES_BY_ENDPOINT = {page["endpoint"]: page for page in PAGES}

@bp.app_template_filter("initials")
def initials_filter(name: str | None) -> str:
    return initials(name)


@bp.app_template_filter("nl_date")
def nl_date(value: str | None) -> str:
    """'2026-10-27' -> '27-10-2026'; an unknown date shows as 'datum onbekend'."""
    if not value:
        return "datum onbekend"
    try:
        return date.fromisoformat(value[:10]).strftime("%d-%m-%Y")
    except ValueError:
        return value


@bp.app_context_processor
def shell_context():
    """Values every page needs for the sidebar, top bar and demo banner."""
    return {
        "pages": PAGES,
        "demo_active": demo.has_demo_data(get_db()),
        "portflow": current_app.extensions["portflow"].status(),
        "fetch": current_app.extensions["fetcher"].status(),
        "portflow_open": request.args.get("portflow") == "open",
        "skills": SKILLS,
        "skill_names": SKILL_NAMES,
        "skill_category": CATEGORY,
        "to_review_count": requests_to_review.open_count(get_db()),   # spec 030, F6
        "update_available": current_app.extensions["updater"].available(),   # spec 020, U2
        "can_update": current_app.extensions["updater"].can_update(),        # spec 020, U5
        "app_version": VERSION,                                              # spec 020, R1
        "beta": current_app.extensions["updater"].beta(),                    # spec 020, B7
        "hide_names": hide_names.is_on(),                                    # spec 033
    }


def render_page(endpoint: str, **context):
    page = dict(PAGES_BY_ENDPOINT[endpoint])
    template = {"settings": "settings.html", "overview": "overview.html",
                "columns": "columns.html", "choice_lists": "choice_lists.html",
                "students": "students.html",
                "semesters": "semesters.html",
                "squads": "projects.html", "evaluations": "evaluations.html"}.get(endpoint, "page.html")
    return render_template(template, page=page, active=endpoint, **context)


def _add_students_page(title: str) -> dict:
    """A page dict for the 'Studenten toevoegen' flow (spec 004): not in PAGES, so it
    does not get its own sidebar item, but keeps the look of the other pages."""
    return {"title": title, "label": title}


def _table_context() -> dict:
    """The student table (spec 001) with the filters from the query string (F13-F18)."""
    conn = get_db()
    user = current_app.extensions["portflow"].user_name
    all_rows = overview_data.student_rows(conn, date.today())
    default_grouping = overview_data.default_grouping(conn)   # spec 019, F8
    # Spec 023: filters in the address are a choice (the form always sends "f") and are
    # remembered per page; without them the remembered choices apply.
    page = request.endpoint.split(".")[-1]
    keys = overview_data.filter_keys(conn)   # spec 024, G2: plus one per choice column
    if "f" in request.args or any(key in request.args for key in keys):
        chosen = {key: request.args.get(key, "") for key in keys}
        overview_data.save_filters(conn, page, chosen, default_grouping)
    else:
        chosen = overview_data.saved_filters(conn, page)
    args = overview_data.valid_filters(conn, chosen, default_grouping, user, page)
    grouping = args.pop("groep")
    filtered = any(v for k, v in args.items() if k != "wie") \
        or args["wie"] != overview_data.WHO_DEFAULT or grouping != default_grouping   # F4
    rows = overview_data.apply_filters(all_rows, args, user)
    shown = rows
    mine = staff.user_guild_ids(conn, user)
    for row in shown:   # spec 021: the "make me coach/guild master" buttons (F1-F3)
        row["can_make_me_coach"] = bool(user) and not row["coach_full"]
        row["can_make_me_guild_master"] = bool(user) and staff.guild_master_targets(
            row["guild_ids"], bool(row["guild_masters"]), mine) is not None
    visible = overview_data.visible_columns(conn)
    custom = [c for c in overview_data.custom_columns(conn)]
    return {
        "table": {
            "groups": overview_data.group_rows(shown, grouping, overview_data.column_items(conn)),
            "total": len(all_rows),
            "matching": len(rows),
            "shown": len(shown),
            "args": args,
            "grouping": grouping,
            "default_grouping": default_grouping,
            "filtered": filtered,
            "compact": overview_data.filters_compact(conn, page),   # spec 028
            "active_filters": overview_data.active_filter_count(args, grouping, default_grouping),
            "can_hide": True,   # spec 019, F4-F6: the eye icon with every choice of who (2026-11-19)
            "all_hidden": args["wie"] == "zichtbaar" and bool(all_rows) and all(r["hidden"] for r in all_rows),
            "who_options": overview_data.who_options(conn, user, page),
            "grouping_options": overview_data.grouping_options(conn),
            "options": overview_data.filter_options(conn),
            "extra_columns": [(key, label) for key, label in overview_data.EXTRA_COLUMNS if key in visible],
            "all_extra_columns": overview_data.EXTRA_COLUMNS,
            "name_columns": overview_data.NAME_COLUMNS,
            "custom_columns": [c for c in custom if f"custom:{c['id']}" in visible],
            # Spec 024, G1: the items of every choice column, for the list in the cell.
            "column_choices": {c["id"]: choices.column_items(conn, c["id"]) for c in custom if c["type"] == "choice"},
            "all_custom_columns": custom,
            "visible": visible,
            "colours_off": overview_data.colours_off(conn),
            "list_columns": overview_data.list_columns(conn),
            "list_hidden": overview_data.list_hidden(conn),
            # Spec 024, G1: the custom columns in the Studentenlijst (a hidden one is left out).
            "list_custom": [c for c in custom if f"custom:{c['id']}" not in overview_data.list_hidden(conn)],
            "list_custom_hidden": sum(1 for c in custom if f"custom:{c['id']}" in overview_data.list_hidden(conn)),
            "query": request.query_string.decode(),
            "error": request.args.get("fout", ""),
            # Spec 021: "make me coach/guild master" needs the user's name (F3).
        },
    }


@bp.get("/")
def overview():
    added = request.args.get("toegevoegd", "")
    linked = request.args.get("gekoppeld", "")
    context = _table_context()  # spec 001, F1: the full progress table
    return render_page(
        "overview",
        message=request.args.get("melding", ""),
        student_count=context["table"]["total"],
        added=int(added) if added.isdigit() else 0,
        linked=int(linked) if linked.isdigit() else 0,
        **context,
    )


@bp.get("/studenten")
def students():
    context = _table_context()
    context["table"]["choices"] = student_edit.inline_options(get_db())   # spec 022
    return render_page("students", student_count=context["table"]["total"],
                       management=summary.students(get_db()) if context["table"]["total"] else None,   # spec 027
                       message=request.args.get("melding", ""), **context)


def _back_to_table():
    """Back to the page with the table, keeping its filters (only local paths)."""
    target = request.form.get("next", "")
    if not target.startswith("/") or target.startswith("//"):
        target = url_for("pages.students")
    return target


@bp.post("/studenten/kolommen")
def save_columns():
    """F3: the visible extra and custom columns are kept."""
    overview_data.save_visible_columns(get_db(), request.form.getlist("kolom"))
    return redirect(_back_to_table())


@bp.post("/filters/<page>")
def fold_filters(page: str):
    """Spec 028, F1, F5: fold the filters away or show them; the state is kept per page."""
    if page not in overview_data.COMPACT_PAGES:
        abort(404)
    overview_data.save_filters_compact(get_db(), page, request.form.get("stand") == "compact")
    return _done_or_back()


@bp.post("/studenten/lijstkolommen")
def save_list_columns():
    """Spec 010, F5: the visible columns of the student list; the choice is kept."""
    overview_data.save_list_visible(get_db(), request.form.getlist("kolom"))
    return redirect(_back_to_table())


@bp.post("/studenten/kleuren")
def save_colours():
    """F23: which legend colours are shown; the choice is kept."""
    overview_data.save_colours_on(get_db(), request.form.getlist("kleur"))
    return redirect(_back_to_table())


def _done_or_back(error: str | None = None):
    """For app.js (fetch): 204, or 400 with the message. Without JavaScript: back to the table."""
    if request.headers.get("X-Requested-With") == "fetch":
        return (error, 400) if error else ("", 204)
    target = _back_to_table()
    if error:
        target += ("&" if "?" in target else "?") + urlencode({"fout": error})
    return redirect(target)


def _semester_saved(student_id: int, save):
    """Spec 025, F2: when choosing a semester filled the invulling, app.js reloads the page (205)."""
    track = lambda: (get_db().execute("SELECT track_id FROM students WHERE id = ?", (student_id,)).fetchone() or [None])[0]
    before = track()
    error = save()
    if not error and request.headers.get("X-Requested-With") == "fetch" and track() != before:
        return "", 205
    return _done_or_back(error)


@bp.post("/studenten/<int:student_id>/verbergen")
def hide_student(student_id: int):
    """Spec 019, F4: hidden in the overview, not removed."""
    if not overview_data.set_hidden(get_db(), student_id, True):
        abort(404)
    return _done_or_back()


@bp.post("/studenten/<int:student_id>/tonen")
def show_student(student_id: int):
    """Spec 019, F5."""
    if not overview_data.set_hidden(get_db(), student_id, False):
        abort(404)
    return _done_or_back()


@bp.post("/studenten/<int:student_id>/veld/<field>")
def save_student_field(student_id: int, field: str):
    """Spec 022, F1, F4: one list in the student list saves right away."""
    save = lambda: student_edit.save_inline(get_db(), student_id, field, request.form.get("waarde", ""))
    return _semester_saved(student_id, save) if field == "semester" else _done_or_back(save())


@bp.post("/studenten/<int:student_id>/gildemeester/<int:guild_id>")
def save_student_guild_master(student_id: int, guild_id: int):
    """Spec 022, F5."""
    return _done_or_back(student_edit.save_inline_guild_master(get_db(), student_id, guild_id,
                                                               request.form.get("waarde", "")))


@bp.post("/studenten/<int:student_id>/mij-als-coach")
def make_me_coach(student_id: int):
    """Spec 021, F1."""
    user = current_app.extensions["portflow"].user_name
    return _done_or_back(staff.make_user_coach(get_db(), student_id, user))


@bp.post("/studenten/<int:student_id>/mij-als-gildemeester")
def make_me_guild_master(student_id: int):
    """Spec 021, F2."""
    user = current_app.extensions["portflow"].user_name
    return _done_or_back(staff.make_user_guild_master(get_db(), student_id, user))


@bp.post("/studenten/<int:student_id>/kolom/<int:column_id>")
def save_custom_value(student_id: int, column_id: int):
    """F8: a value in a custom column."""
    error = overview_data.save_custom_value(get_db(), student_id, column_id, request.form.get("waarde", ""))
    target = _back_to_table()
    if error:
        target += ("&" if "?" in target else "?") + urlencode({"fout": error})
    return redirect(target)


@bp.get("/evaluaties")
def evaluations():
    """Spec 029: the timeline of evaluations for the chosen students."""
    conn = get_db()
    me = current_app.extensions["portflow"].user_name
    who = timeline.save_who(conn, request.args["wie"], me) if "wie" in request.args else timeline.saved_who(conn, me)
    start, end, period_saved = overview_data.semester_period(conn, date.today())
    rows = overview_data.apply_filters(overview_data.student_rows(conn, date.today()), {"wie": who},
                                       current_app.extensions["portflow"].user_name)
    weeks = timeline.week_counts(rows, start, end)
    return render_page("evaluations", who=who, who_options=overview_data.who_options(conn, me), weeks=weeks,
                       scale=timeline.scale(weeks), period=f"{timeline.long_date(start)} – {timeline.long_date(end)}",
                       period_saved=period_saved,
                       blocks=timeline.project_blocks(rows),
                       requests=requests_to_review.open_requests(conn, date.today()),   # spec 030
                       fetched=bool(db.get_setting(current_app.config["DATABASE"], S_REQUESTS_FETCHED)),
                       student_count=len(rows))


@bp.post("/namen-verbergen")
def toggle_names():
    """Spec 033, F1: switch hiding the names of students on or off (until a restart, F6)."""
    hide_names.set_on(current_app._get_current_object(), request.form.get("aan") == "1")
    target = request.form.get("next") or ""
    return redirect(target if target.startswith("/") and not target.startswith("//") else url_for("pages.overview"))


@bp.get("/studenten/<int:student_id>")
def student_page(student_id: int):
    """Spec 032: the progress, a detailed timeline and the open evaluations of one student."""
    conn = get_db()
    came_from = request.args.get("van") if request.args.get("van") in ("overview", "evaluations") else "overview"
    rows = [r for r in overview_data.student_rows(conn, date.today()) if r["id"] == student_id]
    if not rows:   # F6
        return render_template("student.html", page={"title": "Student niet gevonden", "label": "Student"},
                               active=came_from, row=None), 404
    row = rows[0]
    start, end, period_saved = overview_data.semester_period(conn, date.today())
    weeks = timeline.student_weeks(row, start, end)
    return render_template(
        "student.html", page={"title": row["name"], "label": row["name"]}, active=came_from, row=row,
        **_evidence_context(conn, student_id, weeks, start, end),   # spec 034
        blocks=[[row]], weeks=weeks, tallest=max((len(w["blocks"]) for w in weeks), default=0),
        period=f"{timeline.long_date(start)} – {timeline.long_date(end)}", period_saved=period_saved,
        requests=timeline.student_open_requests(conn, row, date.today()),
        assessed=timeline.student_assessed_requests(conn, student_id, start, end),   # F7
        edit_url=url_for("pages.student_edit_page", student_id=student_id, terug=request.full_path.rstrip("?")))


def _evidence_context(conn, student_id: int, weeks: list[dict], start: date, end: date, message: str | None = None,
                      skills: list[str] | None = None) -> dict:
    """Spec 034: what the evidence timeline needs; spec 039, F7: only the rows of `skills`, without
    the feedback rows (those are per skill on the evaluation page)."""
    fetched = evidence.last_fetch(conn, student_id)
    when = None
    if fetched and fetched["fetched_at"]:
        when = updated_text(datetime.fromisoformat(fetched["fetched_at"]), datetime.now(timezone.utc))
    shown = evidence.timeline(conn, student_id, start, end)
    if skills:
        shown = dict(shown, rows=[r for r in shown["rows"] if r["code"] in skills])
        shown["total"] = sum(len(r["dots"]) for r in shown["rows"])
    return {"evidence": shown, "evidence_weeks": weeks, "evidence_skills": ",".join(skills or []),
            "feedback_stats": feedback.summary(conn, student_id, start, end),     # spec 035
            "feedback_rows": feedback.rows(conn, student_id, start, end, skills),
            "evidence_fetched": when, "evidence_collections": fetched["collections"] if fetched else None,
            "evidence_message": message, "student_id": student_id}


@bp.post("/studenten/<int:student_id>/bewijsstukken")
def fetch_evidence(student_id: int):
    """Spec 034, F1: fetch the evidence of one student (called by the page when it opens)."""
    conn = get_db()
    if not conn.execute("SELECT 1 FROM students WHERE id = ?", (student_id,)).fetchone():
        abort(404)
    start, end, _ = overview_data.semester_period(conn, date.today())
    message = evidence.fetch_for_student(conn, student_id, current_app.extensions["portflow"].token, period=(start, end))
    if request.headers.get("X-Requested-With") != "fetch":
        return redirect(url_for("pages.student_page", student_id=student_id))
    row = next(r for r in overview_data.student_rows(conn, date.today()) if r["id"] == student_id)
    weeks = timeline.student_weeks(row, start, end)
    skills = [s for s in request.args.get("vaardigheden", "").split(",") if s in SKILLS]   # spec 039, F7
    return render_template("_evidence_timeline.html",
                           **_evidence_context(conn, student_id, weeks, start, end, message, skills or None))


@bp.get("/evaluaties/<int:request_id>")
def evaluation_page(request_id: int):
    """Spec 039: one review request with everything needed to assess it."""
    conn = get_db()
    today = date.today()
    start, end, period_saved = overview_data.semester_period(conn, today)
    came_from = request.args.get("van") if request.args.get("van") in ("overview", "evaluations") else "evaluations"
    _, student_id = evaluation_page_data.student_of(conn, request_id)

    def mention(evidence_id: int, label: str) -> str | None:   # F6
        return url_for("pages.evidence_panel", student_id=student_id, ids=evidence_id) if student_id else None

    data = evaluation_page_data.build(conn, request_id, today, start, end, mention)
    if data is None:   # F9
        return render_template("evaluation_page.html", page={"title": "Evaluatie niet gevonden", "label": "Evaluatie"},
                               active="evaluations", data=None), 404
    context = {}
    row = next((r for r in overview_data.student_rows(conn, today) if r["id"] == student_id), None) if student_id else None
    if row:
        weeks = timeline.student_weeks(row, start, end)
        context = dict(_evidence_context(conn, student_id, weeks, start, end, skills=data["codes"]),
                       row=row, blocks=[[row]], weeks=weeks, tallest=max((len(w["blocks"]) for w in weeks), default=0))
    if data["skills"]:
        context.update(ai_routes.card_context(conn, request_id))   # spec 040
    r = data["request"]
    parent = {"title": r["student"],   # spec 039, F1: Evaluaties › <student> › <title>
              "href": url_for("pages.student_page", student_id=r["student_id"], van=came_from) if r["student_id"] else None}
    return render_template(
        "evaluation_page.html", page={"title": r["title"], "label": r["title"], "parent": parent},
        active=came_from, data=data, period=f"{timeline.long_date(start)} – {timeline.long_date(end)}",
        period_saved=period_saved, **context)


@bp.get("/studenten/<int:student_id>/feedback")
def feedback_panel(student_id: int):
    """Spec 035, F4: the feedback requests with their replies, for the side panel (or as a page)."""
    conn = get_db()
    row = conn.execute("SELECT name FROM students WHERE id = ?", (student_id,)).fetchone()
    if row is None:
        abort(404)
    ids = [int(i) for i in request.args.get("vragen", "").split(",") if i.strip().isdigit()]
    start, end, _ = overview_data.semester_period(conn, date.today())
    threads = feedback.threads(conn, student_id, ids, start, end)
    _add_evidence_text(conn, student_id, threads)
    return _panel(student_id, "_feedback_panel.html", "Feedback", threads=threads)


def _add_evidence_text(conn, student_id: int, items: list[dict]) -> None:
    """Spec 036: the text of a text evidence comes first in the conversation (live from Portflow);
    spec 038: so do the files of a file evidence (shown by the file route below)."""
    token = current_app.extensions["portflow"].token
    for item in items:
        if item.get("live"):   # spec 039, F6: not stored; name and kind come from Portflow
            details, item["evidence_error"] = evidence.detail(conn, student_id, item["evidence_id"], token)
            if details:
                item.update(evidence=details["name"], kind=details["kind"], raw_kind=details["raw_kind"])
            item.update(evidence_text=details["text"] if details else "", evidence_images=details["images"] if details else 0,
                        files=details["files"] if details else [], portfolio_id=details["portfolio_id"] if details else None)
        elif item["raw_kind"] in ("free_text", "file"):
            details, item["evidence_error"] = evidence.detail(conn, student_id, item["evidence_id"], token)
            item["evidence_text"] = details["text"] if details else ""
            item["evidence_images"] = details["images"] if details else 0
            item["files"] = details["files"] if details else []
            item["portfolio_id"] = details["portfolio_id"] if details else None


@bp.get("/studenten/<int:student_id>/bestand/<int:portfolio_id>/<int:file_id>")
def evidence_file(student_id: int, portfolio_id: int, file_id: int):
    """Spec 038, F1, F5: the file itself (pdf, image or video), from the cache or fetched now."""
    try:
        path, mime = evidence_files.shown_file(current_app.config["DATABASE"], get_db(),
                                               current_app.extensions["portflow"].token,
                                               student_id, portfolio_id, file_id)
    except evidence_files.FileError as error:
        return render_template("_file_message.html", message=error.message), error.status
    response = send_file(path, mimetype=mime, conditional=True, max_age=0)   # conditional: seeking in a video
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Disposition"] = "inline"
    return response


@bp.get("/studenten/<int:student_id>/bestand/<int:portfolio_id>/<int:file_id>/downloaden")
def evidence_file_download(student_id: int, portfolio_id: int, file_id: int):
    """Spec 038, F4: the original, via a fresh signed link of Portflow (not stored)."""
    try:
        link = evidence_files.original_link(get_db(), current_app.extensions["portflow"].token,
                                            student_id, portfolio_id, file_id)
    except evidence_files.FileError as error:
        return render_template("_file_message.html", message=error.message), error.status
    return redirect(link)


def _panel(student_id: int, template: str, title: str, **context):
    """The side panel (as a fragment) or, without JavaScript, the same as a page."""
    if request.headers.get("X-Requested-With") == "fetch":
        return render_template(template, student_id=student_id, **context)
    name = get_db().execute("SELECT name FROM students WHERE id = ?", (student_id,)).fetchone()["name"]
    return render_template("feedback_page.html", page={"title": title, "label": f"{title} · {name}"},
                           active="overview", panel_template=template, student_id=student_id, **context)


@bp.get("/studenten/<int:student_id>/evaluaties")
def evaluation_panel(student_id: int):
    """Spec 037, F2: the whole evaluation request(s) of a block or a level cell."""
    conn = get_db()
    if not conn.execute("SELECT 1 FROM students WHERE id = ?", (student_id,)).fetchone():
        abort(404)
    request_ids, loose = evaluation_panel_data.parse_args(request.args)
    return _panel(student_id, "_evaluation_panel.html", "Evaluaties",
                  requests=evaluation_panel_data.conversations(conn, student_id, request_ids, loose))


@bp.get("/studenten/<int:student_id>/bewijsstuk")
def evidence_panel(student_id: int):
    """Spec 037, F3: the evidence of a dot with its feedback requests and replies."""
    conn = get_db()
    if not conn.execute("SELECT 1 FROM students WHERE id = ?", (student_id,)).fetchone():
        abort(404)
    ids = [int(i) for i in request.args.get("ids", "").split(",") if i.strip().isdigit()]
    start, end, _ = overview_data.semester_period(conn, date.today())
    items = feedback.evidence_items(conn, student_id, ids, start, end)
    _add_evidence_text(conn, student_id, items)
    return _panel(student_id, "_evidence_panel.html", "Bewijsstuk", items=items)


@bp.get("/projecten")
def squads():
    """Spec 012, F1-F4 and the confirmation of F9."""
    conn = get_db()
    items = projects.all_projects(conn)
    loose = projects.without_project(conn)
    confirm_id = request.args.get("verwijder", "")
    return render_page("squads", items=items, without=loose,
                       management=summary.projects(conn) if items else None,   # spec 027
                       confirm=next((p for p in items if str(p["id"]) == confirm_id), None),
                       added=request.args.get("toegevoegd", ""))


# Kolommen (spec 024, K1-K5) ------------------------------------------------------------------

@bp.get("/kolommen")
def columns():
    conn = get_db()
    items = column_data.all_columns(conn)
    confirm_id = request.args.get("verwijder", "")
    return render_page("columns", items=items, management=summary.columns(conn) if items else None,
                       confirm=next((c for c in items if str(c["id"]) == confirm_id), None))


def _sub_page(endpoint: str, title: str) -> dict:
    page = dict(PAGES_BY_ENDPOINT[endpoint])
    page.update(title=title, label=title)
    return page


def _column_form(column=None):
    conn = get_db()
    error = None
    if request.method == "POST":
        form = {f: request.form.get(f, "") for f in ("code", "naam", "beschrijving", "type")}
        values, error = column_data.validate(conn, form["code"], form["naam"], form["beschrijving"],
                                             None if column else form["type"], column["id"] if column else None)
        if values:
            if column:
                column_data.update(conn, column["id"], values)
            else:
                column_data.create(conn, values)
            return redirect(url_for("pages.columns"))
    elif column:
        form = {"code": column["code"], "naam": column["name"], "beschrijving": column["description"], "type": column["type"]}
    else:
        form = {"code": "", "naam": "", "beschrijving": "", "type": "text"}
    page = _sub_page("columns", "Kolom bewerken" if column else "Nieuwe kolom")
    return render_template("column_form.html", active="columns", form=form, error=error, page=page,
                           column=column, types=column_data.TYPES)


@bp.route("/kolommen/nieuw", methods=["GET", "POST"])
def column_new():
    return _column_form()


@bp.route("/kolommen/<int:column_id>/bewerken", methods=["GET", "POST"])
def column_edit(column_id: int):
    column = column_data.find(get_db(), column_id)
    if column is None:
        abort(404)
    return _column_form(column)


@bp.post("/kolommen/<int:column_id>/<direction>")
def column_move(column_id: int, direction: str):
    if direction not in ("omhoog", "omlaag"):
        abort(404)
    column_data.move(get_db(), column_id, -1 if direction == "omhoog" else 1)
    return redirect(url_for("pages.columns"))


@bp.post("/kolommen/<int:column_id>/verwijderen")
def column_delete(column_id: int):
    column_data.delete(get_db(), column_id)
    return redirect(url_for("pages.columns"))


# Keuzelijsten (spec 024, L1-L5) ----------------------------------------------------------------

@bp.get("/keuzelijsten")
def choice_lists():
    conn = get_db()
    lists = choices.all_lists(conn)
    confirm_id = request.args.get("verwijder", "")
    confirm = next((dict(i, list_name=l["name"], anchor=l["anchor"]) for l in lists for i in l["entries"]
                    if str(i["id"]) == confirm_id), None)
    return render_page("choice_lists", lists=lists, confirm=confirm, management=summary.choice_lists(lists),
                       error=request.args.get("fout", ""), error_list=request.args.get("lijst", ""),
                       added=request.args.get("toegevoegd", ""))


def _list_anchor(list_id: int) -> str:
    found = choices.find_list(get_db(), list_id)
    return found["anchor"] if found else ""


@bp.post("/keuzelijsten/<int:list_id>/items")
def choice_item_add(list_id: int):
    """L2: add an item at the end of the list."""
    conn = get_db()
    if choices.find_list(conn, list_id) is None:
        abort(404)
    values, error = choices.validate(conn, list_id, request.form.get("code", ""), request.form.get("omschrijving", ""))
    if error:
        return redirect(url_for("pages.choice_lists", fout=error, lijst=list_id, _anchor=_list_anchor(list_id)))
    with conn:
        choices.add_item(conn, list_id, values["code"], values["description"])
    return redirect(url_for("pages.choice_lists", _anchor=_list_anchor(list_id)))


@bp.post("/keuzelijsten/<int:list_id>/open-ict")
def choice_list_standard(list_id: int):
    """L5."""
    conn = get_db()
    if choices.find_list(conn, list_id) is None:
        abort(404)
    with conn:
        added = choices.add_standard(conn, list_id)
    return redirect(url_for("pages.choice_lists", toegevoegd=added, lijst=list_id, _anchor=_list_anchor(list_id)))


@bp.route("/keuzelijsten/items/<int:item_id>/bewerken", methods=["GET", "POST"])
def choice_item_edit(item_id: int):
    """L2: code and description."""
    conn = get_db()
    item = choices.find_item(conn, item_id)
    if item is None:
        abort(404)
    lst = choices.find_list(conn, item["list_id"])
    error = None
    if request.method == "POST":
        form = {"code": request.form.get("code", ""), "omschrijving": request.form.get("omschrijving", "")}
        values, error = choices.validate(conn, item["list_id"], form["code"], form["omschrijving"], item_id)
        if values:
            choices.update_item(conn, item_id, values["code"], values["description"])
            return redirect(url_for("pages.choice_lists", _anchor=lst["anchor"]))
    else:
        form = {"code": item["code"], "omschrijving": item["description"]}
    page = _sub_page("choice_lists", "Keuze bewerken")
    return render_template("choice_item_form.html", active="choice_lists", form=form, error=error, page=page,
                           back=url_for("pages.choice_lists", _anchor=lst["anchor"]))


@bp.post("/keuzelijsten/items/<int:item_id>/<direction>")
def choice_item_move(item_id: int, direction: str):
    """L3."""
    if direction not in ("omhoog", "omlaag"):
        abort(404)
    conn = get_db()
    item = choices.find_item(conn, item_id)
    if item is None:
        abort(404)
    choices.move_item(conn, item_id, -1 if direction == "omhoog" else 1)
    return redirect(url_for("pages.choice_lists", _anchor=_list_anchor(item["list_id"])))


@bp.post("/keuzelijsten/items/<int:item_id>/verwijderen")
def choice_item_delete(item_id: int):
    """L4: after the confirmation on the page."""
    conn = get_db()
    item = choices.find_item(conn, item_id)
    if item is None:
        return redirect(url_for("pages.choice_lists"))
    anchor = _list_anchor(item["list_id"])
    choices.delete_item(conn, item_id)
    return redirect(url_for("pages.choice_lists", _anchor=anchor))


@bp.get("/semesters")
def semesters():
    """Spec 009, F1-F4 and the confirmation of F10."""
    conn = get_db()
    items = semester_data.all_semesters(conn)
    confirm_id = request.args.get("verwijder", "")
    return render_page("semesters", items=items, management=summary.semesters(conn) if items else None,
                       confirm=next((s for s in items if str(s["id"]) == confirm_id), None),
                       added=request.args.get("toegevoegd", ""))


def data_paths() -> dict:
    """Spec 031, F1, F2: the files and folders this dashboard uses."""
    database = Path(current_app.config["DATABASE"]).resolve()
    log = database.parent / "dashboard.log"
    return {
        "database": str(database),
        "profile": str(database.parent / "browser-profile"),
        "backups": str(database.parent / reset.BACKUP_DIR),
        "log": str(log) if log.exists() else None,
        "source": paths.SOURCES.get(current_app.config.get("DATA_SOURCE"), current_app.config.get("DATA_SOURCE")),
        "file_manager": "Verkenner" if os.name == "nt" else "Finder",
    }


@bp.post("/instellingen/data/openen")
def open_data_folder():
    """Spec 031, F3: open the folder of the database, never a path from the request."""
    folder = str(Path(current_app.config["DATABASE"]).resolve().parent)
    opener = current_app.config.get("OPEN_FOLDER") or (
        (lambda path: subprocess.Popen(["explorer", path])) if os.name == "nt"
        else (lambda path: subprocess.Popen(["open", path])))
    try:
        opener(folder)
    except OSError:
        pass
    return redirect(url_for("pages.settings", _anchor="data"))


@bp.get("/instellingen")
def settings():
    conn = get_db()
    connection = current_app.extensions["portflow"]
    start, end, saved = overview_data.semester_period(conn, date.today())
    ai_state = ai_routes.readiness(current_app.config["DATABASE"])   # spec 040, F11; writes the log first (spec 042)
    return render_page(
        "settings",
        semester_start=start.isoformat(),
        semester_end=end.isoformat(),
        semester_saved=saved,
        semester_error=request.args.get("fout", ""),
        reset_step=request.args.get("bevestig") if request.args.get("bevestig") in ("alles-verwijderen", "alles-verwijderen-2") else None,
        reset_summary=reset.summary(conn),
        reset_busy=reset.is_busy(current_app._get_current_object()),
        reset_error=request.args.get("reset_fout", ""),
        confirm_word=reset.CONFIRM_WORD,
        demo_counts=demo.demo_counts(conn),
        confirm_remove=request.args.get("bevestig") == "demodata-verwijderen",
        confirm_disconnect=request.args.get("bevestig") == "verbinding-verbreken",
        canvas_url=connection.canvas_url,
        update_check=current_app.extensions["updater"].enabled(),   # spec 020, U4
        data=data_paths(),                                          # spec 031
        version_check=request.args.get("versie") if request.args.get("versie") in ("nieuw", "actueel", "mislukt") else None,
        latest_release=current_app.extensions["updater"].latest(),  # spec 020, U6
        always_visible=connection.always_visible,
        ai=ai_state,                                                # spec 040, F11
        **ai_routes.log_context(conn, ai_state, "instellingen"),    # spec 042
        ai_tested=ai_routes.ollama.TESTED_MODELS,                   # spec 040, F28
        ai_default=ai_routes.ollama.DEFAULT_MODEL,                  # spec 040, F27
        ai_pull=current_app.extensions["ollama_pull"].status(),     # spec 040, F28
        ai_saved=request.args.get("model") == "ok",
        ai_laptop=ai_routes.ai_advice.laptop(current_app.config["DATABASE"]),   # spec 040, F29-F31
        ai_cores=ai_routes.ollama.cores(),
        ai_wait_range=ai_routes.ollama.WAIT_MINUTES,                 # spec 040, F33
        ai_wait_default=ai_routes.ollama.DEFAULT_WAIT,
        ai_laptop_saved=request.args.get("laptop") == "ok",
    )


@bp.post("/instellingen/semesterperiode")
def save_semester_period():
    """Spec 001, F22."""
    error = overview_data.save_semester_period(
        get_db(), request.form.get("start", ""), request.form.get("end", ""))
    if error:
        return redirect(url_for("pages.settings", fout=error) + "#semesterperiode")
    return redirect(url_for("pages.settings") + "#semesterperiode")


@bp.post("/instellingen/alles-verwijderen")
def reset_everything():
    """Spec 014: only after the second confirmation with the typed word (F3)."""
    if request.form.get("bevestiging", "").strip().upper() != reset.CONFIRM_WORD:
        return redirect(url_for("pages.settings", bevestig="alles-verwijderen-2",
                                reset_fout=f"Typ {reset.CONFIRM_WORD} om te bevestigen.") + "#alles-verwijderen")
    try:
        copy = reset.reset_all(current_app._get_current_object())
    except reset.ResetError as error:
        return redirect(url_for("pages.settings", reset_fout=error.message) + "#alles-verwijderen")
    message = f"Alle gegevens zijn verwijderd. De reservekopie staat in data/{reset.BACKUP_DIR}/{copy.name}."
    return redirect(url_for("pages.overview", melding=message))


@bp.post("/instellingen/demodata/laden")
def load_demo_data():
    demo.load_demo_data(get_db())
    return redirect(url_for("pages.settings"))


@bp.post("/instellingen/demodata/verwijderen")
def remove_demo_data():
    demo.remove_demo_data(get_db())
    return redirect(url_for("pages.settings"))


# Studenten toevoegen (spec 004) --------------------------------------------------

@bp.get("/studenten/toevoegen")
def add_students():
    """The chooser between the four manners (F3); only 'Uit Portflow kiezen' works so far."""
    page = _add_students_page("Studenten toevoegen")
    return render_template("add_students.html", page=page, active="students")


@bp.post("/studenten/toevoegen/portflow/starten")
def add_students_portflow_start():
    """Starts the Portflow connection without an extra click (F5), unless already connected."""
    connection = current_app.extensions["portflow"]
    if not connection.token:
        connection.connect()
    return redirect(url_for("pages.add_students_portflow"))


@bp.get("/studenten/toevoegen/portflow")
def add_students_portflow():
    """Entry point (F5): the connect panel, or a fast loading shell (F6 technical: app.js
    fetches the slow share list as a fragment; the no-JS fallback is the /lijst route)."""
    page = _add_students_page("Uit Portflow kiezen")
    connection = current_app.extensions["portflow"]
    if not connection.token:
        return render_template("add_students_portflow.html", page=page, active="students",
                                connected=False, loading=False)
    return render_template(
        "add_students_portflow.html", page=page, active="students", connected=True, loading=True,
        fragment_url=url_for("pages.add_students_portflow_list", fragment=1),
        fallback_url=url_for("pages.add_students_portflow_list"),
    )


def _portflow_candidates_context() -> dict:
    """F6: fetch, filter and group the shared portfolios; can be slow (pagination, retries),
    so it lives on its own route instead of blocking the page shell."""
    connection = current_app.extensions["portflow"]
    token = connection.token
    if not token:
        return {"error": "unauthorized", "rows": None}

    status, raw_items = connection.api.shared_with_me(token)
    if status == 401:
        connection.mark_unauthorized()
        return {"error": "unauthorized", "rows": None}
    if status != 200:
        return {"error": "unreachable", "rows": None}

    candidates = student_intake.group_shared_students(raw_items or [])
    conn = get_db()
    tracked = student_intake.tracked_portflow_ids(conn)
    name_matches = student_intake.unlinked_students_by_name(conn)
    rows = []
    for candidate in candidates:
        already_tracked = candidate["portflow_user_id"] in tracked
        possible_match = not already_tracked and student_intake.normalize_name(candidate["name"]) in name_matches
        rows.append(dict(candidate, already_tracked=already_tracked, possible_match=possible_match))
    return {"error": None, "rows": rows}


@bp.get("/studenten/toevoegen/portflow/lijst")
def add_students_portflow_list():
    """The share list itself (F6-F10): an HTML fragment for app.js, or a full page without it."""
    context = _portflow_candidates_context()
    if request.args.get("fragment") == "1":
        return render_template("_add_students_portflow_result.html", **context)
    page = _add_students_page("Uit Portflow kiezen")
    return render_template("add_students_portflow.html", page=page, active="students",
                            connected=True, loading=False, **context)


@bp.post("/studenten/toevoegen/portflow")
def add_students_portflow_submit():
    """Adds or links the selected students (F10, F11) and goes back to Overzicht with a
    confirmation (F12)."""
    connection = current_app.extensions["portflow"]
    token = connection.token
    if not token:
        return redirect(url_for("pages.add_students_portflow"))

    selected_ids = {int(value) for value in request.form.getlist("portflow_user_id") if value.isdigit()}
    added = linked = 0
    if selected_ids:
        status, raw_items = connection.api.shared_with_me(token)
        if status == 200:
            conn = get_db()
            tracked = student_intake.tracked_portflow_ids(conn)
            to_add = [
                candidate
                for candidate in student_intake.group_shared_students(raw_items or [])
                if candidate["portflow_user_id"] in selected_ids and candidate["portflow_user_id"] not in tracked
            ]
            coach_id = None
            if request.form.get("coach") == "1":
                coach_id = student_intake.staff_id_by_name(conn, connection.user_name)
            added, linked = student_intake.add_or_link_students_from_portflow(conn, to_add, coach_id=coach_id)
    return redirect(url_for("pages.overview", toegevoegd=added, gekoppeld=linked))


# Coaches and guild masters (specs 006 and 007) -------------------------------------------

ROLE_PAGES = {
    "coach": {"endpoint": "coaches", "single": "coach", "plural": "coaches", "Single": "Coach",
              "other": "gildemeester", "already": "Al coach", "skills": "coachvaardigheden (PL … RE)"},
    "guild_master": {"endpoint": "guild_masters", "single": "gildemeester", "plural": "gildemeesters",
                     "Single": "Gildemeester", "other": "coach", "already": "Al gildemeester",
                     "skills": "productvaardigheden (OC … KPM)"},
}


def _role_page(role: str, title: str | None = None) -> dict:
    page = dict(PAGES_BY_ENDPOINT[ROLE_PAGES[role]["endpoint"]])
    if title:
        page.update(title=title, label=title)
    return page


def _staff_list(role: str):
    conn = get_db()
    user = current_app.extensions["portflow"].user_name
    people = staff.people(conn, role, user)
    confirm_id = request.args.get("verwijder", "")
    return render_template(
        "staff.html", page=_role_page(role), active=ROLE_PAGES[role]["endpoint"], role=role,
        words=ROLE_PAGES[role], people=people,
        management=summary.staff(conn, role, len(people), sum(p["evaluations"] for p in people)) if people else None,
        confirm=next((p for p in people if str(p["id"]) == confirm_id), None),
        added=request.args.get("toegevoegd", ""),
    )


@bp.get("/coaches")
def coaches():
    return _staff_list("coach")


@bp.get("/gildemeesters")
def guild_masters():
    return _staff_list("guild_master")


def _role_from_path(kind: str) -> str:
    role = {"coaches": "coach", "gildemeesters": "guild_master"}.get(kind)
    if role is None:
        abort(404)
    return role


@bp.get("/<any(coaches, gildemeesters):kind>/toevoegen")
def staff_add(kind: str):
    """F4: the two manners of adding."""
    role = _role_from_path(kind)
    words = ROLE_PAGES[role]
    page = _role_page(role, f"{words['Single']} toevoegen")
    return render_template("staff_add.html", page=page, active=words["endpoint"], role=role, kind=kind, words=words,
                           preset=staff.read_preset() if role == "guild_master" else [])


@bp.get("/<any(coaches, gildemeesters):kind>/toevoegen/portflow")
def staff_add_portflow(kind: str):
    """F5: every assessor in the fetched evaluations."""
    role = _role_from_path(kind)
    words = ROLE_PAGES[role]
    conn = get_db()
    page = _role_page(role, "Uit Portflow kiezen")
    return render_template("staff_add_portflow.html", page=page, active=words["endpoint"], role=role, kind=kind,
                           words=words, candidates=staff.candidates(conn, role),
                           has_evaluations=bool(conn.execute("SELECT 1 FROM evaluations LIMIT 1").fetchone()))


@bp.post("/<any(coaches, gildemeesters):kind>/toevoegen/portflow")
def staff_add_portflow_submit(kind: str):
    role = _role_from_path(kind)
    added = staff.add(get_db(), request.form.getlist("naam"), role)
    return redirect(url_for("pages." + ROLE_PAGES[role]["endpoint"], toegevoegd=added))


@bp.post("/gildemeesters/toevoegen/open-ict")
def guild_masters_add_preset():
    """Spec 006, F11: the Open-ICT guild masters of September 2026, with their guilds."""
    added = staff.add_guild_masters_with_guilds(get_db(), staff.read_preset())
    return redirect(url_for("pages.guild_masters", toegevoegd=added))


@bp.route("/<any(coaches, gildemeesters):kind>/toevoegen/namen", methods=["GET", "POST"])
def staff_add_names(kind: str):
    """F6: one name per line; unknown names get a warning first, then can be added anyway."""
    role = _role_from_path(kind)
    words = ROLE_PAGES[role]
    conn = get_db()
    text = request.form.get("namen", "")
    names = staff.parse_names(text)
    if request.method == "POST" and names:
        known = staff.assessor_names(conn)
        unknown = [n for n in names if staff.normalize_name(n) not in known]
        if not unknown or request.form.get("toch") == "1":
            added = staff.add(conn, names, role)
            return redirect(url_for("pages." + words["endpoint"], toegevoegd=added))
    else:
        unknown = []
    page = _role_page(role, "Namen typen of plakken")
    return render_template("staff_add_names.html", page=page, active=words["endpoint"], role=role, kind=kind,
                           words=words, text=text, unknown=unknown,
                           empty=request.method == "POST" and not names)


@bp.route("/<any(coaches, gildemeesters):kind>/<int:staff_id>/bewerken", methods=["GET", "POST"])
def staff_edit(kind: str, staff_id: int):
    """F7, F20: first and last name, and for a guild master the guilds."""
    role = _role_from_path(kind)
    words = ROLE_PAGES[role]
    conn = get_db()
    person = staff.find(conn, staff_id)
    if person is None:
        abort(404)
    error = None
    if request.method == "POST":
        error = staff.update_name(conn, staff_id, request.form.get("voornaam", ""), request.form.get("achternaam", ""))
        if not error:
            if role == "guild_master":
                staff.set_guilds(conn, staff_id, [int(v) for v in request.form.getlist("gilde") if v.isdigit()])
            staff.set_excluded(conn, staff.find(conn, staff_id)["name"], request.form.get("uitsluiten") == "1")   # spec 019, F12
            return redirect(url_for("pages." + words["endpoint"]))
    chosen = {r[0] for r in conn.execute("SELECT guild_id FROM staff_guilds WHERE staff_id = ?", (staff_id,))}
    page = _role_page(role, f"{words['Single']} bewerken")
    return render_template("staff_edit.html", page=page, active=words["endpoint"], role=role, kind=kind,
                           words=words, person=person, error=error,
                           first_name=request.form.get("voornaam", person["first_name"]),
                           last_name=request.form.get("achternaam", person["last_name"]),
                           guild_options=[dict(r) for r in conn.execute("SELECT id, code, name FROM guilds ORDER BY code")],
                           chosen=chosen,
                           excluded=(request.form.get("uitsluiten") == "1") if request.method == "POST"
                           else staff.is_excluded(conn, person["name"]))


@bp.post("/<any(coaches, gildemeesters):kind>/<int:staff_id>/verwijderen")
def staff_remove(kind: str, staff_id: int):
    """F8: removes only this role."""
    role = _role_from_path(kind)
    staff.remove_role(get_db(), staff_id, role, current_app.extensions["portflow"].user_name)
    return redirect(url_for("pages." + ROLE_PAGES[role]["endpoint"]))


# Guilds (spec 006, F12-F19) ------------------------------------------------------------------

def _guild_page(title: str | None = None) -> dict:
    page = dict(PAGES_BY_ENDPOINT["guilds"])
    if title:
        page.update(title=title, label=title)
    return page


@bp.get("/gildes", endpoint="guilds")
def guilds_list():
    conn = get_db()
    items = guilds.all_guilds(conn)
    confirm_id = request.args.get("verwijder", "")
    return render_template("guilds.html", page=_guild_page(), active="guilds", items=items,
                           management=summary.guilds(conn) if items else None,   # spec 027
                           confirm=next((g for g in items if str(g["id"]) == confirm_id), None),
                           added=request.args.get("toegevoegd", ""))


@bp.get("/gildes/toevoegen")
def guilds_add():
    """F14: make one yourself, or add the Open-ICT guilds."""
    return render_template("guilds_add.html", page=_guild_page("Gilde toevoegen"),
                           active="guilds", preset=guilds.read_preset())


@bp.post("/gildes/toevoegen/open-ict")
def guilds_add_preset():
    added = guilds.add_preset(get_db())
    return redirect(url_for("pages.guilds", toegevoegd=added))


def _guild_form(guild=None):
    """F14 (new) and F16 (edit), spec 018 F2: code, name, professional role, description and colour."""
    conn = get_db()
    guild_id = guild["id"] if guild else None
    error = None
    fields = ("code", "naam", "beroepsrol", "beschrijving", "kleur")
    if request.method == "POST":
        form = {f: request.form.get(f, "") for f in fields}
        values, error = guilds.validate(conn, *(form[f] for f in fields), guild_id)
        if values:
            if guild:
                guilds.update(conn, guild_id, values)
            else:
                guilds.create(conn, values)
            return redirect(url_for("pages.guilds"))
        form["kleur"] = form["kleur"] or guilds.DEFAULT_COLOR
    elif guild:
        form = {"code": guild["code"], "naam": guild["name"], "beroepsrol": guild["role_name"],
                "beschrijving": guild["description"], "kleur": guild["color"]}
    else:
        form = {"code": "", "naam": "", "beroepsrol": "", "beschrijving": "", "kleur": guilds.DEFAULT_COLOR}
    title = "Gilde bewerken" if guild else "Gilde aanmaken"
    return render_template("guild_form.html", page=_guild_page(title), active="guilds", form=form, error=error)


@bp.route("/gildes/nieuw", methods=["GET", "POST"])
def guild_new():
    return _guild_form()


@bp.route("/gildes/<int:guild_id>/bewerken", methods=["GET", "POST"])
def guild_edit(guild_id: int):
    guild = guilds.find(get_db(), guild_id)
    if guild is None:
        abort(404)
    return _guild_form(guild)


@bp.post("/gildes/<int:guild_id>/verwijderen")
def guild_delete(guild_id: int):
    """F17."""
    guilds.delete(get_db(), guild_id)
    return redirect(url_for("pages.guilds"))


@bp.get("/beroepsrollen", endpoint="professional_roles")
def professional_roles_moved():
    """Spec 018, F1: the professional role is part of the guild now."""
    return redirect(url_for("pages.guilds"))


# Semesters (spec 009) --------------------------------------------------------------------------

def _semester_page(title: str | None = None) -> dict:
    page = dict(PAGES_BY_ENDPOINT["semesters"])
    if title:
        page.update(title=title, label=title)
    return page


@bp.get("/semesters/toevoegen")
def semesters_add():
    """F5: make one yourself, or add the Open-ICT semesters."""
    return render_template("semesters_add.html", active="semesters", preset=semester_data.read_preset(),
                           page=_semester_page("Semester toevoegen"))


@bp.post("/semesters/toevoegen/open-ict")
def semesters_add_preset():
    added = semester_data.add_preset(get_db())
    return redirect(url_for("pages.semesters", toegevoegd=added))


def _semester_form(semester=None):
    """F5 (new) and F8 (edit), checked as in F7."""
    conn = get_db()
    semester_id = semester["id"] if semester else None
    error = None
    if request.method == "POST":
        form = {field: request.form.get(field, "") for field in ("number",) + semester_data.FIELDS}
        values, error = semester_data.validate(conn, form["number"], form, semester_id)
        if values:
            if semester:
                semester_data.update(conn, semester_id, values)
            else:
                semester_data.create(conn, values)
            return redirect(url_for("pages.semesters"))
    elif semester:
        form = {field: semester[field] for field in ("number",) + semester_data.FIELDS}
    else:
        form = {field: "" for field in ("number",) + semester_data.FIELDS}
    title = "Semester bewerken" if semester else "Semester aanmaken"
    return render_template("semester_form.html", active="semesters", form=form, error=error,
                           editing=bool(semester), page=_semester_page(title))


@bp.route("/semesters/nieuw", methods=["GET", "POST"])
def semester_new():
    return _semester_form()


@bp.route("/semesters/<int:semester_id>/bewerken", methods=["GET", "POST"])
def semester_edit(semester_id: int):
    semester = semester_data.find(get_db(), semester_id)
    if semester is None:
        abort(404)
    return _semester_form(semester)


@bp.post("/semesters/<int:semester_id>/verwijderen")
def semester_delete(semester_id: int):
    """F10."""
    semester_data.delete(get_db(), semester_id)
    return redirect(url_for("pages.semesters"))


# Student bewerken (spec 011) ----------------------------------------------------------------

def _list_path() -> str:
    """The student list with the filters the user came from (only local paths, F1, F4)."""
    target = request.values.get("terug", "")
    if not target.startswith("/studenten") or target.startswith("//"):
        target = url_for("pages.students")
    return target


def _with_message(target: str, message: str) -> str:
    return target + ("&" if "?" in target else "?") + urlencode({"melding": message})


def _student_form_from_request() -> dict:
    """The fields of the student form (spec 011, 016, 017) from the request."""
    form = {key: request.form.get(key, "") for key in (
        "name", "student_number", "semester", "start_date", "squad_id", "track", "squad_role", "coach_id", "notes")}
    # Spec 026: the custom columns ("kolom-<id>").
    form["custom"] = {key[6:]: value for key, value in request.form.items() if key.startswith("kolom-")}
    form["guilds"] = [{"guild_id": r, "guild_master_id": m} for r, m in
                      zip(request.form.getlist("guild"), request.form.getlist("guild_master"))]
    return form


@bp.route("/studenten/toevoegen/handmatig", methods=["GET", "POST"])
def student_new_page():
    """Spec 017: add one student with the form of Student bewerken."""
    conn = get_db()
    error, duplicate = None, None
    if request.method == "POST":
        form = _student_form_from_request()
        values, error = student_edit.validate(conn, form)
        if values and not error:
            owner = student_edit.number_owner(conn, values["student_number"])
            if owner:
                error = f"Dit studentnummer hoort al bij {owner}."
        if values and not error:
            duplicate = student_edit.same_name(conn, values["name"])
            if duplicate and request.form.get("toch") != "1":
                pass   # F3: show the warning first
            else:
                student_id = student_edit.create(conn, values)
                message = f"{values['name']} toegevoegd. " + _link_new_student(conn, student_id)
                return redirect(_with_message(url_for("pages.students"), message.strip()))
    else:
        form = student_edit.empty_form()
    page = dict(PAGES_BY_ENDPOINT["students"], title="Student toevoegen",
                label="Student toevoegen")
    return render_template("student_edit.html", page=page, active="students", student=None, form=form,
                           error=error, duplicate=duplicate, options=student_edit.options(conn),
                           back=url_for("pages.add_students"), confirm=False)


def _link_new_student(conn, student_id: int) -> str:
    """Spec 017, F4: link to Portflow on name right away when the connection is valid."""
    connection = current_app.extensions["portflow"]
    token = connection.token
    if not token:
        return "Klik op Verversen om de student aan Portflow te koppelen."
    try:
        candidates = portflow_link.shared_students(connection.api, token, use_cache=False)
    except portflow_link.Unauthorized:
        connection.mark_unauthorized()
        return "Klik op Verversen om de student aan Portflow te koppelen."
    if candidates is None:
        return "Klik op Verversen om de student aan Portflow te koppelen."
    portflow_link.auto_link(conn, candidates)
    linked = conn.execute("SELECT portflow_user_id FROM students WHERE id = ?", (student_id,)).fetchone()[0]
    if linked is not None:
        return "Gekoppeld aan Portflow. Klik op Verversen om de evaluaties op te halen."
    return "Niet gevonden in je gedeelde portfolio's."


@bp.route("/studenten/<int:student_id>/bewerken", methods=["GET", "POST"])
def student_edit_page(student_id: int):
    conn = get_db()
    student = student_edit.find(conn, student_id)
    if student is None:
        abort(404)
    error = None
    if request.method == "POST":
        form = _student_form_from_request()
        form["name"] = hide_names.real_name(conn, student_id, form["name"])   # spec 033, F7
        values, error = student_edit.validate(conn, form)
        link_choice = request.form.get("portflow", "")
        candidate = None
        if values and link_choice.isdigit() and int(link_choice) != student["portflow_user_id"]:
            candidate = next((c for c in _link_choices(conn, student_id) or [] if c["portflow_user_id"] == int(link_choice)), None)
            if candidate is None:
                error = "Kies een Portflow-student uit de lijst."
        if values and not error:
            student_edit.save(conn, student_id, values)
            if candidate is not None:
                portflow_link.set_link(conn, student_id, candidate)          # spec 015, F5
            elif link_choice == "geen" and student["portflow_user_id"] is not None:
                portflow_link.set_link(conn, student_id, None)
            return redirect(_with_message(_list_path(), f"Gegevens van {values['name']} opgeslagen."))
        form["portflow"] = link_choice
    else:
        form = student_edit.form_values(conn, student)
        form["portflow"] = str(student["portflow_user_id"] or "geen")
    page = dict(PAGES_BY_ENDPOINT["students"], title="Student bewerken",
                label=f"Student bewerken · {student['name']}")
    return render_template("student_edit.html", page=page, active="students", student=student, form=form,
                           error=error, options=student_edit.options(conn),
                           link_info=student_edit.portflow_link(conn, student), back=_list_path(),
                           link_choices=_link_choices(conn, student_id),
                           confirm=request.args.get("bevestig") == "verbergen")


def _link_choices(conn, student_id: int) -> list[dict] | None:
    """Spec 015, F5: shared Portflow students to choose from, or None without a valid connection."""
    connection = current_app.extensions["portflow"]
    token = connection.token
    if not token:
        return None
    try:
        candidates = portflow_link.shared_students(connection.api, token)
    except portflow_link.Unauthorized:
        connection.mark_unauthorized()
        return None
    return portflow_link.choices(conn, candidates, student_id) if candidates is not None else None


@bp.post("/studenten/<int:student_id>/verbergen-bevestigd")
def student_hide_confirmed(student_id: int):
    """Spec 011, F6: hide the student (Verversen leaves him alone), or show him again."""
    conn = get_db()
    student = student_edit.find(conn, student_id)
    if student is None:
        abort(404)
    show = request.form.get("tonen") == "1"
    overview_data.set_hidden(conn, student_id, not show)
    return redirect(_with_message(_list_path(), f"{student['name']} is weer zichtbaar." if show else f"{student['name']} is verborgen."))


# Projecten (spec 012) -------------------------------------------------------------------------

def _project_page(title: str | None = None) -> dict:
    page = dict(PAGES_BY_ENDPOINT["squads"])
    if title:
        page.update(title=title, label=title)
    return page


@bp.get("/projecten/nieuw")
def projects_add():
    """F5: add by hand, or add the Open-ICT projects."""
    return render_template("projects_add.html", active="squads", preset=projects.read_preset(),
                           page=_project_page("Nieuw project"))


@bp.post("/projecten/nieuw/open-ict")
def projects_add_preset():
    added = projects.add_preset(get_db())
    return redirect(url_for("pages.squads", toegevoegd=added))


def _project_form(project=None):
    """F5 (by hand) and F8 (edit), checked as in F7."""
    conn = get_db()
    project_id = project["id"] if project else None
    error = None
    fields = ("nummer", "naam", "opdrachtgever")
    if request.method == "POST":
        form = {f: request.form.get(f, "") for f in fields + ("weergavenaam",)}
        values, error = projects.validate(conn, *(form[f] for f in fields), project_id, form["weergavenaam"])
        if values:
            if project:
                projects.update(conn, project_id, values)
            else:
                projects.create(conn, values)
            return redirect(url_for("pages.squads"))
    elif project:
        form = {"nummer": project["number"] or "", "naam": project["name"], "opdrachtgever": project["client"],
                "weergavenaam": project["display_name"]}
    else:
        form = {"nummer": "", "naam": "", "opdrachtgever": "", "weergavenaam": ""}
    title = "Project bewerken" if project else "Handmatig toevoegen"
    return render_template("project_form.html", active="squads", form=form, error=error, page=_project_page(title))


@bp.route("/projecten/handmatig", methods=["GET", "POST"])
def project_new():
    return _project_form()


@bp.route("/projecten/<int:project_id>/bewerken", methods=["GET", "POST"])
def project_edit(project_id: int):
    project = projects.find(get_db(), project_id)
    if project is None:
        abort(404)
    return _project_form(project)


@bp.post("/projecten/<int:project_id>/verwijderen")
def project_delete(project_id: int):
    """F9."""
    projects.delete(get_db(), project_id)
    return redirect(url_for("pages.squads"))
