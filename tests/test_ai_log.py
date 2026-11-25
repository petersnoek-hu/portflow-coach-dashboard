"""Tests for spec 042: the log of the AI advice. A fake Ollama; invented names and data."""
import time
import unittest
from unittest import mock

from dashboard import ai_advice, ai_log, db, ollama, reset
from dashboard.version import VERSION
from tests.test_ai_advice import ANSWER, JUDGMENT, FakeOllama, TestJobsAndPage


class TestAiLog(TestJobsAndPage):
    def lines(self):
        return ai_log.recent(self.conn)

    def all_text(self):
        return " ".join(r["text"] + " " + r["detail"] for r in self.lines())

    def test_check_of_ollama_off_then_on(self):   # F1 acceptance
        with FakeOllama(running=False):
            self.client.get("/instellingen")
        first = self.lines()[0]
        self.assertEqual((first["topic"], first["ok"]), ("Ollama", False))
        self.assertIn("http://127.0.0.1:11434", first["text"])
        self.assertIn("niet bereikbaar", first["text"])
        with FakeOllama():
            self.client.get("/instellingen/ai-advies")   # "Controleren" reloads the wizard
        newest = self.lines()[0]
        self.assertTrue(newest["ok"])
        self.assertIn("Ollama 0.34.2", newest["text"])
        self.assertIn(f"standaardmodel {ollama.DEFAULT_MODEL} staat erin", newest["text"])

    def test_same_check_is_counted_not_repeated(self):   # F1: no line per page view
        with FakeOllama():
            for _ in range(3):
                self.client.get("/instellingen")
        self.assertEqual(len(self.lines()), 1)
        self.assertEqual(self.lines()[0]["times"], 3)

    def test_technical_reason(self):   # F2
        with self.assertRaises(ollama.OllamaError) as error:
            ollama.version("http://127.0.0.1:9")
        self.assertIn("ConnectionRefusedError", error.exception.detail)
        self.assertEqual(ollama._reason(TimeoutError("timed out"), 5), "timed out na 5 s")

    def test_advice_and_question_are_logged_without_names(self):   # F1, F6 acceptance
        with FakeOllama():
            self.client.post("/evaluaties/70/advies", data=JUDGMENT)
            self.wait(self.app.extensions["ai_jobs"])
            self.client.post("/evaluaties/70/advies/vraag", data={"vraag": "Waarom niet hoger voor Lotte Bakker?"})
            self.wait(self.app.extensions["ai_jobs"])
            self.client.get("/instellingen")
        advice = next(r for r in self.lines() if r["topic"] == "Advies")
        self.assertTrue(advice["ok"])
        self.assertIn("Verzoek 70", advice["text"])
        self.assertIn(ollama.DEFAULT_MODEL, advice["text"])
        self.assertIn("2 vaardigheden", advice["text"])
        self.assertIn("kernen", advice["text"])
        self.assertTrue(any(r["topic"] == "Vervolgvraag" and r["ok"] for r in self.lines()))
        text = self.all_text()
        for secret in ("Lotte", "Bakker", "Noor Smit", "Kees de Wit", "PL & BD", "Plant voor het team", "Sprintplanning"):
            self.assertNotIn(secret, text)

    def test_failed_and_stopped_advice(self):   # F1, F2
        with FakeOllama(answer={"iets": "anders"}):
            self.app.extensions["ai_jobs"].start(70)
            self.wait(self.app.extensions["ai_jobs"])
        line = self.lines()[0]
        self.assertFalse(line["ok"])
        self.assertIn("mislukt bij het controleren van het antwoord", line["text"])
        self.assertIn("geen bruikbaar advies", line["text"])
        with FakeOllama(delay=5):
            jobs = self.app.extensions["ai_jobs"]
            jobs.start(70)
            for _ in range(300):
                if (jobs.status(70) or {}).get("step", "").startswith("Advies schrijven"):
                    break
                time.sleep(0.01)
            jobs.stop(70)
            self.wait(jobs)
        self.assertIn("gestopt door de gebruiker", self.lines()[0]["text"])

    def test_trial_download_and_settings(self):   # F1
        with FakeOllama(answer={"vaardigheden": [{"code": "PL", "niveau": 1, "onderbouwing": "x", "ontbreekt": "y"}]}):
            self.client.post("/instellingen/ai-advies/proefvraag")
        self.assertIn("Proefvraag aan", self.lines()[0]["text"])
        self.client.post("/instellingen/ai-advies", data={"model": "gemma4:e4b", "terug": "instellingen"})
        self.assertEqual(self.lines()[0]["text"], "Standaardmodel is nu gemma4:e4b")
        with mock.patch.object(ollama, "cores", lambda: 8):
            self.client.post("/instellingen/ai-advies/laptop", data={"kernen": "3", "materiaal": "normaal"})
        self.assertIn("3 van 8 kernen, materiaal normaal", self.lines()[0]["text"])
        done = []
        pull = ollama.Pull()
        pull.start("http://127.0.0.1:9", "gemma4:e4b", lambda ok, text, detail="": done.append((ok, text, detail)))
        for _ in range(300):
            if done:
                break
            time.sleep(0.01)
        self.assertFalse(done[0][0])
        self.assertIn("Downloaden van gemma4:e4b mislukt", done[0][1])
        self.assertIn("ConnectionRefusedError", done[0][2])

    def test_shown_copied_and_cleared(self):   # F3, F4, F5
        with FakeOllama(running=False):
            html = self.client.get("/instellingen").get_data(as_text=True)
            wizard = self.client.get("/instellingen/ai-advies").get_data(as_text=True)
        self.assertIn('<details class="ai-log" id="ai-logboek" open>', html)   # open after a failure
        self.assertIn("Wat de app deed", wizard)
        self.assertIn("Kopiëren", html)
        self.assertIn(f"Portflow coach dashboard {VERSION}", html)              # the text to copy
        self.assertIn("Ollama: niet bereikbaar", html)
        self.client.post("/instellingen/ai-advies/logboek/leegmaken")
        self.assertEqual(self.lines(), [])
        ai_log.add(self.db_path, "Instellingen", True, "x")
        reset.reset_all(self.app)
        self.assertEqual(self.lines(), [])

    def test_keeps_the_last_lines_and_never_raises(self):   # F5, technical
        with mock.patch.object(ai_log, "KEEP", 5):
            for i in range(8):
                ai_log.add(self.db_path, "Instellingen", True, f"regel {i}")
        self.assertEqual([r["text"] for r in self.lines()], [f"regel {i}" for i in (7, 6, 5, 4, 3)])
        ai_log.add(self.db_path, "Advies", False, "x" * 1000)
        self.assertEqual(len(self.lines()[0]["text"]), ai_log.MAX_TEXT)
        ai_log.add("/bestaat/niet/db.sqlite3", "Advies", True, "x")   # no exception


if __name__ == "__main__":
    unittest.main()
