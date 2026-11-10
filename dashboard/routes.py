"""Pages of the dashboard (spec 002 shell; specs 001, 004, 006 and 007)."""

from datetime import date, datetime

from urllib.parse import urlencode

from flask import Blueprint, abort, current_app, redirect, render_template, request, url_for

from . import (demo, guilds, overview as overview_data, portflow_link, projects, reset,
               semesters as semester_data, staff, student_edit, student_intake)
from .db import get_db
from .portflow_connection import initials
from .skills import CATEGORY, NAMES as SKILL_NAMES, SKILLS

bp = Blueprint("pages", __name__)

# Sidebar menu and page headers (spec 002, F5 and F8). Text is Dutch: it is shown to the user.
PAGES = [
    {"endpoint": "overview", "path": "/", "label": "Overzicht", "icon": "home",
     "eyebrow": None, "title": None, "intro": "Dit vraagt vandaag je aandacht.",
     "placeholder": None},
    {"endpoint": "students", "path": "/studenten", "label": "Studenten", "icon": "users",
     "eyebrow": "Studievoortgang", "title": "Studenten",
     "intro": "Alle studenten die je volgt, met hun indeling.",
     "placeholder": None,
     "show_add_student": True},
    {"endpoint": "evaluations", "path": "/evaluaties", "label": "Evaluaties", "icon": "clipboard",
     "eyebrow": "Studievoortgang", "title": "Evaluaties",
     "intro": "Evaluatieverzoeken die op jouw beoordeling wachten.",
     "placeholder": "Hier komen de evaluatieverzoeken die op jouw beoordeling wachten."},
    {"endpoint": "squads", "path": "/projecten", "label": "Projecten", "icon": "folder",
     "eyebrow": "Beheer", "title": "Projecten",
     "intro": "Beheer de projectgroepen waarin je studenten zijn ingedeeld.",
     "placeholder": None},
    {"endpoint": "coaches", "path": "/coaches", "label": "Coaches", "icon": "coach",
     "eyebrow": "Beheer", "title": "Coaches",
     "intro": "Beheer de coaches van wie de evaluaties meetellen.", "placeholder": None},
    {"endpoint": "guild_masters", "path": "/gildemeesters", "label": "Gildemeesters", "icon": "guild",
     "eyebrow": "Beheer", "title": "Gildemeesters",
     "intro": "Beheer de gildemeesters van wie de evaluaties meetellen.", "placeholder": None},
    {"endpoint": "guilds", "path": "/gildes", "label": "Gildes", "icon": "flag",
     "eyebrow": "Beheer", "title": "Gildes",
     "intro": "Beheer de gildes en zie welke gildemeesters en studenten erbij horen.", "placeholder": None},
    {"endpoint": "columns", "path": "/kolommen", "label": "Kolommen", "icon": "columns",
     "eyebrow": "Curriculum", "title": "Kolommen",
     "intro": "De bouwstenen van je studentenoverzicht, op één plek beheerd.",
     "placeholder": "Hier beheer je straks de kolommen van het studentenoverzicht."},
    {"endpoint": "semesters", "path": "/semesters", "label": "Semesters", "icon": "calendar",
     "eyebrow": "Studievoortgang", "title": "Semesters",
     "intro": "Bekijk de semesters, hun eisen en hoeveel studenten erin zitten.",
     "placeholder": None},
    {"endpoint": "settings", "path": "/instellingen", "label": "Instellingen", "icon": "sliders",
     "eyebrow": "Beheer", "title": "Instellingen",
     "intro": "Je gegevens, de semesterperiode en de koppeling met Portflow.",
     "placeholder": None},
]
# Spec 002, F17: the management pages sit in one collapsible group "Beheer", in this order.
MENU_ORDER = ["overview", "students", "evaluations",
              "semesters", "guilds", "guild_masters", "coaches", "squads", "columns",
              "settings"]   # spec 018: no Beroepsrollen any more
