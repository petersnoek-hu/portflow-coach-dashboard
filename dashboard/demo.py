"""Fixed set of invented demo data (spec 002, F10-F13).

All names are made up. Every demo record is marked with is_demo = 1, so
removing the demo data never touches real records. The set covers the cases
of spec 001, so the progress rules can be tried out and tested later.
"""

import sqlite3

from . import guilds, projects, roles, semesters
from .skills import SKILLS

STAFF = ["Marieke Ploeg", "Joost Hendriks", "Femke Bos", "Ruben Smit"]

# An assessor who is NOT in the staff list (for example an older student).
# Evaluations by this person must be hidden in the student overview.
UNKNOWN_ASSESSOR = "Kevin Brandsma"

SQUADS = [
    # (number, name, client, colour); spec 012. All invented.
    ("04", "Horizon", "Stichting Verzonnen Zorg", "#7D6BA8"),
    ("11", "Lantaarn", "Gemeente Denkbeeldig", "#C17661"),
    ("15", "Noorderlicht", "Fictief Logistiek BV", "#5E8C74"),
]


def _a(skill, level, date, assessor):
    """An assessed evaluation."""
    return {"skill": skill, "level": level, "date": date, "assessor": assessor}


def _req(request_id, title, status, skills, date):
    """A review request: the student's self-evaluation on one or more skills."""
    return {"id": request_id, "title": title, "status": status, "skills": skills, "date": date}


GM, CO, GM2, CO2 = "Joost Hendriks", "Marieke Ploeg", "Femke Bos", "Ruben Smit"

# Roles and guilds of the demo staff (specs 006, 007); Ruben Smit is coach and guild master.
STAFF_ROLES = {CO: ("coach",), CO2: ("coach", "guild_master"), GM: ("guild_master",), GM2: ("guild_master",)}
STAFF_GUILDS = {GM: ["FE", "UX"], GM2: ["AI", "BE"], CO2: ["GD"]}

# Demo professional roles (spec 002, F18): an invented short description and a colour per role.
# Only used for roles the demo adds itself; existing roles are never changed.
ROLE_DETAILS = {
    "UX": ("Onderzoekt gebruikers en ontwerpt bruikbare, toegankelijke interfaces.", "#C17661"),
    "BIT": ("Verbindt bedrijfsprocessen, informatie en technologie.", "#5E8C74"),
    "CS": ("Beveiligt systemen, netwerken en gegevens.", "#3F5578"),
    "CI": ("Bouwt en beheert cloud- en infrastructuuromgevingen.", "#4F8FA8"),
    "FE": ("Bouwt de kant van een webapplicatie die de gebruiker ziet.", "#7D6BA8"),
    "BE": ("Bouwt servers, API's en de opslag van gegevens.", "#5B76A8"),
    "AI": ("Ontwikkelt toepassingen met data en machine learning.", "#A86B8A"),
    "GD": ("Ontwerpt en bouwt games en interactieve ervaringen.", "#B58A4A"),
    "TI": ("Ontwikkelt software voor apparaten en sensoren.", "#6B8F3F"),
}

# Custom columns (spec 001, F8) with a few values per student name.
CUSTOM_COLUMNS = [("AW", "Aanwezigheid", "Aanwezigheid bij de stand-ups", "percentage"),
                  ("NT", "Notitie", "Eigen aantekening van de coach", "text")]
CUSTOM_VALUES = {"Lieke Jansen": {"AW": "92", "NT": "Wil richting UX-onderzoek groeien"},
                 "Sem Bakker": {"AW": "75"}, "Daan Mulder": {"AW": "60", "NT": "Plant deze week een coachgesprek"}}

