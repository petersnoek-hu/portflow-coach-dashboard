"""Tests for spec 039: the page of one review request. Invented names and data."""

import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dashboard import create_app, evaluation_page, evidence, feedback, lef

TODAY = date.today()
START, END = TODAY - timedelta(days=60), TODAY + timedelta(days=60)
MENTION = ('<span data-type="mention" data-id="{id}" data-label="{label}" data-mention-type="evidence" '
           'data-portfolio-id="101">@{label}</span>')


def iso(days_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def day(days_ago: int) -> str:
    return (TODAY - timedelta(days=days_ago)).isoformat()


class PageCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        q = self.conn.execute
        with self.conn:
            q("INSERT INTO settings (key, value) VALUES ('semester_start', ?), ('semester_end', ?)", (START.isoformat(), END.isoformat()))
            q("INSERT INTO students (id, name, portflow_user_id) VALUES (1, 'Lotte Bakker', 11), (2, 'Daan Visser', 12)")
            q("INSERT INTO student_portfolios (student_id, portfolio_id) VALUES (1, 101), (2, 202)")
            q("INSERT INTO staff (name, is_coach, is_guild_master) VALUES ('Noor Smit', 1, 0)")
            # The request: PL and BD, handed in 5 days ago, to the user.
            self_pl = "<p>Ik plan met " + MENTION.format(id=501, label="Sprintplanning") + " en " \
                      + MENTION.format(id=999, label="Oud verslag") + "</p>"
            q("INSERT INTO evaluations (student_id, skill, kind, level, date, review_request_id, review_request_title, "
              "review_request_status, text) VALUES (1, 'PL', 'self', '2', ?, 70, 'PL & BD 2e evaluatie', 'not_started', ?), "
              "(1, 'BD', 'self', '1', ?, 70, 'PL & BD 2e evaluatie', 'not_started', '<p>Presentaties</p>')",
              (day(5), self_pl, day(5)))
            # Earlier: PL level 1 by the coach, 30 days ago, in another request.
            q("INSERT INTO evaluations (student_id, skill, kind, level, date, assessor, review_request_id, review_request_title, "
              "review_request_status, text) VALUES (1, 'PL', 'assessed', '1', ?, 'Noor Smit', 60, 'PL 1e evaluatie', 'scored', "
              "'<p>Goed begin</p>')", (day(30),))
            q("INSERT INTO received_requests (review_request_id, title, student_name, student_portflow_id, portfolio_id, "
              "status, created_at, note) VALUES (70, 'PL & BD 2e evaluatie', 'Lotte Bakker', 11, 101, 'not_started', ?, ?), "
              "(80, 'Ouder verzoek', 'Daan Visser', 12, 202, 'in_progress', ?, '<p></p>'), "
              "(90, 'Nieuwer verzoek', 'Iemand Anders', 99, 303, 'not_started', ?, NULL)",
              (iso(5), "<p>Zie " + MENTION.format(id=502, label="Retro") + "</p>", iso(9), iso(1)))
            # Evidence: 501 (PL, after the earlier assessment), 502 (BD), 503 (PL, before), 504 (KO, not asked).
            for eid, name, kind, skills, created in ((501, "Sprintplanning", "file", "PL", 10), (502, "Retro", "free_text", "BD", 3),
                                                     (503, "Planning oud", "url", "PL", 40), (504, "Onderzoek", "file", "KO", 4)):
                q("INSERT INTO evidence_items (student_id, evidence_id, name, kind, created_at, updated_at, collections, skills) "
                  "VALUES (1, ?, ?, ?, ?, ?, 'Semester 3', ?)", (eid, name, kind, iso(created), iso(created), skills))
            q("INSERT INTO evidence_fetches (student_id, fetched_at, collections) VALUES (1, ?, 1)", (iso(0),))
            q("INSERT INTO evidence_comments (comment_id, student_id, evidence_id, kind, text, created_at, author_id, author_name, "
              "author_role) VALUES (1, 1, 501, 'feedback_request', 'Klopt mijn planning?', ?, 11, 'Lotte Bakker', 'student'), "
              "(2, 1, 501, 'comment', 'Ja, mooi', ?, 13, 'Noor Smit', 'coach')", (iso(8), iso(7)))
            q("UPDATE evidence_comments SET parent_id = 1 WHERE comment_id = 2")

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def build(self, request_id=70):
        return evaluation_page.build(self.conn, request_id, TODAY, START, END,
                                     mention=lambda eid, label: f"/studenten/1/bewijsstuk?ids={eid}")

    def page(self, request_id=70):
        return self.client.get(f"/evaluaties/{request_id}")


class TestData(PageCase):
    def test_request_and_skills(self):   # F1, F4
        data = self.build()
        r = data["request"]
        self.assertEqual((r["title"], r["student"], r["student_id"], r["waiting"], r["to_me"]),
                         ("PL & BD 2e evaluatie", "Lotte Bakker", 1, "5 dagen", True))
        self.assertEqual(data["codes"], ["PL", "BD"])
        pl = data["skills"][0]
        self.assertEqual((pl["code"], pl["assessor"], pl["current"], pl["claimed"]), ("PL", "coach", 1, 2))

    def test_self_evaluation_and_note_with_mentions(self):   # F5, F6
        data = self.build()
        self.assertIn('href="/studenten/1/bewijsstuk?ids=502"', data["request"]["note"])
        pl = data["skills"][0]["self_text"]
        self.assertIn('<a class="evidence-mention" href="/studenten/1/bewijsstuk?ids=501" data-feedback', pl)
        self.assertIn(">Sprintplanning</a>", pl)
        self.assertNotIn("<span", pl)

    def test_lef_texts(self):   # F10
        pl = self.build()["skills"][0]
        self.assertEqual(pl["lef_claimed"], lef.level_text("PL", 2))
        self.assertEqual(pl["lef_current"], lef.level_text("PL", 1))
        self.assertTrue(pl["lef_claimed"]["title"])

    def test_earlier_evaluations(self):   # F11
        pl, bd = self.build()["skills"]
        self.assertEqual([(e["author"], e["role"], e["level"]) for e in pl["earlier"]], [("Noor Smit", "coach", "1")])
        self.assertIn("Goed begin", pl["earlier"][0]["text"])
        self.assertEqual(bd["earlier"], [])

    def test_evidence_per_skill_with_marks(self):   # F8
        pl, bd = self.build()["skills"]
        self.assertEqual([e["name"] for e in pl["evidence"]], ["Sprintplanning", "Planning oud"])   # newest first, not KO
        sprint, old = pl["evidence"]
        self.assertEqual((sprint["new"], sprint["mentioned"], sprint["requests"], sprint["replies"]), (True, True, 1, 1))
        self.assertEqual((old["new"], old["mentioned"]), (False, False))
        self.assertTrue(bd["evidence"][0]["mentioned"])   # mentioned in the note

    def test_feedback_requests_per_skill(self):   # F12
        pl, bd = self.build()["skills"]
        self.assertEqual([(t["evidence"], t["replies"], t["roles"]) for t in pl["threads"]], [("Sprintplanning", 1, ["coach"])])
        self.assertEqual(bd["threads"], [])

    def test_previous_and_next_in_to_review(self):   # F13: oldest first: 80, 70, 90
        data = self.build()
        self.assertEqual((data["previous"], data["next"], data["queue_position"]), (80, 90, (2, 3)))

    def test_request_to_someone_else(self):   # F1, F5
        with self.conn:
            self.conn.execute("INSERT INTO evaluations (student_id, skill, kind, level, date, review_request_id, "
                              "review_request_title, review_request_status) VALUES (1, 'OC', 'self', '1', ?, 75, "
                              "'OC voor de gildemeester', 'submitted')", (day(2),))
        data = self.build(75)
        self.assertEqual((data["request"]["note_known"], data["request"]["to_me"], data["queue_position"]), (False, False, None))
        self.assertEqual(data["codes"], ["OC"])
        self.assertEqual(data["skills"][0]["assessor"], "gildemeester")

    def test_unknown(self):   # F9
        self.assertIsNone(self.build(12345))


class TestPage(PageCase):
    def test_remarks_per_skill(self):   # spec 043, F4
        with self.conn:
            self.conn.execute("INSERT INTO evidence_comments (comment_id, student_id, evidence_id, kind, text, created_at, "
                              "author_id, author_name, author_role, version) VALUES (3, 1, 501, 'comment', 'Let op de planning', ?, "
                              "50, 'Joost Visser', 'coach', 1)", (datetime.now(timezone.utc).isoformat(),))
        html = self.page().get_data(as_text=True)
        self.assertIn("1 feedbackvraag · 1 opmerking", html)
        self.assertIn("opmerking van Joost Visser (coach)", html)
        self.assertIn("1 opmerking</span>", html)

    def test_page_shows_everything(self):   # F1-F13
        html = self.page().get_data(as_text=True)
        for text in ("PL &amp; BD 2e evaluatie", "Stand van zaken", "Evaluaties per week", "Toelichting van de student",
                     "Zelfevaluatie", "Eerdere evaluaties", "Bewijsstukken", "Feedback <span", "genoemd in zelfevaluatie",
                     "nieuw sinds vorige beoordeling", "2 van 3", "Bewijsstukken per vaardigheid"):
            self.assertIn(text, html)
        self.assertIn('class="col-skill cat-social is-requested"', html)   # F2: PL and BD marked
        self.assertIn('href="/evaluaties/80"', html)
        self.assertIn('data-refresh-scope', html)   # spec 041, F3: Verversen fetches only Lotte
        # F1 (changed 2026-11-23): Evaluaties › <student> › <title>, the student links to the student page.
        self.assertRegex(html, r'<a class="crumb-link" href="/evaluaties">Evaluaties</a>\s*<span class="crumb-sep"[^>]*>›</span>\s*'
                               r'<a class="crumb-link" href="/studenten/1\?van=evaluations">Lotte Bakker</a>\s*'
                               r'<span class="crumb-sep"[^>]*>›</span>\s*<h1 class="crumb-title">PL &amp; BD 2e evaluatie</h1>')
        self.assertIn('data-live="cell-1-PL"', html)   # spec 041, F7: updated without reloading
        self.assertIn('data-live="eval-note"', html)
        self.assertIn('href="/evaluaties/90"', html)

    def test_timeline_only_requested_skills(self):   # F7
        html = self.page().get_data(as_text=True)
        block = html[html.index('id="evidence-block"'):]
        self.assertIn('title="Plannen">PL</span>', block)
        self.assertNotIn('>KO</span>', block)
        self.assertIn("vaardigheden=PL,BD", block)

    def test_feedback_rows_in_the_timeline(self):   # F12: feedback questions/replies as rows, for the requested skills
        html = self.page().get_data(as_text=True)
        block = html[html.index('id="evidence-block"'):]
        self.assertIn("feedback-mark feedback-request", block)   # the Feedbackvraag row (on evidence 501, PL)
        self.assertIn("feedback-mark feedback-reply", block)     # the Reactie row

    def test_note_before_and_after_fetching(self):   # F5
        self.assertIn("De student heeft geen toelichting geschreven.", self.page(80).get_data(as_text=True))
        with self.conn:
            self.conn.execute("UPDATE received_requests SET note = NULL WHERE review_request_id = 80")
        self.assertIn("Klik op Verversen", self.page(80).get_data(as_text=True))

    def test_student_not_in_dashboard(self):   # F9
        html = self.page(90).get_data(as_text=True)
        self.assertIn("Deze student staat niet in het dashboard", html)
        self.assertIn("Iemand Anders", html)
        self.assertIn('<span class="crumb-section">Iemand Anders</span>', html)   # F1: in the breadcrumb, without a link

    def test_not_found(self):   # F9
        response = self.page(12345)
        self.assertEqual(response.status_code, 404)
        self.assertIn("bestaat niet (meer)", response.get_data(as_text=True))

    def test_links_from_to_review_and_student_page(self):   # F1
        self.assertIn('href="/evaluaties/70"', self.client.get("/evaluaties").get_data(as_text=True))
        self.assertIn('href="/evaluaties/70?van=overview"', self.client.get("/studenten/1").get_data(as_text=True))


class TestMentions(PageCase):
    def test_mentioned_ids(self):
        self.assertEqual(evaluation_page.mentioned_ids(MENTION.format(id=7, label="a") + MENTION.format(id=8, label="b")), {7, 8})
        self.assertEqual(evaluation_page.mentioned_ids("<span data-id='3'>x</span>"), set())

    def test_safe_html_without_mention_stays_label(self):   # spec 036 unchanged
        self.assertEqual(evidence.safe_html(MENTION.format(id=7, label="Verslag")), "[Verslag]")

    def test_unknown_evidence_is_fetched_live(self):   # F6
        items = feedback.evidence_items(self.conn, 1, [999], START, END)
        self.assertEqual((items[0]["evidence_id"], items[0].get("live")), (999, True))


if __name__ == "__main__":
    unittest.main()
