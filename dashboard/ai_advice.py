"""AI-advies bij een evaluatie (spec 040): collect the material of one review request, replace the
names, ask the local model (Ollama) for an advice per skill, check the answer and keep the last one.

Everything stays on the laptop: Portflow is only asked for the evidence (as on the evaluation page),
and the model runs in Ollama on the laptop itself (ollama.py). Labels are Dutch.
"""

import base64
import json
import re
import sqlite3
import threading
from datetime import date, datetime, timezone

from . import ai_log, claude_ai, db, evaluation_page, evidence, evidence_files, file_text, lef, ollama
from .evidence import plain_text
from .hide_names import anonymize, numbers
from .overview import semester_period
from .portflow_connection import S_USER_NAME
from .progress import name_key
from .skills import NAMES, SKILLS

BUDGET_CHARS = 80000        # F8: about 3.5 characters per token; the default, F30 sets it per advice
MAX_IMAGES = 6
MAX_IMAGE_BYTES = 4 * 1024 * 1024

SYSTEM = (
    "Je helpt een coach of gildemeester van de HBO-ICT-opleiding Open-ICT bij het voorbereiden van een beoordeling. "
    "Geef per gevraagde vaardigheid een advies over het niveau: 0 is startniveau, daarna 1 tot en met 4. "
    "De LEF-teksten zijn de maatstaf: een niveau past als het materiaal laat zien wat de LEF-tekst van dat niveau beschrijft. "
    "Baseer je alleen op het aangeleverde materiaal. Verzin niets: noem alleen bewijsstukken, feedback en handelingen die in "
    "het materiaal staan, en noem bewijsstukken bij hun naam. Ontbreekt er bewijs, zeg dat dan. "
    "Schrijf in het Nederlands, kort, ontwikkelingsgericht en niet beoordelend, gericht aan de coach. "
    "Geef bij 'ontbreekt' wat er nog ontbreekt voor het gevraagde niveau of wat de student kan doen om verder te komen. "
    "Het is een advies: de coach of gildemeester beslist."
)


S_PROMPT = "ai_prompt"                  # F18: the general instruction, if the user changed it
SKILL_PROMPT = "ai_prompt_{}"           # F19: an addition per skill
PROMPT_SETTINGS = (S_PROMPT, *(SKILL_PROMPT.format(code) for code in SKILLS))


def system_prompt(database: str) -> str:
    """F18: the user's own general instruction, or the standard one."""
    return (db.get_setting(database, S_PROMPT) or "").strip() or SYSTEM


def skill_prompts(database: str) -> dict[str, str]:
    """F19: per skill the user's addition (only the ones filled in)."""
    result = {}
    for code in SKILLS:
        text = (db.get_setting(database, SKILL_PROMPT.format(code)) or "").strip()
        if text:
            result[code] = text
    return result


def schema(codes: list[str], difference: bool = True) -> dict:
    """F5: the fixed answer of the model; with `difference` (F25) also how the advice compares with the
    assessor's own judgment."""
    fields = {"code": {"type": "string", "enum": codes},
              "niveau": {"type": "integer", "enum": [0, 1, 2, 3, 4]},
              "onderbouwing": {"type": "string"},
              "ontbreekt": {"type": "string"}}
    if difference:
        fields["verschil"] = {"type": "string"}
    return {"type": "object", "required": ["vaardigheden"], "properties": {"vaardigheden": {
        "type": "array", "items": {"type": "object", "required": list(fields), "additionalProperties": False,
                                   "properties": fields}}},
            "additionalProperties": False}


SERVICES = {"lokaal": "Lokaal model (Ollama)", "claude": "Claude (Anthropic, via internet)"}


def model_label(model: str) -> str:
    """F27, F14: the model name, with "(aangeraden)" for the recommended one."""
    return f"{model} (aangeraden)" if model == ollama.DEFAULT_MODEL else model


def choice_key(service: str, model: str | None = None) -> str:
    """F14: the value in the choice on the evaluation page: "lokaal:<model>" or "claude"."""
    return f"lokaal:{model}" if service == "lokaal" and model else service


def parse_choice(key: str, database: str) -> tuple[str, str | None]:
    """F14: (service, model) of a choice; plain "lokaal" means the default model."""
    service, _, model = (key or "").partition(":")
    if service == "lokaal":
        return service, model or settings(database)[1]
    return service, None


