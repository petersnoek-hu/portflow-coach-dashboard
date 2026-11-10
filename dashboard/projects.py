"""Projects, called squads in the code (spec 012; docs/gegevensmodel.md#squad-project)."""

import re
import sqlite3
from pathlib import Path

from .portflow_connection import initials

PRESET_FILE = Path(__file__).resolve().parent.parent / "docs" / "openict-projecten.md"
_PRESET_LINE = re.compile(r"^\|\s*(\d{1,2})\s*\|\s*(.+?)\s*\|\s*(.*?)\s*\|\s*$")
# F6: colours from the designs (docs/design-system.md#projecten), used in turn.
PALETTE = ["#7D6BA8", "#C17661", "#5E8C74", "#5B76A8", "#B58A4A", "#A86B8A", "#4F8FA8", "#6B8F3F"]
_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def full_name(number: str | None, name: str) -> str:
    return f"{number} {name}" if number else name


def read_preset(path: Path = PRESET_FILE) -> list[dict]:
    """Rows '| NN | Projectnaam | Opdrachtgever |' from docs/openict-projecten.md (F5)."""
    if not path.exists():
        return []
    return [{"number": m.group(1).zfill(2), "name": " ".join(m.group(2).split()), "client": " ".join(m.group(3).split())}
            for m in map(_PRESET_LINE.match, path.read_text(encoding="utf-8").splitlines()) if m]


def next_color(conn: sqlite3.Connection) -> str:
    """The next colour of the palette, after the projects that exist (F5, F6)."""
    count = conn.execute("SELECT COUNT(*) FROM squads").fetchone()[0]
    return PALETTE[count % len(PALETTE)]


def _students(conn, squad_id):
    sql = "SELECT id, name FROM students WHERE squad_id IS ? ORDER BY name"
    return [dict(r) for r in conn.execute(sql, (squad_id,))]


def all_projects(conn: sqlite3.Connection) -> list[dict]:
    """The cards (F3): by number, projects without a number after them, by name."""
    rows = conn.execute("SELECT * FROM squads ORDER BY number IS NULL, number, name COLLATE NOCASE").fetchall()
    return [dict(row, initials=project_initials(row["name"]), students=_students(conn, row["id"])) for row in rows]


def project_initials(name: str) -> str:
    """Two letters: first and last word ("Gamified Learning" -> GL); one word -> its first two ("BE")."""
    letters = initials(name)
    return letters if len(letters) >= 2 else "".join(c for c in name if c.isalnum())[:2].upper()


def without_project(conn: sqlite3.Connection) -> list[dict]:
    """F4: the students without a project."""
    return _students(conn, None)


def find(conn: sqlite3.Connection, squad_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM squads WHERE id = ?", (squad_id,)).fetchone()


def validate(conn: sqlite3.Connection, number: str, name: str, client: str, color: str,
             squad_id: int | None = None) -> tuple[dict | None, str | None]:
    """F7: returns (clean values, None) or (None, Dutch error message)."""
    number, name, client = number.strip(), " ".join(name.split()), " ".join(client.split())
    if not name:
        return None, "Vul een naam in."
    if number and (not number.isdigit() or len(number) > 2):
        return None, "Een nummer bestaat uit 1 of 2 cijfers, bijvoorbeeld 02."
    number = number.zfill(2) if number else None
    if number and conn.execute("SELECT 1 FROM squads WHERE number = ? AND id != ?", (number, squad_id or -1)).fetchone():
        return None, f"Er is al een project met nummer {number}."
    if not _COLOR.match(color.strip()):
        color = next_color(conn)
    return {"number": number, "name": name, "client": client, "color": color.strip(),
            "full_name": full_name(number, name)}, None


def create(conn: sqlite3.Connection, values: dict, *, is_demo: bool = False) -> int:
    with conn:
        return conn.execute("INSERT INTO squads (number, name, client, full_name, color, is_demo) "
                            "VALUES (:number, :name, :client, :full_name, :color, :is_demo)",
                            dict(values, is_demo=int(is_demo))).lastrowid


def update(conn: sqlite3.Connection, squad_id: int, values: dict) -> None:
    """F8: the students stay in the project."""
    with conn:
        conn.execute("UPDATE squads SET number = :number, name = :name, client = :client, full_name = :full_name, "
                     "color = :color WHERE id = :id", dict(values, id=squad_id))


def delete(conn: sqlite3.Connection, squad_id: int) -> None:
    """F9: the students stay, without a project (foreign key ON DELETE SET NULL)."""
    with conn:
        conn.execute("DELETE FROM squads WHERE id = ?", (squad_id,))


def add_preset(conn: sqlite3.Connection) -> int:
    """F5: the Open-ICT projects; a number that exists already is skipped. Returns the number added."""
    added = 0
    for project in read_preset():
        if conn.execute("SELECT 1 FROM squads WHERE number = ?", (project["number"],)).fetchone():
            continue
        create(conn, dict(project, color=next_color(conn), full_name=full_name(project["number"], project["name"])))
        added += 1
    return added
