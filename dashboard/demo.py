"""Fixed set of invented demo data (spec 002, F10-F13).

All names are made up. Every demo record is marked with is_demo = 1, so
removing the demo data never touches real records. The set covers the cases
of spec 001, so the progress rules can be tried out and tested later.
"""

import sqlite3

SKILLS = ["OC", "KO", "JKO", "KPM", "PL", "BD", "SW", "FO", "PH", "RE"]

STAFF = ["Marieke Ploeg", "Joost Hendriks", "Femke Bos", "Ruben Smit"]

# An assessor who is NOT in the staff list (for example an older student).
# Evaluations by this person must be hidden in the student overview.
UNKNOWN_ASSESSOR = "Kevin Brandsma"

SQUADS = [
    # (name, full name, colour)
    ("Horizon", "04 Horizon", "#7D6BA8"),
    ("Lantaarn", "11 Lantaarn", "#C17661"),
    ("Noorderlicht", "15 Noorderlicht", "#5E8C74"),
]


def _a(skill, level, date, assessor):
    """An assessed evaluation."""
    return {"skill": skill, "level": level, "date": date, "assessor": assessor}


def _req(request_id, title, status, skills, date):
    """A review request: the student's self-evaluation on one or more skills."""
    return {"id": request_id, "title": title, "status": status, "skills": skills, "date": date}


GM, CO, GM2, CO2 = "Joost Hendriks", "Marieke Ploeg", "Femke Bos", "Ruben Smit"

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
                "evaluations": "Evaluaties"}


def has_demo_data(conn: sqlite3.Connection) -> bool:
    return any(
        conn.execute(f"SELECT 1 FROM {table} WHERE is_demo = 1 LIMIT 1").fetchone()
        for table in COUNT_TABLES
    )


def demo_counts(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """Number of demo records per kind, as (Dutch label, count)."""
    return [
        (label, conn.execute(f"SELECT COUNT(*) FROM {table} WHERE is_demo = 1").fetchone()[0])
        for table, label in COUNT_TABLES.items()
    ]


def load_demo_data(conn: sqlite3.Connection) -> bool:
    """Insert the demo set. Returns False if demo data is already present."""
    if has_demo_data(conn):
        return False
    with conn:
        for name in STAFF:
            conn.execute("INSERT INTO staff (name, is_demo) VALUES (?, 1)", (name,))
        for name, full_name, color in SQUADS:
            conn.execute(
                "INSERT INTO squads (name, full_name, color, is_demo) VALUES (?, ?, ?, 1)",
                (name, full_name, color),
            )
        for student in STUDENTS:
            _insert_student(conn, student)
    return True


def remove_demo_data(conn: sqlite3.Connection) -> None:
    """Delete all demo records and nothing else."""
    with conn:
        conn.execute("DELETE FROM evaluations WHERE is_demo = 1")
        conn.execute("DELETE FROM students WHERE is_demo = 1")
        conn.execute("DELETE FROM squads WHERE is_demo = 1")
        conn.execute("DELETE FROM staff WHERE is_demo = 1")


def _lookup(conn, sql, value):
    if value is None:
        return None
    return conn.execute(sql, (value,)).fetchone()[0]


def _insert_student(conn: sqlite3.Connection, student: dict) -> None:
    staff_id = "SELECT id FROM staff WHERE name = ? AND is_demo = 1"
    cursor = conn.execute(
        """INSERT INTO students (name, semester, squad_id, squad_role, track, primary_role_id,
                                 coach_id, guild_master_id, has_access, is_demo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        (
            student["name"],
            student["semester"],
            _lookup(conn, "SELECT id FROM squads WHERE name = ? AND is_demo = 1", student["squad"]),
            student.get("squad_role"),
            student["track"],
            _lookup(conn, "SELECT id FROM professional_roles WHERE code = ?", student["role"]),
            _lookup(conn, staff_id, student["coach"]),
            _lookup(conn, staff_id, student["guild_master"]),
            int(student.get("has_access", True)),
        ),
    )
    student_id = cursor.lastrowid

    for code in student.get("secondary_roles", []):
        conn.execute(
            "INSERT INTO student_secondary_roles (student_id, role_id) VALUES (?, ?)",
            (student_id, _lookup(conn, "SELECT id FROM professional_roles WHERE code = ?", code)),
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