def available(database: str, user_name: str | None = None) -> list[dict]:
    """F14: the AIs that are set up, for the choice on the evaluation page: every model in Ollama apart
    (the default first), then Claude, only for the allowed Portflow user (F22)."""
    result = []
    url, default = settings(database)
    try:
        names = [m["name"] for m in ollama.models(url)]
    except ollama.OllamaError:
        names = []
    for name in sorted(names, key=lambda n: (n != default, n)):
        result.append({"key": choice_key("lokaal", name), "label": f"Lokaal model · {model_label(name)}",
                       "external": False, "default": name == default})
    if claude_ai.ready(database) and claude_ai.allowed(user_name):
        result.append({"key": "claude", "label": f"Claude · {claude_ai.MODEL} (via internet)", "external": True})
    return result


def laptop(database: str) -> dict:
    """F29-F31: how much of the laptop the local model may use: {'threads', 'context', 'unload'}."""
    try:
        threads = int(db.get_setting(database, ollama.S_THREADS) or 0)
    except ValueError:
        threads = 0
    threads = min(threads, ollama.cores()) if threads >= 1 else ollama.default_threads()
    context = db.get_setting(database, ollama.S_CONTEXT) or ollama.DEFAULT_CONTEXT
    if context not in ollama.CONTEXTS:
        context = ollama.DEFAULT_CONTEXT
    return {"threads": threads, "context": context, "unload": db.get_setting(database, ollama.S_UNLOAD) == "1"}


def model_options(database: str) -> dict:
    """F29-F31: the extra arguments for ollama.chat; the budget of F8 goes along with the context."""
    own = laptop(database)
    num_ctx, budget = ollama.CONTEXTS[own["context"]]
    return {"num_ctx": num_ctx, "budget": budget, "num_thread": own["threads"],
            "keep_alive": 0 if own["unload"] else None}


def settings(database: str) -> tuple[str, str]:
    """F11: the address of Ollama and the chosen model."""
    return (db.get_setting(database, ollama.S_URL) or ollama.DEFAULT_URL,
            db.get_setting(database, ollama.S_MODEL) or ollama.DEFAULT_MODEL)


# Names (F3) ----------------------------------------------------------------------------------------

def replacements(conn: sqlite3.Connection, student_name: str) -> dict[str, str]:
    """The student -> "Student"; coaches and guild masters -> "Coach 1", "Gildemeester 1"; the user ->
    "de beoordelaar"; other known names (fellow students, authors of feedback) -> "Medestudent N"."""
    names: dict[str, str] = {}
    me = next((r[0] for r in conn.execute("SELECT value FROM settings WHERE key = ?", (S_USER_NAME,)) if r[0]), None)
    if me:
        names[me] = "de beoordelaar"
    if student_name:
        names[student_name] = "Student"
        first = student_name.split()[0]
        if len(first) >= 3:
            names.setdefault(first, "Student")
    counters = {"Coach": 0, "Gildemeester": 0}
    for row in conn.execute("SELECT name, is_coach, is_guild_master FROM staff ORDER BY id"):
        if row["name"] and row["name"] not in names and name_key(row["name"]) != name_key(me):
            label = "Gildemeester" if row["is_guild_master"] and not row["is_coach"] else "Coach"
            counters[label] += 1
            names[row["name"]] = f"{label} {counters[label]}"
    others = 0
    for name in numbers(conn):
        if name not in names:
            others += 1
            names[name] = f"Medestudent {others}"
    return names


def restore(text: str, names: dict[str, str]) -> str:
    """F23: undo the name replacement in the AI output, so the real names are shown again.
    names is real -> placeholder (as used before sending). A single-word placeholder ("Student")
    is matched case-sensitively so a generic "de student" stays; multi-word placeholders
    ("Coach 1", "de beoordelaar") case-insensitively. Longest placeholder first, whole words."""
    if not text or not names:
        return text
    # When two names map to the same placeholder (the student's full name and first name both to
    # "Student"), restore to the longest real name.
    by_placeholder: dict[str, str] = {}
    for real, placeholder in names.items():
        if placeholder and (placeholder not in by_placeholder or len(real) > len(by_placeholder[placeholder])):
            by_placeholder[placeholder] = real
    for placeholder, real in sorted(by_placeholder.items(), key=lambda kv: len(kv[0]), reverse=True):
        flags = 0 if placeholder.isalnum() else re.IGNORECASE   # bare word: exact case only
        text = re.sub(r"(?<!\w)" + re.escape(placeholder) + r"(?!\w)", lambda _m: real, text, flags=flags)
    return text


# Collecting the material (F2, F7, F8) ------------------------------------------------------------------

def _plain(html_text: str | None) -> str:
    return plain_text(html_text or "")


