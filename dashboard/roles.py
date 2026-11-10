"""Professional roles (spec 008; docs/gegevensmodel.md#beroepsrol): code, name, description, colour."""

import re
import sqlite3
from pathlib import Path

PRESET_FILE = Path(__file__).resolve().parent.parent / "docs" / "beroepsrollen.md"
_PRESET_LINE = re.compile(r"^\|\s*\*\*([A-Za-z]{2,3})\*\*\s*\|\s*(.+?)\s*\|\s*$")
DEFAULT_COLOR = "#909DB9"
CODE = re.compile(r"^[A-Za-z]{2,3}$")
COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def read_preset(path: Path = PRESET_FILE) -> list[tuple[str, str]]:
    """Rows '| **CODE** | Naam |' from the table in docs/beroepsrollen.md, the one source (F5)."""
    if not path.exists():
        return []
    return [(m.group(1).upper(), m.group(2))
            for m in map(_PRESET_LINE.match, path.read_text(encoding="utf-8").splitlines()) if m]


def all_roles(conn: sqlite3.Connection) -> list[dict]:
    """The cards (F3): role, guild and the students who have this guild (spec 016)."""
    rows = conn.execute(
        "SELECT r.*, g.code AS guild_code, g.name AS guild_name, g.color AS guild_color "
        "FROM professional_roles r LEFT JOIN guilds g ON g.role_id = r.id ORDER BY r.code"
    ).fetchall()
    result = []
    for row in rows:
        students = conn.execute("SELECT s.id, s.name, (SELECT COUNT(*) FROM student_guilds o WHERE o.student_id = s.id) "
                                "AS guild_count FROM student_guilds sg JOIN students s ON s.id = sg.student_id "
                                "WHERE sg.role_id = ? ORDER BY s.name", (row["id"],)).fetchall()
        students = [dict(s) for s in students]
        result.append(dict(row, students=students, only_guild=[s for s in students if s["guild_count"] == 1]))
    return result


def linked_students(conn: sqlite3.Connection) -> int:
    """F2: students with at least one guild (spec 016)."""
    return conn.execute("SELECT COUNT(DISTINCT student_id) FROM student_guilds").fetchone()[0]


def find(conn: sqlite3.Connection, role_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM professional_roles WHERE id = ?", (role_id,)).fetchone()


def count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM professional_roles").fetchone()[0]


def validate(conn: sqlite3.Connection, code: str, name: str, description: str, color: str,
             role_id: int | None = None) -> tuple[dict | None, str | None]:
    """F6: returns (clean values, None) or (None, Dutch error message)."""
    code, name = code.strip().upper(), " ".join(name.split())
    description, color = " ".join(description.split()), color.strip()
    if not CODE.match(code):
        return None, "De code bestaat uit 2 of 3 letters, bijvoorbeeld FE of BIT."
    if not name:
        return None, "Vul een naam in."
    if not COLOR.match(color):
        color = DEFAULT_COLOR
    if conn.execute("SELECT 1 FROM professional_roles WHERE code = ? AND id != ?", (code, role_id or -1)).fetchone():
        return None, f"Er is al een beroepsrol met de code {code}."
    return {"code": code, "name": name, "description": description, "color": color}, None


def create(conn: sqlite3.Connection, values: dict) -> int:
    with conn:
        return conn.execute("INSERT INTO professional_roles (code, name, description, color) "
                            "VALUES (:code, :name, :description, :color)", values).lastrowid


def update(conn: sqlite3.Connection, role_id: int, values: dict) -> None:
    with conn:
        conn.execute("UPDATE professional_roles SET code = :code, name = :name, description = :description, "
                     "color = :color WHERE id = :id", dict(values, id=role_id))


def delete(conn: sqlite3.Connection, role_id: int) -> None:
    """F8: the guild of this role goes at every student, and the guild itself (foreign keys)."""
    with conn:
        conn.execute("DELETE FROM professional_roles WHERE id = ?", (role_id,))


def add_preset(conn: sqlite3.Connection, *, is_demo: bool = False) -> int:
    """F5: the Open-ICT roles; a code that exists already is skipped. Returns the number added."""
    added = 0
    with conn:
        for code, name in read_preset():
            if conn.execute("SELECT 1 FROM professional_roles WHERE code = ?", (code,)).fetchone():
                continue
            conn.execute("INSERT INTO professional_roles (code, name, color, is_demo) VALUES (?, ?, ?, ?)",
                         (code, name, DEFAULT_COLOR, int(is_demo)))
            added += 1
    return added
