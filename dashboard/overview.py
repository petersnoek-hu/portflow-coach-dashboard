"""Data for the student overview (spec 001): rows, filters, groups and column choice.

The progress rules themselves live in progress.py; this module only gathers the
data from the database and arranges it for the template.
"""

import json
import sqlite3
from datetime import date

from . import db, progress, student_guilds
from .portflow_connection import initials
from .progress import normalize_name

S_SEMESTER_START = "semester_start"
S_SEMESTER_END = "semester_end"
S_VISIBLE_COLUMNS = "overview_visible_columns"
S_COLOURS_OFF = "overview_colours_off"      # spec 001, F23
S_LIST_HIDDEN = "list_hidden_columns"       # spec 010, F5
LIST_COLUMNS = [("semester", "Semester"), ("project", "Project"), ("track", "Invulling"), ("squadrole", "Rol"),
                ("guild", "Gilde"), ("coach", "Coach (voornaam)"), ("coachfull", "Coach (volledige naam)"),
                ("guildmaster", "Gildemeester (voornaam)"), ("guildmasterfull", "Gildemeester (volledige naam)"),
                ("portflow", "Portflow")]
LIST_DEFAULT_HIDDEN = ["coachfull", "guildmasterfull"]   # spec 006, F21
COLOUR_KINDS = ["n0", "n1", "n2", "pending"]

# Spec 006, F21: coach and guild master show the first name; the full name is a column of its own.
EXTRA_COLUMNS = [("coach", "Coach (voornaam)"), ("coach_full", "Coach (volledige naam)"),
                 ("guild_master", "Gildemeester (voornaam)"), ("guild_master_full", "Gildemeester (volledige naam)"),
                 ("track", "Invulling")]
NAME_COLUMNS = {"coach", "coach_full", "guild_master", "guild_master_full"}
DEFAULT_VISIBLE = ["guild_master"]      # F3

WHO = [("alle", "Alle gevolgde studenten"), ("coach", "Mijn coachstudenten"), ("gilde", "Mijn gildestudenten")]
GROUPINGS = [("squad", "Project"), ("none", "Niet groeperen"), ("track", "Invulling"), ("semester", "Semester"),
             ("guild", "Gilde")]   # "Beroepsrol" is the same as "Gilde" since spec 016
TRACKS = ["Open projecten", "Open innovatieproject", "Stage", "Minor", "Afstuderen"]
# The stored value stays short; dropdowns and filters show this label (docs/gegevensmodel.md#student).
TRACK_LABELS = {"Open projecten": "Open Projecten (jaar 2)",
                "Open innovatieproject": "Open Innovatieproject (semester 5, 6 of 7)",
                "Stage": "Stage (semester 5, 6 of 7)", "Minor": "Minor (semester 6)",
                "Afstuderen": "Afstuderen (semester 8)"}
UNASSIGNED = "Nog in te delen"


# Settings -------------------------------------------------------------------------------

def semester_period(conn: sqlite3.Connection, today: date) -> tuple[date, date, bool]:
    """(start, end, saved): the saved period, or the running semester (F22)."""
    values = {row["key"]: row["value"] for row in conn.execute(
        "SELECT key, value FROM settings WHERE key IN (?, ?)", (S_SEMESTER_START, S_SEMESTER_END))}
    try:
        return date.fromisoformat(values[S_SEMESTER_START]), date.fromisoformat(values[S_SEMESTER_END]), True
    except (KeyError, TypeError, ValueError):
        start, end = progress.default_semester_period(today)
        return start, end, False


def save_semester_period(conn: sqlite3.Connection, start: str, end: str) -> str | None:
    """F22: returns an error message (Dutch) or None."""
    try:
        start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError:
        return "Vul een geldige begin- en einddatum in."
    if start_date > end_date:
        return "De begindatum ligt na de einddatum. Pas een van de twee aan."
    with conn:
        for key, value in ((S_SEMESTER_START, start_date), (S_SEMESTER_END, end_date)):
            conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                         "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value.isoformat()))
    return None


def visible_columns(conn: sqlite3.Connection) -> list[str]:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (S_VISIBLE_COLUMNS,)).fetchone()
    if row and row["value"]:
        try:
            return list(json.loads(row["value"]))
        except ValueError:
            pass
    return DEFAULT_VISIBLE + [f"custom:{c['id']}" for c in custom_columns(conn)]


def colours_off(conn: sqlite3.Connection) -> list[str]:
    """F23: legend items whose colour the user switched off."""
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (S_COLOURS_OFF,)).fetchone()
    try:
        return [k for k in json.loads(row["value"]) if k in COLOUR_KINDS] if row and row["value"] else []
    except ValueError:
        return []


def save_colours_on(conn: sqlite3.Connection, on: list[str]) -> None:
    """F23: store the kinds that are NOT ticked."""
    with conn:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                     (S_COLOURS_OFF, json.dumps([k for k in COLOUR_KINDS if k not in on])))