def _lef_plain(code: str) -> str:
    parts = []
    for level in (1, 2, 3, 4):
        text = lef.level_text(code, level)
        if text:
            parts.append(f"Niveau {level} – {text['title']}:\n" + re.sub(r"\n{2,}", "\n", plain_text(
                text["html"].replace("</li>", "</li>\n").replace("<li>", "- "))))
    return "\n\n".join(parts)


def overview(data: dict) -> dict:
    """F2: what goes to the model, as counts (before asking; the files are read while asking)."""
    skills = data["skills"]
    evidence_ids = {e["id"] for s in skills for e in s["evidence"]}
    files = {e["id"] for s in skills for e in s["evidence"] if e["raw_kind"] == "file"}
    return {"skills": len(skills), "evidence": len(evidence_ids), "files": len(files),
            "earlier": sum(len(s["earlier"]) for s in skills),
            "feedback": sum(1 + t["replies"] for s in skills for t in s["threads"])}


def collect(conn: sqlite3.Connection, database: str, token: str | None, request_id: int, today: date,
            progress=None, *, vision: bool = True, detail=evidence.detail, files=evidence_files) -> dict:
    """Everything about the request as text, names not yet replaced. Returns
    {'codes', 'student', 'sections', 'evidence': [...], 'images': [...], 'counts', 'names_only': [...]}."""
    start, end, _ = semester_period(conn, today)
    data = evaluation_page.build(conn, request_id, today, start, end)
    if data is None or not data["skills"]:
        raise ollama.OllamaError("Van dit verzoek zijn geen vaardigheden bekend; klik eerst op Verversen.")
    r, student_id = data["request"], data["request"]["student_id"]
    note = conn.execute("SELECT note FROM received_requests WHERE review_request_id = ?", (request_id,)).fetchone()
    feedback_text = _feedback_texts(conn, student_id, start, end)
    extra = skill_prompts(database)   # F19

    head = [f'Evaluatieverzoek "{r["title"]}" van {r["student"]}, ingediend {r["submitted"]}.']
    if note and _plain(note["note"]):
        head.append("Toelichting van de student:\n" + _plain(note["note"]))
    sections, contents, images, names_only = [], [], [], []
    all_evidence = {}
    for s in data["skills"]:
        lines = [f"## Vaardigheid {s['code']} ({s['name']})",
                 f"Beoordeeld door: {s['assessor']}. Hoogste behaalde niveau tot nu toe: "
                 f"{s['current'] if s['current'] is not None else 'nog geen'}. De student vraagt niveau: "
                 f"{s['claimed'] if s['claimed'] is not None else 'niet aangegeven'}.",
                 "Zelfevaluatie van de student:\n" + (_plain(s["self_text"]) or "(geen tekst)"),
                 "LEF-teksten (de maatstaf):\n" + _lef_plain(s["code"])]
        if s["code"] in extra:
            lines.append(f"Waar de beoordelaar bij {s['code']} in het bijzonder op wil letten:\n{extra[s['code']]}")
        if s["earlier"]:
            lines.append("Eerdere beoordelingen:\n" + "\n".join(
                f"- niveau {e['level']} op {e['date']} door {e['author']} ({e['role']}): {_plain(e['text']) or '(geen tekst)'}"
                for e in s["earlier"]))
        else:
            lines.append("Eerdere beoordelingen: geen.")
        if s["evidence"]:
            lines.append("Bewijsstukken bij deze vaardigheid (nieuwste eerst; de inhoud staat verderop):\n" + "\n".join(
                f"- {e['name']} ({e['kind']}, toegevoegd {e['created']})" for e in s["evidence"]))
        else:
            lines.append("Bewijsstukken bij deze vaardigheid: geen.")
        threads = [feedback_text[t["id"]] for t in s["threads"] if t["id"] in feedback_text]
        if threads:
            lines.append("Feedbackvragen en reacties op deze bewijsstukken:\n" + "\n".join(threads))
        sections.append("\n\n".join(lines))
        for e in s["evidence"]:
            all_evidence.setdefault(e["id"], dict(e, skills=[]))["skills"].append(s["code"])

    # F7: the contents of the evidence, newest first per skill (F8 trims them later).
    total = len(all_evidence)
    for number, (evidence_id, e) in enumerate(all_evidence.items(), start=1):
        if progress:
            progress(f"Bewijsstukken lezen ({number} van {total})")
        details, _ = detail(conn, student_id, evidence_id, token)
        if not details:
            names_only.append(e["name"])
            continue
        if details.get("text"):
            contents.append({"name": e["name"], "skills": e["skills"], "text": _plain(details["text"])})
            continue
        texts = []
        for f in details.get("files") or []:
            kind = f["display"]
            try:
                if kind == "image" and vision and len(images) < MAX_IMAGES:
                    path, mime = files.shown_file(database, conn, token, student_id, details["portfolio_id"], f["id"])
                    data_bytes = path.read_bytes()
                    if len(data_bytes) <= MAX_IMAGE_BYTES and mime in ("image/png", "image/jpeg", "image/gif", "image/webp"):
                        images.append({"name": f"{e['name']} – {f['name']}", "mime": mime,
                                       "data": base64.b64encode(data_bytes).decode()})
                        texts.append(f"[afbeelding {f['name']}: meegestuurd als afbeelding {len(images)}]")
                        continue
                elif file_text.readable(f["mime"]):
                    raw = files.original_bytes(conn, token, student_id, details["portfolio_id"], f["id"])
                    text = file_text.text_of(raw, f["mime"])
                    if text:
                        texts.append(f"[bestand {f['name']}]\n{text}")
                        continue
            except evidence_files.FileError:
                pass
            texts.append(f"[bestand {f['name']}: inhoud niet gelezen]")
            names_only.append(f"{e['name']} – {f['name']}")
        if details.get("url"):
            texts.append(f"[link naar {details['url']}]")
        contents.append({"name": e["name"], "skills": e["skills"], "text": "\n".join(texts) or "(geen inhoud)"})

    counts = overview(data)
    return {"codes": data["codes"], "student": r["student"], "head": "\n".join(head), "sections": sections,
            "contents": contents, "images": images, "names_only": names_only, "counts": counts}


