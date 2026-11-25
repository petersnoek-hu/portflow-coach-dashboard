"""Tijdlijn van bewijsstukken (spec 034): the evidence of one student, fetched from Portflow when
his page is opened, and arranged as dots per skill over the semester period.

Read only: GET /portfolios/{id}/collections and /portfolios/{id}/collections/{id}/evidence (see
docs/portflow-API-reverse-engineer.md). The contents of evidence are never fetched.
"""

import html
import html.parser
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

from . import evidence_files, portflow_api
from .skills import NAMES, SKILLS, skill_for_goal_name

OTHER = "Overig"   # F4: a row for evidence linked to none of the ten skills
KINDS = {"file": "bestand", "free_text": "tekst", "url": "link"}


def _local_day(value: str) -> date | None:
    try:
        moment = datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment.astimezone().date() if moment.tzinfo else moment.date()


def fetch_for_student(conn: sqlite3.Connection, student_id: int, token: str | None, *, api=portflow_api,
                      now=lambda: datetime.now(timezone.utc), period: tuple[date, date] | None = None) -> str | None:
    """F1: fetch and store the evidence of one student, and (spec 035, F1) the feedback requests
    and replies on the evidence added or updated in `period`. Returns a message (Dutch) when it did
    not work; what was stored then stays as it was."""
    if not token:
        return "Niet verbonden met Portflow: de bewijsstukken zijn niet opgehaald."
    portfolios = [r[0] for r in conn.execute("SELECT portfolio_id FROM student_portfolios WHERE student_id = ?",
                                             (student_id,))]
    if not portfolios:
        return "Deze student is niet gekoppeld aan een Portflow-portfolio."
    found: dict[int, dict] = {}
    collection_count = 0
    for portfolio_id in portfolios:
        status, items = api.collections(token, portfolio_id)
        if status == 401:
            return "Portflow accepteert de verbinding niet meer; verbind opnieuw en probeer het nog eens."
        if status == 404 or status == 403:
            continue   # not shared (any more)
        if status != 200:
            return "De bewijsstukken konden niet worden opgehaald. Probeer het later opnieuw."
        for collection in items or []:
            collection_count += 1
            status, entries = api.collection_evidence(token, portfolio_id, collection.get("id"))
            if status != 200:
                continue
            for entry in entries or []:
                evidence = entry.get("evidence") if isinstance(entry.get("evidence"), dict) else None
                if not evidence or not isinstance(evidence.get("id"), int):
                    continue
                item = found.setdefault(evidence["id"], {
                    "evidence_id": evidence["id"], "portfolio_id": portfolio_id, "name": str(evidence.get("name") or ""),
                    "kind": str(evidence.get("latest_version_type") or ""),
                    "created_at": str(evidence.get("created_at") or ""),
                    "updated_at": str(evidence.get("latest_version_created_at") or ""),
                    "collections": [], "skills": set()})
                name = str(collection.get("name") or "")
                if name and name not in item["collections"]:
                    item["collections"].append(name)
                for goal in evidence.get("goals") or []:
                    code = skill_for_goal_name(goal.get("name")) if isinstance(goal, dict) else None
                    if code:
                        item["skills"].add(code)
    comments = _fetch_comments(api, token, [i for i in found.values() if _in_period(i, period)])
    with conn:
        conn.execute("DELETE FROM evidence_items WHERE student_id = ?", (student_id,))
        conn.execute("DELETE FROM evidence_comments WHERE student_id = ?", (student_id,))
        conn.executemany(
            "INSERT OR REPLACE INTO evidence_comments (comment_id, student_id, evidence_id, parent_id, kind, text, "
            "created_at, author_id, author_name, author_role, version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(c["comment_id"], student_id, c["evidence_id"], c["parent_id"], c["kind"], c["text"], c["created_at"],
              c["author_id"], c["author_name"], c["author_role"], c.get("version")) for c in comments])
        conn.executemany(
            "INSERT INTO evidence_items (student_id, evidence_id, name, kind, created_at, updated_at, collections, skills) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [(student_id, i["evidence_id"], i["name"], i["kind"], i["created_at"], i["updated_at"],
              "; ".join(i["collections"]), ",".join(s for s in SKILLS if s in i["skills"])) for i in found.values()])
        conn.execute("INSERT INTO evidence_fetches (student_id, fetched_at, collections, error) VALUES (?, ?, ?, '') "
                     "ON CONFLICT(student_id) DO UPDATE SET fetched_at = excluded.fetched_at, "
                     "collections = excluded.collections, error = ''", (student_id, now().isoformat(), collection_count))
    return None


