"""SQLite storage. The tables follow docs/gegevensmodel.md, as far as needed so far."""

import sqlite3
from pathlib import Path

from flask import Flask, current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

-- The managed list of coaches and guild masters (Instellingen).
CREATE TABLE IF NOT EXISTS staff (
    id      INTEGER PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE,
    is_demo INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS professional_roles (
    id          INTEGER PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS squads (
    id        INTEGER PRIMARY KEY,
    name      TEXT NOT NULL,
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
    primary_role_id  INTEGER REFERENCES professional_roles(id) ON DELETE SET NULL,
    coach_id         INTEGER REFERENCES staff(id) ON DELETE SET NULL,
    guild_master_id  INTEGER REFERENCES staff(id) ON DELETE SET NULL,
    has_access       INTEGER NOT NULL DEFAULT 1,  -- 0 = portfolio not shared (n/b)
    is_demo          INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS student_secondary_roles (
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    role_id    INTEGER NOT NULL REFERENCES professional_roles(id) ON DELETE CASCADE,
    PRIMARY KEY (student_id, role_id)
);

-- Local copy of Portflow feedback items, one row per skill.
CREATE TABLE IF NOT EXISTS evaluations (
    id                    INTEGER PRIMARY KEY,
    student_id            INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    skill                 TEXT NOT NULL,      -- OC, KO, ... RE
    kind                  TEXT NOT NULL,      -- 'assessed' or 'self'
    level                 TEXT,               -- '0' (startniveau) .. '4', NULL if not assessed
    date                  TEXT NOT NULL,      -- ISO date
    assessor              TEXT,
    review_request_id     INTEGER,
    review_request_title  TEXT,
    review_request_status TEXT,               -- not_started, in_progress, submitted, scored, denied
    is_demo               INTEGER NOT NULL DEFAULT 0
);
"""

# The nine standard professional roles (docs/beroepsrollen.md).
DEFAULT_ROLES = [
    ("UX", "UI/UX designer"),
    ("BIT", "Business IT engineer"),
    ("CS", "Cybersecurity engineer"),
    ("CI", "Cloud & Infra engineer"),
    ("FE", "Front-end developer"),
    ("BE", "Back-end developer"),
    ("AI", "AI engineer"),
    ("GD", "Game developer"),
    ("TI", "Embedded technologie engineer"),
]


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
        conn.executemany(
            "INSERT OR IGNORE INTO professional_roles (code, name) VALUES (?, ?)", DEFAULT_ROLES
        )
    conn.close()


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
