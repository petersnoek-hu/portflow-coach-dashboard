"""Projects, called squads in the code (spec 012; docs/gegevensmodel.md#squad-project)."""

import re
import sqlite3
from pathlib import Path

from .portflow_connection import initials

PRESET_FILE = Path(__file__).resolve().parent.parent / "docs" / "openict-projecten.md"


def full_name(number: str | None, name: str) -> str:
    return f"{number} {name}" if number else name


def read_preset(path: Path = PRESET_FILE) -> list[dict]:
    """Rows '| NN | Projectnaam | Opdrachtgever | Weergave |' from docs/openict-projecten.md (F5, F11).
    The Weergave column may be missing."""
    if not path.exists():
        return []
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [" ".join(c.split()) for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.fullmatch(r"\d{1,2}", cells[0]):
            continue
        number = cells[0].zfill(2)
        short = cells[3] if len(cells) > 3 and cells[3] else ""
        result.append({"number": number, "name": cells[1], "client": cells[2],
                       "display_name": with_number(short, number) if short else default_display(number, cells[1], cells[2])})
    return result


def with_number(text: str, number: str | None) -> str:
    """F11: 'Condor - Gamified learning' + 02 -> 'Condor - Gamified learning (02)'."""
    return f"{text} ({number})" if number else text


def default_display(number: str | None, name: str, client: str) -> str:
    """F11: 'Opdrachtgever - Projectnaam (NN)' for a project added by hand."""
    return with_number(f"{client} - {name}" if client else name, number)


def fill_display_names(conn: sqlite3.Connection) -> None:
    """F11: give existing projects without a display name the one from the file, else the default."""
    preset = {p["number"]: p["display_name"] for p in read_preset()}
    for row in conn.execute("SELECT id, number, name, client FROM squads WHERE display_name = ''").fetchall():
        display = preset.get(row["number"]) or default_display(row["number"], row["name"], row["client"])
        conn.execute("UPDATE squads SET display_name = ? WHERE id = ?", (display, row["id"]))


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


def validate(conn: sqlite3.Connection, number: str, name: str, client: str,
             squad_id: int | None = None, display_name: str = "") -> tuple[dict | None, str | None]:
    """F7, F10: returns (clean values, None) or (None, Dutch error message)."""
    number, name, client = number.strip(), " ".join(name.split()), " ".join(client.split())
    display_name = " ".join(display_name.split())
    if not name:
        return None, "Vul een naam in."
    if number and (not number.isdigit() or len(number) > 2):
        return None, "Een nummer bestaat uit 1 of 2 cijfers, bijvoorbeeld 02."
    number = number.zfill(2) if number else None
    if number and conn.execute("SELECT 1 FROM squads WHERE number = ? AND id != ?", (number, squad_id or -1)).fetchone():
        return None, f"Er is al een project met nummer {number}."
    return {"number": number, "name": name, "client": client,
            "full_name": full_name(number, name),
            "display_name": display_name or default_display(number, name, client)}, None


def create(conn: sqlite3.Connection, values: dict, *, is_demo: bool = False) -> int:
    with conn:
        return conn.execute("INSERT INTO squads (number, name, client, full_name, display_name, is_demo) "
                            "VALUES (:number, :name, :client, :full_name, :display_name, :is_demo)",
                            dict(values, is_demo=int(is_demo))).lastrowid


def update(conn: sqlite3.Connection, squad_id: int, values: dict) -> None:
    """F8: the students stay in the project."""
    with conn:
        conn.execute("UPDATE squads SET number = :number, name = :name, client = :client, full_name = :full_name, "
                     "display_name = :display_name WHERE id = :id", dict(values, id=squad_id))


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
        create(conn, dict(project, full_name=full_name(project["number"], project["name"])))  # F11
        added += 1
    return added