MANAGEMENT = {"semesters", "guilds", "guild_masters", "coaches", "squads", "columns"}
PAGES.sort(key=lambda page: MENU_ORDER.index(page["endpoint"]))
for _page in PAGES:
    _page["group"] = "beheer" if _page["endpoint"] in MANAGEMENT else None
PAGES_BY_ENDPOINT = {page["endpoint"]: page for page in PAGES}

DAYS = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
          "augustus", "september", "oktober", "november", "december"]


def dutch_date(moment: datetime) -> str:
    return f"{DAYS[moment.weekday()]} {moment.day} {MONTHS[moment.month - 1]}"


def greeting(moment: datetime) -> str:
    if moment.hour < 12:
        return "Goedemorgen"
    if moment.hour < 18:
        return "Goedemiddag"
    return "Goedenavond"


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
    }


def render_page(endpoint: str, **context):
    page = dict(PAGES_BY_ENDPOINT[endpoint])
    if endpoint == "overview":
        now = datetime.now()
        page["eyebrow"], page["title"] = dutch_date(now), greeting(now)
    template = {"settings": "settings.html", "overview": "overview.html",
                "students": "students.html",
                "semesters": "semesters.html",
                "squads": "projects.html"}.get(endpoint, "page.html")
    return render_template(template, page=page, active=endpoint, **context)


def _add_students_page(title: str, intro: str) -> dict:
    """A page dict for the 'Studenten toevoegen' flow (spec 004): not in PAGES, so it
    does not get its own sidebar item, but keeps the look of the other pages."""
    return {"eyebrow": "Studievoortgang", "title": title, "intro": intro, "label": title}