def _feedback_texts(conn, student_id: int, start: date, end: date) -> dict[int, str]:
    from .feedback import _requests
    result = {}
    names = {r["evidence_id"]: r["name"] for r in conn.execute(
        "SELECT evidence_id, name FROM evidence_items WHERE student_id = ?", (student_id,))}
    for request in _requests(conn, student_id, start, end):
        lines = [f"- Feedbackvraag bij {names.get(request['evidence_id'], 'een bewijsstuk')} van {request['author_name']}: "
                 f"{plain_text(request['text'])}"]
        lines += [f"  - Reactie van {reply['author_name']} ({reply['role']}): {plain_text(reply['text'])}"
                  for reply in request["replies"]]
        result[request["comment_id"]] = "\n".join(lines)
    return result


JUDGMENT_INTRO = (
    "# Voorlopig oordeel van de beoordelaar\n"
    "De beoordelaar heeft eerst zelf een oordeel gevormd. Kom eerst zelf, alleen op basis van het materiaal en de "
    "LEF-teksten, tot je advies; ga niet zomaar mee met dit oordeel. Zeg daarna per vaardigheid bij 'verschil' of je "
    "advies overeenkomt met dit oordeel, en zo niet, waarin het afwijkt en waarom.")


def judgment_text(codes: list[str], judgment: dict) -> str:
    """F25: the assessor's own judgment as text for the model (names not yet replaced)."""
    lines = [JUDGMENT_INTRO]
    for code in codes:
        own = judgment.get(code) or {}
        lines.append(f"- {code} ({NAMES[code]}): niveau {own.get('level', '?')}. Toelichting: {own.get('text') or '(geen)'}")
    return "\n".join(lines)


def judgment_complete(codes: list[str], judgment: dict) -> bool:
    """F24: a level and an explanation for every requested skill."""
    return all(isinstance((judgment.get(c) or {}).get("level"), int) and (judgment.get(c) or {}).get("text", "").strip()
               for c in codes)


def judgment_from_form(codes: list[str], form) -> dict:
    """F24: the fields "oordeel_niveau_<code>" (0-4) and "oordeel_<code>" (text) of the advice form."""
    result = {}
    for code in codes:
        raw = (form.get(f"oordeel_niveau_{code}") or "").strip()
        level = int(raw) if raw.isdigit() and 0 <= int(raw) <= 4 else None
        result[code] = {"level": level, "text": (form.get(f"oordeel_{code}") or "").strip()[:4000]}
    return result


def saved_judgment(conn: sqlite3.Connection, request_id: int) -> dict:
    """F26: the kept judgment of this request ({} if none)."""
    row = conn.execute("SELECT judgment FROM ai_judgment WHERE review_request_id = ?", (request_id,)).fetchone()
    return json.loads(row["judgment"]) if row else {}


def save_judgment(database: str, request_id: int, judgment: dict) -> None:
    conn = db.connect(database)
    try:
        with conn:
            conn.execute("INSERT OR REPLACE INTO ai_judgment (review_request_id, judgment, saved_at) VALUES (?, ?, ?)",
                         (request_id, json.dumps(judgment), datetime.now(timezone.utc).isoformat()))
    finally:
        conn.close()


