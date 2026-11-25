"""Tests for spec 035: feedback requests and replies on evidence. A fake Portflow; invented data."""

import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

from dashboard import create_app, evidence, feedback, hide_names, overview, portflow_api

START, END = date(2026, 9, 1), date(2027, 1, 31)
NOW = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)


def comment(cid, day, author, author_id, role="student", kind="feedback_request", children=0, text="<p>Wat vind je?</p>"):
    return {"id": cid, "comment_type": kind, "text": text, "created_at": f"{day}T10:00:00Z", "created_by_role": role,
            "created_by": {"id": author_id, "name": author}, "child_count": children, "parent_id": None}


class FakeApi:
    def __init__(self):
        self.calls = []

    def collections(self, token, portfolio_id):
        return 200, [{"id": 1, "name": "Semester 3"}]

    def collection_evidence(self, token, portfolio_id, collection_id):
        return 200, [
            {"evidence": {"id": 10, "name": "Sprintverslag", "latest_version_type": "file",
                          "created_at": "2026-10-01T09:00:00Z", "latest_version_created_at": "2026-10-01T09:00:00Z",
                          "goals": [{"name": "Plannen"}]}},
            {"evidence": {"id": 11, "name": "Oud werk", "latest_version_type": "file",
                          "created_at": "2026-05-01T09:00:00Z", "latest_version_created_at": "2026-05-01T09:00:00Z",
                          "goals": []}}]

    def evidence_comments(self, token, portfolio_id, evidence_id):
        self.calls.append(("comments", evidence_id))
        if evidence_id != 10:
            return 200, []
        return 200, [comment(100, "2026-10-02", "Lotte Bakker", 11, children=3),
                     comment(101, "2026-10-09", "Lotte Bakker", 11),   # not answered yet
                     comment(102, "2026-10-03", "Joost Visser", 50, role="coach", kind="comment")]

    def comment_children(self, token, portfolio_id, comment_id):
        self.calls.append(("children", comment_id))
        return 200, [comment(200, "2026-10-04", "Noor Smit", 21, kind="comment", text="Goed<br>bezig"),
                     comment(201, "2026-10-06", "Joost Visser", 50, role="coach", kind="comment"),
                     comment(202, "2026-10-06", "Lotte Bakker", 11, kind="comment", text="Dank je")]


class FeedbackCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        overview.save_semester_period(self.conn, START.isoformat(), END.isoformat())
        with self.conn:
            self.conn.execute("INSERT INTO students (id, name, semester, portflow_user_id) VALUES (1, 'Lotte Bakker', 3, 11)")
            self.conn.execute("INSERT INTO student_portfolios (student_id, portfolio_id) VALUES (1, 101)")
            self.conn.execute("INSERT INTO staff (name, is_coach, is_guild_master) VALUES ('Joost Visser', 0, 1)")
        self.api = FakeApi()
        evidence.fetch_for_student(self.conn, 1, "token", api=self.api, now=lambda: NOW, period=(START, END))

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()


class TestFetch(FeedbackCase):   # F1
    def test_only_evidence_in_the_period_and_replies_once(self):
        self.assertIn(("comments", 10), self.api.calls)
        self.assertNotIn(("comments", 11), self.api.calls)   # added and updated before the period
        self.assertEqual([c for c in self.api.calls if c[0] == "children"], [("children", 100)])
        stored = self.conn.execute("SELECT COUNT(*) FROM evidence_comments WHERE parent_id = 100").fetchone()[0]
        self.assertEqual(stored, 3)

    def test_pages_stop_when_portflow_repeats_a_page(self):   # the endpoints ignore `page`
        with mock.patch.object(portflow_api, "_get_json_with_retry", return_value=(200, [{"id": 1}, {"id": 2}])) as get:
            status, items = portflow_api.comment_children("token", 101, 100)
        self.assertEqual((status, [i["id"] for i in items]), (200, [1, 2]))
        self.assertEqual(get.call_count, 2)


