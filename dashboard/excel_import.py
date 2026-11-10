"""Importing students from an Excel file (spec 013): recognising columns, converting
values, finding existing students, the preview and saving. No HTML here.

Flow: read_workbook -> choose_sheet -> find_header / auto_mapping (F3, F4)
-> build_preview (F6-F10) -> apply (F11).
"""

import re
import sqlite3
from dataclasses import dataclass, field

from . import student_guilds
from .overview import TRACKS
from .progress import name_key, normalize_name
from .student_edit import SQUAD_ROLES
from .xlsx_reader import Sheet

HEADER_SEARCH_ROWS = 20

# F4: field -> recognised column names (compared with `normalize_header`). Extend here.
FIELDS = {
    "student_number": ("Studentnummer", ["nummer", "studentnummer", "studentnr", "ovnummer", "studentnumber"]),
    "name": ("Naam", ["naam", "student", "studentnaam", "voorenachternaam", "name", "volledigenaam"]),
    "semester": ("Semester", ["semester", "sem"]),
    "squad": ("Project", ["project", "projectgroep", "squad"]),
    "track": ("Invulling", ["invulling"]),
    "squad_role": ("Rol in de squad", ["rol", "rolinsquad", "rolindesquad", "squadrol"]),
    # Spec 016, F8: both columns become guilds of the student (no primary guild).
    "primary_role": ("Gilde", ["gilde", "beroepsrol", "primaireberoepsrol", "gildevoorkeur", "gildes"]),
    "secondary_roles": ("Extra gilde", ["eventueel2egilde", "2egilde", "tweedegilde", "3egilde", "derdegilde",
                                        "secundaireberoepsrol", "secundaireberoepsrollen"]),
    "coach": ("Coach", ["coach"]),
    "guild_master": ("Gildemeester", ["gildemeester"]),
}
NOTE, UNUSED = "note", "unused"
EXCEL_ERRORS = {"#n/a", "#n/b", "#ref!", "#value!", "#name?", "#div/0!", "#num!", "#null!", "#getting_data"}


def normalize_header(text: str) -> str:
    """Without case, spaces, '-', '_' and punctuation (F4)."""
    return re.sub(r"[^0-9a-z]", "", (text or "").casefold())


def clean(value: str) -> str:
    """Excel error values and empty cells count as empty (F7)."""
    value = " ".join((value or "").split())
    return "" if value.casefold() in EXCEL_ERRORS else value


# Sheet and header (F3, F4) --------------------------------------------------------------

def _known(header: str) -> str | None:
    key = normalize_header(header)
    for field_name, (_, names) in FIELDS.items():
        if key in names:
            return field_name
    return None


def find_header(rows: list[list[str]]) -> int | None:
    """Index of the row (within the first 20) with the most recognised column names."""
    best, best_count = None, 0
    for index, row in enumerate(rows[:HEADER_SEARCH_ROWS]):
        count = sum(1 for cell in row if _known(cell))
        if count > best_count:
            best, best_count = index, count
    if best is None:  # nothing recognised: the first row with at least two filled cells
        best = next((i for i, row in enumerate(rows[:HEADER_SEARCH_ROWS]) if sum(1 for c in row if c) >= 2), None)
    return best


def auto_mapping(header: list[str]) -> list[str]:
    """Per column a field, NOTE or UNUSED; a field goes to the first column that fits (F4)."""
    used, mapping = set(), []
    for cell in header:
        field_name = _known(cell)
        if field_name and field_name not in used:
            used.add(field_name)
            mapping.append(field_name)
        else:
            mapping.append(NOTE if cell.strip() else UNUSED)
    return mapping


def choose_sheet(sheets: list[Sheet]) -> int:
    """F3: the first sheet in which a name column is recognised (else the first sheet)."""
    for index, sheet in enumerate(sheets):
        header = find_header(sheet.rows)
        if header is not None and "name" in auto_mapping(sheet.rows[header]):
            return index
    return 0


def mapping_error(mapping: list[str]) -> str | None:
    """F5: a field once at most, and a name column is required."""
    fields = [m for m in mapping if m not in (NOTE, UNUSED)]
    duplicate = next((m for m in fields if fields.count(m) > 1), None)
    if duplicate:
        return f"{FIELDS[duplicate][0]} is aan meer dan één kolom gekoppeld. Kies voor één kolom."
    if "name" not in fields:
        return "Koppel een kolom aan Naam."
    return None