def list_hidden(conn: sqlite3.Connection) -> list[str]:
    """Spec 010, F5: columns of the student list that the user switched off."""
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (S_LIST_HIDDEN,)).fetchone()
    try:
        data = json.loads(row["value"]) if row and row["value"] else {"hidden": LIST_DEFAULT_HIDDEN}
    except ValueError:
        data = {"hidden": LIST_DEFAULT_HIDDEN}
    # A plain list was saved before the full-name columns existed; those stay off (spec 006, F21).
    hidden = data.get("hidden", []) if isinstance(data, dict) else list(data) + LIST_DEFAULT_HIDDEN
    keys = {k for k, _ in LIST_COLUMNS}
    return [k for k in dict.fromkeys(hidden) if k in keys]


def save_list_visible(conn: sqlite3.Connection, visible: list[str]) -> None:
    with conn:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                     (S_LIST_HIDDEN, json.dumps({"hidden": [k for k, _ in LIST_COLUMNS if k not in visible]})))


def save_visible_columns(conn: sqlite3.Connection, keys: list[str]) -> None:
    allowed = {k for k, _ in EXTRA_COLUMNS} | {f"custom:{c['id']}" for c in custom_columns(conn)}
    with conn:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                     (S_VISIBLE_COLUMNS, json.dumps([k for k in keys if k in allowed])))


