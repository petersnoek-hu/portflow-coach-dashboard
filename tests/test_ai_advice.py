"""Tests for spec 040: AI advice with a local model. A fake Ollama; invented names and data."""

import io
import json
import threading
import time
import unittest
import zipfile
from unittest import mock

from dashboard import ai_advice, ai_log, ai_routes, db, file_text, ollama, reset
from tests.test_evaluation_page import PageCase


def fake_detail(conn, student_id, evidence_id, token, **_):
    if evidence_id == 501:
        return {"text": "", "files": [{"id": 1, "name": "plan.docx", "mime": file_text.DOCX, "display": "pdf"},
                                      {"id": 2, "name": "bord.png", "mime": "image/png", "display": "image"},
                                      {"id": 3, "name": "demo.mp4", "mime": "video/mp4", "display": "video"}],
                "portfolio_id": 101, "url": ""}, None
    if evidence_id == 502:
        return {"text": "<p>Retro met Noor Smit en Lotte Bakker: we schatten te optimistisch.</p>", "files": [],
                "portfolio_id": 101, "url": ""}, None
    return None, "niet gevonden"


def docx(text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                         f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p><w:p><w:r><w:t>Tweede alinea</w:t></w:r></w:p></w:body></w:document>")
    return buffer.getvalue()


class FakeFiles:
    def __init__(self, tmp):
        self.tmp = tmp

    def shown_file(self, database, conn, token, sid, pid, fid):
        path = self.tmp / f"{fid}.png"
        path.write_bytes(b"\x89PNG fake")
        return path, "image/png"

    def original_bytes(self, conn, token, sid, pid, fid):
        return docx("Planning sprint 3 voor Lotte Bakker")


ANSWER = {"vaardigheden": [
    {"code": "BD", "niveau": 1, "onderbouwing": "Retro laat het zien.", "ontbreekt": "Meer bewijs."},
    {"code": "PL", "niveau": 2, "onderbouwing": "Sprintplanning laat afstemming zien.", "ontbreekt": "Niveau 3: betrokkenen."},
    {"code": "KO", "niveau": 3, "onderbouwing": "niet gevraagd", "ontbreekt": ""}]}


class AdviceCase(PageCase):
    def setUp(self):
        super().setUp()
        from pathlib import Path
        self.files = FakeFiles(Path(self.tmp.name))
        with self.conn:
            self.conn.execute("INSERT INTO settings (key, value) VALUES ('portflow_user_name', 'Kees de Wit')")
        from dashboard import claude_ai
        from dashboard.progress import name_key
        patcher = mock.patch.object(claude_ai, "ALLOWED_USERS", {name_key("Kees de Wit")})   # F22: fixture user may use Claude
        patcher.start(); self.addCleanup(patcher.stop)

    def material(self, vision=True):
        return ai_advice.collect(self.conn, self.db_path, "token", 70, ai_advice.date.today(), vision=vision,
                                 detail=fake_detail, files=self.files)


class TestFileText(unittest.TestCase):   # F7
    def test_word_powerpoint_excel(self):
        self.assertEqual(file_text.text_of(docx("Hallo"), file_text.DOCX), "Hallo\nTweede alinea")
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            ns = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
            archive.writestr("ppt/slides/slide2.xml", f'<p:sld xmlns:p="x" {ns}><a:p><a:r><a:t>Tweede dia</a:t></a:r></a:p></p:sld>')
            archive.writestr("ppt/slides/slide1.xml", f'<p:sld xmlns:p="x" {ns}><a:p><a:r><a:t>Titel</a:t></a:r></a:p></p:sld>')
        self.assertEqual(file_text.text_of(buffer.getvalue(), file_text.PPTX), "Dia 1:\nTitel\n\nDia 2:\nTweede dia")

    def test_unreadable_gives_none(self):
        self.assertIsNone(file_text.text_of(b"geen zip", file_text.DOCX))
        self.assertIsNone(file_text.text_of(b"%PDF kapot", "application/pdf"))
        self.assertIsNone(file_text.text_of(b"x", "video/mp4"))


class TestOllama(unittest.TestCase):
    def test_only_an_address_on_the_laptop(self):   # F11, privacy
        self.assertTrue(ollama.is_local("http://127.0.0.1:11434"))
        self.assertTrue(ollama.is_local("http://localhost:11434"))
        for url in ("http://example.org:11434", "https://127.0.0.1:11434", "http://127.0.0.1:11434/x", "ftp://localhost"):
            self.assertFalse(ollama.is_local(url), url)
        with self.assertRaises(ollama.OllamaError):
            ollama.version("http://example.org:11434")
        with self.assertRaises(ollama.OllamaError):
            ollama.chat("http://example.org:11434", "m", "s", "u", None)

    def test_not_running(self):   # F10, F12 step 2
        with self.assertRaises(ollama.OllamaError) as error:
            ollama.version("http://127.0.0.1:9")
        self.assertIn("niet bereikbaar", error.exception.message)

    def test_memory(self):   # F12 step 1
        self.assertGreater(ollama.memory_gb() or 1, 0)


class TestMaterial(AdviceCase):
    def test_everything_goes_along(self):   # F2, F7
        m = self.material()
        self.assertEqual(m["codes"], ["PL", "BD"])
        text = "\n".join(m["sections"])
        for part in ("Zelfevaluatie", "LEF-teksten", "Niveau 4", "Eerdere beoordelingen", "Goed begin", "Klopt mijn planning?",
                     "Ja, mooi", "Sprintplanning"):
            self.assertIn(part, text)
        contents = {c["name"]: c["text"] for c in m["contents"]}
        self.assertIn("Planning sprint 3", contents["Sprintplanning"])       # Word: text from the original
        self.assertIn("meegestuurd als afbeelding 1", contents["Sprintplanning"])   # image as image
        self.assertIn("demo.mp4: inhoud niet gelezen", contents["Sprintplanning"])  # video: name only
        self.assertIn("te optimistisch", contents["Retro"])                  # text evidence
        self.assertEqual(len(m["images"]), 1)
        self.assertIn("Sprintplanning – demo.mp4", m["names_only"])

    def test_without_vision_no_images(self):   # F7
        self.assertEqual(self.material(vision=False)["images"], [])

    def test_names_are_replaced(self):   # F3
        m = self.material()
        names = ai_advice.replacements(self.conn, m["student"])
        text, _, counts = ai_advice.prompt(m, names)
        for real in ("Lotte Bakker", "Lotte", "Noor Smit", "Kees de Wit", "Daan Visser"):
            self.assertNotIn(real, text)
        self.assertIn("Student", text)
        self.assertIn("Coach 1", text)

    def test_budget(self):   # F8
        m = self.material()
        fixed = len(m["head"]) + 2 + len("\n\n".join(m["sections"]))
        with mock.patch.object(ai_advice, "BUDGET_CHARS", fixed + 2000 + 100):
            text, _, counts = ai_advice.prompt(m, {})
        self.assertGreaterEqual(counts["cut"], 1)
        self.assertIn("past de inhoud niet", text)


class TestCheck(unittest.TestCase):   # F5
    def test_only_requested_and_well_formed(self):
        advice = ai_advice.check(ANSWER, ["PL", "BD"])
        self.assertEqual([(a["code"], a["level"]) for a in advice], [("PL", 2), ("BD", 1)])   # order OC ... RE, not KO

    def test_bad_answers(self):
        for answer in ({}, {"vaardigheden": "x"}, {"vaardigheden": [{"code": "PL", "niveau": 7}]}):
            with self.assertRaises(ollama.OllamaError):
                ai_advice.check(answer, ["PL"])


# F24: the assessor's own judgment that has to be sent with every advice (request 70 asks PL and BD).
JUDGMENT = {"oordeel_niveau_PL": "2", "oordeel_PL": "Plant voor het team.", "oordeel_niveau_BD": "1", "oordeel_BD": "Deelt een boodschap."}


class OllamaServer:
    """A tiny local HTTP server that answers /api/chat like Ollama: optionally silent first (`delay`),
    then the `chunks` one by one (`gap` seconds apart). Records the request bodies."""

    def __init__(self, chunks=("ok",), delay=0.0, gap=0.0):
        import http.server
        self.bodies, outer = [], self
        self.chunks, self.delay, self.gap = chunks, delay, gap

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                outer.bodies.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                try:
                    time.sleep(outer.delay)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/x-ndjson")
                    self.end_headers()
                    for i, chunk in enumerate(outer.chunks):
                        if i:
                            time.sleep(outer.gap)
                        self.wfile.write(json.dumps({"message": {"content": chunk}, "done": False}).encode() + b"\n")
                        self.wfile.flush()
                    self.wfile.write(json.dumps({"message": {"content": ""}, "done": True}).encode() + b"\n")
                except (BrokenPipeError, ConnectionResetError):
                    pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def __enter__(self):
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


class FakeOllama:
    """Patches ollama.py: running, with the model, answering ANSWER (slowly if asked)."""

    def __init__(self, running=True, model=True, answer=ANSWER, delay=0.0):
        self.running, self.model, self.answer, self.delay, self.calls = running, model, answer, delay, []

    def models(self, url):
        if not self.running:
            raise ollama.OllamaError("Ollama is niet bereikbaar. Is Ollama gestart?")
        return [{"name": ollama.DEFAULT_MODEL, "size_gb": 7.2}] if self.model else []

    def __enter__(self):
        def version(url):
            if not self.running:
                raise ollama.OllamaError("Ollama is niet bereikbaar. Is Ollama gestart?")
            return "0.34.2"

        def chat(url, model, system, user, schema, **kwargs):
            self.calls.append({"user": user, "images": kwargs.get("images"), "schema": schema, "history": kwargs.get("history"),
                               "options": {k: kwargs.get(k) for k in ("num_ctx", "num_thread", "keep_alive", "timeout")}})
            cancel = kwargs.get("cancel")
            end = time.monotonic() + self.delay
            while time.monotonic() < end:
                if cancel is not None and cancel.is_set():
                    raise ollama.OllamaError("Gestopt.")
                time.sleep(0.01)
            return self.answer if schema is not None else "Omdat de afstemming met de opdrachtgever ontbreekt."

        self.patches = [mock.patch.object(ollama, "version", version),
                        mock.patch.object(ollama, "models", self.models),
                        mock.patch.object(ollama, "has_model", lambda url, m: self.running and self.model),
                        mock.patch.object(ollama, "capabilities", lambda url, m: {"vision"}),
                        mock.patch.object(ollama, "chat", chat)]
        for p in self.patches:
            p.start()
        return self

    def __exit__(self, *exc):
        for p in self.patches:
            p.stop()


class TestJobsAndPage(AdviceCase):
    def setUp(self):
        super().setUp()
        original = ai_advice.collect
        self.patch = mock.patch.object(ai_advice, "collect", lambda conn, database, token, rid, today, progress=None, vision=True:
                                       original(conn, database, token, rid, today, progress, vision=vision,
                                                detail=fake_detail, files=self.files))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        super().tearDown()

    def wait(self, jobs, request_id=70):
        for _ in range(500):
            status = jobs.status(request_id)
            if status and status["state"] != "running":
                return status
            time.sleep(0.01)
        self.fail("the advice did not finish")

    def test_advice_is_made_saved_and_shown(self):   # F1, F4, F5, F6, F9
        with FakeOllama() as fake:
            self.assertEqual(self.client.post("/evaluaties/70/advies", data=JUDGMENT).status_code, 302)
            status = self.wait(self.app.extensions["ai_jobs"])
            self.assertEqual(status["state"], "done")
            html = self.page().get_data(as_text=True)
        self.assertNotIn("Lotte Bakker", fake.calls[0]["user"])                       # F3
        self.assertEqual(fake.calls[0]["schema"]["properties"]["vaardigheden"]["items"]["properties"]["code"]["enum"], ["PL", "BD"])
        self.assertEqual(len(fake.calls[0]["images"]), 1)
        saved = ai_advice.saved(self.conn, 70)
        self.assertEqual([(s["code"], s["level"]) for s in saved["skills"]], [("PL", 2), ("BD", 1)])
        for text in ("Advies (AI)", "advies: niveau 2", "Sprintplanning laat afstemming zien.", "Nog te laten zien:",
                     "jij beslist over het niveau", ollama.DEFAULT_MODEL, "Opnieuw vragen", "Wat gaat er naar het model?"):
            self.assertIn(text, html)

    def test_stop(self):   # F4
        with FakeOllama(delay=5):
            jobs = self.app.extensions["ai_jobs"]
            jobs.start(70)
            for _ in range(300):
                if (jobs.status(70) or {}).get("step", "").startswith("Advies schrijven"):
                    break
                time.sleep(0.01)
            self.assertIn("Stoppen", self.client.get("/evaluaties/70/advies").get_data(as_text=True))
            jobs.stop(70)
            self.assertEqual(self.wait(jobs)["state"], "stopped")
        self.assertIsNone(ai_advice.saved(self.conn, 70))

    def test_invalid_answer(self):   # F5
        with FakeOllama(answer={"iets": "anders"}):
            self.app.extensions["ai_jobs"].start(70)
            status = self.wait(self.app.extensions["ai_jobs"])
        self.assertEqual(status["state"], "error")
        self.assertIn("geen bruikbaar advies", status["error"])

    def test_not_ready_links_to_wizard(self):   # F10
        with FakeOllama(running=False):
            html = self.page().get_data(as_text=True)
        self.assertIn("Ollama is niet gevonden", html)
        self.assertIn('href="/instellingen/ai-advies"', html)
        self.assertNotIn("AI-advies vragen", html)

    def test_reset_removes_advice_keeps_settings(self):   # F9, spec 014
        ai_advice.save(self.db_path, 70, "m", [], {})
        db.set_setting(self.db_path, ollama.S_MODEL, "qwen3.5:9b")
        reset.reset_all(self.app)
        self.assertIsNone(ai_advice.saved(self.conn, 70))
        self.assertEqual(db.get_setting(self.db_path, ollama.S_MODEL), "qwen3.5:9b")


class TestWizard(AdviceCase):   # F11, F12
    def steps(self, html):
        return {n: ('id="stap-%d" open' % n) in html for n in (1, 2, 3, 4)}

    def test_without_ollama_step_2_is_open(self):
        with FakeOllama(running=False):
            html = self.client.get("/instellingen/ai-advies").get_data(as_text=True)
        self.assertEqual(self.steps(html)[2], True)
        self.assertIn("ollama.com/download", html)
        self.assertIn("Controleren", html)

    def test_without_model_step_3_is_open(self):
        with FakeOllama(model=False):
            html = self.client.get("/instellingen/ai-advies").get_data(as_text=True)
        self.assertEqual(self.steps(html), {1: False, 2: False, 3: True, 4: False})
        self.assertIn("Ollama 0.34.2 draait", html)
        self.assertIn("Model downloaden", html)
        self.assertIn(f"ollama pull {ollama.DEFAULT_MODEL}", html)

    def test_trial_then_done(self):
        with FakeOllama(answer={"vaardigheden": [{"code": "PL", "niveau": 1, "onderbouwing": "x", "ontbreekt": "y"}]}):
            self.assertEqual(self.steps(self.client.get("/instellingen/ai-advies").get_data(as_text=True))[4], True)
            result = self.client.post("/instellingen/ai-advies/proefvraag").get_json()
            self.assertTrue(result["ok"])
            html = self.client.get("/instellingen/ai-advies").get_data(as_text=True)
        self.assertIn("De proefvraag werkte", html)
        self.assertIn("Naar Evaluaties", html)

    def test_trial_failure_is_explained(self):
        with FakeOllama(answer={}):
            result = self.client.post("/instellingen/ai-advies/proefvraag").get_json()
        self.assertFalse(result["ok"])
        self.assertIn("geen bruikbaar advies", result["message"])

    def test_settings_only_local_address(self):   # F11
        self.client.post("/instellingen/ai-advies", data={"url": "http://example.org:11434"})
        self.assertIsNone(db.get_setting(self.db_path, ollama.S_URL))
        self.client.post("/instellingen/ai-advies", data={"model": "qwen3.5:9b", "url": "http://localhost:11434/"})
        self.assertEqual(ai_advice.settings(self.db_path), ("http://localhost:11434", "qwen3.5:9b"))

    def test_section_in_settings(self):   # F11
        with FakeOllama():
            html = self.client.get("/instellingen").get_data(as_text=True)
        self.assertIn("AI-advies instellen", html)
        self.assertIn(f"model <strong>{ollama.DEFAULT_MODEL}</strong> is geïnstalleerd", html)


class TestOwnJudgment(TestJobsAndPage):   # F24, F25, F26
    def test_button_waits_for_a_complete_judgment(self):   # F24 acceptance
        with FakeOllama():
            html = self.page().get_data(as_text=True)
            self.assertIn("Jouw oordeel", html)
            self.assertIn('name="oordeel_niveau_PL"', html)
            self.assertIn('name="oordeel_BD"', html)
            self.assertIn("Vul eerst je eigen oordeel in.", html)
            self.assertRegex(html, r'<button class="button" type="submit"\s+disabled>Advies vragen')
            incomplete = dict(JUDGMENT, oordeel_BD="  ")
            self.assertEqual(self.client.post("/evaluaties/70/advies", data=incomplete).status_code, 400)
            card = self.client.post("/evaluaties/70/advies", data=incomplete,
                                    headers={"X-Requested-With": "fetch"}).get_data(as_text=True)
        self.assertIn("Vul eerst bij elke vaardigheid je eigen niveau en een toelichting in.", card)
        self.assertIn("Plant voor het team.", card)            # what was typed stays
        self.assertIsNone(self.app.extensions["ai_jobs"].status(70))
        self.assertEqual(ai_advice.saved_judgment(self.conn, 70), {})

    def test_judgment_goes_along_and_is_compared(self):   # F25
        answer = {"vaardigheden": [dict(a, verschil=v) for a, v in zip(ANSWER["vaardigheden"][:2],
                                                                        ("Komt overeen.", "Lotte Bakker zit hoger dan jij denkt."))]}
        judgment = dict(JUDGMENT, oordeel_PL="Lotte Bakker plant voor het team.")
        with FakeOllama(answer=answer) as fake:
            self.client.post("/evaluaties/70/advies", data=judgment)
            self.assertEqual(self.wait(self.app.extensions["ai_jobs"])["state"], "done")
            html = self.page().get_data(as_text=True)
        user = fake.calls[0]["user"]
        self.assertIn("Voorlopig oordeel van de beoordelaar", user)
        self.assertIn("- PL (Plannen): niveau 2. Toelichting: Student plant voor het team.", user)
        self.assertNotIn("Lotte Bakker", user)                                         # F3
        self.assertIn("verschil", fake.calls[0]["schema"]["properties"]["vaardigheden"]["items"]["required"])
        self.assertIn("jij: niveau 2", html)
        self.assertIn("advies: niveau 2", html)
        self.assertIn("Vergeleken met jouw oordeel:", html)
        self.assertIn("Lotte Bakker zit hoger dan jij denkt.", html)                   # F23: real name back

    def test_judgment_is_kept_and_reset_clears_it(self):   # F26
        with FakeOllama():
            self.client.post("/evaluaties/70/advies", data=JUDGMENT)
            self.wait(self.app.extensions["ai_jobs"])
            html = self.page().get_data(as_text=True)
        self.assertEqual(ai_advice.saved_judgment(self.conn, 70)["PL"], {"level": 2, "text": "Plant voor het team."})
        self.assertIn(">Plant voor het team.</textarea>", html)
        self.assertRegex(html, r'<option value="2"\s+selected>2</option>')
        self.assertNotRegex(html, r'type="submit"\s+disabled>Opnieuw vragen')
        reset.reset_all(self.app)
        self.assertEqual(ai_advice.saved_judgment(self.conn, 70), {})

    def test_follow_up_carries_the_judgment(self):   # F26
        with FakeOllama() as fake:
            self.client.post("/evaluaties/70/advies", data=JUDGMENT)
            self.wait(self.app.extensions["ai_jobs"])
            self.client.post("/evaluaties/70/advies/vraag", data={"vraag": "Waarom?"})
            self.wait(self.app.extensions["ai_jobs"])
        self.assertIn("Voorlopig oordeel van de beoordelaar", fake.calls[1]["user"])


class TestModelChoice(TestJobsAndPage):   # F14 (2026-11-24), F27, F28
    def two_models(self, fake):
        fake.models = lambda url: [{"name": ollama.DEFAULT_MODEL, "size_gb": 7.2}, {"name": "gemma4:e4b", "size_gb": 9.6}]
        ollama.models = fake.models

    def test_every_model_apart_and_the_chosen_one_is_used(self):   # F14 acceptance
        with FakeOllama() as fake:
            self.two_models(fake)
            calls = []
            original = ollama.chat
            ollama.chat = lambda url, model, *a, **kw: calls.append(model) or original(url, model, *a, **kw)
            html = self.page().get_data(as_text=True)
            self.assertIn(f"Lokaal model · {ollama.DEFAULT_MODEL} (aangeraden)", html)
            self.assertIn("Lokaal model · gemma4:e4b", html)
            self.assertRegex(html, rf'<option value="lokaal:{ollama.DEFAULT_MODEL}"\s+selected>')
            self.client.post("/evaluaties/70/advies", data=dict(JUDGMENT, dienst="lokaal:gemma4:e4b"))
            self.wait(self.app.extensions["ai_jobs"])
            html = self.page().get_data(as_text=True)
        self.assertEqual(calls, ["gemma4:e4b"])
        self.assertEqual(ai_advice.saved(self.conn, 70)["model"], "gemma4:e4b")
        self.assertRegex(html, r'<option value="lokaal:gemma4:e4b"\s+selected>')   # the model of the advice

    def test_a_model_not_in_ollama_is_refused(self):
        with FakeOllama():
            self.assertEqual(self.client.post("/evaluaties/70/advies",
                                              data=dict(JUDGMENT, dienst="lokaal:bestaat:niet")).status_code, 400)

    def test_default_model_in_settings(self):   # F27
        with FakeOllama() as fake:
            self.two_models(fake)
            html = self.client.get("/instellingen").get_data(as_text=True)
            self.assertIn(f"{ollama.DEFAULT_MODEL} (aangeraden)", html)
            self.assertIn("Standaardmodel", html)
            response = self.client.post("/instellingen/ai-advies", data={"model": "gemma4:e4b", "terug": "instellingen"})
            self.assertTrue(response.headers["Location"].endswith("/instellingen?model=ok#ai-advies"))
            self.assertEqual(ai_advice.settings(self.db_path)[1], "gemma4:e4b")
            self.assertIn("✓ Opgeslagen", self.client.get("/instellingen?model=ok").get_data(as_text=True))
        self.assertEqual(self.client.post("/instellingen/ai-advies", data={"model": "a; rm"}).status_code, 400)

    def test_download_tested_or_named_model(self):   # F28 acceptance
        started = []
        pull = self.app.extensions["ollama_pull"]
        with FakeOllama(), mock.patch.object(pull, "start", lambda url, model, log=None: started.append(model) or True):
            html = self.client.get("/instellingen").get_data(as_text=True)
            self.assertIn("Modellen downloaden", html)
            self.assertIn("geïnstalleerd", html)                                  # the recommended one is there
            self.assertIn('<input type="hidden" name="model" value="gemma4:e4b">', html)
            self.assertNotIn(f'<input type="hidden" name="model" value="{ollama.DEFAULT_MODEL}">', html)
            self.client.post("/instellingen/ai-advies/downloaden", data={"model": "gemma4:e4b"},
                             headers={"X-Requested-With": "fetch"})
            self.client.post("/instellingen/ai-advies/downloaden", data={"model": "qwen3.5:9b", "terug": "instellingen"})
            bad = self.client.post("/instellingen/ai-advies/downloaden", data={"model": "geen geldige naam"},
                                   headers={"X-Requested-With": "fetch"}).get_json()
        self.assertEqual(started, ["gemma4:e4b", "qwen3.5:9b"])
        self.assertIn("geen geldige modelnaam", bad["error"])
        self.assertTrue(ollama.valid_name("hf.co/org/model:Q4_K_M"))


class TestLaptopLimits(TestJobsAndPage):   # F29-F32
    def test_defaults_are_as_before(self):
        own = ai_advice.laptop(self.db_path)
        self.assertEqual(own, {"threads": ollama.default_threads(), "context": "veel", "unload": False, "wait": 15})
        options = ai_advice.model_options(self.db_path)
        self.assertEqual((options["num_ctx"], options["budget"], options["keep_alive"]), (32768, 80000, None))

    def test_settings_are_saved_and_sent_along(self):   # F29, F30, F31 acceptance
        with FakeOllama() as fake, mock.patch.object(ollama, "cores", lambda: 8):
            html = self.client.get("/instellingen").get_data(as_text=True)
            self.assertIn("De laptop ontlasten", html)
            self.assertIn('max="8"', html)
            response = self.client.post("/instellingen/ai-advies/laptop", data={"kernen": "2", "materiaal": "weinig", "vrijgeven": "1"})
            self.assertTrue(response.headers["Location"].endswith("/instellingen?laptop=ok#ai-laptop"))
            html = self.client.get("/instellingen?laptop=ok").get_data(as_text=True)
            self.assertIn("2 van 8", html)
            self.assertRegex(html, r'value="weinig"\s+checked')
            self.client.post("/evaluaties/70/advies", data=JUDGMENT)
            self.wait(self.app.extensions["ai_jobs"])
            self.client.post("/evaluaties/70/advies/vraag", data={"vraag": "Waarom?"})
            self.wait(self.app.extensions["ai_jobs"])
            self.client.post("/instellingen/ai-advies/proefvraag")
        for call in fake.calls:
            self.assertEqual(call["options"]["num_thread"], 2)
            self.assertEqual(call["options"]["keep_alive"], 0)
        self.assertEqual(fake.calls[0]["options"]["num_ctx"], 8192)
        self.assertEqual(fake.calls[1]["options"]["num_ctx"], 8192)

    def test_less_material_with_a_smaller_context(self):   # F30, F8
        m = ai_advice.collect(self.conn, self.db_path, "token", 70, ai_advice.date.today())
        _, _, small = ai_advice.prompt(m, {}, budget=len(m["head"]) + len("\n\n".join(m["sections"])) + 2100)
        _, _, large = ai_advice.prompt(m, {}, budget=80000)
        self.assertGreater(small["cut"], large["cut"])

    def test_wrong_values_are_refused(self):   # F29, F30
        with mock.patch.object(ollama, "cores", lambda: 4):
            for data in ({"kernen": "0", "materiaal": "veel"}, {"kernen": "5", "materiaal": "veel"},
                         {"kernen": "x", "materiaal": "veel"}, {"kernen": "2", "materiaal": "alles"}):
                self.assertEqual(self.client.post("/instellingen/ai-advies/laptop", data=data).status_code, 400, data)
        db.set_setting(self.db_path, ollama.S_THREADS, "99")
        db.set_setting(self.db_path, ollama.S_CONTEXT, "raar")
        own = ai_advice.laptop(self.db_path)
        self.assertEqual((own["threads"], own["context"]), (ollama.cores(), "veel"))

    def test_chat_sends_the_options(self):   # F29, F31: what goes to Ollama
        with OllamaServer() as server:
            ollama.chat(server.url, "m", "s", "u", None, num_thread=3, keep_alive=0)
            ollama.chat(server.url, "m", "s", "u", None)
        self.assertEqual(server.bodies[0]["options"]["num_thread"], 3)
        self.assertEqual(server.bodies[0]["keep_alive"], 0)
        self.assertNotIn("num_thread", server.bodies[1]["options"])
        self.assertNotIn("keep_alive", server.bodies[1])


class FakeStream:
    def __init__(self, message):
        self.message = message

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        return iter([object(), object()])

    def get_final_message(self):
        return self.message


def claude_client(text='{"vaardigheden": []}', stop_reason="end_turn", calls=None):
    from types import SimpleNamespace as NS
    message = NS(stop_reason=stop_reason, content=[NS(type="text", text=text)])

    def stream(**kwargs):
        if calls is not None:
            calls.append(kwargs)
        return FakeStream(message)
    return NS(beta=NS(messages=NS(stream=stream)), models=NS(retrieve=lambda model: NS(id=model)))


class TestClaude(AdviceCase):   # F13-F17
    def test_chat_request_and_answer(self):   # F16
        from dashboard import claude_ai
        calls = []
        with mock.patch.object(claude_ai, "_client", lambda key, timeout=600: claude_client(json.dumps(ANSWER), calls=calls)):
            answer = claude_ai.chat("sk-test", "opdracht", "vraag", ai_advice.schema(["PL"]),
                                    images=[{"data": "QUJD", "mime": "image/png"}])
        self.assertEqual(answer, ANSWER)
        sent = calls[0]
        self.assertEqual((sent["model"], sent["output_config"]["effort"], sent["fallbacks"]), ("claude-opus-5-5", "high", "default"))
        self.assertEqual(sent["output_config"]["format"]["type"], "json_schema")
        content = sent["messages"][0]["content"]
        self.assertEqual((content[0]["type"], content[0]["source"]["media_type"], content[-1]["text"]), ("image", "image/png", "vraag"))

    def test_refusal_and_bad_answer(self):   # F16
        from dashboard import claude_ai
        with mock.patch.object(claude_ai, "_client", lambda key, timeout=600: claude_client(stop_reason="refusal")):
            with self.assertRaises(ollama.OllamaError) as error:
                claude_ai.chat("k", "s", "u", {})
        self.assertIn("wilde dit verzoek niet", error.exception.message)
        with mock.patch.object(claude_ai, "_client", lambda key, timeout=600: claude_client(text="geen json")):
            with self.assertRaises(ollama.OllamaError):
                claude_ai.chat("k", "s", "u", {})

    def test_setup_needs_confirmation_and_a_good_key(self):   # F13
        from dashboard import claude_ai
        self.client.post("/instellingen/ai-advies/claude", data={"sleutel": "sk-ant-abc123456789"})
        self.assertIsNone(claude_ai.key(self.db_path))   # no tick: not saved
        with mock.patch.object(claude_ai, "check_key", side_effect=ollama.OllamaError("Anthropic accepteert deze API-sleutel niet.")):
            response = self.client.post("/instellingen/ai-advies/claude", data={"sleutel": "sk-ant-fout", "toegestaan": "1"})
        self.assertIn("accepteert", response.headers["Location"].replace("+", " ").replace("%20", " "))
        self.assertIsNone(claude_ai.key(self.db_path))
        with mock.patch.object(claude_ai, "check_key", lambda key: None):
            self.client.post("/instellingen/ai-advies/claude", data={"sleutel": "sk-ant-abc123456789", "toegestaan": "1"})
        self.assertTrue(claude_ai.ready(self.db_path))
        with FakeOllama():
            html = self.client.get("/instellingen/ai-advies").get_data(as_text=True)
        self.assertIn("sk-ant-…6789", html)
        self.assertNotIn("sk-ant-abc123456789", html)   # F17: never in the browser
        self.assertIn("door de HU zijn goedgekeurd", html)
        self.client.post("/instellingen/ai-advies/claude/verwijderen")
        self.assertIsNone(claude_ai.key(self.db_path))

    def test_key_not_in_backup_but_kept_on_reset(self):   # F17
        from dashboard import claude_ai
        claude_ai.save(self.db_path, "sk-ant-geheim-1234")
        backup = reset.backup(self.db_path)
        import sqlite3
        conn = sqlite3.connect(backup)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM settings WHERE key = ?", (claude_ai.S_KEY,)).fetchone()[0], 0)
        conn.close()
        reset.reset_all(self.app)
        self.assertEqual(claude_ai.key(self.db_path), "sk-ant-geheim-1234")


class TestChoiceAndPrompts(TestJobsAndPage):   # F14, F18, F19
    def test_dropdown_and_advice_with_claude(self):
        from dashboard import claude_ai
        claude_ai.save(self.db_path, "sk-ant-abc123456789")
        calls = []
        with FakeOllama(), mock.patch.object(claude_ai, "chat",
                                             lambda key, system, user, schema, **kw: calls.append((key, system, user)) or ANSWER):
            html = self.page().get_data(as_text=True)
            self.assertIn('<option value="lokaal:', html)
            self.assertIn('<option value="claude"', html)
            self.assertIn("(via internet)", html)
            self.client.post("/evaluaties/70/advies", data=dict(JUDGMENT, dienst="claude"))
            self.assertEqual(self.wait(self.app.extensions["ai_jobs"])["state"], "done")
            html = self.page().get_data(as_text=True)
        self.assertEqual(calls[0][0], "sk-ant-abc123456789")
        self.assertNotIn("Lotte Bakker", calls[0][2])
        self.assertIn("Claude (Anthropic, via internet)", html)
        self.assertEqual(ai_advice.saved(self.conn, 70)["service"], "claude")

    def test_unknown_or_unset_service_is_refused(self):
        with FakeOllama():
            self.assertEqual(self.client.post("/evaluaties/70/advies", data={"dienst": "claude"}).status_code, 400)

    def test_own_instruction_and_addition_per_skill(self):   # F18, F19 acceptance
        self.client.post("/instellingen/ai-advies/opdracht", data={"opdracht": "Mijn eigen opdracht.",
                                                                  "opdracht_PL": "Let op afstemming met de opdrachtgever."})
        self.assertEqual(ai_advice.system_prompt(self.db_path), "Mijn eigen opdracht.")
        sections = ai_advice.collect(self.conn, self.db_path, "token", 70, ai_advice.date.today())["sections"]
        self.assertIn("Let op afstemming met de opdrachtgever.", sections[0])   # PL
        self.assertNotIn("Let op afstemming", sections[1])                     # BD
        with FakeOllama() as fake:
            self.client.post("/evaluaties/70/advies", data=dict(JUDGMENT, dienst="lokaal"))
            self.wait(self.app.extensions["ai_jobs"])
        self.client.post("/instellingen/ai-advies/opdracht", data={"standaard": "1"})
        self.assertEqual(ai_advice.system_prompt(self.db_path), ai_advice.SYSTEM)
        self.assertEqual(ai_advice.skill_prompts(self.db_path), {"PL": "Let op afstemming met de opdrachtgever."})


class TestDurationAndQuestions(TestJobsAndPage):   # F20, F21
    def advice(self, fake):
        self.client.post("/evaluaties/70/advies", data=dict(JUDGMENT, dienst="lokaal"))
        self.assertEqual(self.wait(self.app.extensions["ai_jobs"])["state"], "done")

    def test_duration_is_shown(self):   # F20
        self.assertEqual(ai_advice.duration(45), "45 s")
        self.assertEqual(ai_advice.duration(72), "1 min 12 s")
        with FakeOllama() as fake:
            self.advice(fake)
            html = self.page().get_data(as_text=True)
        self.assertIn("het model deed er 0 s over", html)

    def test_follow_up_question_and_answer_are_kept(self):   # F21 acceptance
        with FakeOllama() as fake:
            self.advice(fake)
            self.client.post("/evaluaties/70/advies/vraag", data={"vraag": "Waarom niet niveau 3 bij PL voor Lotte Bakker?"})
            self.assertEqual(self.wait(self.app.extensions["ai_jobs"])["state"], "done")
            html = self.page().get_data(as_text=True)
        follow_up = fake.calls[-1]
        self.assertIsNone(follow_up["schema"])                                     # free text
        self.assertEqual(follow_up["user"], fake.calls[0]["user"])                 # the same material
        self.assertEqual([m["role"] for m in follow_up["history"]], ["assistant", "user"])
        self.assertIn("Sprintplanning laat afstemming zien.", follow_up["history"][0]["content"])   # the advice
        self.assertIn("Waarom niet niveau 3 bij PL voor Student?", follow_up["history"][1]["content"])   # names replaced
        for text in ("Vragen over dit advies", "Waarom niet niveau 3 bij PL voor Lotte Bakker?",
                     "Omdat de afstemming met de opdrachtgever ontbreekt.", "Vraag stellen"):
            self.assertIn(text, html)
        turns = ai_advice.saved(self.conn, 70)["conversation"]
        self.assertEqual(len(turns), 1)
        with FakeOllama() as fake:   # a second question carries the first one along
            self.client.post("/evaluaties/70/advies/vraag", data={"vraag": "En bij BD?"})
            self.wait(self.app.extensions["ai_jobs"])
        self.assertEqual([m["role"] for m in fake.calls[-1]["history"]], ["assistant", "user", "assistant", "user"])

    def test_new_advice_clears_the_conversation(self):   # F21
        with FakeOllama() as fake:
            self.advice(fake)
            self.client.post("/evaluaties/70/advies/vraag", data={"vraag": "Waarom?"})
            self.wait(self.app.extensions["ai_jobs"])
            self.advice(fake)
        self.assertEqual(ai_advice.saved(self.conn, 70)["conversation"], [])

    def test_no_question_without_advice(self):
        self.assertEqual(self.client.post("/evaluaties/70/advies/vraag", data={"vraag": "x"}).status_code, 404)


class TestClaudeVisibility(AdviceCase):   # F22: Claude only for the allowed Portflow user
    def setUp(self):
        super().setUp()
        from dashboard import claude_ai
        from dashboard.progress import name_key
        patcher = mock.patch.object(claude_ai, "ALLOWED_USERS", {name_key("Peter Snoek")})
        patcher.start(); self.addCleanup(patcher.stop)
        claude_ai.save(self.db_path, "sk-ant-abc123456789")

    def test_hidden_for_other_users(self):
        from dashboard import ai_advice, claude_ai
        with FakeOllama():   # so the local model is deterministically available (CI has no Ollama)
            self.assertEqual([s["key"] for s in ai_advice.available(self.db_path, "Kees de Wit")], [f"lokaal:{ollama.DEFAULT_MODEL}"])
            self.assertEqual([s["key"] for s in ai_advice.available(self.db_path, "Peter Snoek")], [f"lokaal:{ollama.DEFAULT_MODEL}", "claude"])
        self.assertFalse(claude_ai.allowed("Kees de Wit"))
        self.assertTrue(claude_ai.allowed("peter  snoek"))   # case/space-insensitive

    def test_setup_page_and_routes_blocked_for_others(self):
        with FakeOllama():
            html = self.client.get("/instellingen/ai-advies").get_data(as_text=True)   # logged in as Kees
        self.assertNotIn("Claude (via internet)", html)
        self.assertEqual(self.client.post("/instellingen/ai-advies/claude", data={"sleutel": "sk-x", "toegestaan": "1"}).status_code, 403)
        self.assertEqual(self.client.post("/evaluaties/70/advies", data={"dienst": "claude"}).status_code, 400)

    def test_shown_for_the_allowed_user(self):
        with self.conn:
            self.conn.execute("UPDATE settings SET value = 'Peter Snoek' WHERE key = 'portflow_user_name'")
        with FakeOllama():
            html = self.client.get("/instellingen/ai-advies").get_data(as_text=True)
        self.assertIn("Claude (via internet)", html)


class TestRestoreNames(TestJobsAndPage):   # F23: remember the replacement and undo it in the output
    def test_real_names_in_advice_but_placeholders_to_the_ai(self):
        advice = {"vaardigheden": [
            {"code": "PL", "niveau": 2, "onderbouwing": "Student plant goed; Coach 1 bevestigt dit. De student groeit.",
             "ontbreekt": "Student kan meer met Coach 1 afstemmen."},
            {"code": "BD", "niveau": 1, "onderbouwing": "x", "ontbreekt": "y"}]}
        with FakeOllama(answer=advice) as fake:
            self.client.post("/evaluaties/70/advies", data=dict(JUDGMENT, dienst="lokaal"))
            self.assertEqual(self.wait(self.app.extensions["ai_jobs"])["state"], "done")
            html = self.page().get_data(as_text=True)
        # What went to the AI used placeholders (no real names).
        self.assertNotIn("Lotte Bakker", fake.calls[0]["user"])
        # What is shown has the real names back; "de student" (generic) stays.
        shown = ai_advice.saved(self.conn, 70)
        pl = shown["skills"][0]
        self.assertIn("Lotte Bakker plant goed; Noor Smit bevestigt", pl["reasoning"])
        self.assertIn("De student groeit", pl["reasoning"])              # generic lowercase kept
        self.assertIn("Lotte Bakker kan meer met Noor Smit", pl["missing"])
        self.assertIn("Lotte Bakker plant goed", html)
        # The stored advice itself stays anonymized (it is sent back to the AI on a follow-up).
        self.assertIn("Student plant goed", self.conn.execute(
            "SELECT advice FROM ai_advice WHERE review_request_id = 70").fetchone()["advice"])

    def test_follow_up_answer_restored_without_leaking_to_the_ai(self):
        advice = {"vaardigheden": [{"code": "PL", "niveau": 2, "onderbouwing": "Student plant.", "ontbreekt": "-"},
                                   {"code": "BD", "niveau": 1, "onderbouwing": "x", "ontbreekt": "y"}]}
        answer = "Student kan bij Coach 1 navragen hoe de planning overkwam."
        with FakeOllama(answer=advice) as fake:
            self.client.post("/evaluaties/70/advies", data=dict(JUDGMENT, dienst="lokaal"))
            self.wait(self.app.extensions["ai_jobs"])
        with FakeOllama(answer=advice, delay=0) as fake:
            fake.answer = advice  # advice path returns dict; the follow-up asks for free text
            import dashboard.ollama as ollama_mod
            with mock.patch.object(ollama_mod, "chat", lambda *a, **k: answer):
                self.client.post("/evaluaties/70/advies/vraag", data={"vraag": "Wat kan Lotte Bakker nog doen?"})
                self.assertEqual(self.wait(self.app.extensions["ai_jobs"])["state"], "done")
            html = self.page().get_data(as_text=True)
        # Shown: real names restored in the answer; the typed question keeps its real name.
        self.assertIn("Lotte Bakker kan bij Noor Smit navragen", html)
        self.assertIn("Wat kan Lotte Bakker nog doen?", html)
        # Stored for the AI history: anonymized question and answer (no real names).
        turn = json.loads(self.conn.execute("SELECT conversation FROM ai_advice WHERE review_request_id = 70").fetchone()["conversation"])[0]
        self.assertEqual(turn["answer"], answer)                         # as the AI returned it (placeholders)
        self.assertNotIn("Lotte Bakker", turn["question_anon"])
        self.assertIn("Student", turn["question_anon"])


class TestWaitAndProgress(TestJobsAndPage):   # F33, F34, F35
    def test_silence_longer_than_the_waiting_time(self):   # F33 acceptance
        with OllamaServer(delay=1.5) as server, self.assertRaises(ollama.OllamaError) as error:
            ollama.chat(server.url, "m", "s", "u", None, timeout=0.5)
        self.assertIn("geen teken van leven", error.exception.message)
        self.assertIn("timed out", error.exception.detail)
        with OllamaServer(chunks=("eerst", "dan"), gap=1.5) as server, self.assertRaises(ollama.OllamaError) as error:
            ollama.chat(server.url, "m", "s", "u", None, timeout=0.5)        # silent after the first words
        self.assertIn("geen teken van leven", error.exception.message)

    def test_stop_while_the_model_is_silent(self):   # F4 with F33
        cancel = threading.Event()
        threading.Timer(0.3, cancel.set).start()
        started = time.monotonic()
        with OllamaServer(delay=5) as server, self.assertRaises(ollama.OllamaError) as error:
            ollama.chat(server.url, "m", "s", "u", None, timeout=60, cancel=cancel)
        self.assertEqual(error.exception.message, "Gestopt.")
        self.assertLess(time.monotonic() - started, 3)

    def test_stop_while_silent_also_when_closing_does_not_wake_the_read(self):   # F4 on Windows
        import socket
        cancel = threading.Event()
        threading.Timer(0.3, cancel.set).start()
        started = time.monotonic()
        with mock.patch.object(socket.socket, "shutdown", lambda self, how: None), \
                OllamaServer(delay=4) as server, self.assertRaises(ollama.OllamaError) as error:
            ollama.chat(server.url, "m", "s", "u", None, timeout=60, cancel=cancel)
        self.assertEqual(error.exception.message, "Gestopt.")
        self.assertLess(time.monotonic() - started, 3)

    def test_progress_gets_the_text_so_far(self):   # F34, F35
        seen = []
        with OllamaServer(chunks=("Omdat ", "de afstemming")) as server:
            answer = ollama.chat(server.url, "m", "s", "u", None, progress=seen.append)
        self.assertEqual(seen, ["Omdat ", "Omdat de afstemming", "Omdat de afstemming"])
        self.assertEqual(answer, "Omdat de afstemming")

    def test_waiting_time_setting(self):   # F33
        with FakeOllama() as fake, mock.patch.object(ollama, "cores", lambda: 8):
            html = self.client.get("/instellingen").get_data(as_text=True)
            self.assertIn("Maximaal wachten op een teken van leven van het model", html)
            self.assertIn('name="wachten" min="5" max="60" value="15"', html)
            self.client.post("/instellingen/ai-advies/laptop", data={"kernen": "2", "materiaal": "veel", "wachten": "30"})
            self.client.post("/instellingen/ai-advies/proefvraag")
            self.client.post("/evaluaties/70/advies", data=JUDGMENT)
            self.wait(self.app.extensions["ai_jobs"])
        self.assertEqual(ai_advice.laptop(self.db_path)["wait"], 30)
        self.assertEqual([c["options"]["timeout"] for c in fake.calls], [1800, 1800])
        for wrong in ("4", "61", "x"):
            with mock.patch.object(ollama, "cores", lambda: 8):
                self.assertEqual(self.client.post("/instellingen/ai-advies/laptop",
                                                  data={"kernen": "2", "materiaal": "veel", "wachten": wrong}).status_code, 400)

    def test_progress_view_per_phase(self):   # F34, F35
        now = 1000.0
        collect = ai_advice.progress_view({"phase": "collect", "started_at": now - 5, "collect_done": 3, "collect_total": 19,
                                           "step": "Bewijsstukken lezen (3 van 19)"}, now)
        self.assertEqual((collect["label"], collect["detail"]), ("Materiaal verzamelen", "Bewijsstukken lezen (3 van 19)"))
        read_early = ai_advice.progress_view({"phase": "read", "started_at": now - 20, "phase_at": now - 10, "timeout": 900}, now)
        read_late = ai_advice.progress_view({"phase": "read", "started_at": now - 200, "phase_at": now - 190, "timeout": 900}, now)
        self.assertEqual(read_early["label"], "Het model leest het materiaal")
        self.assertIn("bezig sinds 10 s; het dashboard wacht hoogstens 15 min op een teken van leven", read_early["detail"])
        self.assertLess(collect["percent"], read_early["percent"])
        self.assertLess(read_early["percent"], read_late["percent"])
        self.assertLessEqual(read_late["percent"], 40)
        raw = '{"vaardigheden":[{"code":"PL","niveau":2,"onderbouwing":"Student plant voor het team.","ontbreekt":"Meer'
        write = ai_advice.progress_view({"phase": "write", "started_at": now - 300, "phase_at": now - 30, "last_at": now - 1,
                                         "chars": len(raw), "raw": raw, "expected_chars": 3600,
                                         "names": {"Lotte Bakker": "Student"}}, now)
        self.assertEqual(write["label"], "Advies schrijven")
        self.assertIn("tekens geschreven, schrijft nu", write["detail"])
        self.assertIn("Lotte Bakker plant voor het team.", write["preview"])   # F23: the real name back
        self.assertIn("Nog te laten zien: Meer", write["preview"])
        self.assertNotIn('"onderbouwing"', write["preview"])
        self.assertGreater(write["percent"], read_late["percent"])
        done = ai_advice.progress_view({"phase": "write", "chars": 99999, "expected_chars": 10, "last_at": now}, now)
        self.assertEqual(done["percent"], 98)                                   # never full before it is done

    def test_card_shows_the_progress(self):   # F34 acceptance
        with FakeOllama(delay=5):
            jobs = self.app.extensions["ai_jobs"]
            self.client.post("/evaluaties/70/advies", data=JUDGMENT)
            for _ in range(300):
                if (jobs.status(70) or {}).get("phase") == "read":
                    break
                time.sleep(0.01)
            card = self.client.get("/evaluaties/70/advies").get_data(as_text=True)
            jobs.stop(70)
            self.wait(jobs)
        self.assertIn("<progress", card)
        self.assertIn("Het model leest het materiaal", card)
        self.assertIn("een schatting", card)
        self.assertIn("Stoppen", card)


def big_material(skills=("PL", "BD", "SW", "RE"), images=6, content_chars=30000, earlier=4, feedback=6, text_chars=1500):
    """Invented material that is too large for "Normaal" (16,384 tokens)."""
    parts = []
    for code in skills:
        parts.append({"core": [f"## Vaardigheid {code}", "LEF-teksten (de maatstaf):\n" + "L" * 3000],
                      "earlier": [{"full": f"- niveau 1 op dag {i} door Joost Visser (coach): " + "E" * text_chars,
                                   "short": f"- niveau 1 op dag {i} door Joost Visser (coach): (tekst weggelaten)"}
                                  for i in range(earlier)],
                      "evidence": "Bewijsstukken bij deze vaardigheid: geen.",
                      "feedback": [{"full": f"- Opmerking {i} van Noor Smit (medestudent): " + "F" * text_chars,
                                    "short": f"- Opmerking {i} van Noor Smit (medestudent): (tekst weggelaten)"}
                                   for i in range(feedback)]})
    pics = [{"name": f"Bord – foto{i}.png", "mime": "image/png", "data": "QUJD",
             "placeholder": f"[afbeelding foto{i}.png: meegestuurd als afbeelding {i + 1}]",
             "dropped": f"[afbeelding foto{i}.png: niet meegestuurd, te weinig ruimte]"} for i in range(images)]
    contents = [{"name": "Sprintplanning", "skills": list(skills),
                 "text": " ".join(p["placeholder"] for p in pics) + "\n" + "C" * content_chars}]
    return {"codes": list(skills), "student": "Lotte Bakker", "head": "Evaluatieverzoek", "parts": parts,
            "sections": [ai_advice._section(p, set()) for p in parts], "contents": contents, "images": pics,
            "names_only": [], "counts": {"skills": len(skills)}}


class TestFitsTheModel(unittest.TestCase):   # F36-F39
    def fits(self, text, images, max_tokens, skills=4, system=len(ai_advice.SYSTEM)):
        answer = ai_advice.ANSWER_TOKENS + ai_advice.ANSWER_TOKENS_PER_SKILL * skills
        return ai_advice.estimated_tokens(text, images, system) + answer <= max_tokens

    def test_normaal_fits_by_leaving_out_images_first(self):   # F36 acceptance
        m = big_material()
        text, images, counts = ai_advice.prompt(m, {}, max_tokens=16384, system_chars=len(ai_advice.SYSTEM))
        self.assertTrue(self.fits(text, images, 16384))
        self.assertGreater(counts["images_dropped"], 0)
        self.assertEqual(counts["images"], len(images))
        self.assertIn("niet meegestuurd, te weinig ruimte", text)              # the placeholder says so
        self.assertIn("LEF-teksten (de maatstaf)", text)                        # never shortened

    def test_images_go_before_the_contents(self):   # F36 order
        m = big_material(images=6, content_chars=12000, earlier=0, feedback=0, text_chars=10)
        text, images, counts = ai_advice.prompt(m, {}, max_tokens=12000, system_chars=0)
        self.assertGreater(counts["images_dropped"], 0)
        self.assertEqual(counts["cut"], 0)
        self.assertNotIn("[…ingekort]", text)                                   # the contents are complete
        self.assertEqual(counts["shortened"], 0)

    def test_oldest_feedback_and_earlier_texts_are_shortened_last(self):   # F36 step 3
        m = big_material(images=2, content_chars=1000, earlier=4, feedback=6, text_chars=3000)
        text, images, counts = ai_advice.prompt(m, {}, max_tokens=16384, system_chars=len(ai_advice.SYSTEM))
        self.assertTrue(self.fits(text, images, 16384))
        self.assertEqual(images, [])                                             # images first
        self.assertGreater(counts["shortened"], 0)
        self.assertIn("Opmerking 5 van Noor Smit (medestudent): (tekst weggelaten)", text)   # the oldest
        self.assertIn("Opmerking 0 van Noor Smit (medestudent): " + "F" * 50, text)          # the newest kept
        self.assertEqual(text.count("L" * 3000), 4)                              # LEF texts complete

    def test_without_max_tokens_as_before(self):   # Claude: F8 only
        m = big_material()
        text, images, counts = ai_advice.prompt(m, {})
        self.assertEqual(len(images), 6)
        self.assertEqual((counts["images_dropped"], counts["shortened"]), (0, 0))

    def test_reading_the_message_of_ollama(self):   # F37
        error = ollama.OllamaError("Ollama gaf een fout (400): request (20950 tokens) exceeds the available context "
                                   "size (16384 tokens), try increasing it.", "HTTP 400 op /api/chat")
        self.assertEqual(ai_advice.too_large(error), (20950, 16384))
        self.assertIsNone(ai_advice.too_large(ollama.OllamaError("Ollama is niet bereikbaar.")))
        self.assertIn("instelling Normaal", ai_advice.too_large_message({"num_ctx": 16384}))
        self.assertIn("Kies Veel", ai_advice.too_large_message({"num_ctx": 16384}))
        self.assertNotIn("Kies Veel", ai_advice.too_large_message({"num_ctx": 32768}))

    def test_claude_too_long(self):   # F38 for Claude
        from dashboard import claude_ai
        error = claude_ai._sdk().BadRequestError.__new__(claude_ai._sdk().BadRequestError)
        error.args = ("prompt is too long: 250000 tokens > 200000 maximum",)
        self.assertIn("te groot voor Claude", claude_ai._message(error))


class TestRetryWithLess(TestJobsAndPage):   # F37, F38
    TOO_LARGE = "Ollama gaf een fout (400): request (20950 tokens) exceeds the available context size (16384 tokens)."

    def test_once_more_with_less(self):   # F37
        with FakeOllama() as fake:
            original = ollama.chat
            calls = []

            def chat(url, model, system, user, schema, **kwargs):
                calls.append(len(user))
                if len(calls) == 1:
                    raise ollama.OllamaError(self.TOO_LARGE, "HTTP 400 op /api/chat")
                return original(url, model, system, user, schema, **kwargs)
            ollama.chat = chat
            self.client.post("/evaluaties/70/advies", data=JUDGMENT)
            status = self.wait(self.app.extensions["ai_jobs"])
        self.assertEqual(status["state"], "done")
        self.assertEqual(len(calls), 2)
        self.assertLessEqual(calls[1], calls[0])
        lines = " ".join(r["text"] for r in ai_log.recent(self.conn))
        self.assertIn("te veel materiaal voor het model (20950 van 16384 tokens); opnieuw met minder", lines)

    def test_still_too_large_gives_a_clear_message(self):   # F38
        with FakeOllama():
            def chat(*args, **kwargs):
                raise ollama.OllamaError(self.TOO_LARGE, "HTTP 400 op /api/chat")
            ollama.chat = chat
            self.client.post("/evaluaties/70/advies", data=JUDGMENT)
            status = self.wait(self.app.extensions["ai_jobs"])
            html = self.client.get("/evaluaties/70/advies").get_data(as_text=True)
        self.assertEqual(status["state"], "error")
        self.assertIn("past niet bij de instelling Veel", status["error"])
        self.assertIn("past niet bij de instelling Veel", html)
        self.assertNotIn("exceeds the available context", html)

    def test_overview_says_what_was_left_out(self):   # F39
        ai_advice.save(self.db_path, 70, "m", [], {"skills": 2, "evidence": 1, "files": 0, "earlier": 0, "feedback": 0,
                                                 "cut": 0, "names_only": [], "images_dropped": 3, "shortened": 2})
        with FakeOllama():
            html = self.page().get_data(as_text=True)
        self.assertIn("gingen 3 afbeeldingen niet mee", html)
        self.assertIn("gingen 2 eerdere beoordeling(en) of feedbackbericht(en) mee zonder tekst", html)
