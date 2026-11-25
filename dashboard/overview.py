"""Data for the student overview (spec 001): rows, filters, groups and column choice.

The progress rules themselves live in progress.py; this module only gathers the
data from the database and arranges it for the template.
"""

import json
import sqlite3
from datetime import date

from . import choices, db, progress, student_guilds
from .portflow_connection import initials
from .progress import normalize_name

S_SEMESTER_START = "semester_start"
S_SEMESTER_END = "semester_end"
S_VISIBLE_COLUMNS = "overview_visible_columns"
S_COLOURS_OFF = "overview_colours_off"      # spec 001, F23
S_LIST_HIDDEN = "list_hidden_columns"       # spec 010, F5
LIST_COLUMNS = [("semester", "Semester"), ("project", "Project"), ("track", "Invulling"), ("squadrole", "Rol"),
                ("guild", "Gilde"), ("coach", "Coach"), ("coachfull", "Coach (volledig)"),
                ("guildmaster", "Gildemeester"), ("guildmasterfull", "Gildemeester (volledig)"),
                ("portflow", "Portflow")]
LIST_DEFAULT_HIDDEN = ["coachfull", "guildmasterfull"]   # spec 006, F21
COLOUR_KINDS = ["n0", "n1", "n2", "pending", "pm1", "pm2", "pm3", "pm4"]
# Spec 044, F1: what the colours of the level labels mean; the legend items (F3) per scheme.
S_SCHEME = "level_colour_scheme"
SCHEMES = {
    "none": ("Geen kleuren", []),
    "blue": ("Geen kleuren, alleen blauw voor ingediend", ["pending"]),
    "openict": ("Open-ICT: aantal evaluaties", ["n0", "n1", "n2", "pending"]),
    "hcai": ("HCAI: peilmomenten", ["pm1", "pm2", "pm3", "pm4", "pending"]),
}
DEFAULT_SCHEME = "openict"


def level_scheme(conn: sqlite3.Connection) -> str:
    """Spec 044, F1: the chosen colour scheme (Open-ICT when nothing was chosen)."""
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (S_SCHEME,)).fetchone()
    return row["value"] if row and row["value"] in SCHEMES else DEFAULT_SCHEME


def save_level_scheme(conn: sqlite3.Connection, scheme: str) -> bool:
    if scheme not in SCHEMES:
        return False
    with conn:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                     (S_SCHEME, scheme))
    return True

# Spec 006, F21: coach and guild master show the first name; the full name is a column of its own.
EXTRA_COLUMNS = [("coach", "Coach"), ("coach_full", "Coach (volledig)"),
                 ("guild_master", "Gildemeester"), ("guild_master_full", "Gildemeester (volledig)"),
                 ("track", "Invulling")]
NAME_COLUMNS = {"coach", "coach_full", "guild_master", "guild_master_full"}
DEFAULT_VISIBLE = ["guild_master"]      # F3

# Spec 019, F6: "zichtbaar" is the default; hiding (F4, F5) only plays a part in "zichtbaar" and "alle".
# "iedereen" filters nothing: hidden students are ordinary rows there.
WHO = [("iedereen", "Alle studenten"), ("zichtbaar", "Alle studenten die ik niet heb verborgen"), ("coach", "Mijn coachstudenten"),
       ("gilde", "Studenten van wie ik gildemeester ben"), ("alle", "Alle studenten van wie ik het portfolio kan zien")]
HIDDEN_ONLY = ("verborgen", "Studenten die ik heb verborgen")   # spec 019, F6: only on Beheer › Studenten
GUILD_PREFIX = "gilde-"   # spec 019, F6: "gilde-<id>", all students in one of the user's guilds
WHO_DEFAULT = "zichtbaar"
GROUPINGS = [("none", "Niet groeperen"), ("squad", "Project"), ("track", "Invulling"), ("semester", "Semester"),
             ("guild", "Gilde")]   # "Beroepsrol" is the same as "Gilde" since spec 016
# Invulling and Rol in de squad are choice lists since spec 024 (choices.py); the cells show the
# code, dropdowns and filters the description.
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