def _in_period(item: dict, period: tuple[date, date] | None) -> bool:
    """Spec 035, F1: only evidence added or updated in the period is checked for feedback requests."""
    if period is None:
        return True
    start, end = period
    return any(day is not None and start <= day <= end
               for day in (_local_day(item["created_at"]), _local_day(item["updated_at"])))


def _comment(raw: dict, evidence_id: int, parent_id: int | None, version: int | None = None) -> dict | None:
    """One comment; spec 043: hidden comments are left out (F1, open question 3), and the version
    of the evidence it belongs to is kept (a reply without one takes `version`, that of its parent)."""
    if not isinstance(raw.get("id"), int) or raw.get("hidden") is True:
        return None
    author = raw.get("created_by") if isinstance(raw.get("created_by"), dict) else {}
    own = raw.get("evidence_version") if isinstance(raw.get("evidence_version"), dict) else {}
    number = own.get("version_number")
    return {"comment_id": raw["id"], "evidence_id": evidence_id, "parent_id": parent_id,
            "kind": str(raw.get("comment_type") or ""), "text": str(raw.get("text") or ""),
            "created_at": str(raw.get("created_at") or ""),
            "author_id": author.get("id") if isinstance(author.get("id"), int) else None,
            "author_name": str(author.get("name") or ""), "author_role": str(raw.get("created_by_role") or ""),
            "version": number if isinstance(number, int) and not isinstance(number, bool) else version}


def _fetch_comments(api, token: str, items: list[dict]) -> list[dict]:
    """Spec 035, F1: the comments on each piece of evidence, and the replies to feedback requests.
    In parallel, because a student easily has a hundred pieces of evidence."""
    def for_evidence(item: dict) -> list[dict]:
        status, comments = api.evidence_comments(token, item["portfolio_id"], item["evidence_id"])
        result = []
        for raw in comments or [] if status == 200 else []:
            comment = _comment(raw, item["evidence_id"], None)
            if comment is None:
                continue
            result.append(comment)
            if raw.get("child_count"):
                status, children = api.comment_children(token, item["portfolio_id"], comment["comment_id"])
                for child in children or [] if status == 200 else []:
                    reply = _comment(child, item["evidence_id"], comment["comment_id"], comment["version"])
                    if reply is not None and reply["comment_id"] != comment["comment_id"]:
                        result.append(reply)
        return result

    with ThreadPoolExecutor(max_workers=6) as pool:
        return [comment for comments in pool.map(for_evidence, items) for comment in comments]


def plain_text(text: str) -> str:
    """Comments come as HTML; show them as plain text with line breaks (escaped by the template)."""
    text = re.sub(r"(?i)<br\s*/?>|</p>|</li>", "\n", text or "")
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(text)).strip()