class TestSummary(FeedbackCase):   # F2
    def test_key_figures(self):
        stats = feedback.summary(self.conn, 1, START, END)
        # two requests, one answered; replies by the student himself do not count
        self.assertEqual((stats["requests"], stats["answered"], stats["replies"], stats["people"]), (2, 1, 2, 2))
        self.assertEqual(stats["first_reply_days"], 2)
        html = self.client.get("/studenten/1").get_data(as_text=True)
        self.assertRegex(html, r"<strong>2</strong> feedbackvragen\s*· <strong>1</strong> beantwoord")


class TestRows(FeedbackCase):   # F3
    def test_requests_and_replies_by_role(self):
        requests, replies = feedback.rows(self.conn, 1, START, END)
        self.assertEqual([(m["kind"], m["ids"]) for m in requests["marks"]], [("answered", "100"), ("open", "101")])
        # spec 043, F3: the remark of the guild master (102, 3 Oct) is in the row Reactie too
        self.assertEqual([(m["count"], m["kind"], m["ids"]) for m in replies["marks"]],
                         [(1, "gildemeester", "102"), (1, "medestudent", "100"), (2, "gemengd", "100")])
        self.assertIn("Opmerking van Joost Visser (gildemeester) bij Sprintverslag", replies["marks"][0]["tip"])
        self.assertIn("Feedbackvraag bij Sprintverslag · 2 reacties", requests["marks"][0]["tip"])
        html = self.client.get("/studenten/1").get_data(as_text=True)
        self.assertIn('href="/studenten/1/feedback?vragen=100" data-feedback', html)

    def test_roles(self):
        staff = {"joost visser": "gildemeester"}
        self.assertEqual(feedback.role_of({"author_id": 11, "author_name": "Lotte Bakker", "author_role": "student"}, 11, staff), "zelf")
        self.assertEqual(feedback.role_of({"author_id": 50, "author_name": "Joost Visser", "author_role": "coach"}, 11, staff), "gildemeester")
        self.assertEqual(feedback.role_of({"author_id": 21, "author_name": "Noor Smit", "author_role": "student"}, 11, staff), "medestudent")
        self.assertEqual(feedback.role_of({"author_id": 22, "author_name": "X", "author_role": "teacher"}, 11, staff), "coach")


class TestPanel(FeedbackCase):   # F4, F5
    def test_conversation_in_order(self):
        html = self.client.get("/studenten/1/feedback?vragen=100", headers={"X-Requested-With": "fetch"}).get_data(as_text=True)
        self.assertIn("Sprintverslag", html)
        self.assertIn("Wat vind je?", html)
        self.assertLess(html.index("Noor Smit"), html.index("Joost Visser"))
        self.assertIn("Goed\nbezig", html)
        self.assertIn("gildemeester", html)
        self.assertNotIn("<html", html)   # a fragment for the panel
        page = self.client.get("/studenten/1/feedback?vragen=101").get_data(as_text=True)
        self.assertIn("Nog geen reacties.", page)
        self.assertIn("Terug naar de student", page)

    def test_names_of_responders_are_hidden_too(self):   # F5
        self.client.post("/namen-verbergen", data={"aan": "1"})
        html = self.client.get("/studenten/1/feedback?vragen=100").get_data(as_text=True)
        self.assertNotIn("Noor Smit", html)
        self.assertNotIn("Lotte Bakker", html)
        self.assertIn("Joost Visser", html)   # staff stays visible
        self.assertIn("Student 2", html)


class TestEmpty(unittest.TestCase):   # F6
    def test_no_requests(self):
        with tempfile.TemporaryDirectory() as folder:
            app = create_app(str(Path(folder) / "t.sqlite3"))
            conn = sqlite3.connect(str(Path(folder) / "t.sqlite3"))
            with conn:
                conn.execute("INSERT INTO students (id, name) VALUES (1, 'Lotte Bakker')")
                conn.execute("INSERT INTO evidence_fetches (student_id, fetched_at, collections) VALUES (1, '2026-11-18T10:00:00+00:00', 1)")
            conn.close()
            html = app.test_client().get("/studenten/1").get_data(as_text=True)
            self.assertIn("Nog geen feedbackvragen in deze semesterperiode.", html)