def prompt(material: dict, names: dict[str, str], judgment: dict | None = None,
           budget: int | None = None) -> tuple[str, list[dict], dict]:
    """F3, F8, F25: the question for the model with the names replaced, within the budget, with the
    assessor's own judgment. Returns (text, images as {'data', 'mime'}, counts)."""
    fixed = anonymize(material["head"] + "\n\n" + "\n\n".join(material["sections"]), names)
    room = max(0, (budget or BUDGET_CHARS) - len(fixed) - 2000)   # F8, F30
    contents = [dict(c, text=anonymize(c["text"], names), name=anonymize(c["name"], names)) for c in material["contents"]]
    # F8: per skill the same room, newest first; what does not fit goes with its name only.
    per_item = room // max(1, len(contents))
    shown, cut = [], []
    used = 0
    for c in contents:
        text = c["text"]
        if used >= room:
            cut.append(c["name"])
            continue
        if len(text) > per_item and len(contents) > 1:
            text = text[:max(per_item, 2000)] + " […ingekort]"
        text = text[:room - used]
        used += len(text)
        shown.append(f"### {c['name']} (bij {', '.join(c['skills'])})\n{text}")
    parts = [fixed]
    if shown:
        parts.append("# Inhoud van de bewijsstukken\n\n" + "\n\n".join(shown))
    if cut:
        parts.append("Van deze bewijsstukken past de inhoud niet; alleen de naam: " + ", ".join(cut))
    if judgment:
        parts.append(anonymize(judgment_text(material["codes"], judgment), names))
    parts.append("Geef nu per vaardigheid (" + ", ".join(material["codes"]) + ") het advies.")
    counts = dict(material["counts"], cut=len(cut), names_only=[anonymize(n, names) for n in material["names_only"]],
                  images=len(material["images"]))
    return "\n\n".join(parts), [{"data": i["data"], "mime": i["mime"]} for i in material["images"]], counts


def check(answer: dict, codes: list[str]) -> list[dict]:
    """F5: only well-formed advice for the requested skills, in the order OC ... RE."""
    if not isinstance(answer, dict) or not isinstance(answer.get("vaardigheden"), list):
        raise ollama.OllamaError("Het model gaf geen bruikbaar advies. Probeer het opnieuw.")
    found = {}
    for item in answer["vaardigheden"]:
        if not isinstance(item, dict) or item.get("code") not in codes or item["code"] in found:
            continue
        level = item.get("niveau")
        if isinstance(level, str) and level.isdigit():
            level = int(level)
        if not isinstance(level, int) or isinstance(level, bool) or not 0 <= level <= 4:
            continue
        found[item["code"]] = {"code": item["code"], "name": NAMES[item["code"]], "level": level,
                               "reasoning": str(item.get("onderbouwing") or "").strip(),
                               "missing": str(item.get("ontbreekt") or "").strip(),
                               "difference": str(item.get("verschil") or "").strip()}
    if not found:
        raise ollama.OllamaError("Het model gaf geen bruikbaar advies. Probeer het opnieuw.")
    return [found[c] for c in SKILLS if c in found]


# Keeping the advice (F9) -------------------------------------------------------------------------

def duration(seconds: int | None) -> str:
    """F20: '45 s', '1 min 12 s'."""
    if seconds is None:
        return ""
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes} min {rest} s" if minutes else f"{rest} s"