def last_fetch(conn: sqlite3.Connection, student_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM evidence_fetches WHERE student_id = ?", (student_id,)).fetchone()
    return dict(row) if row else None


def _nl(day: date | None) -> str:
    return f"{day.day}-{day.month}-{day.year}" if day else "onbekend"


def timeline(conn: sqlite3.Connection, student_id: int, start: date, end: date) -> dict:
    """F2-F4: one row per skill (OC ... RE) and Overig; per row the dots of evidence added in the
    period, one dot per day (with a count when more than one). Positions in percent of the weeks of
    the period (the same weeks as the evaluation timeline)."""
    first = start - timedelta(days=start.weekday())
    span = ((end - first).days // 7 + 1) * 7
    rows = {code: {} for code in list(SKILLS) + [OTHER]}
    total = 0
    for item in conn.execute("SELECT * FROM evidence_items WHERE student_id = ? ORDER BY created_at, evidence_id",
                             (student_id,)):
        day = _local_day(item["created_at"])
        if day is None or not start <= day <= end:
            continue
        total += 1
        skills = [s for s in item["skills"].split(",") if s] or [OTHER]
        tip = (f"{item['name'] or 'Bewijsstuk'} ({KINDS.get(item['kind'], item['kind'] or 'onbekend')})"
               f", toegevoegd {_nl(day)}")
        updated = _local_day(item["updated_at"])
        if updated and updated != day:
            tip += f", laatste versie {_nl(updated)}"
        if item["collections"]:
            tip += f", collectie {item['collections']}"
        tip += ", " + (", ".join(skills) if skills != [OTHER] else "geen vaardigheid")
        for code in skills:
            dot = rows[code].setdefault(day, {"day": day, "kinds": set(), "tips": [], "ids": []})
            dot["kinds"].add(item["kind"])
            dot["ids"].append(item["evidence_id"])
            dot["tips"].append(tip)
    result = []
    for code, dots in rows.items():
        result.append({
            "code": code, "name": NAMES.get(code, "Niet aan een vaardigheid gekoppeld"),
            "dots": [{"left": round(100 * ((d["day"] - first).days + 0.5) / span, 2), "count": len(d["tips"]),
                      "kind": next(iter(d["kinds"])) if len(d["kinds"]) == 1 else "mixed",
                      "tip": "\n".join(d["tips"]), "ids": ",".join(map(str, d["ids"]))} for d in dots.values()],
        })
    return {"rows": result, "total": total}


# One piece of evidence (spec 036) ------------------------------------------------------------------

FILE_TYPES = {"application/pdf": "pdf", "image/png": "afbeelding (png)", "image/jpeg": "afbeelding (jpg)",
              "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word-document",
              "application/msword": "Word-document",
              "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PowerPoint",
              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel-bestand",
              "text/plain": "tekstbestand", "application/zip": "zip-bestand"}
_ALLOWED = {"p", "br", "ul", "ol", "li", "strong", "b", "em", "i", "a", "h1", "h2", "h3", "h4", "blockquote"}


class _SafeHtml(html.parser.HTMLParser):
    """Keep a fixed set of simple tags (F3, technical requirement); everything else becomes text.
    Links only to http(s), opening in a new tab; mentions of other evidence become their label."""

    def __init__(self, mention=None):
        super().__init__(convert_charrefs=True)
        self.mention = mention   # spec 039, F6: (evidence id, label) -> address of a link, or None
        self.out: list[str] = []
        self.open: list[str] = []
        self.skip: list[str] = []   # inside <script>, <style> or a mention: no text of its own

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.skip:
            if tag == self.skip[-1]:
                self.skip.append(tag)
            return
        if tag in ("script", "style"):
            self.skip.append(tag)
        elif tag == "br":
            self.out.append("<br>")
        elif tag == "a" and (attrs.get("href") or "").startswith(("http://", "https://")):
            self.out.append(f'<a href="{html.escape(attrs["href"], quote=True)}" target="_blank" rel="noopener noreferrer">')
            self.open.append("a")
        elif tag in _ALLOWED and tag != "a":
            tag = {"b": "strong", "i": "em", "h1": "h4", "h2": "h4", "h3": "h4"}.get(tag, tag)
            self.out.append(f"<{tag}>")
            self.open.append(tag)
        elif tag == "span" and attrs.get("data-mention-type") == "evidence" and attrs.get("data-label"):
            evidence_id = attrs.get("data-id") or ""
            href = self.mention(int(evidence_id), attrs["data-label"]) if self.mention and evidence_id.isdigit() else None
            if href and "a" not in self.open:
                self.out.append(f'<a class="evidence-mention" href="{html.escape(href, quote=True)}" data-feedback '
                                f'data-panel-title="Bewijsstuk">{html.escape(attrs["data-label"])}</a>')
            else:
                self.out.append(html.escape(f"[{attrs['data-label']}]"))
            self.skip.append("span")

    def handle_endtag(self, tag):
        if self.skip:
            if tag == self.skip[-1]:
                self.skip.pop()
            return
        tag = {"b": "strong", "i": "em", "h1": "h4", "h2": "h4", "h3": "h4"}.get(tag, tag)
        if tag in self.open:
            while self.open:
                last = self.open.pop()
                self.out.append(f"</{last}>")
                if last == tag:
                    break

    def handle_data(self, data):
        if not self.skip:
            self.out.append(html.escape(data))

    def result(self) -> str:
        return "".join(self.out) + "".join(f"</{t}>" for t in reversed(self.open))


def safe_html(text: str, mention=None) -> str:
    """mention: optional (evidence id, label) -> link address; then a mention of evidence becomes a
    link that opens it in the side panel (spec 039, F6) instead of "[label]"."""
    parser = _SafeHtml(mention)
    parser.feed(text or "")
    parser.close()
    return parser.result()


def detail(conn: sqlite3.Connection, student_id: int, evidence_id: int, token: str | None, *,
           api=portflow_api) -> tuple[dict | None, str | None]:
    """F2, F3: the details of one piece of evidence, live from Portflow and not stored.
    Returns (details, None) or (None, a message in Dutch)."""
    if not token:
        return None, "Niet verbonden met Portflow: het bewijsstuk kan niet worden opgehaald."
    portfolios = [r[0] for r in conn.execute("SELECT portfolio_id FROM student_portfolios WHERE student_id = ?",
                                             (student_id,))]
    stored = conn.execute("SELECT * FROM evidence_items WHERE student_id = ? AND evidence_id = ?",
                          (student_id, evidence_id)).fetchone()
    for portfolio_id in portfolios:
        status, data = api.evidence_detail(token, portfolio_id, evidence_id)
        if status == 401:
            return None, "Portflow accepteert de verbinding niet meer; verbind opnieuw."
        if status != 200 or not isinstance(data, dict):
            continue
        version = data.get("latest_version") if isinstance(data.get("latest_version"), dict) else {}
        files = [f for f in version.get("files") or [] if isinstance(f, dict)]
        kind = str(data.get("latest_version_type") or version.get("version_type") or "")
        result = {
            "name": str(data.get("name") or "Bewijsstuk"), "kind": KINDS.get(kind, kind or "onbekend"), "raw_kind": kind,
            "description": safe_html(str(data.get("description") or "")),
            "created": _nl(_local_day(str(data.get("created_at") or ""))),
            "updated": _nl(_local_day(str(data.get("latest_version_created_at") or ""))),
            "versions": data.get("versions_count") or 1,
            "skills": [s for s in ((stored["skills"] if stored else "") or "").split(",") if s],
            "text": "", "images": 0, "file_name": "", "file_type": "", "url": "",
            "portfolio_id": portfolio_id, "files": evidence_files.files_of(version),   # spec 038
        }
        for f in files:
            if isinstance(f.get("free_text"), dict):
                result["text"] += safe_html(str(f["free_text"].get("free_text") or ""))
                result["images"] += len(f["free_text"].get("images") or [])
            if isinstance(f.get("file"), dict):
                result["file_name"] = str(f["file"].get("file_name") or "")
                mime = str(f["file"].get("type") or "")
                result["file_type"] = FILE_TYPES.get(mime, mime.split("/")[-1] if mime else "")
            for key in ("url", "link"):
                value = f.get(key) if isinstance(f.get(key), str) else (f.get(key) or {}).get("url") if isinstance(f.get(key), dict) else None
                if value and value.startswith(("http://", "https://")):
                    result["url"] = value
        return result, None
    return None, "Dit bewijsstuk is niet (meer) te openen; misschien is het niet meer gedeeld."
