"""Editing one student (spec 011; guilds: spec 016): choices, checks, saving and no longer following."""

import sqlite3
from datetime import date

from . import student_guilds
from .progress import name_key
from .overview import TRACK_LABELS, TRACKS

SQUAD_ROLES = [("PO", "product owner"), ("SM", "scrum master"),
               ("2ePO", "tweede product owner"), ("2eSM", "tweede scrum master")]


def find(conn: sqlite3.Connection, student_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()


def form_values(conn: sqlite3.Connection, student: sqlite3.Row) -> dict:
    """The current values, as strings for the form (F2)."""
    text = lambda value: "" if value is None else str(value)
    guilds = [{"role_id": str(g["role_id"]), "guild_master_id": text(g["guild_master_id"])}
              for g in student_guilds.of_student(conn, student["id"])]
    return {
        "name": student["name"], "student_number": text(student["student_number"]),
        "semester": text(student["semester"]), "start_date": text(student["start_date"]),
        "squad_id": text(student["squad_id"]), "track": text(student["track"]),
        "squad_role": text(student["squad_role"]), "guilds": guilds, "coach_id": text(student["coach_id"]),
        "notes": text(student["notes"]),
    }


def options(conn: sqlite3.Connection) -> dict:
    """The choices of the form (F2)."""
    rows = lambda sql: [dict(r) for r in conn.execute(sql)]
    return {
        "semesters": rows("SELECT number, osiris_code FROM semesters ORDER BY number"),
        # The display name of the project (spec 012, F12), in the order of the project numbers.
        "squads": [dict(s, full_name=s["display_name"] or s["full_name"]) for s in
                   rows("SELECT id, name, full_name, display_name FROM squads ORDER BY full_name")],
        "tracks": [(t, TRACK_LABELS[t]) for t in TRACKS],
        "squad_roles": SQUAD_ROLES,
        "roles": rows("SELECT r.id, r.code, r.name, g.code AS guild_code, g.name AS guild_name "
                      "FROM professional_roles r LEFT JOIN guilds g ON g.role_id = r.id ORDER BY r.code"),
        "coaches": rows("SELECT id, name FROM staff WHERE is_coach = 1 ORDER BY name COLLATE NOCASE"),
        "guild_masters": rows("SELECT id, name FROM staff WHERE is_guild_master = 1 ORDER BY name COLLATE NOCASE"),
    }


def portflow_link(conn: sqlite3.Connection, student: sqlite3.Row) -> dict:
    """F3: the Portflow link, read only."""
    portfolios = [r[0] for r in conn.execute(
        "SELECT portfolio_id FROM student_portfolios WHERE student_id = ? ORDER BY portfolio_id", (student["id"],))]
    if student["portflow_user_id"] is None:
        status = "Niet gekoppeld"
    elif not student["has_access"]:
        status = "Portfolio niet gedeeld"
    else:
        status = "Gekoppeld"
    return {"status": status, "portfolios": portfolios}


def _choice(conn, value: str, sql: str) -> tuple[int | None, bool]:
    """(id or None, valid): an empty choice is None; otherwise the id must exist."""
    if not value:
        return None, True
    if not value.isdigit() or not conn.execute(sql, (int(value),)).fetchone():
        return None, False
    return int(value), True


def validate(conn: sqlite3.Connection, form: dict) -> tuple[dict | None, str | None]:
    """F5: returns (clean values, None) or (None, Dutch error message)."""
    name = " ".join((form.get("name") or "").split())
    if not name:
        return None, "Vul een naam in."
    start = (form.get("start_date") or "").strip()
    if start:
        try:
            start = date.fromisoformat(start).isoformat()
        except ValueError:
            return None, "Vul een geldige startdatum in, of laat het veld leeg."
    values = {"name": name, "student_number": " ".join((form.get("student_number") or "").split()) or None,
              "start_date": start or None,
              "notes": "\n".join(line.rstrip() for line in (form.get("notes") or "").strip().splitlines()) or None}
    checks = {
        "semester": ("SELECT 1 FROM semesters WHERE number = ?", "Kies een semester uit de lijst."),
        "squad_id": ("SELECT 1 FROM squads WHERE id = ?", "Kies een project uit de lijst."),
        "coach_id": ("SELECT 1 FROM staff WHERE id = ? AND is_coach = 1", "Kies een coach uit de lijst."),
    }
    for field, (sql, message) in checks.items():
        value, ok = _choice(conn, (form.get(field) or "").strip(), sql)
        if not ok:
            return None, message
        values[field] = value
    track = (form.get("track") or "").strip()
    squad_role = (form.get("squad_role") or "").strip()
    if track and track not in TRACKS:
        return None, "Kies een invulling uit de lijst."
    if squad_role and squad_role not in dict(SQUAD_ROLES):
        return None, "Kies een rol uit de lijst."
    values["track"], values["squad_role"] = track or None, squad_role or None
    # Spec 016, F4: guild rows (professional role + guild master); an empty role is ignored.
    pairs: list[tuple[int, int | None]] = []
    for row in form.get("guilds") or []:
        role_id, ok = _choice(conn, (row.get("role_id") or "").strip(), "SELECT 1 FROM professional_roles WHERE id = ?")
        if not ok:
            return None, "Kies een beroepsrol uit de lijst."
        if role_id is None:
            continue
        if role_id in [r for r, _ in pairs]:
            code = conn.execute("SELECT code FROM professional_roles WHERE id = ?", (role_id,)).fetchone()[0]
            return None, f"{code} staat er twee keer in."
        master, ok = _choice(conn, (row.get("guild_master_id") or "").strip(),
                             "SELECT 1 FROM staff WHERE id = ? AND is_guild_master = 1")
        if not ok:
            return None, "Kies een gildemeester uit de lijst."
        pairs.append((role_id, master))
    values["guilds"] = pairs
    return values, None


def save(conn: sqlite3.Connection, student_id: int, values: dict) -> None:
    """F4."""
    with conn:
        conn.execute(
            "UPDATE students SET name = :name, student_number = :student_number, semester = :semester, "
            "start_date = :start_date, squad_id = :squad_id, track = :track, squad_role = :squad_role, "
            "coach_id = :coach_id, notes = :notes WHERE id = :id",
            {k: v for k, v in dict(values, id=student_id).items() if k != "guilds"})
        student_guilds.replace(conn, student_id, values["guilds"])


def empty_form() -> dict:
    """Spec 017, F2: the edit form, empty."""
    keys = ("name", "student_number", "semester", "start_date", "squad_id", "track", "squad_role", "coach_id", "notes")
    return dict({key: "" for key in keys}, guilds=[])


def same_name(conn: sqlite3.Connection, name: str) -> dict | None:
    """Spec 017, F3: an existing student with the same name (case, spaces and accents ignored)."""
    key = name_key(name)
    return next((dict(r) for r in conn.execute("SELECT id, name FROM students ORDER BY id") if name_key(r["name"]) == key), None)


def number_owner(conn: sqlite3.Connection, number: str | None, student_id: int | None = None) -> str | None:
    """Spec 017, F3: the name of another student with this student number, if any."""
    if not number:
        return None
    row = conn.execute("SELECT name FROM students WHERE student_number = ? AND id != ?", (number, student_id or -1)).fetchone()
    return row[0] if row else None


def create(conn: sqlite3.Connection, values: dict) -> int:
    """Spec 017, F4: add a student with all values of the form."""
    with conn:
        student_id = conn.execute(
            "INSERT INTO students (name, student_number, semester, start_date, squad_id, track, squad_role, coach_id, notes) "
            "VALUES (:name, :student_number, :semester, :start_date, :squad_id, :track, :squad_role, :coach_id, :notes)",
            {k: v for k, v in values.items() if k != "guilds"}).lastrowid
        student_guilds.replace(conn, student_id, values["guilds"])
    return student_id


def delete(conn: sqlite3.Connection, student_id: int) -> None:
    """F6: evaluations, portfolios, guilds and custom values go along (foreign keys)."""
    with conn:
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