def _column_choices(conn: sqlite3.Connection) -> dict[str, bool]:
    """The columns the user switched on or off themself (F3). Before spec 019 the whole list was
    saved at once; such a list counts as a choice for every column."""
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (S_VISIBLE_COLUMNS,)).fetchone()
    try:
        data = json.loads(row["value"]) if row and row["value"] else {}
    except ValueError:
        data = {}
    if isinstance(data, list):
        keys = [k for k, _ in EXTRA_COLUMNS] + [f"custom:{c['id']}" for c in custom_columns(conn)]
        return {key: key in data for key in keys}
    return {key: bool(on) for key, on in data.items()} if isinstance(data, dict) else {}


def filled_extra_columns(conn: sqlite3.Connection) -> set[str]:
    """Spec 019, F9: the extra columns that are filled for at least one student."""
    filled = set()
    if conn.execute("SELECT 1 FROM students WHERE coach_id IS NOT NULL LIMIT 1").fetchone():
        filled |= {"coach", "coach_full"}
    if conn.execute("SELECT 1 FROM student_guilds WHERE guild_master_id IS NOT NULL LIMIT 1").fetchone():
        filled |= {"guild_master", "guild_master_full"}
    if conn.execute("SELECT 1 FROM students WHERE track_id IS NOT NULL LIMIT 1").fetchone():
        filled.add("track")
    return filled


def visible_columns(conn: sqlite3.Connection) -> list[str]:
    """F3 and spec 019, F9: the user's own choice per column; otherwise the default, where an
    extra column that is empty for every student is not shown. Custom columns show by default."""
    choices = _column_choices(conn)
    filled = filled_extra_columns(conn)
    result = []
    for key, _ in EXTRA_COLUMNS:
        if choices.get(key, key in DEFAULT_VISIBLE and key in filled):
            result.append(key)
    for c in custom_columns(conn):
        key = f"custom:{c['id']}"
        if choices.get(key, True):
            result.append(key)
    return result


def colours_off(conn: sqlite3.Connection) -> list[str]:
    """F23: legend items whose colour the user switched off."""
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (S_COLOURS_OFF,)).fetchone()
    try:
        return [k for k in json.loads(row["value"]) if k in COLOUR_KINDS] if row and row["value"] else []
    except ValueError:
        return []


def save_colours_on(conn: sqlite3.Connection, on: list[str], kinds: list[str] | None = None) -> None:
    """F23: store the kinds that are NOT ticked. Spec 044, F3: only the legend items of the current
    scheme (`kinds`) change; the choice for the other schemes is kept."""
    kinds = kinds if kinds is not None else COLOUR_KINDS
    keep = [k for k in colours_off(conn) if k not in kinds]
    with conn:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                     (S_COLOURS_OFF, json.dumps(keep + [k for k in kinds if k not in on])))


def list_columns(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    """Spec 010, F5 and spec 024, G1: the fixed columns of the student list, then the custom columns."""
    return LIST_COLUMNS + [(f"custom:{c['id']}", c["name"]) for c in custom_columns(conn)]


def list_hidden(conn: sqlite3.Connection) -> list[str]:
    """Spec 010, F5: columns of the student list that the user switched off."""
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (S_LIST_HIDDEN,)).fetchone()
    try:
        data = json.loads(row["value"]) if row and row["value"] else {"hidden": LIST_DEFAULT_HIDDEN}
    except ValueError:
        data = {"hidden": LIST_DEFAULT_HIDDEN}
    # A plain list was saved before the full-name columns existed; those stay off (spec 006, F21).
    hidden = data.get("hidden", []) if isinstance(data, dict) else list(data) + LIST_DEFAULT_HIDDEN
    keys = {k for k, _ in list_columns(conn)}
    return [k for k in dict.fromkeys(hidden) if k in keys]


def save_list_visible(conn: sqlite3.Connection, visible: list[str]) -> None:
    with conn:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                     (S_LIST_HIDDEN, json.dumps({"hidden": [k for k, _ in list_columns(conn) if k not in visible]})))