def custom_columns(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM custom_columns ORDER BY position, id")]


def save_custom_value(conn: sqlite3.Connection, student_id: int, column_id: int, raw: str) -> str | None:
    """F8: percentage 0-100 (whole number) or free text; empty clears. Returns an error or None."""
    column = conn.execute("SELECT * FROM custom_columns WHERE id = ?", (column_id,)).fetchone()
    if column is None or not conn.execute("SELECT 1 FROM students WHERE id = ?", (student_id,)).fetchone():
        return "Deze kolom of student bestaat niet (meer)."
    value = raw.strip()
    if column["type"] == "percentage" and value:
        value = value.rstrip("%").strip()
        if not value.isdigit() or not 0 <= int(value) <= 100:
            return f"{column['name']}: vul een heel getal van 0 tot en met 100 in."
        value = str(int(value))
    with conn:
        if value:
            conn.execute("INSERT INTO custom_values (student_id, column_id, value) VALUES (?, ?, ?) "
                         "ON CONFLICT(student_id, column_id) DO UPDATE SET value = excluded.value",
                         (student_id, column_id, value))
        else:
            conn.execute("DELETE FROM custom_values WHERE student_id = ? AND column_id = ?", (student_id, column_id))
    return None


# Rows -----------------------------------------------------------------------------------

STUDENT_SQL = """
SELECT s.*, sq.name AS squad_name, sq.full_name AS squad_full_name, sq.display_name AS squad_display,
       c.name AS coach_name, c.first_name AS coach_first
FROM students s
LEFT JOIN squads sq ON sq.id = s.squad_id
LEFT JOIN staff c ON c.id = s.coach_id
ORDER BY s.name COLLATE NOCASE
"""


def student_rows(conn: sqlite3.Connection, today: date) -> list[dict]:
    start, end, _ = semester_period(conn, today)
    known = {r[0] for r in conn.execute("SELECT name FROM staff WHERE is_coach = 1 OR is_guild_master = 1")}
    evaluations: dict[int, list[dict]] = {}
    for row in conn.execute("SELECT * FROM evaluations"):
        evaluations.setdefault(row["student_id"], []).append(dict(row))
    guilds_of = student_guilds.by_student(conn)   # spec 016
    values: dict[int, dict[int, str]] = {}
    for row in conn.execute("SELECT * FROM custom_values"):
        values.setdefault(row["student_id"], {})[row["column_id"]] = row["value"]

    rows = []
    for s in conn.execute(STUDENT_SQL):
        result = progress.student_progress(
            evaluations.get(s["id"], []), semester=s["semester"], known_assessors=known,
            period=(start, end), start_date=s["start_date"], has_access=bool(s["has_access"]),
        )
        sub = f"Sem {s['semester']}" if s["semester"] else ""   # the project is in the group header (spec 001, F2)
        rows.append({
            "id": s["id"],
            "name": s["name"],
            "initials": initials(s["name"]),
            "sub": sub,
            "semester": s["semester"],
            "squad_id": s["squad_id"],
            # Spec 012, F12: the overviews show the display name instead of the project name.
            "squad": s["squad_display"] or s["squad_name"],
            "squad_full_name": s["squad_display"] or s["squad_full_name"],
            "squad_sort": s["squad_full_name"] or "",
            "squad_role": s["squad_role"],
            "track": s["track"],
            "guilds": guilds_of.get(s["id"], []),
            "guild_codes": ", ".join(g["code"] for g in guilds_of.get(s["id"], [])),
            "guild_names": ", ".join(g["guild_name"] or g["name"] for g in guilds_of.get(s["id"], [])),
            "guild_masters": [g["guild_master"] for g in guilds_of.get(s["id"], []) if g["guild_master"]],
            # Spec 006, F21: the columns show first names; the full names have their own columns.
            "guild_master": ", ".join(dict.fromkeys(g["guild_master_first"] for g in guilds_of.get(s["id"], [])
                                                     if g["guild_master"])) or None,
            "guild_master_full": ", ".join(dict.fromkeys(g["guild_master"] for g in guilds_of.get(s["id"], [])
                                                          if g["guild_master"])) or None,
            "coach": s["coach_first"],
            "coach_full": s["coach_name"],
            "has_access": bool(s["has_access"]),
            "linked": s["portflow_user_id"] is not None,
            "unassigned": s["semester"] is None or not guilds_of.get(s["id"]),   # spec 016, F2
            "progress": result,
            "custom": values.get(s["id"], {}),
        })
    return rows


def counted_evaluations_by_assessor(conn: sqlite3.Connection, today: date | None = None) -> dict[str, int]:
    """Counted evaluations per (normalised) assessor name, for the staff cards (spec 006, F2)."""
    counts: dict[str, int] = {}
    for row in student_rows(conn, today or date.today()):
        for cell in row["progress"].cells.values():
            for evaluation in cell.evaluations:
                key = normalize_name(evaluation.assessor)
                counts[key] = counts.get(key, 0) + 1
    return counts


# Filters (F13-F15) -------------------------------------------------------------------------

def apply_filters(rows: list[dict], args: dict, user_name: str | None) -> list[dict]:
    who = args.get("wie", "alle")
    me = normalize_name(user_name)
    result = []
    for row in rows:
        if who == "coach" and (not me or normalize_name(row["coach_full"]) != me):
            continue
        # Spec 016, F6: the user is guild master at one of the student's guilds.
        if who == "gilde" and (not me or me not in {normalize_name(n) for n in row["guild_masters"]}):
            continue
        if args.get("semester") and str(row["semester"] or "") != args["semester"]:
            continue
        if args.get("invulling") and (row["track"] or "") != args["invulling"]:
            continue
        if args.get("project") and str(row["squad_id"] or "") != args["project"]:
            continue
        if args.get("rol") and args["rol"] not in {str(g["role_id"]) for g in row["guilds"]}:
            continue
        if args.get("aansporen") and not row["progress"].signals:
            continue
        result.append(row)
    return result


# Groups (F16) --------------------------------------------------------------------------------

def group_rows(rows: list[dict], grouping: str) -> list[dict]:
    """Groups with a header; "Zonder …" and "Nog in te delen" come last."""
    if grouping == "none":  # F16: one list without group headers, by name
        return [{"title": None, "full_name": "", "colour": "", "rows": sorted(rows, key=lambda r: r["name"].casefold())}] if rows else []
    groups: dict[tuple, dict] = {}

    def put(key, title, full_name, colour, row):
        group = groups.setdefault(key, {"title": title, "full_name": full_name, "colour": colour, "rows": []})
        group["rows"].append(row)

    for row in rows:
        if row["unassigned"]:
            put((3, ""), UNASSIGNED, "Semester of gilde nog invullen", "#B9BFBB", row)
        elif grouping == "track":
            if row["track"]:
                put((1, TRACKS.index(row["track"]) if row["track"] in TRACKS else 99, row["track"]),
                    row["track"], "", "#909DB9", row)
            else:
                put((2, ""), "Zonder invulling", "", "#B9BFBB", row)
        elif grouping == "semester":
            put((1, row["semester"]), f"Semester {row['semester']}", "", "#5E8C74", row)
        elif grouping == "guild":  # spec 016, F6: a student with more guilds is in every group
            for guild in row["guilds"]:
                put((1, guild["code"]), guild["code"], guild["guild_name"] or guild["name"],
                    guild["guild_color"] or "#909DB9", row)
        else:  # squad
            if row["squad_id"]:
                put((1, row["squad_sort"].casefold()), row["squad"], "", "#909DB9", row)   # spec 012: no project colours
            else:
                put((2, ""), "Zonder project", "", "#B9BFBB", row)
    return [groups[key] for key in sorted(groups, key=lambda k: tuple(str(p) for p in k))]


def filter_options(conn: sqlite3.Connection) -> dict:
    return {
        # F12: the filter shows the display name (in the order of the project numbers)
        "squads": [dict(r, full_name=r["display_name"] or r["full_name"]) for r in conn.execute(
            "SELECT id, name, full_name, display_name FROM squads ORDER BY full_name")],
        "roles": [dict(r) for r in conn.execute("SELECT id, code, name FROM professional_roles ORDER BY code")],
        "tracks": [(t, TRACK_LABELS[t]) for t in TRACKS],
        "semesters": list(range(1, 9)),
    }


def user_name(database: str) -> str | None:
    return db.get_setting(database, "portflow_user_name")
