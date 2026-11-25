"""Tests for spec 030: Te beoordelen, the open review requests sent to the user. Invented names."""

import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from dashboard import create_app, db, requests_to_review
from dashboard.portflow_fetch import S_REQUESTS_FETCHED
from dashboard.skills import SKILLS
from tests.test_fetch import FetchTestCase


def invitation(rid, status="not_started", name="Lotte Bakker", user_id=11, created="2026-11-12T09:14:38.478Z",
               title="OC & KO 1ste evaluatie"):
    return {"id": rid + 1000, "reviewer_id": 1, "review_request_id": rid, "review_request_note": "<p>geheim</p>",
            "portfolio_id": 101, "status": status, "submitted_at": None, "denied_at": None, "created_at": created,
            "updated_at": created, "review_request_title": title, "suggested_due_date": "2026-12-01T00:00:00.000Z",
            "requester": {"id": user_id, "name": name, "profile_picture_url": "https://example.invalid/a.png"}}


class TestStoredByFetch(FetchTestCase):   # Data
    def test_requests_are_stored_with_note_without_due_date(self):   # spec 039: the note is kept
        self.api.invitations = [invitation(1), invitation(2, status="scored")]
        self.fetcher.start()
        rows = self.sql("SELECT review_request_id, title, student_name, student_portflow_id, status, created_at "
                        "FROM received_requests ORDER BY review_request_id")
        self.assertEqual(rows, [(1, "OC & KO 1ste evaluatie", "Lotte Bakker", 11, "not_started", "2026-11-12T09:14:38.478Z"),
                                (2, "OC & KO 1ste evaluatie", "Lotte Bakker", 11, "scored", "2026-11-12T09:14:38.478Z")])
        columns = [r[1] for r in self.sql("PRAGMA table_info(received_requests)")]
        self.assertFalse(any("due" in c or "picture" in c for c in columns))
        self.assertEqual(self.sql("SELECT note FROM received_requests WHERE review_request_id = 1"), [("<p>geheim</p>",)])

    def test_no_note_is_stored_as_empty(self):   # spec 039: null in Portflow is "no note", not "not fetched"
        item = invitation(1)
        item["review_request_note"] = None
        self.api.invitations = [item]
        self.fetcher.start()
        self.assertEqual(self.sql("SELECT note FROM received_requests"), [("",)])

    def test_next_round_replaces_and_failed_call_keeps(self):
        self.api.invitations = [invitation(1), invitation(2)]
        self.fetcher.start()
        self.api.invitations = [invitation(2, status="submitted")]
        self.fetcher.start()
        self.assertEqual(self.sql("SELECT review_request_id, status FROM received_requests"), [(2, "submitted")])
        self.api.received_invitations = lambda token, own, **retry: (500, None)
        self.fetcher.start()
        self.assertEqual(self.sql("SELECT review_request_id FROM received_requests"), [(2,)])

    def test_marks_when_requests_were_fetched(self):   # F5
        self.assertIsNone(db.get_setting(self.database, S_REQUESTS_FETCHED))
        self.fetcher.start()
        self.assertIsNotNone(db.get_setting(self.database, S_REQUESTS_FETCHED))


class ToReviewCase(unittest.TestCase):
    def setUp(self):
        self.TODAY = date.today()   # per test, so it matches datetime.now() in request() (also near midnight)
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        db.set_setting(self.db_path, S_REQUESTS_FETCHED, "2026-11-17T10:00:00+00:00")
        conn = self.conn()
        with conn:
            conn.execute("INSERT INTO students (id, name, portflow_user_id) VALUES (1, 'Lotte Bakker', 11)")
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def request(self, rid, days_ago, status="not_started", user_id=11, name="Lotte Bakker", title="Verzoek",
                skills=()):
        created = (datetime.now() - timedelta(days=days_ago)).astimezone().isoformat()
        conn = self.conn()
        with conn:
            conn.execute("INSERT INTO received_requests (review_request_id, title, student_name, student_portflow_id, "
                         "status, created_at) VALUES (?, ?, ?, ?, ?, ?)", (rid, title, name, user_id, status, created))
            for skill in skills:
                conn.execute("INSERT INTO evaluations (student_id, skill, kind, level, date, review_request_id, "
                             "review_request_status) VALUES (1, ?, 'self', '1', ?, ?, ?)",
                             (skill, created[:10], rid, status))
        conn.close()

    def requests(self):
        conn = self.conn()
        try:
            return requests_to_review.open_requests(conn, self.TODAY)
        finally:
            conn.close()

    def html(self):
        return self.client.get("/evaluaties").get_data(as_text=True)


