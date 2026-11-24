"""Spec 040: the wizard "AI-advies instellen" (F12), the settings (F11) and the advice on the
evaluation page (F1-F10)."""

from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, url_for

from . import ai_advice, claude_ai, db, evaluation_page, ollama
from .skills import NAMES as SKILL_NAMES, SKILLS
from .db import get_db
from .overview import semester_period

bp = Blueprint("ai", __name__)

S_TRIAL = "ai_trial"   # JSON: {"model", "seconds"} of the last successful trial question (step 4)
SLOW_SECONDS = 120


def _database() -> str:
    return current_app.config["DATABASE"]


def _user() -> str | None:
    return current_app.extensions["portflow"].user_name


def readiness(database: str, timeout_ok: bool = True) -> dict:
    """The state of Ollama and the model, for the wizard, Instellingen and the evaluation page."""
    url, model = ai_advice.settings(database)
    state = {"url": url, "model": model, "version": None, "has_model": False, "models": [], "error": ""}
    try:
        state["version"] = ollama.version(url)
        state["models"] = ollama.models(url)
        state["has_model"] = ollama.has_model(url, model)
    except ollama.OllamaError as error:
        state["error"] = error.message
    state["ready"] = bool(state["version"] and state["has_model"])
    return state


def _trial(database: str, model: str) -> dict | None:
    import json
    try:
        value = json.loads(db.get_setting(database, S_TRIAL) or "null")
    except ValueError:
        return None
    return value if isinstance(value, dict) and value.get("model") == model else None


@bp.get("/instellingen/ollama")
def settings_status():
    """F11: the state of Ollama for Instellingen, loaded after the page (a stopped Ollama takes 2 s),
    with the default model (F27), downloading (F28) and the laptop limits (F29-F32)."""
    database = _database()
    return render_template(
        "_ai_status.html",
        ai=readiness(database),
        ai_tested=ollama.TESTED_MODELS,
        ai_default=ollama.DEFAULT_MODEL,
        ai_pull=current_app.extensions["ollama_pull"].status(),
        ai_saved=request.args.get("model") == "ok",
        ai_laptop=ai_advice.laptop(database),
        ai_cores=ollama.cores(),
        ai_laptop_saved=request.args.get("laptop") == "ok",
    )


@bp.get("/instellingen/ai-advies")
def setup():
    """F12: the wizard, with the checks done when the page opens (and with every "Controleren")."""
    database = _database()
    state = readiness(database)
    claude_allowed = claude_ai.allowed(_user())   # F22
    memory = ollama.memory_gb()
    trial = _trial(database, state["model"])
    steps = {"memory": memory is not None, "ollama": bool(state["version"]), "model": state["has_model"],
             "trial": bool(state["has_model"] and trial)}
    order = ["memory", "ollama", "model", "trial"]
    current = next((s for s in order[1:] if not steps[s]), "done")
    return render_template(
        "ai_setup.html", page={"title": "AI-advies instellen", "label": "Instellingen › AI-advies"}, active="settings",
        state=state, steps=steps, current=current, memory=memory, min_memory=ollama.MIN_MEMORY_GB,
        system=ollama.system_name(), trial=trial, slow=SLOW_SECONDS, download_url=ollama.DOWNLOAD_URL,
        default_model=ollama.DEFAULT_MODEL, default_size=ollama.DEFAULT_MODEL_SIZE,
        pull=current_app.extensions["ollama_pull"].status(),
        claude={"key": claude_ai.short(claude_ai.key(database)), "approved": claude_ai.approved(database),
                "model": claude_ai.MODEL, "error": request.args.get("claude_fout", ""),
                "saved": request.args.get("claude") == "ok", "allowed": claude_allowed},
        prompt=ai_advice.system_prompt(database), prompt_is_default=ai_advice.system_prompt(database) == ai_advice.SYSTEM,
        skill_prompts=ai_advice.skill_prompts(database), skills=SKILLS, skill_names=SKILL_NAMES,
        prompt_saved=request.args.get("opdracht") == "ok")


@bp.post("/instellingen/ai-advies")
def save_settings():
    """F11: the chosen model and the address of Ollama (only on the laptop itself)."""
    database = _database()
    model = request.form.get("model", "").strip()
    url = request.form.get("url", "").strip()
    if model:
        if not ollama.valid_name(model):
            abort(400)
        db.set_setting(database, ollama.S_MODEL, model)
    if url:
        if not ollama.is_local(url):
            return redirect(url_for("ai.setup", fout="adres"))
        db.set_setting(database, ollama.S_URL, url.rstrip("/"))
    if request.form.get("terug") == "instellingen":   # F27: the default model chosen in Instellingen
        return redirect(url_for("pages.settings", model="ok") + "#ai-advies")
    return redirect(url_for("ai.setup") + "#stap-" + request.form.get("stap", "3"))