def save_visible_columns(conn: sqlite3.Connection, keys: list[str]) -> None:
    """F3: only the columns the user changed become a choice of their own (spec 019, F9)."""
    allowed = [k for k, _ in EXTRA_COLUMNS] + [f"custom:{c['id']}" for c in custom_columns(conn)]
    shown, choices = set(visible_columns(conn)), _column_choices(conn)
    for key in allowed:
        if (key in keys) != (key in shown):
            choices[key] = key in keys
    with conn:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                     (S_VISIBLE_COLUMNS, json.dumps({k: v for k, v in choices.items() if k in allowed})))


def set_hidden(conn: sqlite3.Connection, student_id: int, hidden: bool) -> bool:
    """Spec 019, F4, F5: hide a student in the overview, or show again. False if not found."""
    with conn:
        return conn.execute("UPDATE students SET is_hidden = ? WHERE id = ?", (int(hidden), student_id)).rowcount > 0


def default_grouping(conn: sqlite3.Connection) -> str:
    """Spec 019, F8: as long as no student has a project, semester or guild, do not group."""
    assigned = conn.execute("SELECT 1 FROM students WHERE squad_id IS NOT NULL OR semester IS NOT NULL "
                            "UNION SELECT 1 FROM student_guilds LIMIT 1").fetchone()
    return "squad" if assigned else "none"