# Looking up values (F7) -------------------------------------------------------------------

@dataclass
class Lookups:
    semesters: set[int]
    squads: dict[str, dict]                 # number -> squad
    roles: list[dict]                       # guilds (spec 018)
    coaches: list[dict]
    guild_masters: list[dict]

    @classmethod
    def load(cls, conn: sqlite3.Connection) -> "Lookups":
        rows = lambda sql: [dict(r) for r in conn.execute(sql)]
        return cls(
            semesters={r["number"] for r in conn.execute("SELECT number FROM semesters")},
            squads={r["number"]: r for r in rows("SELECT id, number, full_name FROM squads WHERE number IS NOT NULL")},
            roles=rows("SELECT id, code, name, role_name FROM guilds"),   # spec 018: guilds
            coaches=rows("SELECT id, name FROM staff WHERE is_coach = 1"),
            guild_masters=rows("SELECT id, name FROM staff WHERE is_guild_master = 1"),
        )


def convert_semester(value: str, lookups: Lookups) -> tuple[int | None, str | None]:
    match = re.search(r"\d+", value)
    if not match or not 1 <= int(match.group(0)) <= 8:
        return None, f"Semester '{value}' niet herkend"
    number = int(match.group(0))
    if number not in lookups.semesters:
        return None, f"Semester {number} bestaat nog niet"
    return number, None


def convert_squad(value: str, lookups: Lookups) -> tuple[dict | None, str | None]:
    match = re.match(r"\s*(\d{1,2})\b", value)
    if not match:
        return None, f"Project '{value}' heeft geen nummer"
    number = match.group(1).zfill(2)
    squad = lookups.squads.get(number)
    return (squad, None) if squad else (None, f"Project {number} bestaat niet")


def convert_role(value: str, lookups: Lookups, label: str) -> tuple[dict | None, str | None]:
    match = re.search(r"\(\s*([A-Za-z]{2,3})\s*\)\s*$", value)
    candidates = [match.group(1)] if match else []
    candidates.append(value)
    for candidate in candidates:
        for role in lookups.roles:
            # Spec 018, F8: a guild is recognised by its code, name or professional role.
            if candidate.casefold() in (role["code"].casefold(), role["name"].casefold(), role["role_name"].casefold()):
                return role, None
    return None, f"{label} '{value}' niet herkend"


person_key = name_key  # one place for comparing names (progress.name_key)


def convert_person(value: str, people: list[dict], label: str) -> tuple[dict | None, str | None]:
    """Full name first; otherwise a first name that fits exactly one person (F7)."""
    key = person_key(value)
    exact = [p for p in people if person_key(p["name"]) == key]
    if exact:
        return exact[0], None
    if " " not in key:
        first = [p for p in people if person_key(p["name"]).split(" ")[0] == key]
        if len(first) == 1:
            return first[0], None
        if len(first) > 1:
            return None, f"{label} '{value}' past bij meer dan één persoon"
    return None, f"{label} '{value}' niet gevonden"


def convert_track(value: str) -> str | None:
    return next((t for t in TRACKS if t.casefold() == value.casefold()), None)


# Rows and preview (F6-F10) -------------------------------------------------------------------

@dataclass
class Row:
    number: int                              # row number in the sheet (1-based)
    name: str
    status: str = "new"                      # new, existing, unchanged, skipped
    reason: str = ""
    student_id: int | None = None
    values: dict = field(default_factory=dict)       # field -> (stored value, display text)
    guilds: list = field(default_factory=list)       # roles (spec 016)
    guild_master: dict | None = None                 # belongs to the first guild of the row
    notes: list = field(default_factory=list)        # "Kolomnaam: waarde"
    fills: list = field(default_factory=list)        # (field, label, display)
    changes: list = field(default_factory=list)      # (field, label, old display, new display)
    guild_fills: list = field(default_factory=list)  # (role, guild master or None, display) for existing students
    new_notes: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    mine_column: str | None = None          # F6: column in which the user's name appears

    @property
    def search(self) -> str:
        return self.name.casefold()


LABELS = {key: label for key, (label, _) in FIELDS.items()}
STUDENT_COLUMN = {"student_number": "student_number", "semester": "semester", "squad": "squad_id",
                  "track": "track", "squad_role": "squad_role", "coach": "coach_id"}


