"""SQLite storage. The tables follow docs/gegevensmodel.md, as far as needed so far."""

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
    name            TEXT NOT NULL UNIQUE,
    is_coach        INTEGER NOT NULL DEFAULT 0,
    is_guild_master INTEGER NOT NULL DEFAULT 0,
    is_demo         INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS professional_roles (
    id          INTEGER PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    color       TEXT NOT NULL DEFAULT '#909DB9',   -- spec 008
    is_demo     INTEGER NOT NULL DEFAULT 0
);

-- Projects (squads), spec 012. full_name is derived: "NN name", or the name without a number.
CREATE TABLE IF NOT EXISTS squads (
    id        INTEGER PRIMARY KEY,
    number    TEXT,                          -- two digits, unique when filled
    name      TEXT NOT NULL,
    client    TEXT NOT NULL DEFAULT '',      -- opdrachtgever
    full_name TEXT NOT NULL,
    color     TEXT NOT NULL DEFAULT '#909DB9',
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

-- The guilds of a student (spec 016): zero or more professional roles, each with its own
-- guild master. No order and no "primary" guild.
CREATE TABLE IF NOT EXISTS student_guilds (
    student_id      INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    role_id         INTEGER NOT NULL REFERENCES professional_roles(id) ON DELETE CASCADE,
    guild_master_id INTEGER REFERENCES staff(id) ON DELETE SET NULL,
    PRIMARY KEY (student_id, role_id)
);

-- Guilds: one per professional role at most (spec 006, F12-F19; docs/gegevensmodel.md#gilde).
CREATE TABLE IF NOT EXISTS guilds (
    id      INTEGER PRIMARY KEY,
    code    TEXT NOT NULL UNIQUE,
    name    TEXT NOT NULL,
    role_id INTEGER NOT NULL UNIQUE REFERENCES professional_roles(id) ON DELETE CASCADE,
    color   TEXT NOT NULL DEFAULT '#909DB9',
    is_demo INTEGER NOT NULL DEFAULT 0
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


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns introduced after a table already existed (there is no migration tool)."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(students)")}
    if "portflow_user_id" not in columns:
        conn.execute("ALTER TABLE students ADD COLUMN portflow_user_id INTEGER")
    if "fetched_at" not in columns:
        conn.execute("ALTER TABLE students ADD COLUMN fetched_at TEXT")
    if "notes" not in columns:
        conn.execute("ALTER TABLE students ADD COLUMN notes TEXT")
    role_columns = {row["name"] for row in conn.execute("PRAGMA table_info(professional_roles)")}
    if "color" not in role_columns:
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
    _migrate_student_guilds(conn, columns)
    staff_columns = {row["name"] for row in conn.execute("PRAGMA table_info(staff)")}
    if "is_coach" not in staff_columns:
        # Before specs 006/007 the list had no roles; existing names become coaches.
        conn.execute("ALTER TABLE staff ADD COLUMN is_coach INTEGER NOT NULL DEFAULT 0")
        conn.execute("ALTER TABLE staff ADD COLUMN is_guild_master INTEGER NOT NULL DEFAULT 0")
        conn.execute("UPDATE staff SET is_coach = 1")
    guild_link_columns = {row["name"] for row in conn.execute("PRAGMA table_info(staff_guilds)")}
    if "role_id" in guild_link_columns:
        # Before guilds had their own list, a guild master's guilds were professional roles.
        # Those links lapse (spec 006, open question "Bestaande koppelingen").
        conn.execute("DROP TABLE staff_guilds")
        conn.execute("CREATE TABLE staff_guilds ("
                     "staff_id INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE, "
                     "guild_id INTEGER NOT NULL REFERENCES guilds(id) ON DELETE CASCADE, "
                     "PRIMARY KEY (staff_id, guild_id))")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_students_portflow_user "
        "ON students(portflow_user_id) WHERE portflow_user_id IS NOT NULL"
    )


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