def _table_context() -> dict:
    """The student table (spec 001) with the filters from the query string (F13-F18)."""
    conn = get_db()
    user = current_app.extensions["portflow"].user_name
    all_rows = overview_data.student_rows(conn, date.today())
    args = {key: request.args.get(key, "") for key in ("wie", "semester", "invulling", "project", "gilde", "aansporen")}
    args["wie"] = args["wie"] if args["wie"] in dict(overview_data.WHO) else "alle"
    grouping = request.args.get("groep", "squad")
    grouping = grouping if grouping in dict(overview_data.GROUPINGS) else "squad"
    rows = overview_data.apply_filters(all_rows, args, user)
    shown = rows
    visible = overview_data.visible_columns(conn)
    custom = [c for c in overview_data.custom_columns(conn)]
    return {
        "table": {
            "groups": overview_data.group_rows(shown, grouping),
            "total": len(all_rows),
            "matching": len(rows),
            "shown": len(shown),
            "args": args,
            "grouping": grouping,
            "who_options": overview_data.WHO,
            "grouping_options": overview_data.GROUPINGS,
            "options": overview_data.filter_options(conn),
            "extra_columns": [(key, label) for key, label in overview_data.EXTRA_COLUMNS if key in visible],
            "all_extra_columns": overview_data.EXTRA_COLUMNS,
            "name_columns": overview_data.NAME_COLUMNS,
            "custom_columns": [c for c in custom if f"custom:{c['id']}" in visible],
            "all_custom_columns": custom,
            "visible": visible,
            "colours_off": overview_data.colours_off(conn),
            "list_columns": overview_data.LIST_COLUMNS,
            "list_hidden": overview_data.list_hidden(conn),
            "query": request.query_string.decode(),
            "error": request.args.get("fout", ""),
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
    return render_page("students", student_count=context["table"]["total"],
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
    return render_page("evaluations")


@bp.get("/projecten")
def squads():
    """Spec 012, F1-F4 and the confirmation of F9."""
    conn = get_db()
    items = projects.all_projects(conn)
    loose = projects.without_project(conn)
    confirm_id = request.args.get("verwijder", "")
    return render_page("squads", items=items, without=loose,
                       active_count=sum(1 for p in items if p["students"]),
                       in_project=sum(len(p["students"]) for p in items),
                       confirm=next((p for p in items if str(p["id"]) == confirm_id), None),
                       added=request.args.get("toegevoegd", ""))


@bp.get("/kolommen")
def columns():
    return render_page("columns")


@bp.get("/semesters")
def semesters():
    """Spec 009, F1-F4 and the confirmation of F10."""
    conn = get_db()
    items = semester_data.all_semesters(conn)
    students, active = semester_data.summary(conn)
    confirm_id = request.args.get("verwijder", "")
    return render_page("semesters", items=items, student_total=students, active_count=active,
                       confirm=next((s for s in items if str(s["id"]) == confirm_id), None),
                       added=request.args.get("toegevoegd", ""))


@bp.get("/instellingen")
def settings():
    conn = get_db()
    connection = current_app.extensions["portflow"]
    start, end, saved = overview_data.semester_period(conn, date.today())
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
        always_visible=connection.always_visible,
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
    page = _add_students_page("Studenten toevoegen", "Kies hoe je nieuwe studenten wilt gaan volgen.")
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
    page = _add_students_page(
        "Uit Portflow kiezen", "Kies de studenten die hun portfolio al met je gedeeld hebben."
    )
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
    page = _add_students_page(
        "Uit Portflow kiezen", "Kies de studenten die hun portfolio al met je gedeeld hebben."
    )
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


def _role_page(role: str, title: str | None = None, intro: str | None = None) -> dict:
    page = dict(PAGES_BY_ENDPOINT[ROLE_PAGES[role]["endpoint"]])
    if title:
        page.update(title=title, intro=intro, label=title)
    return page


def _staff_list(role: str):
    conn = get_db()
    user = current_app.extensions["portflow"].user_name
    people = staff.people(conn, role, user)
    confirm_id = request.args.get("verwijder", "")
    return render_template(
        "staff.html", page=_role_page(role), active=ROLE_PAGES[role]["endpoint"], role=role,
        words=ROLE_PAGES[role], people=people,
        evaluations_total=sum(p["evaluations"] for p in people),
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
    page = _role_page(role, f"{words['Single']} toevoegen", f"Kies hoe je {words['plural']} wilt toevoegen.")
    return render_template("staff_add.html", page=page, active=words["endpoint"], role=role, kind=kind, words=words,
                           preset=staff.read_preset() if role == "guild_master" else [])


@bp.get("/<any(coaches, gildemeesters):kind>/toevoegen/portflow")
def staff_add_portflow(kind: str):
    """F5: every assessor in the fetched evaluations."""
    role = _role_from_path(kind)
    words = ROLE_PAGES[role]
    conn = get_db()
    page = _role_page(role, "Uit Portflow kiezen",
                      f"Kies beoordelaars uit de opgehaalde evaluaties; wie de meeste {words['skills']} beoordeelde, staat bovenaan.")
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
    page = _role_page(role, "Namen typen of plakken", "Typ of plak één naam per regel, precies zoals in Portflow.")
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
            return redirect(url_for("pages." + words["endpoint"]))
    chosen = {r[0] for r in conn.execute("SELECT guild_id FROM staff_guilds WHERE staff_id = ?", (staff_id,))}
    page = _role_page(role, f"{words['Single']} bewerken", person["name"])
    return render_template("staff_edit.html", page=page, active=words["endpoint"], role=role, kind=kind,
                           words=words, person=person, error=error,
                           first_name=request.form.get("voornaam", person["first_name"]),
                           last_name=request.form.get("achternaam", person["last_name"]),
                           guild_options=[dict(r) for r in conn.execute("SELECT id, code, name FROM guilds ORDER BY code")],
                           chosen=chosen)


@bp.post("/<any(coaches, gildemeesters):kind>/<int:staff_id>/verwijderen")
def staff_remove(kind: str, staff_id: int):
    """F8: removes only this role."""
    role = _role_from_path(kind)
    staff.remove_role(get_db(), staff_id, role)
    return redirect(url_for("pages." + ROLE_PAGES[role]["endpoint"]))


# Guilds (spec 006, F12-F19) ------------------------------------------------------------------

def _guild_page(title: str | None = None, intro: str | None = None) -> dict:
    page = dict(PAGES_BY_ENDPOINT["guilds"])
    if title:
        page.update(title=title, intro=intro, label=title)
    return page


@bp.get("/gildes", endpoint="guilds")
def guilds_list():
    conn = get_db()
    items = guilds.all_guilds(conn)
    confirm_id = request.args.get("verwijder", "")
    return render_template("guilds.html", page=_guild_page(), active="guilds", items=items,
                           confirm=next((g for g in items if str(g["id"]) == confirm_id), None),
                           added=request.args.get("toegevoegd", ""))


@bp.get("/gildes/toevoegen")
def guilds_add():
    """F14: make one yourself, or add the Open-ICT guilds."""
    return render_template("guilds_add.html", page=_guild_page("Gilde toevoegen", "Kies hoe je gildes wilt toevoegen."),
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
    intro = guild["name"] if guild else "Code, naam, beroepsrol en kleur van het gilde."
    return render_template("guild_form.html", page=_guild_page(title, intro), active="guilds", form=form, error=error)


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

def _semester_page(title: str | None = None, intro: str | None = None) -> dict:
    page = dict(PAGES_BY_ENDPOINT["semesters"])
    if title:
        page.update(title=title, intro=intro, label=title)
    return page


@bp.get("/semesters/toevoegen")
def semesters_add():
    """F5: make one yourself, or add the Open-ICT semesters."""
    return render_template("semesters_add.html", active="semesters", preset=semester_data.read_preset(),
                           page=_semester_page("Semester toevoegen", "Kies hoe je semesters wilt toevoegen."))


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
    intro = f"Semester {semester['number']}" if semester else "Het nummer en de eisen uit het toetsprogramma."
    return render_template("semester_form.html", active="semesters", form=form, error=error,
                           editing=bool(semester), page=_semester_page(title, intro))


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
    page = dict(PAGES_BY_ENDPOINT["students"], title="Student toevoegen", intro="Voeg één student toe en vul meteen zijn gegevens in.",
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
    page = dict(PAGES_BY_ENDPOINT["students"], title="Student bewerken", intro=student["name"],
                label=f"Student bewerken · {student['name']}")
    return render_template("student_edit.html", page=page, active="students", student=student, form=form,
                           error=error, options=student_edit.options(conn),
                           link_info=student_edit.portflow_link(conn, student), back=_list_path(),
                           link_choices=_link_choices(conn, student_id),
                           confirm=request.args.get("bevestig") == "verwijderen")


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


@bp.post("/studenten/<int:student_id>/verwijderen")
def student_delete(student_id: int):
    """F6: no longer follow this student."""
    conn = get_db()
    student = student_edit.find(conn, student_id)
    if student is None:
        abort(404)
    student_edit.delete(conn, student_id)
    return redirect(_with_message(_list_path(), f"{student['name']} wordt niet meer gevolgd."))


# Projecten (spec 012) -------------------------------------------------------------------------

def _project_page(title: str | None = None, intro: str | None = None) -> dict:
    page = dict(PAGES_BY_ENDPOINT["squads"])
    if title:
        page.update(title=title, intro=intro, label=title)
    return page


@bp.get("/projecten/nieuw")
def projects_add():
    """F5: add by hand, or add the Open-ICT projects."""
    return render_template("projects_add.html", active="squads", preset=projects.read_preset(),
                           page=_project_page("Nieuw project", "Kies hoe je projecten wilt toevoegen."))


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
    intro = project["full_name"] if project else "Nummer, naam, opdrachtgever en weergavenaam van het project."
    return render_template("project_form.html", active="squads", form=form, error=error, page=_project_page(title, intro))


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