def custom_columns(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM custom_columns ORDER BY position, id")]


def check_custom_value(conn: sqlite3.Connection, column, raw: str) -> tuple[str, str | None]:
    """F8 (spec 024, G1; spec 026, F3): the value to store ('' clears) and an error (Dutch) or None.
    The one check for the table and the form Student bewerken."""
    value = raw.strip()
    if column["type"] == "choice" and value:   # spec 024, G1: an item of the column's own list
        if not value.isdigit() or not any(i["id"] == int(value) for i in choices.column_items(conn, column["id"])):
            return "", f"{column['name']}: kies een waarde uit de lijst."
    if column["type"] == "percentage" and value:
        value = value.rstrip("%").strip()
        if not value.isdigit() or not 0 <= int(value) <= 100:
            return "", f"{column['name']}: vul een heel getal van 0 tot en met 100 in."
        value = str(int(value))
    return value, None


def set_custom_values(conn: sqlite3.Connection, student_id: int, values: dict[int, str]) -> None:
    """Store checked values (column id -> value; '' clears). The caller runs the transaction."""
    for column_id, value in values.items():
        if value:
            conn.execute("INSERT INTO custom_values (student_id, column_id, value) VALUES (?, ?, ?) "
                         "ON CONFLICT(student_id, column_id) DO UPDATE SET value = excluded.value",
                         (student_id, column_id, value))
        else:
            conn.execute("DELETE FROM custom_values WHERE student_id = ? AND column_id = ?", (student_id, column_id))


def save_custom_value(conn: sqlite3.Connection, student_id: int, column_id: int, raw: str) -> str | None:
    """F8: percentage 0-100 (whole number), free text or a choice; empty clears. Returns an error or None."""
    column = conn.execute("SELECT * FROM custom_columns WHERE id = ?", (column_id,)).fetchone()
    if column is None or not conn.execute("SELECT 1 FROM students WHERE id = ?", (student_id,)).fetchone():
        return "Deze kolom of student bestaat niet (meer)."
    value, error = check_custom_value(conn, column, raw)
    if error:
        return error
    with conn:
        set_custom_values(conn, student_id, {column_id: value})
    return None


# Rows -----------------------------------------------------------------------------------

STUDENT_SQL = """
SELECT s.*, sq.name AS squad_name, sq.full_name AS squad_full_name, sq.display_name AS squad_display,
       c.name AS coach_name, c.first_name AS coach_first,
       t.code AS track, t.position AS track_position, r.code AS squad_role, r.description AS squad_role_description
FROM students s
LEFT JOIN squads sq ON sq.id = s.squad_id
LEFT JOIN staff c ON c.id = s.coach_id
LEFT JOIN choice_items t ON t.id = s.track_id
LEFT JOIN choice_items r ON r.id = s.squad_role_id
ORDER BY s.name COLLATE NOCASE
"""


def student_rows(conn: sqlite3.Connection, today: date) -> list[dict]:
    start, end, _ = semester_period(conn, today)
    excluded = {r[0] for r in conn.execute("SELECT name_key FROM excluded_assessors")}   # spec 019, F12
    evaluations: dict[int, list[dict]] = {}
    for row in conn.execute("SELECT * FROM evaluations"):
        evaluations.setdefault(row["student_id"], []).append(dict(row))
    guilds_of = student_guilds.by_student(conn)   # spec 016
    values: dict[int, dict[int, str]] = {}
    for row in conn.execute("SELECT * FROM custom_values"):
        values.setdefault(row["student_id"], {})[row["column_id"]] = row["value"]
    # Spec 024: the cells of a choice column hold an item id; show its code.
    item_codes = {str(r["id"]): r["code"] for r in conn.execute(
        "SELECT i.id, i.code FROM choice_items i JOIN choice_lists l ON l.id = i.list_id WHERE l.kind = 'column'")}
    choice_columns = {r[0] for r in conn.execute("SELECT id FROM custom_columns WHERE type = 'choice'")}

    rows = []
    for s in conn.execute(STUDENT_SQL):
        result = progress.student_progress(
            evaluations.get(s["id"], []), semester=s["semester"], excluded_assessors=excluded,
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
            "squad_role_id": s["squad_role_id"],
            "squad_role_description": s["squad_role_description"],
            "track": s["track"],
            "track_id": s["track_id"],
            "track_position": s["track_position"],
            # Spec 025, F4: a student on internship without a project shows "(Stage)" at Project.
            "stage_without_project": s["squad_id"] is None and (s["track"] or "").casefold() == choices.STAGE.casefold(),
            "guilds": guilds_of.get(s["id"], []),
            "guild_ids": [g["guild_id"] for g in guilds_of.get(s["id"], [])],
            "guild_codes": ", ".join(g["code"] for g in guilds_of.get(s["id"], [])),
            "guild_names": ", ".join(g["guild_name"] for g in guilds_of.get(s["id"], [])),
            "guild_masters": [g["guild_master"] for g in guilds_of.get(s["id"], []) if g["guild_master"]],
            # Spec 006, F21: the columns show first names; the full names have their own columns.
            "guild_master": ", ".join(dict.fromkeys(g["guild_master_first"] for g in guilds_of.get(s["id"], [])
                                                     if g["guild_master"])) or None,
            "guild_master_full": ", ".join(dict.fromkeys(g["guild_master"] for g in guilds_of.get(s["id"], [])
                                                          if g["guild_master"])) or None,
            "coach": s["coach_first"],
            "coach_full": s["coach_name"],
            "has_access": bool(s["has_access"]),
            "hidden": bool(s["is_hidden"]),   # spec 019, F4
            "linked": s["portflow_user_id"] is not None,
            "unassigned": s["semester"] is None or not guilds_of.get(s["id"]),   # spec 016, F2
            "progress": result,
            "custom": values.get(s["id"], {}),
            "custom_text": {cid: (item_codes.get(v, "") if cid in choice_columns else v)
                            for cid, v in values.get(s["id"], {}).items()},
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

def _own_guilds(conn: sqlite3.Connection, user_name: str | None) -> list[sqlite3.Row]:
    """Spec 019, F6: the guilds at the user's own name in the list of guild masters."""
    me = normalize_name(user_name)
    if not me:
        return []
    staff_ids = [r["id"] for r in conn.execute("SELECT id, name FROM staff WHERE is_guild_master = 1")
                 if normalize_name(r["name"]) == me]
    if not staff_ids:
        return []
    marks = ",".join("?" * len(staff_ids))
    return conn.execute(f"SELECT DISTINCT g.id, g.code, g.name FROM guilds g JOIN staff_guilds sg ON sg.guild_id = g.id "
                        f"WHERE sg.staff_id IN ({marks}) ORDER BY g.code", staff_ids).fetchall()


def who_options(conn: sqlite3.Connection, user_name: str | None, page: str | None = None) -> list[tuple[str, str]]:
    """The choices of the filter on who (spec 019, F6), with a line per guild of the user after
    "Studenten van wie ik gildemeester ben", and on Beheer › Studenten the hidden students last."""
    result = []
    for value, label in WHO:
        result.append((value, label))
        if value == "gilde":
            result += [(f"{GUILD_PREFIX}{g['id']}", f"Alle studenten in mijn {g['name']}") for g in _own_guilds(conn, user_name)]
    if page == "students":
        result.append(HIDDEN_ONLY)
    return result


def apply_filters(rows: list[dict], args: dict, user_name: str | None) -> list[dict]:
    who = args.get("wie") or WHO_DEFAULT
    me = normalize_name(user_name)
    result = []
    for row in rows:
        if who == "zichtbaar" and row["hidden"]:   # spec 019, F6
            continue
        if who == HIDDEN_ONLY[0] and not row["hidden"]:
            continue
        if who == "coach" and (not me or normalize_name(row["coach_full"]) != me):
            continue
        # Spec 016, F6: the user is guild master at one of the student's guilds.
        if who == "gilde" and (not me or me not in {normalize_name(n) for n in row["guild_masters"]}):
            continue
        if who.startswith(GUILD_PREFIX) and who[len(GUILD_PREFIX):] not in {str(g["guild_id"]) for g in row["guilds"]}:
            continue
        if args.get("semester") and str(row["semester"] or "") != args["semester"]:
            continue
        if args.get("invulling") and str(row["track_id"] or "") != args["invulling"]:
            continue
        # Spec 024, G2: a filter per choice column ("kolom<id>").
        if any(value and key.startswith("kolom") and row["custom"].get(int(key[5:]), "") != value
               for key, value in args.items()):
            continue
        if args.get("project") and str(row["squad_id"] or "") != args["project"]:
            continue
        if args.get("gilde") and args["gilde"] not in {str(g["guild_id"]) for g in row["guilds"]}:   # spec 018, F7
            continue
        if args.get("aansporen") and not row["progress"].signals:
            continue
        result.append(row)
    return result


# Groups (F16) --------------------------------------------------------------------------------

def group_rows(rows: list[dict], grouping: str, column_items: dict[str, dict] | None = None) -> list[dict]:
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
        elif grouping == "track":   # spec 024, L3: in the order of the list
            if row["track"]:
                put((1, f"{row['track_position']:06d}", row["track"]), row["track"], "", "#909DB9", row)
            else:
                put((2, ""), "Zonder invulling", "", "#B9BFBB", row)
        elif grouping.startswith("kolom"):   # spec 024, G3
            item = (column_items or {}).get(row["custom"].get(int(grouping[5:]), ""))
            if item:
                put((1, f"{item['position']:06d}", item["id"]), item["code"], item["description"], "#909DB9", row)
            else:
                put((2, ""), "Niet ingevuld", "", "#B9BFBB", row)
        elif grouping == "semester":
            put((1, row["semester"]), f"Semester {row['semester']}", "", "#5E8C74", row)
        elif grouping == "guild":  # spec 016, F6: a student with more guilds is in every group
            for guild in row["guilds"]:
                put((1, guild["code"]), guild["code"], guild["guild_name"],
                    guild["guild_color"] or "#909DB9", row)
        else:  # squad
            if row["squad_id"]:
                put((1, row["squad_sort"].casefold()), row["squad"], "", "#909DB9", row)   # spec 012: no project colours
            elif row["stage_without_project"]:   # spec 025, F5: after the projects, before "Zonder project"
                put(("1z", ""), "(Stage)", "", "#B9BFBB", row)
            else:
                put((2, ""), "Zonder project", "", "#B9BFBB", row)
    return [groups[key] for key in sorted(groups, key=lambda k: tuple(str(p) for p in k))]


def filter_options(conn: sqlite3.Connection) -> dict:
    return {
        # F12: the filter shows the display name (in the order of the project numbers)
        "squads": [dict(r, full_name=r["display_name"] or r["full_name"]) for r in conn.execute(
            "SELECT id, name, full_name, display_name FROM squads ORDER BY full_name")],
        "guilds": [dict(r) for r in conn.execute("SELECT id, code, name FROM guilds ORDER BY code")],
        "tracks": [(str(i["id"]), i["label"]) for i in choices.kind_items(conn, choices.TRACK)],   # spec 024
        "semesters": list(range(1, 9)),
        # Spec 024, G2: one filter per choice column.
        "choice_columns": [{"key": f"kolom{c['id']}", "name": c["name"],
                            "items": choices.column_items(conn, c["id"])}
                           for c in custom_columns(conn) if c["type"] == "choice"],
    }


def grouping_options(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    """F16 and spec 024, G3: the fixed groupings, then one per choice column."""
    return GROUPINGS + [(f"kolom{c['id']}", c["name"]) for c in custom_columns(conn) if c["type"] == "choice"]


def column_items(conn: sqlite3.Connection) -> dict[str, dict]:
    """Spec 024, G3: the items of all choice columns by id (as stored in custom_values)."""
    return {str(r["id"]): dict(r) for r in conn.execute(
        "SELECT i.id, i.code, i.description, i.position FROM choice_items i "
        "JOIN choice_lists l ON l.id = i.list_id WHERE l.kind = 'column'")}


# Remembered filters (spec 023) ------------------------------------------------------------

FILTER_KEYS = ("wie", "semester", "invulling", "project", "gilde", "aansporen", "groep")
FILTER_PAGES = {"overview": "filters_overview", "students": "filters_students"}   # F2


def filter_keys(conn: sqlite3.Connection) -> tuple[str, ...]:
    """The fixed filters plus one per choice column (spec 024, G2)."""
    return FILTER_KEYS + tuple(f"kolom{c['id']}" for c in custom_columns(conn) if c["type"] == "choice")


def saved_filters(conn: sqlite3.Connection, page: str) -> dict[str, str]:
    """F1: the remembered choices of a page; unknown or broken values are ignored."""
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (FILTER_PAGES[page],)).fetchone()
    try:
        data = json.loads(row[0]) if row and row[0] else {}
    except ValueError:
        return {}
    keys = filter_keys(conn)
    return {k: str(v) for k, v in data.items() if k in keys} if isinstance(data, dict) else {}


def save_filters(conn: sqlite3.Connection, page: str, chosen: dict[str, str], default_grouping: str) -> None:
    """F1, F6: only the choices that differ from the standard are stored."""
    standard = {"wie": WHO_DEFAULT, "groep": default_grouping}
    keys = filter_keys(conn)
    stored = {k: v for k, v in chosen.items() if k in keys and v and v != standard.get(k, "")}
    with conn:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (FILTER_PAGES[page], json.dumps(stored)))


# Spec 028: the filters can be folded away; the state is kept per page, compact by default (F5).
COMPACT_PAGES = {"overview": "filters_compact_overview", "students": "filters_compact_students"}


def filters_compact(conn: sqlite3.Connection, page: str) -> bool:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (COMPACT_PAGES[page],)).fetchone()
    return not (row and row[0] == "0")