class TestList(ToReviewCase):
    def test_open_request_with_skills_date_and_waiting(self):   # F1 acceptance
        self.request(1, 5, title="OC & KO 1ste evaluatie", skills=("KO", "OC"))
        [r] = self.requests()
        self.assertEqual((r["student"], r["title"], r["skills"], r["waiting"]),
                         ("Lotte Bakker", "OC & KO 1ste evaluatie", ["OC", "KO"], "5 dagen"))
        html = self.html()
        self.assertIn("OC &amp; KO 1ste evaluatie", html)
        self.assertIn('<span class="to-review-waiting">5 dagen</span>', html)
        self.assertIn(f"ingediend {r['submitted'].day}-{r['submitted'].month}-{r['submitted'].year}", html)

    def test_only_open_statuses(self):   # F1
        for rid, status in enumerate(("not_started", "in_progress", "submitted", "scored", "denied"), start=1):
            self.request(rid, 1, status=status)
        self.assertEqual(sorted(r["id"] for r in self.requests()), [1, 2])

    def test_oldest_first(self):   # F2 acceptance
        self.request(1, 2)
        self.request(2, 9)
        self.assertEqual([r["id"] for r in self.requests()], [2, 1])

    def test_unknown_student_shown_with_portflow_name(self):   # F3 acceptance
        self.request(1, 1, user_id=99, name="Noor Smit")
        [r] = self.requests()
        self.assertEqual((r["student"], r["skills"], r["followed"]), ("Noor Smit", [], False))
        self.assertIn("Noor Smit", self.html())

    def test_list_does_not_follow_who(self):   # F3
        self.request(1, 1, user_id=99, name="Noor Smit")
        html = self.client.get("/evaluaties?wie=coach").get_data(as_text=True)
        self.assertIn("Noor Smit", html.split('id="to-review-title"')[1])

    def test_full_assessment_is_one_label(self):   # F4
        self.request(1, 1, skills=SKILLS)
        [r] = self.requests()
        self.assertTrue(r["full_assessment"])
        section = self.html().split('id="to-review-title"')[1]
        self.assertIn("Assessment ingeleverd", section)
        self.assertNotIn('class="skill-code"', section)

    def test_waiting_text(self):   # F1
        self.assertEqual([requests_to_review.waiting_text(d) for d in (0, 1, 5)], ["vandaag", "1 dag", "5 dagen"])


class TestEmptyAndCounter(ToReviewCase):
    def test_empty(self):   # F5
        self.assertIn("Er wachten geen evaluatieverzoeken op jouw beoordeling.", self.html())

    def test_never_fetched(self):   # F5
        db.set_setting(self.db_path, S_REQUESTS_FETCHED, None)
        self.assertIn("verschijnen hier na \"Verversen\"", self.html().replace("&#34;", '"'))

    def test_counter_in_menu(self):   # F6 acceptance
        self.assertNotIn('class="nav-count"', self.client.get("/").get_data(as_text=True))
        for rid in (1, 2, 3):
            self.request(rid, 1)
        self.request(4, 1, status="scored")
        html = self.client.get("/").get_data(as_text=True)
        self.assertRegex(html, r'Evaluaties</span><span class="live" data-live="nav-count">\s*<span class="nav-count"[^>]*>3</span>')


