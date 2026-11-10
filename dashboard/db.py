"""SQLite storage. The tables follow docs/gegevensmodel.md, as far as needed so far."""

import re
import sqlite3
from pathlib import Path

from flask import Flask, current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

-- Coaches and guild masters: one person, one or both roles (specs 006, 007).
CREATE TABLE IF NOT EXISTS staff (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,   -- full name: first_name + ' ' + last_name, as in Portflow
    first_name      TEXT NOT NULL DEFAULT '',
    last_name       TEXT NOT NULL DEFAULT '',
    is_coach        INTEGER NOT NULL DEFAULT 0,
    is_guild_master INTEGER NOT NULL DEFAULT 0,
    is_demo         INTEGER NOT NULL DEFAULT 0
);

-- Projects (squads), spec 012. full_name is derived: "NN name", or the name without a number.
CREATE TABLE IF NOT EXISTS squads (
    id        INTEGER PRIMARY KEY,
    number    TEXT,                          -- two digits, unique when filled
    name      TEXT NOT NULL,
    client    TEXT NOT NULL DEFAULT '',      -- opdrachtgever
    display_name TEXT NOT NULL DEFAULT '',   -- weergavenaam, shown in the overviews (spec 012, F10-F12)
    full_name TEXT NOT NULL,
    is_demo   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS students (
    id               INTEGER PRIMARY KEY,
    name             TEXT NOT NULL,
    student_number   TEXT,
    semester         INTEGER,                -- 1..8, NULL = nog in te delen
    start_date       TEXT,                   -- own start of the semester period
    squad_id         INTEGER REFERENCES squads(id) ON DELETE SET NULL,
    squad_role       TEXT,                   -- PO, SM, 2ePO, 2eSM
    track            TEXT,                   -- invulling
    coach_id         INTEGER REFERENCES staff(id) ON DELETE SET NULL,
    portflow_user_id INTEGER,                -- Portflow's inviter.id (spec 004), unique per student
    has_access       INTEGER NOT NULL DEFAULT 1,  -- 0 = portfolio not shared (n/b)
    fetched_at       TEXT,                   -- last successful fetch from Portflow (spec 005)
    notes            TEXT,                   -- free text; Excel import puts unknown columns here (spec 013)
    is_demo          INTEGER NOT NULL DEFAULT 0
);

-- A student can have more than one shared portfolio (docs/gegevensmodel.md#student).
CREATE TABLE IF NOT EXISTS student_portfolios (
    student_id   INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    portfolio_id INTEGER NOT NULL,
    PRIMARY KEY (student_id, portfolio_id)
);

-- Guilds, each with its professional role (spec 006, F12-F19; spec 018; docs/gegevensmodel.md#gilde).
CREATE TABLE IF NOT EXISTS guilds (
    id          INTEGER PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    role_name   TEXT NOT NULL DEFAULT '',       -- beroepsrol, e.g. "Front-end developer"
    description TEXT NOT NULL DEFAULT '',       -- of the professional role
    color       TEXT NOT NULL DEFAULT '#909DB9',
    is_demo     INTEGER NOT NULL DEFAULT 0
);

-- The guilds of a student (spec 016, spec 018): zero or more guilds, each with its own
-- guild master. No order and no "primary" guild.
CREATE TABLE IF NOT EXISTS student_guilds (
    student_id      INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    guild_id        INTEGER NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
    guild_master_id INTEGER REFERENCES staff(id) ON DELETE SET NULL,
    PRIMARY KEY (student_id, guild_id)
);

-- The guilds of a guild master (spec 006, F7, F18).
CREATE TABLE IF NOT EXISTS staff_guilds (
    staff_id INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    guild_id INTEGER NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
    PRIMARY KEY (staff_id, guild_id)
);

-- Semesters with the assessment programme as free text (spec 009; docs/gegevensmodel.md#semester).
-- A student's semester stays a number in students.semester.
CREATE TABLE IF NOT EXISTS semesters (
    id          INTEGER PRIMARY KEY,
    number      INTEGER NOT NULL UNIQUE,     -- 1..8
    osiris_code TEXT NOT NULL DEFAULT '',
    min_level   TEXT NOT NULL DEFAULT '',    -- minimum niveau toetsing (LEF)
    kpm_level   TEXT NOT NULL DEFAULT '',    -- niveau KPM
    mastery     TEXT NOT NULL DEFAULT '',    -- beheersingsniveau (Taakgericht, ...)
    is_demo     INTEGER NOT NULL DEFAULT 0
);

-- Custom columns (docs/gegevensmodel.md#kolommen); managed in the spec Kolommen.
CREATE TABLE IF NOT EXISTS custom_columns (
    id          INTEGER PRIMARY KEY,
    code        TEXT NOT NULL,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    type        TEXT NOT NULL,               -- 'percentage' or 'text'
    position    INTEGER NOT NULL DEFAULT 0,
    is_demo     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS custom_values (
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    column_id  INTEGER NOT NULL REFERENCES custom_columns(id) ON DELETE CASCADE,
    value      TEXT NOT NULL,
    PRIMARY KEY (student_id, column_id)
);

-- Local copy of Portflow feedback items, one row per skill (spec 005).
CREATE TABLE IF NOT EXISTS evaluations (
    id                    INTEGER PRIMARY KEY,
    student_id            INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    skill                 TEXT NOT NULL,      -- OC, KO, ... RE
    kind                  TEXT NOT NULL,      -- 'assessed' or 'self'
    level                 TEXT,               -- '0' (startniveau) .. '4', NULL if not assessed
    date                  TEXT NOT NULL,      -- ISO date, '' if unknown
    assessor              TEXT,
    review_request_id     INTEGER,
    review_request_title  TEXT,
    review_request_status TEXT,               -- not_started, in_progress, submitted, scored, denied,
                                              -- or 'not_scored' (Portflow: review_request_scored false)
    is_demo               INTEGER NOT NULL DEFAULT 0
);
"""

# The students table on its own, to rebuild it without old columns (spec 018, F9).
STUDENTS_TABLE = re.search(r"CREATE TABLE IF NOT EXISTS students \(.*?\n\);", SCHEMA, re.S).group(0)
STUDENT_COLUMNS = [line.split()[0] for line in STUDENTS_TABLE.splitlines()[1:-1] if line.strip()]

def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: str) -> None:
    """Create the database file and tables if needed; safe to run on every start."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)  # no roles are added: a new dashboard starts without them (spec 008, F9)
    conn.close()


_SPLIT_NAME = ("first_name = CASE WHEN instr(name, ' ') > 0 THEN substr(name, 1, instr(name, ' ') - 1) ELSE name END, "
               "last_name = CASE WHEN instr(name, ' ') > 0 THEN substr(name, instr(name, ' ') + 1) ELSE '' END")


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns introduced after a table already existed (there is no migration tool)."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(students)")}
    if "portflow_user_id" not in columns:
        conn.execute("ALTER TABLE students ADD COLUMN portflow_user_id INTEGER")
    if "fetched_at" not in columns:
        conn.execute("ALTER TABLE students ADD COLUMN fetched_at TEXT")
    if "notes" not in columns:
        conn.execute("ALTER TABLE students ADD COLUMN notes TEXT")
    has_roles = _table_exists(conn, "professional_roles")   # before spec 018
    role_columns = {row["name"] for row in conn.execute("PRAGMA table_info(professional_roles)")}
    if has_roles and "color" not in role_columns:
        conn.execute("ALTER TABLE professional_roles ADD COLUMN color TEXT NOT NULL DEFAULT '#909DB9'")
        conn.execute("ALTER TABLE professional_roles ADD COLUMN is_demo INTEGER NOT NULL DEFAULT 0")
    squad_columns = {row["name"] for row in conn.execute("PRAGMA table_info(squads)")}
    if "number" not in squad_columns:
        # Spec 012: take the number from the full name ("04 Horizon" -> 04, "Horizon").
        conn.execute("ALTER TABLE squads ADD COLUMN number TEXT")
        conn.execute("ALTER TABLE squads ADD COLUMN client TEXT NOT NULL DEFAULT ''")
        for row in conn.execute("SELECT id, full_name FROM squads").fetchall():
            first, _, rest = (row["full_name"] or "").partition(" ")
            if first.isdigit() and len(first) <= 2 and rest:
                conn.execute("UPDATE squads SET number = ?, name = ? WHERE id = ?", (first.zfill(2), rest, row["id"]))
    if has_roles:
        _migrate_student_guilds(conn, columns)
    squad_columns = {row["name"] for row in conn.execute("PRAGMA table_info(squads)")}
    if "display_name" not in squad_columns:
        conn.execute("ALTER TABLE squads ADD COLUMN display_name TEXT NOT NULL DEFAULT ''")
        from .projects import fill_display_names   # F11: existing projects, once
        fill_display_names(conn)
    if "color" in squad_columns:
        conn.execute("ALTER TABLE squads DROP COLUMN color")   # spec 012: projects have no colour any more
    staff_columns = {row["name"] for row in conn.execute("PRAGMA table_info(staff)")}
    if "is_coach" not in staff_columns:
        # Before specs 006/007 the list had no roles; existing names become coaches.
        conn.execute("ALTER TABLE staff ADD COLUMN is_coach INTEGER NOT NULL DEFAULT 0")
        conn.execute("ALTER TABLE staff ADD COLUMN is_guild_master INTEGER NOT NULL DEFAULT 0")
        conn.execute("UPDATE staff SET is_coach = 1")
    if "first_name" not in staff_columns:
        # Spec 006, F20: split existing names at the first space.
        conn.execute("ALTER TABLE staff ADD COLUMN first_name TEXT NOT NULL DEFAULT ''")
        conn.execute("ALTER TABLE staff ADD COLUMN last_name TEXT NOT NULL DEFAULT ''")
        conn.execute(f"UPDATE staff SET {_SPLIT_NAME}")
    # Any insert with only a full name gets it split at the first space (spec 006, F20).
    conn.execute("CREATE TRIGGER IF NOT EXISTS staff_split_name AFTER INSERT ON staff "
                 f"WHEN NEW.first_name = '' BEGIN UPDATE staff SET {_SPLIT_NAME} WHERE id = NEW.id; END")
    guild_link_columns = {row["name"] for row in conn.execute("PRAGMA table_info(staff_guilds)")}
    if "role_id" in guild_link_columns:
        # Before guilds had their own list, a guild master's guilds were professional roles.
        # Those links lapse (spec 006, open question "Bestaande koppelingen").
        conn.execute("DROP TABLE staff_guilds")
        conn.execute("CREATE TABLE staff_guilds ("
                     "staff_id INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE, "
                     "guild_id INTEGER NOT NULL REFERENCES guilds(id) ON DELETE CASCADE, "
                     "PRIMARY KEY (staff_id, guild_id))")
    if has_roles:
        _merge_roles_into_guilds(conn)
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_students_portflow_user "
        "ON students(portflow_user_id) WHERE portflow_user_id IS NOT NULL"
    )


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() is not None


def _merge_roles_into_guilds(conn: sqlite3.Connection) -> None:
    """Spec 018, F9: the professional role becomes a field of its guild; a role without a guild
    becomes a guild; the guilds of students point to the guild; the list of roles goes."""
    from .guilds import read_preset

    conn.commit()
    conn.execute("PRAGMA foreign_keys = OFF")   # tables are rebuilt; ids stay the same
    try:
        preset_names = {code: name for code, name, _ in read_preset()}
        guild_columns = {row["name"] for row in conn.execute("PRAGMA table_info(guilds)")}
        conn.execute("CREATE TABLE guilds_new (id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL, "
                     "role_name TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '', "
                     "color TEXT NOT NULL DEFAULT '#909DB9', is_demo INTEGER NOT NULL DEFAULT 0)")
        guild_of_role: dict[int, int] = {}
        if "role_id" in guild_columns:
            for g in conn.execute("SELECT g.*, r.name AS role_name, r.description FROM guilds g "
                                  "JOIN professional_roles r ON r.id = g.role_id").fetchall():
                conn.execute("INSERT INTO guilds_new (id, code, name, role_name, description, color, is_demo) "
                             "VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (g["id"], g["code"], g["name"], g["role_name"], g["description"], g["color"], g["is_demo"]))
                guild_of_role[g["role_id"]] = g["id"]
        else:
            conn.execute("INSERT INTO guilds_new SELECT id, code, name, role_name, description, color, is_demo FROM guilds")
        for r in conn.execute("SELECT * FROM professional_roles").fetchall():
            if r["id"] in guild_of_role:
                continue
            same_code = conn.execute("SELECT id FROM guilds_new WHERE code = ?", (r["code"],)).fetchone()
            if same_code:
                guild_of_role[r["id"]] = same_code["id"]
                continue
            guild_of_role[r["id"]] = conn.execute(
                "INSERT INTO guilds_new (code, name, role_name, description, color, is_demo) VALUES (?, ?, ?, ?, ?, ?)",
                (r["code"], preset_names.get(r["code"], r["name"]), r["name"], r["description"], r["color"], r["is_demo"]),
            ).lastrowid
        conn.execute("DROP TABLE guilds")
        conn.execute("ALTER TABLE guilds_new RENAME TO guilds")

        links = conn.execute("SELECT student_id, role_id, guild_master_id FROM student_guilds").fetchall()
        conn.execute("DROP TABLE student_guilds")
        conn.execute("CREATE TABLE student_guilds ("
                     "student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE, "
                     "guild_id INTEGER NOT NULL REFERENCES guilds(id) ON DELETE CASCADE, "
                     "guild_master_id INTEGER REFERENCES staff(id) ON DELETE SET NULL, "
                     "PRIMARY KEY (student_id, guild_id))")
        conn.executemany("INSERT OR IGNORE INTO student_guilds (student_id, guild_id, guild_master_id) VALUES (?, ?, ?)",
                         [(l["student_id"], guild_of_role[l["role_id"]], l["guild_master_id"])
                          for l in links if l["role_id"] in guild_of_role])

        # The old columns primary_role_id and guild_master_id (spec 016) refer to the role list;
        # rebuild students without them, or every change to a student would fail.
        student_columns = [row["name"] for row in conn.execute("PRAGMA table_info(students)")]
        if "primary_role_id" in student_columns:
            keep = [c for c in STUDENT_COLUMNS if c in student_columns]
            conn.execute(STUDENTS_TABLE.replace("CREATE TABLE IF NOT EXISTS students", "CREATE TABLE students_new"))
            conn.execute(f"INSERT INTO students_new ({', '.join(keep)}) SELECT {', '.join(keep)} FROM students")
            conn.execute("DROP TABLE students")
            conn.execute("ALTER TABLE students_new RENAME TO students")
        conn.execute("DROP TABLE professional_roles")
        conn.commit()
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def _migrate_student_guilds(conn: sqlite3.Connection, student_columns: set[str]) -> None:
    """Spec 016, F3: primary role + guild master and secondary roles become rows in
    student_guilds. The old columns stay in old databases, but are emptied and unused."""
    if "primary_role_id" in student_columns:
        conn.execute("INSERT OR IGNORE INTO student_guilds (student_id, role_id, guild_master_id) "
                     "SELECT id, primary_role_id, guild_master_id FROM students WHERE primary_role_id IS NOT NULL")
        conn.execute("UPDATE students SET primary_role_id = NULL, guild_master_id = NULL")
    exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'student_secondary_roles'").fetchone()
    if exists:
        conn.execute("INSERT OR IGNORE INTO student_guilds (student_id, role_id) "
                     "SELECT student_id, role_id FROM student_secondary_roles")
        conn.execute("DROP TABLE student_secondary_roles")


def get_setting(path: str, key: str, default: str | None = None) -> str | None:
    """Read a setting; usable outside a request (for example in a background thread)."""
    conn = connect(path)
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    finally:
        conn.close()
    return row["value"] if row and row["value"] is not None else default


def set_setting(path: str, key: str, value: str | None) -> None:
    conn = connect(path)
    try:
        with conn:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
    finally:
        conn.close()


S_USER_ADDED_AS_COACH = "user_added_as_coach"


def add_user_as_coach(path: str, name: str) -> None:
    """Spec 007, F2a: the user is added as coach automatically, but only once; if the user
    removes themself later, connecting again does not add them back."""
    if get_setting(path, S_USER_ADDED_AS_COACH) == "1":
        return
    conn = connect(path)
    try:
        with conn:
            row = conn.execute("SELECT id FROM staff WHERE name = ? AND is_demo = 0", (name,)).fetchone()
            if row:
                conn.execute("UPDATE staff SET is_coach = 1 WHERE id = ?", (row["id"],))
            else:
                conn.execute("INSERT INTO staff (name, is_coach, is_demo) VALUES (?, 1, 0)", (name,))
    finally:
        conn.close()
    set_setting(path, S_USER_ADDED_AS_COACH, "1")


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_app(app: Flask) -> None:
    init_db(app.config["DATABASE"])
    app.teardown_appcontext(close_db)
