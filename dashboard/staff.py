"""Coaches and guild masters (specs 006 and 007): one person, one or both roles.

`role` is always "coach" or "guild_master"; the pages differ only in that value.
"""

import re
import sqlite3
from pathlib import Path

from .progress import normalize_name
from .skills import COACH_SKILLS, PRODUCT_SKILLS

ROLES = ("coach", "guild_master")
ROLE_COLUMN = {"coach": "is_coach", "guild_master": "is_guild_master"}
# Which students belong to a person: coach is a field on the student; guild master is per guild (spec 016).
STUDENTS_SQL = {"coach": "SELECT id, name FROM students WHERE coach_id = ? ORDER BY name",
                "guild_master": "SELECT DISTINCT s.id, s.name FROM student_guilds sg JOIN students s ON s.id = sg.student_id "
                                "WHERE sg.guild_master_id = ? ORDER BY s.name"}


def _check(role: str) -> None:
    if role not in ROLES:
        raise ValueError(role)


def known_assessors(conn: sqlite3.Connection) -> set[str]:
    """Names whose evaluations count (voortgangsregels.md#welke-evaluaties-tellen)."""
    return {row[0] for row in conn.execute("SELECT name FROM staff WHERE is_coach = 1 OR is_guild_master = 1")}


def people(conn: sqlite3.Connection, role: str, user_name: str | None) -> list[dict]:
    """The cards of a page (F2): name, other role, guilds, students and counted evaluations."""
    _check(role)
    from . import overview  # counted evaluations follow the progress rules

    counted = overview.counted_evaluations_by_assessor(conn)
    rows = conn.execute(
        f"SELECT * FROM staff WHERE {ROLE_COLUMN[role]} = 1 ORDER BY name COLLATE NOCASE"
    ).fetchall()
    result = []
    for row in rows:
        students = conn.execute(STUDENTS_SQL[role], (row["id"],)).fetchall()
        guilds = conn.execute(
            "SELECT g.id, g.code, g.name, g.color FROM staff_guilds sg JOIN guilds g ON g.id = sg.guild_id "
            "WHERE sg.staff_id = ? ORDER BY g.code", (row["id"],)
        ).fetchall()
        result.append({
            "id": row["id"],
            "name": row["name"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "is_coach": bool(row["is_coach"]),
            "is_guild_master": bool(row["is_guild_master"]),
            "is_user": bool(user_name) and normalize_name(row["name"]) == normalize_name(user_name),
            "is_demo": bool(row["is_demo"]),
            "students": [dict(s) for s in students],
            "guilds": [dict(g) for g in guilds],
            "evaluations": counted.get(normalize_name(row["name"]), 0),
        })
    return result


def find(conn: sqlite3.Connection, staff_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM staff WHERE id = ?", (staff_id,)).fetchone()


def _by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    key = normalize_name(name)
    for row in conn.execute("SELECT * FROM staff"):
        if normalize_name(row["name"]) == key:
            return row
    return None


def full_name(first: str, last: str) -> str:
    """F20: the name as in Portflow."""
    return " ".join(f"{first} {last}".split())


def add(conn: sqlite3.Connection, names: list[str], role: str,
        split: dict[str, tuple[str, str]] | None = None) -> int:
    """Add names with a role (F5, F6, F10). Existing people get the role; returns the number added.
    New people are split at the first space (F20), unless `split` gives first and last name."""
    _check(role)
    added, seen = 0, set()
    with conn:
        for raw in names:
            name = " ".join(raw.split())
            if not name or normalize_name(name) in seen:
                continue
            seen.add(normalize_name(name))
            existing = _by_name(conn, name)
            if existing:
                if not existing[ROLE_COLUMN[role]]:
                    conn.execute(f"UPDATE staff SET {ROLE_COLUMN[role]} = 1 WHERE id = ?", (existing["id"],))
                    added += 1
            else:
                first, last = (split or {}).get(name, ("", ""))
                conn.execute(f"INSERT INTO staff (name, first_name, last_name, {ROLE_COLUMN[role]}) "
                             "VALUES (?, ?, ?, 1)", (name, first, last))
                added += 1
    return added


def parse_names(text: str) -> list[str]:
    """F6: one name per line; empty lines and duplicates (case, spaces) are skipped."""
    names, seen = [], set()
    for line in text.splitlines():
        name = " ".join(line.split())
        if name and normalize_name(name) not in seen:
            seen.add(normalize_name(name))
            names.append(name)
    return names


def assessor_names(conn: sqlite3.Connection) -> set[str]:
    """All assessors in the fetched evaluations (normalised)."""
    return {
        normalize_name(row[0])
        for row in conn.execute("SELECT DISTINCT assessor FROM evaluations WHERE kind = 'assessed' AND assessor IS NOT NULL")
    }


def candidates(conn: sqlite3.Connection, role: str) -> list[dict]:
    """F5 "Uit Portflow kiezen": every assessor in the fetched evaluations, with counts."""
    _check(role)
    rows = conn.execute(
        "SELECT assessor, skill, date FROM evaluations "
        "WHERE kind = 'assessed' AND assessor IS NOT NULL AND level IS NOT NULL"
    ).fetchall()
    by_name: dict[str, dict] = {}
    for row in rows:
        key = normalize_name(row["assessor"])
        entry = by_name.setdefault(key, {"name": " ".join(row["assessor"].split()), "total": 0,
                                         "product": 0, "coach": 0, "last": ""})
        entry["total"] += 1
        if row["skill"] in PRODUCT_SKILLS:
            entry["product"] += 1
        elif row["skill"] in COACH_SKILLS:
            entry["coach"] += 1
        entry["last"] = max(entry["last"], row["date"] or "")
    with_role = {normalize_name(r[0]) for r in conn.execute(f"SELECT name FROM staff WHERE {ROLE_COLUMN[role]} = 1")}
    sort_on = "product" if role == "guild_master" else "coach"
    result = [dict(entry, has_role=key in with_role) for key, entry in by_name.items()]
    result.sort(key=lambda e: (-e[sort_on], -e["total"], e["name"].casefold()))
    return result


def update_name(conn: sqlite3.Connection, staff_id: int, first: str, last: str) -> str | None:
    """F7, F20: returns an error message (Dutch) or None."""
    first, last = " ".join(first.split()), " ".join(last.split())
    if not first:
        return "Vul een voornaam in."
    name = full_name(first, last)
    other = _by_name(conn, name)
    if other and other["id"] != staff_id:
        return f"Er staat al iemand met de naam {other['name']} in de lijst."
    with conn:
        conn.execute("UPDATE staff SET name = ?, first_name = ?, last_name = ? WHERE id = ?",
                     (name, first, last, staff_id))
    return None


def set_guilds(conn: sqlite3.Connection, staff_id: int, guild_ids: list[int]) -> None:
    """F7, F18: the guilds of a guild master, chosen from the guilds."""
    with conn:
        conn.execute("DELETE FROM staff_guilds WHERE staff_id = ?", (staff_id,))
        conn.executemany("INSERT OR IGNORE INTO staff_guilds (staff_id, guild_id) "
                         "SELECT ?, id FROM guilds WHERE id = ?",
                         [(staff_id, guild_id) for guild_id in guild_ids])


def remove_role(conn: sqlite3.Connection, staff_id: int, role: str) -> None:
    """F8: the role goes, the field is emptied at the students; without roles the person goes."""
    _check(role)
    with conn:
        if role == "coach":
            conn.execute("UPDATE students SET coach_id = NULL WHERE coach_id = ?", (staff_id,))
        else:  # spec 016, F7: empty this guild master at every guild of every student
            conn.execute("UPDATE student_guilds SET guild_master_id = NULL WHERE guild_master_id = ?", (staff_id,))
        conn.execute(f"UPDATE staff SET {ROLE_COLUMN[role]} = 0 WHERE id = ?", (staff_id,))
        if role == "guild_master":
            conn.execute("DELETE FROM staff_guilds WHERE staff_id = ?", (staff_id,))
        conn.execute("DELETE FROM staff WHERE id = ? AND is_coach = 0 AND is_guild_master = 0", (staff_id,))


# Open-ICT guild masters, September 2026 (spec 006, F11) -------------------------------------

PRESET_FILE = Path(__file__).resolve().parent.parent / "docs" / "gildemeesters-sept2026.md"
_PRESET_ROW = re.compile(r"^\|([^|]*)\|([^|]*)\|\s*([A-Za-z]+)\s*\|\s*$")


def read_preset(path: Path = PRESET_FILE) -> list[tuple[str, str, str]]:
    """Rows '| Voornaam | Achternaam | Gilde |' from docs/gildemeesters-sept2026.md (F22)."""
    if not path.exists():
        return []
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _PRESET_ROW.match(line)
        if m and m.group(1).strip() and m.group(1).strip() != "Voornaam":
            result.append((" ".join(m.group(1).split()), " ".join(m.group(2).split()), m.group(3).upper()))
    return result


def add_guild_masters_with_guilds(conn: sqlite3.Connection, rows: list[tuple[str, str, str]]) -> int:
    """F11: missing Open-ICT guilds are added first; then each name becomes guild master with
    the guild of that code (existing guilds stay). A code that is no Open-ICT guild either is
    skipped. Returns the number of guild masters added."""
    from . import guilds

    guilds.add_preset(conn, {code for _, _, code in rows})
    split = {full_name(first, last): (first, last) for first, last, _ in rows}
    added = add(conn, list(split), "guild_master", split)
    with conn:
        for first, last, code in rows:
            person = _by_name(conn, full_name(first, last))
            guild = conn.execute("SELECT id FROM guilds WHERE code = ?", (code,)).fetchone()
            if person and guild:
                conn.execute("INSERT OR IGNORE INTO staff_guilds (staff_id, guild_id) VALUES (?, ?)",
                             (person["id"], guild["id"]))
    return added