def _convert_row(cells: dict[str, str], lookups: Lookups, row: Row) -> None:
    """Fill row.values (column value + display text) and row.warnings (F7)."""
    def put(key, stored, display):
        row.values[key] = (stored, display)

    if cells.get("student_number"):
        put("student_number", cells["student_number"], cells["student_number"])
    if cells.get("semester"):
        number, warning = convert_semester(cells["semester"], lookups)
        put("semester", number, f"semester {number}") if number else row.warnings.append(warning)
    if cells.get("squad"):
        squad, warning = convert_squad(cells["squad"], lookups)
        put("squad", squad["id"], squad["full_name"]) if squad else row.warnings.append(warning)
    for key in ("primary_role", "secondary_roles"):   # spec 016, F8: all guild columns together
        parts = [cells.get(key, "")] if key == "primary_role" else re.split(r"[;/,]", cells.get(key, ""))
        for part in parts:
            if clean(part):
                role, warning = convert_role(clean(part), lookups, "Gilde")
                if role and role not in row.guilds:
                    row.guilds.append(role)
                elif warning:
                    row.warnings.append(warning)
    track_value = cells.get("track", "")
    if track_value:
        track = convert_track(track_value)
        put("track", track, track) if track else row.warnings.append(f"Invulling '{track_value}' niet herkend")
    if cells.get("squad_role"):
        code = next((c for c, _ in SQUAD_ROLES if c.casefold() == cells["squad_role"].casefold()), None)
        put("squad_role", code, code) if code else row.warnings.append(f"Rol '{cells['squad_role']}' niet herkend")
    if cells.get("coach"):
        value = cells["coach"]
        if value.casefold() == "stage" or value.casefold().startswith("minor"):
            if "track" not in row.values:   # spec 013, F7: Stage / Minor in the coach column is the track
                track = "Stage" if value.casefold() == "stage" else "Minor"
                put("track", track, track)
        else:
            person, warning = convert_person(value, lookups.coaches, "Coach")
            put("coach", person["id"], person["name"]) if person else row.warnings.append(warning)
    if cells.get("guild_master"):
        person, warning = convert_person(cells["guild_master"], lookups.guild_masters, "Gildemeester")
        if person and row.guilds:
            row.guild_master = person
        elif person:
            row.warnings.append(f"Gildemeester '{person['name']}' zonder gilde in deze rij")
        else:
            row.warnings.append(warning)


def _display(conn, key, value):
    """The current value of a student field as text, for 'old -> new' (F6)."""
    if value is None or value == "":
        return ""
    if key == "squad":
        row = conn.execute("SELECT full_name FROM squads WHERE id = ?", (value,)).fetchone()
        return row[0] if row else ""
    if key == "coach":
        row = conn.execute("SELECT name FROM staff WHERE id = ?", (value,)).fetchone()
        return row[0] if row else ""
    if key == "semester":
        return f"semester {value}"
    return str(value)


def user_keys(user_name: str | None) -> set[str]:
    """F6: the user's full name and first name, compared like person names."""
    if not user_name or not user_name.strip():
        return set()
    full = person_key(user_name)
    return {full, full.split(" ")[0]}


def build_preview(conn: sqlite3.Connection, sheet: Sheet, header_index: int, mapping: list[str],
                  user_name: str | None = None) -> list[Row]:
    lookups = Lookups.load(conn)
    mine = user_keys(user_name)
    header = sheet.rows[header_index]
    students = [dict(r) for r in conn.execute("SELECT * FROM students WHERE is_demo = 0")]
    by_number = {s["student_number"].strip(): s for s in students if (s["student_number"] or "").strip()}
    by_name = {}
    for s in students:
        by_name.setdefault(normalize_name(s["name"]), s)
    seen: set = set()
    result = []
    for offset, cells_list in enumerate(sheet.rows[header_index + 1:], start=header_index + 2):
        cells, notes = {}, []
        for index, kind in enumerate(mapping):
            value = clean(cells_list[index]) if index < len(cells_list) else ""
            if not value or kind == UNUSED:
                continue
            if kind == NOTE:
                label = " ".join((header[index] if index < len(header) else "").split()) or f"Kolom {index + 1}"
                notes.append(f"{label}: {value}")
            else:
                cells[kind] = value
        name = cells.get("name", "")
        if not name:
            if any(cells.values()) or notes:
                result.append(Row(offset, "", status="skipped", reason="Geen naam"))
            continue
        row = Row(offset, name, notes=notes)
        for index, cell in enumerate(cells_list):
            if mine and clean(cell) and person_key(clean(cell)) in mine:
                row.mine_column = " ".join((header[index] if index < len(header) else "").split()) or f"kolom {index + 1}"
                break
        _convert_row(cells, lookups, row)
        number = row.values.get("student_number", ("", ""))[0]
        student = by_number.get(number) if number else None
        student = student or by_name.get(normalize_name(name))
        key = ("id", student["id"]) if student else ("name", normalize_name(name))
        if key in seen or (number and ("nr", number) in seen):
            row.status, row.reason = "skipped", "Staat al eerder in het bestand"
            result.append(row)
            continue
        seen.add(key)
        if number:
            seen.add(("nr", number))
        if student:
            _compare(conn, row, student)
        result.append(row)
    return result