def saved(conn: sqlite3.Connection, request_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM ai_advice WHERE review_request_id = ?", (request_id,)).fetchone()
    if row is None:
        return None
    moment = datetime.fromisoformat(row["created_at"]).astimezone()
    names = json.loads(row["names"] or "{}")   # F23: the real names go back into what is shown
    judgment = json.loads(row["judgment"] or "{}")   # F25: the own judgment that was sent with it
    skills = [dict(s, reasoning=restore(s["reasoning"], names), missing=restore(s["missing"], names),
                   difference=restore(s.get("difference", ""), names), own=judgment.get(s["code"]))
              for s in json.loads(row["advice"])]
    counts = json.loads(row["counts"])
    counts["names_only"] = [restore(n, names) for n in counts.get("names_only", [])]
    conversation = [{"question": turn["question"], "answer": restore(turn["answer"], names),
                     "date": turn.get("date", ""), "duration": duration(turn.get("seconds"))}
                    for turn in json.loads(row["conversation"] or "[]")]
    return {"model": row["model"], "service": row["service"], "service_label": SERVICES.get(row["service"], row["service"]),
            "date": f"{moment.day}-{moment.month}-{moment.year} {moment:%H:%M}",
            "duration": duration(row["seconds"]), "can_ask": bool(row["prompt"]),
            "conversation": conversation, "skills": skills, "counts": counts}


def save(database: str, request_id: int, model: str, skills: list[dict], counts: dict, service: str = "lokaal",
         seconds: int | None = None, prompt_text: str | None = None, names: dict[str, str] | None = None,
         judgment: dict | None = None) -> None:
    """F9: a new advice replaces the old one and its conversation (F21). `names` (F23) is the name
    replacement used, kept to show the real names again; the stored advice itself stays anonymized
    (it is sent back to the AI for follow-up questions)."""
    conn = db.connect(database)
    try:
        with conn:
            conn.execute("INSERT OR REPLACE INTO ai_advice (review_request_id, model, created_at, advice, counts, service, "
                         "seconds, prompt, conversation, names, judgment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]', ?, ?)",
                         (request_id, model, datetime.now(timezone.utc).isoformat(), json.dumps(skills), json.dumps(counts),
                          service, seconds, prompt_text, json.dumps(names or {}), json.dumps(judgment or {})))
    finally:
        conn.close()


def add_turn(database: str, request_id: int, question: str, question_anon: str, answer: str, seconds: int) -> None:
    """F21: keep a follow-up question (the real one for showing, the anonymized one for the AI history,
    F23) with its answer (anonymized; the real names are put back when shown)."""
    conn = db.connect(database)
    try:
        with conn:
            row = conn.execute("SELECT conversation FROM ai_advice WHERE review_request_id = ?", (request_id,)).fetchone()
            turns = json.loads(row["conversation"] or "[]") if row else []
            moment = datetime.now(timezone.utc).astimezone()
            turns.append({"question": question, "question_anon": question_anon, "answer": answer, "seconds": seconds,
                          "date": f"{moment.day}-{moment.month}-{moment.year} {moment:%H:%M}"})
            conn.execute("UPDATE ai_advice SET conversation = ? WHERE review_request_id = ?", (json.dumps(turns), request_id))
    finally:
        conn.close()


FOLLOW_UP = ("Hieronder volgen vervolgvragen van de coach over jouw advies. Antwoord in het Nederlands, kort en "
             "concreet, op basis van hetzelfde materiaal. Verzin niets; zeg het als het materiaal geen antwoord geeft. "
             "Antwoord in gewone tekst, zonder JSON.")


def _history(row, question: str) -> list[dict]:
    """F21: the advice and the conversation so far as messages, then the new question."""
    advice = json.loads(row["advice"])
    messages = [{"role": "assistant", "content": json.dumps({"vaardigheden": [
        dict({"code": a["code"], "niveau": a["level"], "onderbouwing": a["reasoning"], "ontbreekt": a["missing"]},
             **({"verschil": a["difference"]} if a.get("difference") else {})) for a in advice]},
        ensure_ascii=False)}]
    turns = json.loads(row["conversation"] or "[]")
    for i, turn in enumerate(turns):
        prefix = FOLLOW_UP + "\n\n" if i == 0 else ""
        messages += [{"role": "user", "content": prefix + turn.get("question_anon", turn["question"])},
                     {"role": "assistant", "content": turn["answer"]}]
    messages.append({"role": "user", "content": (FOLLOW_UP + "\n\n" if not turns else "") + question})
    return messages


# Running in the background (F4) ------------------------------------------------------------------------

class Jobs:
    """One advice at a time per request; the page polls the status."""

    def __init__(self, database: str, token_source):
        self.database = database
        self.token_source = token_source     # () -> Portflow token or None
        self.lock = threading.Lock()
        self.jobs: dict[int, dict] = {}

    def status(self, request_id: int) -> dict | None:
        with self.lock:
            job = self.jobs.get(request_id)
            return {k: v for k, v in job.items() if k != "cancel"} if job else None

    def ask(self, request_id: int, question: str) -> bool:
        """F21: a follow-up question to the AI that made the advice."""
        question = question.strip()
        if not question:
            return False
        with self.lock:
            job = self.jobs.get(request_id)
            if job and job["state"] == "running":
                return False
            self.jobs[request_id] = {"state": "running", "kind": "question", "step": "Antwoord wordt gemaakt…", "error": "",
                                     "question": question, "cancel": threading.Event()}
        threading.Thread(target=self._ask, args=(request_id, question), daemon=True).start()
        return True

    def _ask(self, request_id: int, question: str) -> None:
        import time
        cancel = self.jobs[request_id]["cancel"]
        conn = db.connect(self.database)
        what, phase, started, failure = "vervolgvraag", "voorbereiden", None, None
        try:
            row = conn.execute("SELECT * FROM ai_advice WHERE review_request_id = ?", (request_id,)).fetchone()
            if row is None or not row["prompt"]:
                raise ollama.OllamaError("Vraag eerst opnieuw een advies; bij dit advies is het materiaal niet bewaard.")
            student = conn.execute("SELECT s.name FROM evaluations e JOIN students s ON s.id = e.student_id "
                                   "WHERE e.review_request_id = ? LIMIT 1", (request_id,)).fetchone()
            names = json.loads(row["names"] or "{}") or replacements(conn, student["name"] if student else "")
            question_anon = anonymize(question, names)
            history = _history(row, question_anon)
            started = time.monotonic()

            def written(*_):
                self._set(request_id, step=f"Antwoord wordt gemaakt… ({int(time.monotonic() - started)} s)")

            phase = "het antwoord"
            if row["service"] == "claude":
                what = f"vervolgvraag aan Claude ({claude_ai.MODEL})"
                if not claude_ai.ready(self.database):
                    raise ollama.OllamaError("Claude is niet meer ingesteld. Open AI-advies instellen.")
                answer = claude_ai.chat(claude_ai.key(self.database), system_prompt(self.database), row["prompt"], None,
                                        history=history, cancel=cancel, progress=written)
            else:
                url, _model = settings(self.database)
                options = model_options(self.database)   # F29-F31
                what = (f"vervolgvraag aan {row['model']} op {url} ({options['num_thread']} kernen, "
                        f"{options['num_ctx']} tokens{', daarna uit het geheugen' if options['keep_alive'] == 0 else ''})")
                answer = ollama.chat(url, row["model"], system_prompt(self.database), row["prompt"], None, history=history,
                                     num_ctx=options["num_ctx"], num_thread=options["num_thread"],
                                     keep_alive=options["keep_alive"], cancel=cancel, progress=written)
            if not answer:
                raise ollama.OllamaError("Het model gaf geen antwoord. Probeer het opnieuw.")
            add_turn(self.database, request_id, question, question_anon, answer, round(time.monotonic() - started))
            self._set(request_id, state="done", step="Klaar")
        except ollama.OllamaError as error:
            failure = error
            self._set(request_id, state="stopped" if cancel.is_set() else "error", error=error.message)
        except Exception as error:
            import logging
            logging.getLogger(__name__).exception("AI follow-up failed")
            failure = ollama.OllamaError("onverwachte fout in het dashboard", type(error).__name__)
            self._set(request_id, state="error", error="Er ging iets mis bij het beantwoorden van de vraag.")
        finally:
            conn.close()
            self._log_end("Vervolgvraag", request_id, what, failure, cancel, started, phase)

    def start(self, request_id: int, service: str = "lokaal", model: str | None = None,
              judgment: dict | None = None) -> bool:
        """F14: `model` is the chosen local model (None: the default); F25: `judgment` goes with it."""
        if service not in SERVICES:
            return False
        if service == "lokaal":
            model = model or settings(self.database)[1]
        with self.lock:
            job = self.jobs.get(request_id)
            if job and job["state"] == "running":
                return False
            label = f"{SERVICES[service]} · {model}" if service == "lokaal" else SERVICES[service]
            self.jobs[request_id] = {"state": "running", "kind": "advice", "step": "Materiaal verzamelen…", "error": "",
                                     "service": service, "choice": choice_key(service, model), "service_label": label,
                                     "cancel": threading.Event()}
        threading.Thread(target=self._run, args=(request_id, service, model, judgment), daemon=True).start()
        return True

    def stop(self, request_id: int) -> None:
        with self.lock:
            job = self.jobs.get(request_id)
            if job and job["state"] == "running":
                job["cancel"].set()
                job["step"] = "Stoppen…"

    def _set(self, request_id: int, **values) -> None:
        with self.lock:
            self.jobs[request_id].update(values)

    def _log_end(self, topic: str, request_id: int, what: str, error: "ollama.OllamaError | None", cancel,
                 started: float | None, phase: str) -> None:
        """Spec 042: one line when an advice or a follow-up question ends: done, stopped or failed, with
        the request number (no names or content, F6) and the duration."""
        import time
        took = f" na {round(time.monotonic() - started)} s" if started else ""
        if error is None:
            ai_log.add(self.database, topic, True, f"Verzoek {request_id}: {what}; klaar{took}")
        elif cancel.is_set():
            ai_log.add(self.database, topic, False, f"Verzoek {request_id}: {what}; gestopt door de gebruiker{took}")
        else:
            ai_log.add(self.database, topic, False, f"Verzoek {request_id}: {what}; mislukt bij {phase}{took}: {error.message}",
                       error.detail)

    def _run(self, request_id: int, service: str, model: str | None = None, judgment: dict | None = None) -> None:
        cancel = self.jobs[request_id]["cancel"]
        url, default = settings(self.database)
        model = model or default
        conn = db.connect(self.database)
        what = f"advies met {model} op {url}" if service != "claude" else f"advies met Claude ({claude_ai.MODEL})"
        phase, started, failure = "de controle van het model", None, None
        try:
            if service == "claude":
                api_key, model, vision = claude_ai.key(self.database), claude_ai.MODEL, True
                if not claude_ai.ready(self.database):
                    raise ollama.OllamaError("Claude is nog niet ingesteld. Open AI-advies instellen.")
            else:
                if not ollama.has_model(url, model):
                    raise ollama.OllamaError(f"Het model {model} staat niet in Ollama. Open de wizard AI-advies instellen.")
                vision = "vision" in ollama.capabilities(url, model)

            def step(text):
                if cancel.is_set():
                    raise ollama.OllamaError("Gestopt.")
                self._set(request_id, step=text)

            phase = "het verzamelen van het materiaal"
            material = collect(conn, self.database, self.token_source(), request_id, date.today(), step, vision=vision)
            names = replacements(conn, material["student"])
            options = model_options(self.database)   # F29-F31, fixed at the start of this advice (F32)
            text, images, counts = prompt(material, names, judgment, options["budget"] if service != "claude" else None)
            # Spec 042: numbers only (F6)
            what += (f" ({len(material['codes'])} vaardighe{'id' if len(material['codes']) == 1 else 'den'}, "
                     f"{len(material['contents'])} bewijsstukken, {len(images)} afbeeldingen, {len(text)} tekens"
                     + (f", {counts['cut']} alleen met naam" if counts.get("cut") else "")
                     + ("" if service == "claude" else f"; {options['num_thread']} kernen, {options['num_ctx']} tokens"
                        + (", daarna uit het geheugen" if options["keep_alive"] == 0 else "")) + ")")
            step("Advies schrijven…")
            import time
            phase = "het schrijven van het advies"
            started = time.monotonic()

            def written(*_):
                self._set(request_id, step=f"Advies schrijven… ({int(time.monotonic() - started)} s)")

            if service == "claude":
                answer = claude_ai.chat(api_key, system_prompt(self.database), text, schema(material["codes"], bool(judgment)), images=images,
                                        cancel=cancel, progress=written)
            else:
                answer = ollama.chat(url, model, system_prompt(self.database), text, schema(material["codes"], bool(judgment)), images=[i["data"] for i in images],
                                     num_ctx=options["num_ctx"], num_thread=options["num_thread"],
                                     keep_alive=options["keep_alive"], cancel=cancel, progress=written)
            phase = "het controleren van het antwoord"
            save(self.database, request_id, model, check(answer, material["codes"]), counts, service,
                 round(time.monotonic() - started), text, names, judgment)
            self._set(request_id, state="done", step="Klaar")
        except ollama.OllamaError as error:
            failure = error
            self._set(request_id, state="stopped" if cancel.is_set() else "error", error=error.message)
        except Exception as error:
            import logging
            logging.getLogger(__name__).exception("AI advice failed")
            failure = ollama.OllamaError("onverwachte fout in het dashboard", type(error).__name__)
            self._set(request_id, state="error", error="Er ging iets mis bij het maken van het advies.")
        finally:
            conn.close()
            self._log_end("Advies", request_id, what, failure, cancel, started, phase)


# The trial question of the wizard (F12, step 4) ------------------------------------------------------------

TRIAL = ("Vaardigheid PL (Plannen). De student vraagt niveau 1.\nZelfevaluatie: Ik heb voor mijn eigen taken in sprint 2 "
         "een planning gemaakt en die bijgehouden.\nLEF niveau 1 – Plannen van eigen werk: je maakt een planning voor je "
         "eigen werk en houdt die bij.\nBewijsstukken: Planning sprint 2 (bestand).\nGeef het advies.")


def trial(url: str, model: str, system: str = SYSTEM, options: dict | None = None) -> dict:
    """A small invented evaluation; returns {'seconds', 'level'} or raises OllamaError. `options`
    (model_options, F29, F31): the cores and unloading; the context stays small."""
    import time
    options = options or {}
    started = time.monotonic()
    answer = ollama.chat(url, model, system, TRIAL, schema(["PL"], difference=False), num_ctx=4096, timeout=600,
                         num_thread=options.get("num_thread"), keep_alive=options.get("keep_alive"))
    advice = check(answer, ["PL"])
    return {"seconds": round(time.monotonic() - started), "level": advice[0]["level"]}