STUDENTS = [
    {
        "name": "Lieke Jansen", "semester": 3, "squad": "Horizon", "track": "Open projecten",
        "role": "FE", "squad_role": "SM", "coach": CO, "guild_master": GM,
        "evaluations": [
            _a("OC", "1", "2026-09-22", GM), _a("OC", "2", "2026-10-27", GM),
            _a("KO", "1", "2026-09-22", GM), _a("JKO", "1", "2026-10-06", GM),
            _a("KPM", "1", "2026-09-29", GM), _a("KPM", "2", "2026-11-03", GM),
            _a("PL", "1", "2026-09-24", CO), _a("BD", "2", "2026-10-08", CO),
            _a("SW", "1", "2026-09-24", CO), _a("SW", "1", "2026-10-22", CO),
            _a("FO", "1", "2026-10-08", CO), _a("PH", "1", "2026-10-15", CO),
            _a("RE", "1", "2026-10-15", CO),
        ],
    },
    {
        # Start level followed by level 2 (0/2) and an open request (?).
        "name": "Sem Bakker", "semester": 3, "squad": "Horizon", "track": "Open projecten",
        "role": "FE", "coach": CO, "guild_master": GM,
        "evaluations": [
            _a("OC", "0", "2026-09-15", GM), _a("OC", "2", "2026-10-20", GM),
            _a("KO", "1", "2026-10-06", GM), _a("PL", "1", "2026-09-24", CO),
        ],
        "requests": [_req(9001, "SW 1ste evaluatie", "not_started", ["SW"], "2026-11-05")],
    },
    {
        # Signal: all four product skills empty.
        "name": "Noor van Dijk", "semester": 3, "squad": "Horizon", "track": "Open projecten",
        "role": "AI", "squad_role": "PO", "coach": CO, "guild_master": GM2,
        "evaluations": [
            _a("PL", "1", "2026-09-24", CO), _a("BD", "1", "2026-10-01", CO),
            _a("SW", "2", "2026-10-22", CO), _a("FO", "1", "2026-10-08", CO),
            _a("PH", "1", "2026-10-15", CO), _a("RE", "1", "2026-10-29", CO),
        ],
    },
    {
        # Signal: all six coach skills empty; plus a denied request.
        "name": "Daan Mulder", "semester": 4, "squad": "Lantaarn", "track": "Open projecten",
        "role": "GD", "coach": CO2, "guild_master": GM,
        "evaluations": [
            _a("OC", "2", "2026-09-29", GM), _a("KO", "2", "2026-10-13", GM),
            _a("JKO", "1", "2026-10-13", GM), _a("KPM", "2", "2026-10-27", GM),
        ],
        "requests": [_req(9002, "PL niveau 2", "denied", ["PL"], "2026-10-30")],
    },
    {
        # Signal: five of the six coach skills empty.
        "name": "Eva Kok", "semester": 4, "squad": "Lantaarn", "track": "Open projecten",
        "role": "GD", "squad_role": "2ePO", "coach": CO2, "guild_master": GM,
        "evaluations": [
            _a("OC", "1", "2026-09-29", GM), _a("KO", "1", "2026-10-13", GM),
            _a("JKO", "1", "2026-10-13", GM), _a("KPM", "1", "2026-10-27", GM),
            _a("PL", "1", "2026-10-01", CO2),
        ],
    },
    {
        # Many levels, plus an evaluation by an assessor who is not in the staff list.
        "name": "Milan de Wit", "semester": 5, "squad": "Lantaarn", "track": "Open innovatieproject",
        "role": "CS", "coach": CO2, "guild_master": GM2,
        "evaluations": [
            _a("OC", "2", "2026-09-17", GM2), _a("OC", "3", "2026-10-29", GM2),
            _a("KO", "2", "2026-09-17", GM2), _a("JKO", "2", "2026-09-24", GM2),
            _a("JKO", "2", "2026-10-22", GM2), _a("KPM", "2", "2026-10-01", GM2),
            _a("KPM", "3", "2026-11-05", GM2), _a("PL", "2", "2026-09-24", CO2),
            _a("BD", "2", "2026-10-08", CO2), _a("BD", "3", "2026-10-21", UNKNOWN_ASSESSOR),
            _a("SW", "2", "2026-10-08", CO2), _a("FO", "3", "2026-10-29", CO2),
            _a("PH", "2", "2026-10-15", CO2), _a("RE", "2", "2026-10-15", CO2),
        ],
    },
    {
        # Full assessment: one request covering all ten skills.
        "name": "Sara Hoekstra", "semester": 5, "squad": "Noorderlicht", "track": "Stage",
        "role": "BIT", "coach": CO, "guild_master": GM2,
        "evaluations": [
            _a("OC", "2", "2026-09-17", GM2), _a("KPM", "2", "2026-10-01", GM2),
            _a("PL", "2", "2026-09-24", CO), _a("SW", "2", "2026-10-08", CO),
        ],
        "requests": [_req(9003, "Eindassessment semester 5", "not_started", SKILLS, "2026-11-06")],
    },
    {
        # Three evaluations on one skill (1/1/2) and one from before the semester period.
        "name": "Jesse Peters", "semester": 5, "squad": "Noorderlicht", "track": "Stage",
        "role": "AI", "coach": CO, "guild_master": GM2,
        "evaluations": [
            _a("OC", "1", "2026-05-12", GM2),
            _a("OC", "2", "2026-09-24", GM2), _a("KO", "2", "2026-10-01", GM2),
            _a("SW", "1", "2026-09-10", CO), _a("SW", "1", "2026-10-01", CO),
            _a("SW", "2", "2026-10-29", CO), _a("RE", "2", "2026-10-15", CO),
        ],
    },
    {
        # Semester 2: not every skill needs an evaluation (grey cells).
        "name": "Fleur Willems", "semester": 2, "squad": "Noorderlicht", "track": None,
        "role": "UX", "coach": CO, "guild_master": GM,
        "evaluations": [
            _a("OC", "1", "2026-10-06", GM), _a("KO", "1", "2026-10-13", GM),
            _a("PL", "1", "2026-10-01", CO), _a("BD", "1", "2026-10-22", CO),
        ],
    },
    {
        "name": "Tim Vos", "semester": 2, "squad": "Horizon", "track": None,
        "role": "UX", "coach": CO2, "guild_master": GM,
        "evaluations": [_a("SW", "1", "2026-10-22", CO2)],
        "requests": [_req(9004, "OC & KO 1ste evaluatie", "in_progress", ["OC", "KO"], "2026-11-04")],
    },
    {
        # No squad: shown under "Zonder project".
        "name": "Lars Koster", "semester": 3, "squad": None, "track": "Open projecten",
        "role": "BE", "coach": CO, "guild_master": GM2,
        "evaluations": [_a("KO", "1", "2026-10-06", GM2), _a("PL", "1", "2026-10-01", CO)],
    },
    {
        # No semester and no professional role yet: "Nog in te delen".
        "name": "Iris Bouma", "semester": None, "squad": None, "track": None,
        "role": None, "coach": None, "guild_master": None,
        "evaluations": [],
    },
    {
        # Portfolio not shared with the user: n/b.
        "name": "Bram Smits", "semester": 4, "squad": "Lantaarn", "track": "Open projecten",
        "role": "BE", "coach": CO2, "guild_master": GM, "has_access": False,
        "evaluations": [],
    },
    {
        "name": "Julia Meijer", "semester": 6, "squad": "Noorderlicht", "track": "Minor",
        "role": "CI", "secondary_roles": ["CS"], "coach": CO, "guild_master": GM2,
        "evaluations": [
            _a("OC", "2", "2026-09-17", GM2), _a("KO", "3", "2026-10-08", GM2),
            _a("PL", "2", "2026-09-24", CO), _a("FO", "2", "2026-10-15", CO),
        ],
    },
]

