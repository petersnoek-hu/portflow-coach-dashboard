"""Guilds (spec 006, F12-F19; spec 018; docs/gegevensmodel.md#gilde).

A guild has a code, a name, its professional role (name and description) and a colour.
Every professional role has exactly one guild, so the role is a field of the guild.
"""

import re
import sqlite3
from pathlib import Path

PRESET_FILE = Path(__file__).resolve().parent.parent / "docs" / "gildes-openict.md"
_PRESET_LINE = re.compile(r"^\|\s*\*\*([A-Za-z]{2,3})\*\*\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$")
DEFAULT_COLOR = "#909DB9"
_CODE = re.compile(r"^[A-Za-z]{2,3}$")
_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def read_preset(path: Path = PRESET_FILE) -> list[tuple[str, str, str]]:
    """Rows '| **CODE** | Gilde | Beroepsrol |' from docs/gildes-openict.md, the one source (spec 018, F4)."""
    if not path.exists():
        return []
    return [(m.group(1).upper(), m.group(2), m.group(3))
            for m in map(_PRESET_LINE.match, path.read_text(encoding="utf-8").splitlines()) if m]


def all_guilds(conn: sqlite3.Connection) -> list[dict]:
    """The cards (F13, spec 018 F3): guild, guild masters and the students with this guild."""
    result = []
    for row in conn.execute("SELECT * FROM guilds ORDER BY code").fetchall():
        masters = conn.execute(
            "SELECT s.id, s.name FROM staff_guilds sg JOIN staff s ON s.id = sg.staff_id "
            "WHERE sg.guild_id = ? ORDER BY s.name COLLATE NOCASE", (row["id"],)
        ).fetchall()
        students = conn.execute(
            "SELECT s.id, s.name, (SELECT COUNT(*) FROM student_guilds o WHERE o.student_id = s.id) AS guild_count "
            "FROM student_guilds sg JOIN students s ON s.id = sg.student_id WHERE sg.guild_id = ? ORDER BY s.name",
            (row["id"],)).fetchall()
        students = [dict(s) for s in students]
        result.append(dict(row, guild_masters=[dict(m) for m in masters], students=len(students),
                           student_list=students, only_guild=[s for s in students if s["guild_count"] == 1]))
    return result


def options(conn: sqlite3.Connection) -> list[dict]:
    """The guilds to choose from (student form, filter): id, code, name, role name."""
    return [dict(r) for r in conn.execute("SELECT id, code, name, role_name FROM guilds ORDER BY code")]


def find(conn: sqlite3.Connection, guild_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM guilds WHERE id = ?", (guild_id,)).fetchone()


def validate(conn: sqlite3.Connection, code: str, name: str, role_name: str, description: str, color: str,
             guild_id: int | None = None) -> tuple[dict | None, str | None]:
    """F15, spec 018 F2: returns (clean values, None) or (None, Dutch error message)."""
    code, name, color = code.strip().upper(), " ".join(name.split()), color.strip()
    role_name, description = " ".join(role_name.split()), " ".join(description.split())
    if not _CODE.match(code):
        return None, "De code bestaat uit 2 of 3 letters, bijvoorbeeld FE of BIT."
    if not name:
        return None, "Vul een naam in."
    if not role_name:
        return None, "Vul een beroepsrol in."
    if not _COLOR.match(color):
        color = DEFAULT_COLOR
    if conn.execute("SELECT 1 FROM guilds WHERE code = ? AND id != ?", (code, guild_id or -1)).fetchone():
        return None, f"Er is al een gilde met de code {code}."
    return {"code": code, "name": name, "role_name": role_name, "description": description, "color": color}, None


def create(conn: sqlite3.Connection, values: dict) -> int:
    with conn:
        return conn.execute("INSERT INTO guilds (code, name, role_name, description, color) "
                            "VALUES (:code, :name, :role_name, :description, :color)", values).lastrowid


def update(conn: sqlite3.Connection, guild_id: int, values: dict) -> None:
    with conn:
        conn.execute("UPDATE guilds SET code = :code, name = :name, role_name = :role_name, "
                     "description = :description, color = :color WHERE id = :id", dict(values, id=guild_id))


def delete(conn: sqlite3.Connection, guild_id: int) -> None:
    """Spec 018, F5: the guild goes at the students and the guild masters (cascade);
    guild masters keep their role."""
    with conn:
        conn.execute("DELETE FROM guilds WHERE id = ?", (guild_id,))


def add_preset(conn: sqlite3.Connection, codes: set[str] | None = None, *, is_demo: bool = False) -> int:
    """F14, spec 018 F4: add the Open-ICT guilds (or only `codes`) with their professional role.
    A code that exists already is skipped. Returns the number added."""
    added = 0
    with conn:
        for code, name, role_name in read_preset():
            if codes is not None and code not in codes:
                continue
            if conn.execute("SELECT 1 FROM guilds WHERE code = ?", (code,)).fetchone():
                continue
            conn.execute("INSERT INTO guilds (code, name, role_name, color, is_demo) VALUES (?, ?, ?, ?, ?)",
                         (code, name, role_name, DEFAULT_COLOR, int(is_demo)))
            added += 1
    return added