def save_filters_compact(conn: sqlite3.Connection, page: str, compact: bool) -> None:
    with conn:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (COMPACT_PAGES[page], "1" if compact else "0"))


def active_filter_count(args: dict[str, str], grouping: str, default_grouping: str) -> int:
    """Spec 028, F4: every filter that differs from the standard (as "Filters wissen", spec 023)."""
    count = sum(1 for k, v in args.items() if k != "wie" and v)
    return count + (args.get("wie", WHO_DEFAULT) != WHO_DEFAULT) + (grouping != default_grouping)


def valid_filters(conn: sqlite3.Connection, chosen: dict[str, str], default_grouping: str,
                  user_name: str | None = None, page: str | None = None) -> dict[str, str]:
    """F5: a choice that no longer exists falls back to its standard."""
    options = filter_options(conn)
    allowed = {
        "wie": dict(who_options(conn, user_name, page)), "groep": dict(grouping_options(conn)), "aansporen": {"1"},
        "semester": {str(s) for s in options["semesters"]}, "invulling": {t for t, _ in options["tracks"]},
        "project": {str(s["id"]) for s in options["squads"]}, "gilde": {str(g["id"]) for g in options["guilds"]},
    }
    for column in options["choice_columns"]:
        allowed[column["key"]] = {str(i["id"]) for i in column["items"]}
    result = {k: chosen.get(k, "") if chosen.get(k, "") in allowed[k] else "" for k in filter_keys(conn)}
    result["wie"] = result["wie"] or WHO_DEFAULT
    result["groep"] = result["groep"] or default_grouping
    return result


def user_name(database: str) -> str | None:
    return db.get_setting(database, "portflow_user_name")