@bp.post("/instellingen/ai-advies/laptop")
def laptop_save():
    """F29-F32: how much of the laptop the local model may use; from the next advice on."""
    database = _database()
    try:
        threads = int(request.form.get("kernen", ""))
    except ValueError:
        abort(400)
    context = request.form.get("materiaal", "")
    if not 1 <= threads <= ollama.cores() or context not in ollama.CONTEXTS:
        abort(400)
    db.set_setting(database, ollama.S_THREADS, str(threads))
    db.set_setting(database, ollama.S_CONTEXT, context)
    db.set_setting(database, ollama.S_UNLOAD, "1" if request.form.get("vrijgeven") == "1" else "")
    return redirect(url_for("pages.settings", laptop="ok") + "#ai-laptop")


@bp.post("/instellingen/ai-advies/downloaden")
def pull():
    """F12, step 3: let Ollama download the chosen model; F28: or the model named in the form."""
    url, model = ai_advice.settings(_database())
    named = request.form.get("model", "").strip()
    if named:
        if not ollama.valid_name(named):
            message = f"\"{named[:100]}\" is geen geldige modelnaam (bijvoorbeeld gemma4:e4b)."
            if request.headers.get("X-Requested-With") == "fetch":
                return jsonify(dict(current_app.extensions["ollama_pull"].status(), error=message, running=False))
            abort(400)
        model = named
    current_app.extensions["ollama_pull"].start(url, model)
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify(current_app.extensions["ollama_pull"].status())
    if request.form.get("terug") == "instellingen":
        return redirect(url_for("pages.settings") + "#ai-advies")
    return redirect(url_for("ai.setup") + "#stap-3")


@bp.get("/instellingen/ai-advies/downloaden")
def pull_status():
    return jsonify(current_app.extensions["ollama_pull"].status())


@bp.post("/instellingen/ai-advies/proefvraag")
def trial():
    """F12, step 4: a small invented evaluation; remembered when it works."""
    import json
    database = _database()
    url, model = ai_advice.settings(database)
    try:
        result = ai_advice.trial(url, model, ai_advice.system_prompt(database), ai_advice.model_options(database))
    except ollama.OllamaError as error:
        return jsonify(ok=False, message=error.message)
    db.set_setting(database, S_TRIAL, json.dumps({"model": model, "seconds": result["seconds"]}))
    return jsonify(ok=True, seconds=result["seconds"], slow=result["seconds"] > SLOW_SECONDS)


@bp.post("/instellingen/ai-advies/claude")
def claude_save():
    """F13: the warning has to be confirmed; the key is checked at Anthropic before it is saved."""
    database = _database()
    if not claude_ai.allowed(_user()):   # F22
        abort(403)
    api_key = request.form.get("sleutel", "").strip()
    if request.form.get("toegestaan") != "1":
        return redirect(url_for("ai.setup", claude_fout="Zet eerst het vinkje dat de HU dit toestaat.") + "#claude")
    if not api_key:
        return redirect(url_for("ai.setup", claude_fout="Vul een API-sleutel in.") + "#claude")
    try:
        claude_ai.check_key(api_key)
    except ollama.OllamaError as error:
        return redirect(url_for("ai.setup", claude_fout=error.message) + "#claude")
    claude_ai.save(database, api_key)
    return redirect(url_for("ai.setup", claude="ok") + "#claude")


@bp.post("/instellingen/ai-advies/claude/verwijderen")
def claude_remove():
    if not claude_ai.allowed(_user()):   # F22
        abort(403)
    claude_ai.remove(_database())
    return redirect(url_for("ai.setup") + "#claude")


@bp.post("/instellingen/ai-advies/opdracht")
def prompts_save():
    """F18, F19: the general instruction and an addition per skill."""
    database = _database()
    if request.form.get("standaard") == "1":
        db.set_setting(database, ai_advice.S_PROMPT, "")
    else:
        text = request.form.get("opdracht", "").strip()
        db.set_setting(database, ai_advice.S_PROMPT, "" if text == ai_advice.SYSTEM else text)
        for code in SKILLS:
            db.set_setting(database, ai_advice.SKILL_PROMPT.format(code), request.form.get(f"opdracht_{code}", "").strip())
    return redirect(url_for("ai.setup", opdracht="ok") + "#opdracht")