if __name__ == "__main__":
    unittest.main()


class TestRemarks(FeedbackCase):   # spec 043
    def add(self, cid, day, author, author_id, role, version=None, parent=None, evidence_id=10, kind="comment"):
        with self.conn:
            self.conn.execute(
                "INSERT INTO evidence_comments (comment_id, student_id, evidence_id, parent_id, kind, text, created_at, "
                "author_id, author_name, author_role, version) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (cid, evidence_id, parent, kind, f"<p>Bericht {cid}</p>", f"{day}T10:00:00Z", author_id, author, role, version))

    def test_version_and_hidden_when_fetched(self):   # F1, open question 3
        raw = comment(300, "2026-10-01", "Joost Visser", 50, role="coach", kind="comment")
        stored = evidence._comment(dict(raw, evidence_version={"evidence_id": 10, "version_number": 2}), 10, None)
        self.assertEqual(stored["version"], 2)
        reply = evidence._comment(comment(301, "2026-10-02", "Noor Smit", 21, kind="comment"), 10, 300, stored["version"])
        self.assertEqual(reply["version"], 2)                                    # a reply takes the version of its parent
        self.assertIsNone(evidence._comment(dict(raw, hidden=True), 10, None))  # hidden: not kept
        columns = [r[1] for r in self.conn.execute("PRAGMA table_info(evidence_comments)")]
        self.assertIn("version", columns)

    def test_side_panel_shows_every_remark_with_version(self):   # F2 acceptance
        with self.conn:
            self.conn.execute("DELETE FROM evidence_comments")
        self.add(400, "2026-08-21", "Joost Visser", 50, "coach", version=1)    # before the period: still shown here
        self.add(401, "2026-09-25", "Lotte Bakker", 11, "student", version=2)
        html = self.client.get("/studenten/1/bewijsstuk?ids=10").get_data(as_text=True)
        self.assertIn("Opmerkingen", html)
        self.assertIn("Bericht 400", html)
        self.assertIn("Bericht 401", html)
        self.assertIn(">V1</span>", html)
        self.assertIn(">V2</span>", html)
        self.assertIn("opmerking", html)
        self.assertNotIn("Geen feedbackvragen bij dit bewijsstuk", html)
        with self.conn:
            self.conn.execute("DELETE FROM evidence_comments")
        self.assertIn("Nog geen feedback bij dit bewijsstuk.",
                      self.client.get("/studenten/1/bewijsstuk?ids=10").get_data(as_text=True))

    def test_timeline_leaves_out_own_and_old_remarks(self):   # F3
        with self.conn:
            self.conn.execute("DELETE FROM evidence_comments")
        self.add(400, "2026-08-21", "Joost Visser", 50, "coach")                 # before the period
        self.add(401, "2026-09-25", "Lotte Bakker", 11, "student")              # by the student himself
        self.add(402, "2026-09-26", "Noor Smit", 21, "student", parent=401)     # a fellow student replies
        _, replies = feedback.rows(self.conn, 1, START, END)
        self.assertEqual([(m["kind"], m["ids"]) for m in replies["marks"]], [("medestudent", "401")])
        self.assertIn("Reactie op een opmerking van Noor Smit (medestudent)", replies["marks"][0]["tip"])
        panel = self.client.get("/studenten/1/feedback?vragen=401").get_data(as_text=True)
        self.assertIn("Bericht 401", panel)
        self.assertIn("Bericht 402", panel)

    def test_key_figures_count_remarks_of_coaches(self):   # F6
        stats = feedback.summary(self.conn, 1, START, END)
        self.assertEqual(stats["staff_remarks"], 1)                               # 102 by the guild master
        self.assertEqual(stats["requests"], 2)                                    # requests unchanged
        self.assertIn("opmerking van coaches en gildemeesters", self.client.get("/studenten/1").get_data(as_text=True))

    def test_remarks_go_to_the_ai(self):   # F5
        from dashboard import ai_advice
        texts = ai_advice._feedback_texts(self.conn, 1, START, END)
        self.assertIn("Opmerking bij Sprintverslag van Joost Visser (gildemeester)", texts[102])
