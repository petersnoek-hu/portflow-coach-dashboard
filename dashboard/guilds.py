"""Guilds (spec 006, F12-F19; docs/gegevensmodel.md#gilde): code, name, colour, one professional role."""

import re
import sqlite3
from pathlib import Path

PRESET_FILE = Path(__file__).resolve().parent.parent / "docs" / "gildes-openict.md"
_PRESET_LINE = re.compile(r"^\|\s*\*\*([A-Za-z]{2,3})\*\*\s*\|\s*(.+?)\s*\|\s*$")
DEFAULT_COLOR = "#909DB9"
_CODE = re.compile(r"^[A-Za-z]{2,3}$")
_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def read_preset(path: Path = PRESET_FILE) -> list[tuple[str, str]]:
    """Rows '| **CODE** | Naam |' from docs/gildes-openict.md, the one source of the Open-ICT guilds."""
    if not path.exists():
        return []
    return [(m.group(1).upper(), m.group(2))
            for m in map(_PRESET_LINE.match, path.read_text(encoding="utf-8").splitlines()) if m]


def all_guilds(conn: sqlite3.Connection) -> list[dict]:
    """The cards (F13): guild, its role, guild masters and number of students."""
    rows = conn.execute(
        "SELECT g.*, r.code AS role_code, r.name AS role_name FROM guilds g "
        "JOIN professional_roles r ON r.id = g.role_id ORDER BY g.code"
    ).fetchall()
    result = []
    for row in rows:
        masters = conn.execute(
            "SELECT s.id, s.name FROM staff_guilds sg JOIN staff s ON s.id = sg.staff_id "
            "WHERE sg.guild_id = ? ORDER BY s.name COLLATE NOCASE", (row["id"],)
        ).fetchall()
        students = conn.execute("SELECT COUNT(*) FROM student_guilds WHERE role_id = ?", (row["role_id"],)).fetchone()[0]
        result.append(dict(row, guild_masters=[dict(m) for m in masters], students=students))
    return result


def find(conn: sqlite3.Connection, guild_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM guilds WHERE id = ?", (guild_id,)).fetchone()


def free_roles(conn: sqlite3.Connection, keep_role_id: int | None = None) -> list[dict]:
    """Professional roles without a guild (plus the role of the guild being edited)."""
    return [dict(r) for r in conn.execute(
        "SELECT id, code, name FROM professional_roles "
        "WHERE id NOT IN (SELECT role_id FROM guilds) OR id = ? ORDER BY code", (keep_role_id or -1,))]


def validate(conn: sqlite3.Connection, code: str, name: str, role_id: str, color: str,
             guild_id: int | None = None) -> tuple[dict | None, str | None]:
    """F15: returns (clean values, None) or (None, Dutch error message)."""
    code, name, color = code.strip().upper(), " ".join(name.split()), color.strip()
    if not _CODE.match(code):
        return None, "De code bestaat uit 2 of 3 letters, bijvoorbeeld FE of BIT."
    if not name:
        return None, "Vul een naam in."
    if not role_id.isdigit() or not conn.execute("SELECT 1 FROM professional_roles WHERE id = ?", (int(role_id),)).fetchone():
        return None, "Kies een beroepsrol."
    if not _COLOR.match(color):
        color = DEFAULT_COLOR
    other = conn.execute("SELECT * FROM guilds WHERE code = ? AND id != ?", (code, guild_id or -1)).fetchone()
    if other:
        return None, f"Er is al een gilde met de code {code}."
    other = conn.execute("SELECT g.name, r.name AS role FROM guilds g JOIN professional_roles r ON r.id = g.role_id "
                         "WHERE g.role_id = ? AND g.id != ?", (int(role_id), guild_id or -1)).fetchone()
    if other:
        return None, f"De beroepsrol {other['role']} heeft al een gilde: {other['name']}."
    return {"code": code, "name": name, "role_id": int(role_id), "color": color}, None


def create(conn: sqlite3.Connection, values: dict) -> int:
    with conn:
        return conn.execute("INSERT INTO guilds (code, name, role_id, color) VALUES (:code, :name, :role_id, :color)",
                            values).lastrowid


def update(conn: sqlite3.Connection, guild_id: int, values: dict) -> None:
    with conn:
        conn.execute("UPDATE guilds SET code = :code, name = :name, role_id = :role_id, color = :color WHERE id = :id",
                     dict(values, id=guild_id))


def delete(conn: sqlite3.Connection, guild_id: int) -> None:
    """F17: guild masters keep their role; only the link to this guild goes (cascade)."""
    with conn:
        conn.execute("DELETE FROM guilds WHERE id = ?", (guild_id,))


def add_preset(conn: sqlite3.Connection, codes: set[str] | None = None, *, is_demo: bool = False) -> int:
    """F14: add the Open-ICT guilds (or only `codes`), each with the role of the same code.
    Skips a guild whose code or role is taken, or whose code is not a role. Returns the number added."""
    added = 0
    with conn:
        for code, name in read_preset():
            if codes is not None and code not in codes:
                continue
            role = conn.execute("SELECT id FROM professional_roles WHERE code = ?", (code,)).fetchone()
            if role is None:
                continue
            if conn.execute("SELECT 1 FROM guilds WHERE code = ? OR role_id = ?", (code, role["id"])).fetchone():
                continue
            conn.execute("INSERT INTO guilds (code, name, role_id, color, is_demo) VALUES (?, ?, ?, ?, ?)",
                         (code, name, role["id"], DEFAULT_COLOR, int(is_demo)))
            added += 1
    return added
