"""Pages for importing students from Excel (spec 013). The file is never stored: the
read rows live in memory under a random key until the import is done or cancelled."""

import secrets
import time
from urllib.parse import urlencode

from flask import Blueprint, abort, current_app, redirect, render_template, request, url_for

from . import excel_import, portflow_link
from .db import get_db
from .xlsx_reader import NotAnXlsx, read_workbook

bp = Blueprint("excel", __name__, url_prefix="/studenten/toevoegen/excel")
MAX_BYTES = 10 * 1024 * 1024
KEEP_SECONDS = 2 * 60 * 60
FIELD_CHOICES = [(key, label) for key, (label, _) in excel_import.FIELDS.items()] + [
    (excel_import.NOTE, "Notitie"), (excel_import.UNUSED, "Niet gebruiken")]


def _store() -> dict:
    store = current_app.extensions.setdefault("excel_imports", {})
    now = time.time()
    for key in [k for k, v in store.items() if now - v["created"] > KEEP_SECONDS]:
        del store[key]  # forget old, unfinished imports
    return store


def _job(key: str) -> dict:
    job = _store().get(key)
    if job is None:
        abort(404)
    return job


def _page(title: str, intro: str) -> dict:
    return {"eyebrow": "Studievoortgang", "title": title, "intro": intro, "label": title}


def _select_sheet(job: dict, index: int) -> None:
    sheet = job["sheets"][index]
    header = excel_import.find_header(sheet.rows)
    job.update(sheet_index=index, header=header,
               mapping=excel_import.auto_mapping(sheet.rows[header]) if header is not None else [])


@bp.route("", methods=["GET", "POST"])
def upload():
    """F1, F2: choose an .xlsx file."""
    error = None
    if request.method == "POST":
        file = request.files.get("bestand")
        data = file.read(MAX_BYTES + 1) if file else b""
        if not data:
            error = "Kies een Excelbestand (.xlsx)."
        elif len(data) > MAX_BYTES:
            error = "Dit bestand is groter dan 10 MB."
        else:
            try:
                sheets = read_workbook(data)
            except NotAnXlsx:
                sheets = None
            if not sheets or not any(s.rows for s in sheets):
                error = "Dit is geen Excelbestand (.xlsx) dat de app kan lezen."
            else:
                key = secrets.token_urlsafe(16)
                job = {"created": time.time(), "filename": file.filename or "bestand.xlsx", "sheets": sheets}
                _select_sheet(job, excel_import.choose_sheet(sheets))
                _store()[key] = job
                return redirect(url_for("excel.preview", key=key))
    return render_template("excel_upload.html", page=_page("Excelbestand uploaden",
                           "Kies een .xlsx-bestand met studenten. De kolommen mogen in elke volgorde staan."),
                           active="students", error=error)


@bp.get("/<key>")
def preview(key: str):
    """F3, F6-F10: choose a sheet and see what will happen."""
    job = _job(key)
    if request.args.get("blad", "").isdigit() and int(request.args["blad"]) < len(job["sheets"]):
        _select_sheet(job, int(request.args["blad"]))
    if job["header"] is None or excel_import.mapping_error(job["mapping"]):
        return redirect(url_for("excel.mapping", key=key))
    sheet = job["sheets"][job["sheet_index"]]
    user = current_app.extensions["portflow"].user_name
    rows = excel_import.build_preview(get_db(), sheet, job["header"], job["mapping"], user)
    coaches = [dict(r) for r in get_db().execute("SELECT id, name FROM staff WHERE is_coach = 1 ORDER BY name COLLATE NOCASE")]
    return render_template("excel_preview.html", page=_page("Voorbeeld van de import", job["filename"]),
                           active="students", key=key, job=job, rows=rows, counts=excel_import.counts(rows),
                           coaches=coaches, sheet_choices=_sheet_choices(job), labels=dict(FIELD_CHOICES),
                           header=sheet.rows[job["header"]], user_known=bool(excel_import.user_keys(user)),
                           mine_count=sum(1 for r in rows if r.status == "new" and r.mine_column))


def _sheet_choices(job: dict) -> list[tuple[int, str]]:
    return [(i, f"{s.name}{' (verborgen)' if s.hidden else ''} · {len(s.rows)} rijen") for i, s in enumerate(job["sheets"])]