def _compare(conn: sqlite3.Connection, row: Row, student: dict) -> None:
    """F6: fill empty fields, list differences, new secondary roles and new note lines."""
    row.student_id = student["id"]
    for key, (stored, display) in row.values.items():
        current = student[STUDENT_COLUMN[key]]
        if current in (None, ""):
            row.fills.append((key, LABELS[key], display))
        elif str(current) != str(stored):
            row.changes.append((key, LABELS[key], _display(conn, key, current), display))
    have = {r[0]: r[1] for r in conn.execute(
        "SELECT guild_id, guild_master_id FROM student_guilds WHERE student_id = ?", (student["id"],))}
    for index, role in enumerate(row.guilds):   # spec 016, F8: add guilds, fill an empty guild master
        master = row.guild_master if index == 0 else None
        if role["id"] not in have:
            text = f"Gilde: {role['code']}" + (f" (gildemeester {master['name']})" if master else "")
            row.guild_fills.append((role, master, text))
        elif have[role["id"]] is None and master:
            row.guild_fills.append((role, master, f"Gildemeester bij {role['code']}: {master['name']}"))
    existing_notes = set((student.get("notes") or "").splitlines())
    row.new_notes = [n for n in row.notes if n not in existing_notes]
    row.status = "existing" if (row.fills or row.changes or row.guild_fills or row.new_notes) else "unchanged"


def counts(rows: list[Row]) -> dict[str, int]:
    return {status: sum(1 for r in rows if r.status == status) for status in ("new", "existing", "unchanged", "skipped")}


# Saving (F8, F9, F11) ---------------------------------------------------------------------------

def apply(conn: sqlite3.Connection, rows: list[Row], *, selected_new: set[int], accepted_changes: set[str],
          default_coach_id: int | None) -> tuple[int, int]:
    """Returns (added, updated). `accepted_changes` holds 'rownumber:field'."""
    added = updated = 0
    with conn:
        for row in rows:
            if row.status == "new" and row.number in selected_new:
                values = {STUDENT_COLUMN[k]: stored for k, (stored, _) in row.values.items()}
                if values.get("coach_id") is None and default_coach_id:
                    values["coach_id"] = default_coach_id
                values["name"], values["notes"] = row.name, "\n".join(row.notes) or None
                columns = ", ".join(values)
                student_id = conn.execute(
                    f"INSERT INTO students ({columns}) VALUES ({', '.join('?' for _ in values)})",
                    list(values.values())).lastrowid
                for index, role in enumerate(row.guilds):   # spec 016
                    master = row.guild_master["id"] if index == 0 and row.guild_master else None
                    student_guilds.add_or_fill(conn, student_id, role["id"], master)
                added += 1
            elif row.status == "existing":
                changed = False
                for key, _, _ in row.fills:
                    conn.execute(f"UPDATE students SET {STUDENT_COLUMN[key]} = ? WHERE id = ?",
                                 (row.values[key][0], row.student_id))
                    changed = True
                for key, _, _, _ in row.changes:
                    if f"{row.number}:{key}" in accepted_changes:
                        conn.execute(f"UPDATE students SET {STUDENT_COLUMN[key]} = ? WHERE id = ?",
                                     (row.values[key][0], row.student_id))
                        changed = True
                for role, master, _ in row.guild_fills:
                    student_guilds.add_or_fill(conn, row.student_id, role["id"], master["id"] if master else None)
                if row.new_notes:
                    current = conn.execute("SELECT notes FROM students WHERE id = ?", (row.student_id,)).fetchone()[0]
                    notes = "\n".join(([current] if current else []) + row.new_notes)
                    conn.execute("UPDATE students SET notes = ? WHERE id = ?", (notes, row.student_id))
                if changed or row.guild_fills or row.new_notes:
                    updated += 1
    return added, updated