COUNT_TABLES = {"students": "Studenten", "squads": "Squads", "staff": "Coaches en gildemeesters",
                "evaluations": "Evaluaties", "custom_columns": "Eigen kolommen", "guilds": "Gildes",
                "professional_roles": "Beroepsrollen", "semesters": "Semesters"}


def has_demo_data(conn: sqlite3.Connection) -> bool:
    return any(
        conn.execute(f"SELECT 1 FROM {table} WHERE is_demo = 1 LIMIT 1").fetchone()
        for table in COUNT_TABLES
    )


SHARED_TABLES = {"professional_roles", "guilds", "semesters"}   # the demo reuses existing ones (F18)


def demo_counts(conn: sqlite3.Connection) -> list[tuple[str, int | str]]:
    """Number of demo records per kind, as (Dutch label, count or explanation).

    For roles, guilds and semesters that the demo did not add because they already
    existed, the text says that the demo uses the existing ones (spec 002, F18).
    """
    result = []
    for table, label in COUNT_TABLES.items():
        demo = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE is_demo = 1").fetchone()[0]
        total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if table in SHARED_TABLES and demo == 0 and total:
            result.append((label, f"gebruikt je bestaande {total}"))
        elif table in SHARED_TABLES and demo < total:
            result.append((label, f"{demo} (plus je bestaande {total - demo})"))
        else:
            result.append((label, demo))
    return result