if __name__ == "__main__":
    unittest.main()


class TestStudentsWithANewRequest(FetchTestCase):   # spec 041, F9
    def goals_fetched(self):
        return [c[1] for c in self.api.calls if c[0] == "goals"]

    def setUp(self):
        super().setUp()
        from dashboard.portflow_fetch import S_LAST_FETCH
        db.set_setting(self.database, S_LAST_FETCH, "2026-11-08T10:00:00+00:00")   # not the first round
        self.on_screen = self.add_student("Lotte Bakker", [101], 11)
        self.elsewhere = self.add_student("Noor Smit", [102], 12)
        self.sql("UPDATE students SET fetched_at = '2026-11-08T10:00:00+00:00'")

    def test_student_not_on_screen_with_a_new_request_is_fetched(self):   # F9 acceptance
        self.api.invitations = [invitation(7, user_id=12, name="Noor Smit", created="2026-11-09T09:00:00.000Z")]
        self.fetcher.start([self.on_screen], screen=True)
        self.assertEqual(self.goals_fetched(), [101, 102])            # the screen first, then the request
        self.api.calls.clear()
        self.fetcher.start([self.on_screen], screen=True)              # now fetched after the request: up to date
        self.assertEqual(self.goals_fetched(), [101])

    def test_older_requests_and_other_statuses_do_not_add_a_student(self):   # F9
        self.api.invitations = [invitation(7, user_id=12, created="2026-11-01T09:00:00.000Z"),         # before the fetch
                                invitation(8, user_id=12, status="submitted", created="2026-11-09T09:00:00.000Z")]
        self.fetcher.start([self.on_screen], screen=True)
        self.assertEqual(self.goals_fetched(), [101])

    def test_hidden_or_never_fetched_student_is_fetched_too(self):   # F9
        self.sql("UPDATE students SET is_hidden = 1, fetched_at = NULL WHERE id = ?", (self.elsewhere,))
        self.api.invitations = [invitation(7, user_id=12, created="2026-11-01T09:00:00.000Z")]
        self.fetcher.start([self.on_screen], screen=True)
        self.assertEqual(self.goals_fetched(), [101, 102])


class TestWhyNoSkills(ToReviewCase):   # spec 041, F10
    def test_not_fetched_since_the_request(self):   # F10 acceptance
        conn = self.conn()
        with conn:
            conn.execute("UPDATE students SET fetched_at = ?", ((datetime.now() - timedelta(days=3)).astimezone().isoformat(),))
        conn.close()
        self.request(1, days_ago=1)
        self.assertEqual(self.requests()[0]["no_skills"][0], "nog niet opgehaald")
        self.assertIn("nog niet opgehaald", self.html())

    def test_fetched_but_no_self_evaluation(self):   # F10 acceptance
        self.request(1, days_ago=2)
        conn = self.conn()
        with conn:
            conn.execute("UPDATE students SET fetched_at = ?", (datetime.now().astimezone().isoformat(),))
        conn.close()
        self.assertEqual(self.requests()[0]["no_skills"][0], "geen zelfevaluatie")
        html = self.html()
        self.assertIn("geen zelfevaluatie", html)
        self.assertIn("geen zelfevaluatie per vaardigheid ingevuld", html)          # the explanation
        page = self.client.get("/evaluaties/1").get_data(as_text=True)
        self.assertIn("geen zelfevaluatie", page)

    def test_with_skills_or_unknown_student(self):   # F10, spec 030 F3
        self.request(1, days_ago=1, skills=("OC",))
        self.request(2, days_ago=1, user_id=99, name="Iemand Anders")
        by_id = {r["id"]: r for r in self.requests()}
        self.assertIsNone(by_id[1]["no_skills"])
        self.assertIsNone(by_id[2]["no_skills"])                                    # not in the dashboard: "–"
