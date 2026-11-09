"""Pages of the dashboard (spec 002: the shell with placeholder pages)."""

from datetime import datetime

from flask import Blueprint, current_app, redirect, render_template, request, url_for

from . import demo
from .db import get_db

bp = Blueprint("pages", __name__)

# Sidebar menu and page headers (spec 002, F5 and F8). Text is Dutch: it is shown to the user.
PAGES = [
    {"endpoint": "overview", "path": "/", "label": "Overzicht", "icon": "home",
     "eyebrow": None, "title": None, "intro": "Dit vraagt vandaag je aandacht.",
     "placeholder": "Hier komen de signaalkaarten, het studentenoverzicht en de evaluaties die op je wachten."},
    {"endpoint": "students", "path": "/studenten", "label": "Studenten", "icon": "users",
     "eyebrow": "Studievoortgang", "title": "Studenten",
     "intro": "Alle studenten die je volgt, met hun voortgang per vaardigheid.",
     "placeholder": "Hier komt het studentenoverzicht met de voortgang per vaardigheid."},
    {"endpoint": "evaluations", "path": "/evaluaties", "label": "Evaluaties", "icon": "clipboard",
     "eyebrow": "Studievoortgang", "title": "Evaluaties",
     "intro": "Evaluatieverzoeken die op jouw beoordeling wachten.",
     "placeholder": "Hier komen de evaluatieverzoeken die op jouw beoordeling wachten."},
    {"endpoint": "squads", "path": "/projecten", "label": "Projecten", "icon": "folder",
     "eyebrow": "Beheer", "title": "Projecten",
     "intro": "Beheer de projectgroepen waarin je studenten zijn ingedeeld.",
     "placeholder": "Hier beheer je straks de squads en wie erin zitten."},
    {"endpoint": "columns", "path": "/kolommen", "label": "Kolommen", "icon": "columns",
     "eyebrow": "Curriculum", "title": "Kolommen",
     "intro": "De bouwstenen van je studentenoverzicht, op één plek beheerd.",
     "placeholder": "Hier beheer je straks de kolommen van het studentenoverzicht."},
    {"endpoint": "professional_roles", "path": "/beroepsrollen", "label": "Beroepsrollen", "icon": "briefcase",
     "eyebrow": "Opleidingsprofiel", "title": "Beroepsrollen",
     "intro": "Beheer rollen en zie direct welke studenten primair of secundair gekoppeld zijn.",
     "placeholder": "Hier beheer je straks de beroepsrollen en zie je wie eraan gekoppeld is."},
    {"endpoint": "semesters", "path": "/semesters", "label": "Semesters", "icon": "calendar",
     "eyebrow": "Studievoortgang", "title": "Semesters",
     "intro": "Bekijk de bezetting van semester 1 tot en met 8 en verplaats studenten.",
     "placeholder": "Hier zie je straks per semester welke studenten erin zitten."},
    {"endpoint": "settings", "path": "/instellingen", "label": "Instellingen", "icon": "sliders",
     "eyebrow": "Beheer", "title": "Instellingen",
     "intro": "Je gegevens, de semesterperiode en de koppeling met Portflow.",
     "placeholder": None},
]
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


@bp.app_context_processor
def shell_context():
    """Values every page needs for the sidebar, top bar and demo banner."""
    return {
        "pages": PAGES,
        "demo_active": demo.has_demo_data(get_db()),
        "portflow": current_app.extensions["portflow"].status(),
        "portflow_open": request.args.get("portflow") == "open",
    }


def render_page(endpoint: str, **context):
    page = dict(PAGES_BY_ENDPOINT[endpoint])
    if endpoint == "overview":
        now = datetime.now()
        page["eyebrow"], page["title"] = dutch_date(now), greeting(now)
    template = "settings.html" if endpoint == "settings" else "page.html"
    return render_template(template, page=page, active=endpoint, **context)


@bp.get("/")
def overview():
    return render_page("overview")


@bp.get("/studenten")
def students():
    return render_page("students")


@bp.get("/evaluaties")
def evaluations():
    return render_page("evaluations")


@bp.get("/projecten")
def squads():
    return render_page("squads")


@bp.get("/kolommen")
def columns():
    return render_page("columns")


@bp.get("/beroepsrollen")
def professional_roles():
    return render_page("professional_roles")


@bp.get("/semesters")
def semesters():
    return render_page("semesters")


@bp.get("/instellingen")
def settings():
    conn = get_db()
    connection = current_app.extensions["portflow"]
    return render_page(
        "settings",
        demo_counts=demo.demo_counts(conn),
        confirm_remove=request.args.get("bevestig") == "demodata-verwijderen",
        confirm_disconnect=request.args.get("bevestig") == "verbinding-verbreken",
        canvas_url=connection.canvas_url,
        always_visible=connection.always_visible,
    )


@bp.post("/instellingen/demodata/laden")
def load_demo_data():
    demo.load_demo_data(get_db())
    return redirect(url_for("pages.settings"))


@bp.post("/instellingen/demodata/verwijderen")
def remove_demo_data():
    demo.remove_demo_data(get_db())
    return redirect(url_for("pages.settings"))