def load_demo_data(conn: sqlite3.Connection) -> bool:
    """Insert the demo set. Returns False if demo data is already present."""
    if has_demo_data(conn):
        return False
    # Demo roles and guilds: the Open-ICT ones that do not exist yet, marked as demo
    # (spec 008 F5, spec 006 F14), so removing the demo data removes only those.
    roles.add_preset(conn, is_demo=True)
    guilds.add_preset(conn, is_demo=True)
    semesters.add_preset(conn, is_demo=True)  # spec 009
    with conn:
        # Spec 002, F18: description and colour for the roles the demo added; its guilds get the role colour.
        for code, (description, color) in ROLE_DETAILS.items():
            conn.execute("UPDATE professional_roles SET description = ?, color = ? WHERE code = ? AND is_demo = 1",
                         (description, color, code))
            conn.execute("UPDATE guilds SET color = ? WHERE is_demo = 1 AND role_id IN "
                         "(SELECT id FROM professional_roles WHERE code = ?)", (color, code))
        for name in STAFF:
            staff_roles = STAFF_ROLES[name]
            cursor = conn.execute(
                "INSERT INTO staff (name, is_coach, is_guild_master, is_demo) VALUES (?, ?, ?, 1)",
                (name, int("coach" in staff_roles), int("guild_master" in staff_roles)),
            )
            for code in STAFF_GUILDS.get(name, []):
                conn.execute("INSERT OR IGNORE INTO staff_guilds (staff_id, guild_id) "
                             "SELECT ?, id FROM guilds WHERE code = ?", (cursor.lastrowid, code))
        for position, (code, name, description, kind) in enumerate(CUSTOM_COLUMNS):
            conn.execute("INSERT INTO custom_columns (code, name, description, type, position, is_demo) "
                         "VALUES (?, ?, ?, ?, ?, 1)", (code, name, description, kind, position))
        for number, name, client, color in SQUADS:
            # Skip a demo project whose number is already used by a real one (numbers are unique).
            if conn.execute("SELECT 1 FROM squads WHERE number = ?", (number,)).fetchone():
                number = None
            conn.execute(
                "INSERT INTO squads (number, name, client, full_name, display_name, color, is_demo) VALUES (?, ?, ?, ?, ?, ?, 1)",
                (number, name, client, projects.full_name(number, name), projects.default_display(number, name, client), color),
            )
        for student in STUDENTS:
            _insert_student(conn, student)
    return True


def remove_demo_data(conn: sqlite3.Connection) -> None:
    """Delete all demo records and nothing else."""
    with conn:
        conn.execute("DELETE FROM evaluations WHERE is_demo = 1")
        conn.execute("DELETE FROM custom_columns WHERE is_demo = 1")
        conn.execute("DELETE FROM students WHERE is_demo = 1")
        conn.execute("DELETE FROM squads WHERE is_demo = 1")
        conn.execute("DELETE FROM staff WHERE is_demo = 1")
        conn.execute("DELETE FROM guilds WHERE is_demo = 1")
        conn.execute("DELETE FROM professional_roles WHERE is_demo = 1")
        conn.execute("DELETE FROM semesters WHERE is_demo = 1")


def _lookup(conn, sql, value):
    if value is None:
        return None
    return conn.execute(sql, (value,)).fetchone()[0]


def _insert_student(conn: sqlite3.Connection, student: dict) -> None:
    staff_id = "SELECT id FROM staff WHERE name = ? AND is_demo = 1"
    cursor = conn.execute(
        """INSERT INTO students (name, semester, squad_id, squad_role, track, coach_id, has_access, is_demo)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
        (
            student["name"],
            student["semester"],
            _lookup(conn, "SELECT id FROM squads WHERE name = ? AND is_demo = 1", student["squad"]),
            student.get("squad_role"),
            student["track"],
            _lookup(conn, staff_id, student["coach"]),
            int(student.get("has_access", True)),
        ),
    )
    student_id = cursor.lastrowid

    for code, value in CUSTOM_VALUES.get(student["name"], {}).items():
        conn.execute("INSERT INTO custom_values (student_id, column_id, value) "
                     "SELECT ?, id, ? FROM custom_columns WHERE code = ? AND is_demo = 1", (student_id, value, code))

    # Spec 016: the guilds of the student; the guild master belongs to the first one ("role").
    codes = ([student["role"]] if student["role"] else []) + student.get("secondary_roles", [])
    for index, code in enumerate(codes):
        conn.execute(
            "INSERT OR IGNORE INTO student_guilds (student_id, role_id, guild_master_id) VALUES (?, ?, ?)",
            (student_id, _lookup(conn, "SELECT id FROM professional_roles WHERE code = ?", code),
             _lookup(conn, staff_id, student["guild_master"]) if index == 0 else None),
        )

    for ev in student["evaluations"]:
        conn.execute(
            """INSERT INTO evaluations (student_id, skill, kind, level, date, assessor,
                                        review_request_status, is_demo)
               VALUES (?, ?, 'assessed', ?, ?, ?, 'scored', 1)""",
            (student_id, ev["skill"], ev["level"], ev["date"], ev["assessor"]),
        )

    for req in student.get("requests", []):
        for skill in req["skills"]:
            conn.execute(
                """INSERT INTO evaluations (student_id, skill, kind, date, review_request_id,
                                            review_request_title, review_request_status, is_demo)
                   VALUES (?, ?, 'self', ?, ?, ?, ?, 1)""",
                (student_id, skill, req["date"], req["id"], req["title"], req["status"]),
            )
