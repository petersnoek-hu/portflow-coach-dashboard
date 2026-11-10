"""Semesters (spec 009; docs/gegevensmodel.md#semester): number, Osiris code and the
assessment programme as free text. A student's semester stays a number in `students`."""

import re
import sqlite3
from pathlib import Path

PRESET_FILE = Path(__file__).resolve().parent.parent / "docs" / "voortgangsregels.md"
PRESET_SECTION = "## Toetsprogramma: eisen per semester"
FIELDS = ("osiris_code", "min_level", "kpm_level", "mastery")

# F9: phase and colour follow from the number (docs/begrippen.md, docs/design-system.md#semesters).
PHASES = [(range(1, 3), "Propedeuse", "#5B76A8"), (range(3, 8), "Hoofdfase", "#4F6F62"),
          (range(8, 9), "Afstudeerfase", "#7D6BA8")]


def phase(number: int) -> tuple[str, str]:
    """(phase name, colour) for a semester number."""
    for numbers, name, color in PHASES:
        if number in numbers:
            return name, color
    return "", "#B9BFBB"


def read_preset(path: Path = PRESET_FILE) -> list[dict]:
    """F6: the rows of the table in docs/voortgangsregels.md#toetsprogramma-eisen-per-semester."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    start = text.find(PRESET_SECTION)
    if start < 0:
        return []
    result = []
    for line in text[start:].splitlines()[1:]:
        if line.startswith("## "):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not cells[0].isdigit():
            continue
        assignment = cells[1]
        result.append({
            "number": int(cells[0]),
            "osiris_code": cells[2].split(" ")[0] if cells[2] else "",   # without "(keuze, minor)"
            "min_level": cells[3],
            "kpm_level": cells[4],
            "mastery": f"{assignment}gericht" if assignment else "",    # Taak -> Taakgericht
        })
    return result


def all_semesters(conn: sqlite3.Connection) -> list[dict]:
    """The cards (F3): semester, phase, colour and its students."""
    result = []
    for row in conn.execute("SELECT * FROM semesters ORDER BY number"):
        students = conn.execute("SELECT id, name FROM students WHERE semester = ? ORDER BY name",
                                (row["number"],)).fetchall()
        name, color = phase(row["number"])
        result.append(dict(row, phase=name, color=color, students=[dict(s) for s in students]))
    return result


def summary(conn: sqlite3.Connection) -> tuple[int, int]:
    """F2: (students with a semester, number of semesters with at least one student)."""
    row = conn.execute("SELECT COUNT(*), COUNT(DISTINCT semester) FROM students WHERE semester IS NOT NULL").fetchone()
    return row[0], row[1]


def find(conn: sqlite3.Connection, semester_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM semesters WHERE id = ?", (semester_id,)).fetchone()


def validate(conn: sqlite3.Connection, number: str, values: dict, semester_id: int | None = None
             ) -> tuple[dict | None, str | None]:
    """F7: returns (clean values, None) or (None, Dutch error message)."""
    number = number.strip()
    if not number.isdigit() or not 1 <= int(number) <= 8:
        return None, "Het semesternummer is een heel getal van 1 tot en met 8."
    if conn.execute("SELECT 1 FROM semesters WHERE number = ? AND id != ?", (int(number), semester_id or -1)).fetchone():
        return None, f"Semester {int(number)} bestaat al."
    clean = {field: " ".join((values.get(field) or "").split()) for field in FIELDS}
    return dict(clean, number=int(number)), None


def create(conn: sqlite3.Connection, values: dict, *, is_demo: bool = False) -> int:
    with conn:
        return conn.execute(
            "INSERT INTO semesters (number, osiris_code, min_level, kpm_level, mastery, is_demo) "
            "VALUES (:number, :osiris_code, :min_level, :kpm_level, :mastery, :is_demo)",
            dict(values, is_demo=int(is_demo))).lastrowid


def update(conn: sqlite3.Connection, semester_id: int, values: dict) -> None:
    """F8: a new number moves the students of this semester along."""
    old = find(conn, semester_id)
    with conn:
        conn.execute("UPDATE semesters SET number = :number, osiris_code = :osiris_code, min_level = :min_level, "
                     "kpm_level = :kpm_level, mastery = :mastery WHERE id = :id", dict(values, id=semester_id))
        if old and old["number"] != values["number"]:
            conn.execute("UPDATE students SET semester = ? WHERE semester = ?", (values["number"], old["number"]))


def delete(conn: sqlite3.Connection, semester_id: int) -> None:
    """F10: the students of this semester go to "Nog in te delen"."""
    old = find(conn, semester_id)
    with conn:
        if old:
            conn.execute("UPDATE students SET semester = NULL WHERE semester = ?", (old["number"],))
        conn.execute("DELETE FROM semesters WHERE id = ?", (semester_id,))


def add_preset(conn: sqlite3.Connection, *, is_demo: bool = False) -> int:
    """F5: the Open-ICT semesters; a number that exists already is skipped. Returns the number added."""
    added = 0
    for values in read_preset():
        if conn.execute("SELECT 1 FROM semesters WHERE number = ?", (values["number"],)).fetchone():
            continue
        create(conn, values, is_demo=is_demo)
        added += 1
    return added
