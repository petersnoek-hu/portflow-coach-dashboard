"""The progress rules of docs/voortgangsregels.md, in one place and without any HTML.

Input: rows of the `evaluations` table (dicts), the names of known assessors (the
Coaches and Guild masters pages) and the semester period. Output: per student the
cells OC … RE, the full-assessment marker and the signals (spec 001, F6-F12, F18).
"""

import unicodedata
from dataclasses import dataclass, field
from datetime import date

from .skills import COACH_SKILLS, PRODUCT_SKILLS, SKILLS

COUNTED_EXCLUDED_STATUSES = {"not_scored"}       # request not yet scored as a whole (console app)
NOT_PENDING_STATUSES = {"scored", "denied"}


def normalize_name(name: str | None) -> str:
    """Compare names without case and extra spaces."""
    return " ".join((name or "").split()).casefold()


def name_key(name: str | None) -> str:
    """Compare person names without case, extra spaces and accents ("André" = "Andre").
    Used by the Excel import (spec 013) and linking to Portflow (spec 015)."""
    decomposed = unicodedata.normalize("NFKD", normalize_name(name))
    return "".join(c for c in decomposed if not unicodedata.combining(c))


# Semester period (spec 001, F22) ----------------------------------------------------------

def default_semester_period(today: date) -> tuple[date, date]:
    """The running semester: 1 September - 31 January, or 1 February - 31 August."""
    if today.month >= 9:
        return date(today.year, 9, 1), date(today.year + 1, 1, 31)
    if today.month == 1:
        return date(today.year - 1, 9, 1), date(today.year, 1, 31)
    return date(today.year, 2, 1), date(today.year, 8, 31)


def in_period(day: str, start: date, end: date) -> bool:
    """An evaluation without a recognisable date counts (voortgangsregels.md, rule 3)."""
    if not day:
        return True
    try:
        moment = date.fromisoformat(day[:10])
    except ValueError:
        return True
    return start <= moment <= end


# Cells ------------------------------------------------------------------------------------

@dataclass
class Evaluation:
    level: str
    date: str
    assessor: str | None


@dataclass
class Pending:
    title: str | None
    date: str


@dataclass
class Cell:
    skill: str
    evaluations: list[Evaluation] = field(default_factory=list)
    pending: Pending | None = None
    no_access: bool = False
    early_semester: bool = False     # semester 1, 2 or unknown: an empty cell is grey

    @property
    def count(self) -> int:
        return len(self.evaluations)

    @property
    def highest(self) -> int:
        levels = [int(e.level) for e in self.evaluations if e.level.isdigit()]
        return max(levels) if levels else -1

    @property
    def text(self) -> str:
        """voortgangsregels.md#weergave-per-vaardigheid: '-/-', '', '0', '1/2', '1/?', 'n/b'."""
        if self.no_access:
            return "n/b"
        parts = [e.level for e in self.evaluations]
        if self.pending:
            parts.append("?")
        if parts:
            return "/".join(parts)
        return "" if self.early_semester else "-/-"

    @property
    def colour(self) -> str:
        """F7: by number of counted evaluations; 'grey' for an empty early-semester cell."""
        if self.no_access:
            return "na"
        if self.count >= 2:
            return "n2"
        if self.count == 1:
            return "n1"
        return "grey" if self.early_semester else "n0"

    @property
    def sort_key(self) -> tuple[int, int]:
        """F18: number of evaluations, then the highest level."""
        return (self.count, self.highest)


@dataclass
class Progress:
    cells: dict[str, Cell]
    full_assessment: bool = False
    signals: list[tuple[str, str]] = field(default_factory=list)   # (colour, label)


def _counts(row: dict, known: set[str], start: date, end: date) -> bool:
    """voortgangsregels.md#welke-evaluaties-tellen: all four conditions."""
    return (
        row["kind"] == "assessed"
        and row.get("level") not in (None, "")
        and row.get("review_request_status") not in COUNTED_EXCLUDED_STATUSES
        and normalize_name(row.get("assessor")) in known
        and in_period(row.get("date") or "", start, end)
        and row["skill"] in SKILLS
    )


def student_progress(
    rows: list[dict],
    *,
    semester: int | None,
    known_assessors: set[str],
    period: tuple[date, date],
    start_date: str | None = None,
    has_access: bool = True,
) -> Progress:
    start, end = period
    if start_date:
        try:
            start = date.fromisoformat(start_date[:10])   # the student's own start (gegevensmodel.md)
        except ValueError:
            pass
    known = {normalize_name(name) for name in known_assessors}
    early = semester is None or semester <= 2
    cells = {skill: Cell(skill, no_access=not has_access, early_semester=early) for skill in SKILLS}
    if not has_access:
        return Progress(cells)

    ordered = sorted(rows, key=lambda r: (r.get("date") or "", r.get("id") or 0))
    for row in ordered:
        if _counts(row, known, start, end):
            cells[row["skill"]].evaluations.append(Evaluation(row["level"], row.get("date") or "", row.get("assessor")))

    # Open requests (voortgangsregels.md#openstaand).
    assessed_dates: dict[str, list[str]] = {skill: [] for skill in SKILLS}
    for row in ordered:
        if row["kind"] == "assessed" and row["skill"] in SKILLS:
            assessed_dates[row["skill"]].append(row.get("date") or "")
    candidates: dict[str, list[dict]] = {skill: [] for skill in SKILLS}
    for row in ordered:
        if (row["kind"] == "self" and row["skill"] in SKILLS
                and row.get("review_request_status") not in NOT_PENDING_STATUSES
                and in_period(row.get("date") or "", start, end)
                and not any(d >= (row.get("date") or "") for d in assessed_dates[row["skill"]])):
            candidates[row["skill"]].append(row)

    by_request: dict[int, set[str]] = {}
    for skill, items in candidates.items():
        for row in items:
            if row.get("review_request_id") is not None:
                by_request.setdefault(row["review_request_id"], set()).add(skill)
    full_requests = {rid for rid, skills in by_request.items() if skills >= set(SKILLS)}

    for skill, items in candidates.items():
        items = [row for row in items if row.get("review_request_id") not in full_requests]
        if items:
            newest = items[-1]
            cells[skill].pending = Pending(newest.get("review_request_title"), newest.get("date") or "")

    return Progress(cells, full_assessment=bool(full_requests), signals=signals(cells, semester))


# Signals (voortgangsregels.md#signalen) --------------------------------------------------------

def signals(cells: dict[str, Cell], semester: int | None) -> list[tuple[str, str]]:
    if semester is None or semester < 3 or any(cell.no_access for cell in cells.values()):
        return []
    result = []
    if all(cells[s].count == 0 for s in PRODUCT_SKILLS):
        result.append(("red", "Product nog leeg"))
    empty_coach = sum(1 for s in COACH_SKILLS if cells[s].count == 0)
    if empty_coach == 6:
        result.append(("orange", "Coach nog leeg"))
    elif empty_coach >= 4:
        result.append(("yellow", "Coach nog leeg"))
    return result