# The advice on the evaluation page -----------------------------------------------------------------

def card_context(conn, request_id: int, judgment: dict | None = None, error: str = "") -> dict:
    """What the advice card needs (F1-F10, F24-F26). `judgment` and `error`: a form that was sent
    back because the own judgment was not complete (F24)."""
    database = _database()
    from datetime import date
    start, end, _ = semester_period(conn, date.today())
    data = evaluation_page.build(conn, request_id, date.today(), start, end)
    advice = ai_advice.saved(conn, request_id)
    job = current_app.extensions["ai_jobs"].status(request_id)
    services = ai_advice.available(database, _user())
    # F14: the AI of a running or failed job, else the one of the advice, else the default model.
    if job and job.get("kind") == "advice" and job.get("choice"):
        chosen = job["choice"]
    elif advice:
        chosen = ai_advice.choice_key(advice["service"], advice["model"])
    else:
        chosen = ai_advice.choice_key("lokaal", ai_advice.settings(database)[1])
    if chosen not in {s["key"] for s in services}:
        chosen = services[0]["key"] if services else ""
    skills = [{"code": s["code"], "name": s["name"], "assessor": s["assessor"]} for s in data["skills"]] if data else []
    own = judgment if judgment is not None else ai_advice.saved_judgment(conn, request_id)
    return {"advice_request_id": request_id, "advice": advice, "advice_job": job,
            "advice_ready": readiness(database), "advice_services": services, "advice_choice": chosen,
            "advice_counts": ai_advice.overview(data) if data else None,
            "judgment_skills": skills, "judgment": own, "judgment_error": error,
            "judgment_complete": ai_advice.judgment_complete([s["code"] for s in skills], own)}


@bp.get("/evaluaties/<int:request_id>/advies")
def advice_card(request_id: int):
    return render_template("_ai_advice.html", **card_context(get_db(), request_id))


JUDGMENT_MISSING = "Vul eerst bij elke vaardigheid je eigen niveau en een toelichting in."


@bp.post("/evaluaties/<int:request_id>/advies")
def advice_start(request_id: int):
    """F1, F9: ask (or ask again) for an advice; it is made in the background (F4). F24: only with a
    complete own judgment, which is kept (F26) and sent with it (F25)."""
    conn = get_db()
    if not conn.execute("SELECT 1 FROM evaluations WHERE review_request_id = ? LIMIT 1", (request_id,)).fetchone():
        abort(404)
    choice = request.form.get("dienst", "lokaal")
    services = {s["key"] for s in ai_advice.available(_database(), _user())}
    if choice not in services and not (choice == "lokaal" and ai_advice.choice_key("lokaal", ai_advice.settings(_database())[1]) in services):
        abort(400)
    from datetime import date
    start, end, _ = semester_period(conn, date.today())
    data = evaluation_page.build(conn, request_id, date.today(), start, end)
    codes = data["codes"] if data else []
    judgment = ai_advice.judgment_from_form(codes, request.form)
    if not ai_advice.judgment_complete(codes, judgment):
        if request.headers.get("X-Requested-With") == "fetch":
            return render_template("_ai_advice.html", **card_context(conn, request_id, judgment, JUDGMENT_MISSING))
        abort(400)
    ai_advice.save_judgment(_database(), request_id, judgment)
    service, model = ai_advice.parse_choice(choice, _database())
    current_app.extensions["ai_jobs"].start(request_id, service, model, judgment)
    if request.headers.get("X-Requested-With") == "fetch":
        return advice_card(request_id)
    return redirect(url_for("pages.evaluation_page", request_id=request_id) + "#ai-advies")


@bp.post("/evaluaties/<int:request_id>/advies/vraag")
def advice_question(request_id: int):
    """F21: a follow-up question about the advice, to the AI that made it."""
    if ai_advice.saved(get_db(), request_id) is None:
        abort(404)
    current_app.extensions["ai_jobs"].ask(request_id, request.form.get("vraag", "")[:4000])
    if request.headers.get("X-Requested-With") == "fetch":
        return advice_card(request_id)
    return redirect(url_for("pages.evaluation_page", request_id=request_id) + "#ai-advies")


@bp.post("/evaluaties/<int:request_id>/advies/stoppen")
def advice_stop(request_id: int):
    current_app.extensions["ai_jobs"].stop(request_id)
    if request.headers.get("X-Requested-With") == "fetch":
        return advice_card(request_id)
    return redirect(url_for("pages.evaluation_page", request_id=request_id) + "#ai-advies")