@bp.route("/<key>/koppelen", methods=["GET", "POST"])
def mapping(key: str):
    """F5: link columns to fields by hand."""
    job = _job(key)
    sheet = job["sheets"][job["sheet_index"]]
    error = None
    if request.method == "POST":
        if request.form.get("kopregel", "").isdigit():
            header = int(request.form["kopregel"]) - 1
            if 0 <= header < min(len(sheet.rows), excel_import.HEADER_SEARCH_ROWS) and header != job["header"]:
                job.update(header=header, mapping=excel_import.auto_mapping(sheet.rows[header]))
                return redirect(url_for("excel.mapping", key=key))
        if job["header"] is not None:
            choices = {value for value, _ in FIELD_CHOICES}
            mapping = [request.form.get(f"kolom{i}", excel_import.UNUSED) for i in range(len(sheet.rows[job["header"]]))]
            mapping = [m if m in choices else excel_import.UNUSED for m in mapping]
            error = excel_import.mapping_error(mapping)
            job["mapping"] = mapping
            if not error:
                return redirect(url_for("excel.preview", key=key))
    header_index = job["header"] if job["header"] is not None else 0
    header = sheet.rows[header_index] if sheet.rows else []
    data = sheet.rows[header_index + 1:]
    columns = []
    for i, name in enumerate(header):
        samples = [excel_import.clean(r[i]) for r in data if i < len(r) and excel_import.clean(r[i])][:3]
        columns.append({"index": i, "name": name or f"Kolom {i + 1}", "samples": samples,
                        "choice": job["mapping"][i] if i < len(job["mapping"]) else excel_import.UNUSED})
    if error is None and request.method == "GET" and excel_import.mapping_error(job["mapping"]) and job["header"] is not None:
        error = "De app herkent niet alle kolommen. Koppel minstens een kolom aan Naam."
    return render_template("excel_mapping.html", page=_page("Kolommen koppelen", job["filename"]),
                           active="students", key=key, columns=columns, choices=FIELD_CHOICES, error=error,
                           header_row=header_index + 1, sheet=sheet, sheet_choices=_sheet_choices(job),
                           sheet_index=job["sheet_index"])


@bp.post("/<key>/importeren")
def run(key: str):
    """F11: save what is ticked and filled in."""
    job = _job(key)
    sheet = job["sheets"][job["sheet_index"]]
    conn = get_db()
    rows = excel_import.build_preview(conn, sheet, job["header"], job["mapping"])
    selected = {int(v) for v in request.form.getlist("nieuw") if v.isdigit()}
    coach = request.form.get("coach", "")
    coach_id = int(coach) if coach.isdigit() and conn.execute(
        "SELECT 1 FROM staff WHERE id = ? AND is_coach = 1", (int(coach),)).fetchone() else None
    added, updated = excel_import.apply(conn, rows, selected_new=selected,
                                        accepted_changes=set(request.form.getlist("overnemen")),
                                        default_coach_id=coach_id)
    _store().pop(key, None)  # the read rows are no longer needed
    message = f"{added} student{'en' if added != 1 else ''} toegevoegd, {updated} bijgewerkt."
    message += " " + _link_after_import(conn)
    return redirect(url_for("pages.students") + "?" + urlencode({"melding": message}))


def _link_after_import(conn) -> str:
    """Spec 015, F3: link to Portflow right away when the connection is valid."""
    connection = current_app.extensions["portflow"]
    token = connection.token
    if token:
        try:
            candidates = portflow_link.shared_students(connection.api, token, use_cache=False)
        except portflow_link.Unauthorized:
            connection.mark_unauthorized()
            candidates = None
        if candidates is not None:
            linked, _ = portflow_link.auto_link(conn, candidates)
            return f"{linked} gekoppeld aan Portflow. Klik op Verversen om hun evaluaties op te halen."
    return "Klik op Verversen om ze aan Portflow te koppelen en hun evaluaties op te halen."


@bp.post("/<key>/annuleren")
def cancel(key: str):
    _store().pop(key, None)
    return redirect(url_for("pages.add_students"))
