"""The guilds of a student (spec 016): professional role + guild master, no order, no primary."""

import sqlite3

SQL = """
SELECT sg.student_id, sg.role_id, sg.guild_master_id, r.code, r.name,
       g.code AS guild_code, g.name AS guild_name, g.color AS guild_color, s.name AS guild_master, s.first_name AS guild_master_first
FROM student_guilds sg
JOIN professional_roles r ON r.id = sg.role_id
LEFT JOIN guilds g ON g.role_id = sg.role_id
LEFT JOIN staff s ON s.id = sg.guild_master_id
"""


def by_student(conn: sqlite3.Connection) -> dict[int, list[dict]]:
    """Per student their guilds, sorted on code (F5: sorting on the first code alphabetically)."""
    result: dict[int, list[dict]] = {}
    for row in conn.execute(SQL + " ORDER BY r.code"):
        result.setdefault(row["student_id"], []).append(dict(row))
    return result


def of_student(conn: sqlite3.Connection, student_id: int) -> list[dict]:
    return [dict(r) for r in conn.execute(SQL + " WHERE sg.student_id = ? ORDER BY r.code", (student_id,))]


def replace(conn: sqlite3.Connection, student_id: int, pairs: list[tuple[int, int | None]]) -> None:
    """F4: the guilds of one student become exactly `pairs` (role id, guild master id or None)."""
    conn.execute("DELETE FROM student_guilds WHERE student_id = ?", (student_id,))
    conn.executemany("INSERT INTO student_guilds (student_id, role_id, guild_master_id) VALUES (?, ?, ?)",
                     [(student_id, role_id, gm) for role_id, gm in pairs])


def add_or_fill(conn: sqlite3.Connection, student_id: int, role_id: int, guild_master_id: int | None) -> str | None:
    """F8: add a guild the student does not have yet, or fill an empty guild master.
    Returns 'added', 'filled' or None (nothing changed)."""
    row = conn.execute("SELECT guild_master_id FROM student_guilds WHERE student_id = ? AND role_id = ?",
                       (student_id, role_id)).fetchone()
    if row is None:
        conn.execute("INSERT INTO student_guilds (student_id, role_id, guild_master_id) VALUES (?, ?, ?)",
                     (student_id, role_id, guild_master_id))
        return "added"
    if row[0] is None and guild_master_id is not None:
        conn.execute("UPDATE student_guilds SET guild_master_id = ? WHERE student_id = ? AND role_id = ?",
                     (guild_master_id, student_id, role_id))
        return "filled"
    return None
