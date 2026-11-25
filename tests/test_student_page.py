"""Tests for spec 032: the page of one student. All names are invented."""

import re
import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from dashboard import create_app, db, overview, timeline
from dashboard.skills import SKILLS

USER = "Marieke Ploeg"
PERIOD = ("2026-09-01", "2027-01-31")


class StudentPageCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        db.set_setting(self.db_path, "portflow_user_name", USER)
        conn = self.conn()
        overview.save_semester_period(conn, *PERIOD)
        with conn:
            conn.execute("INSERT INTO squads (id, number, name, full_name) VALUES (1, '02', 'Condor', '02 Condor')")
            conn.execute("INSERT INTO students (id, name, semester, squad_id) VALUES (1, 'Lotte Bakker', 3, 1)")
            conn.execute("INSERT INTO students (id, name, semester) VALUES (2, 'Sem de Wit', 3)")
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add(self, skill, kind, day, level=None, rid=None, status="scored", assessor="Joost Visser", student=1,
            title="Verzoek"):
        conn = self.conn()
        with conn:
            conn.execute("INSERT INTO evaluations (student_id, skill, kind, level, date, assessor, review_request_id, "
                         "review_request_title, review_request_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (student, skill, kind, level, day, None if kind == "self" else assessor, rid, title, status))
        conn.close()

    def row(self, student_id=1):
        conn = self.conn()
        try:
            return next(r for r in overview.student_rows(conn, date(2026, 11, 18)) if r["id"] == student_id)
        finally:
            conn.close()

    def html(self, path="/studenten/1"):
        return self.client.get(path).get_data(as_text=True)


class TestLinks(StudentPageCase):   # F1
    def test_names_link_to_the_student_page(self):
        for path, came_from in (("/", "overview"), ("/evaluaties?wie=iedereen", "evaluations")):
            with self.subTest(path=path):
                self.assertIn(f'href="/studenten/1?van={came_from}"', self.html(path))

    def test_name_on_studenten_still_opens_edit(self):
        html = self.html("/studenten")
        self.assertRegex(html, r'class="student-name student-link" href="/studenten/1/bewerken')
        self.assertNotIn('href="/studenten/1?van=', html)
        self.assertNotIn("student-edit", html)

    def test_breadcrumb_under_the_page_you_came_from(self):   # F2
        for came_from, label in (("overview", "Overzicht"), ("evaluations", "Evaluaties")):
            with self.subTest(came_from=came_from):
                html = self.html(f"/studenten/1?van={came_from}")
                self.assertRegex(html, rf'class="crumb-link" href="[^"]*">{label}</a>')
                self.assertIn('<h1 class="crumb-title">Lotte Bakker</h1>', html)


class TestPage(StudentPageCase):
    def test_table_with_only_this_student(self):   # F2
        table = self.html().split('class="student-table compact-table"')[1].split("</table>")[0]
        self.assertIn("Lotte Bakker", table)
        self.assertNotIn("Sem de Wit", table)

    def test_blocks_per_week(self):   # F3 acceptance
        self.add("OC", "self", "2026-09-22", rid=7)
        self.add("OC", "assessed", "2026-10-01", level="1", rid=7)
        self.add("BD", "self", "2026-10-07", rid=8, status="submitted", title="BD eerste keer")
        weeks = timeline.student_weeks(self.row(), date(2026, 9, 1), date(2027, 1, 31))
        self.assertEqual([b["label"] for b in weeks[3]["blocks"]], ["OC 1"])   # week of 21 September
        self.assertEqual([b["label"] for b in weeks[5]["blocks"]], ["BD ?"])   # week of 5 October
        self.assertEqual(weeks[3]["blocks"][0]["category"], "product")
        self.assertIn("ingediend 22-9-2026, beoordeeld 1-10-2026 door Joost Visser", weeks[3]["blocks"][0]["tip"])
        html = self.html()
        self.assertIn('<a class="skill-block skill-product" title="Overzicht creëren: niveau 1', html)
        self.assertIn('<a class="skill-block skill-pending"', html)
        self.assertIn(">BD ?</a>", html)

    def test_achieved_below_pending_in_skill_order(self):   # F3
        for skill in ("RE", "PL", "OC"):
            self.add(skill, "assessed", "2026-10-01", level="2")
        self.add("KO", "self", "2026-10-02", rid=3, status="submitted")
        week = timeline.student_weeks(self.row(), date(2026, 9, 1), date(2027, 1, 31))[4]
        self.assertEqual([b["label"] for b in week["blocks"]], ["OC 2", "PL 2", "RE 2", "KO ?"])

    def test_open_requests_with_to_me(self):   # F4 acceptance
        self.add("BD", "self", "2026-10-07", rid=8, status="submitted", title="BD voor mij")
        self.add("SW", "self", "2026-10-07", rid=8, status="submitted", title="BD voor mij")
        self.add("PL", "self", "2026-10-09", rid=9, status="submitted", title="PL voor een ander")
        conn = self.conn()
        with conn:
            conn.execute("INSERT INTO received_requests (review_request_id, title, student_name, status, created_at) "
                         "VALUES (8, 'BD voor mij', 'Lotte Bakker', 'not_started', '2026-10-07T10:00:00Z')")
        requests = timeline.student_open_requests(conn, self.row(), date(2026, 11, 18))
        conn.close()
        self.assertEqual([(r["title"], r["skills"], r["to_me"]) for r in requests],
                         [("BD voor mij", ["BD", "SW"], True), ("PL voor een ander", ["PL"], False)])
        section = self.html().split('id="student-open-title"')[1]
        self.assertEqual(section.count("aan jou"), 1)
        self.assertIn("ingediend 7-10-2026", section)

    def test_full_assessment_is_one_line(self):   # F4
        for skill in SKILLS:
            self.add(skill, "self", "2026-12-01", rid=11, status="submitted", title="Eindassessment")
        section = self.html().split('id="student-open-title"')[1]
        self.assertIn("Eindassessment", section)
        self.assertIn("Assessment ingeleverd", section)
        self.assertNotIn('class="skill-code"', section)

    def test_empty_states(self):   # F6
        html = self.html()
        self.assertIn("Nog geen evaluaties in deze semesterperiode.", html)
        self.assertIn("Er staan geen evaluaties open.", html)
        response = self.client.get("/studenten/99")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Deze student bestaat niet (meer).", response.get_data(as_text=True))

    def test_outside_period_not_shown(self):   # F5
        self.add("OC", "assessed", "2026-08-20", level="1")
        self.assertIn("Nog geen evaluaties in deze semesterperiode.", self.html())


if __name__ == "__main__":
    unittest.main()


class TestAssessed(StudentPageCase):   # F7
    def assessed(self):
        conn = self.conn()
        try:
            return timeline.student_assessed_requests(conn, 1, date(2026, 9, 1), date(2027, 1, 31))
        finally:
            conn.close()

    def test_newest_first_with_levels_who_and_dates(self):   # F7 acceptance
        self.add("PL", "self", "2026-11-12", "2", rid=70, title="Plannen 2")
        self.add("PL", "assessed", "2026-11-20", "2", rid=70, assessor=USER, title="Plannen 2")
        self.add("OC", "self", "2026-11-03", "1", rid=60, title="OC en KO")
        self.add("OC", "assessed", "2026-11-10", "1", rid=60, title="OC en KO")
        self.add("KO", "assessed", "2026-11-10", "1", rid=60, title="OC en KO")
        items = self.assessed()
        self.assertEqual([r["request_id"] for r in items], [70, 60])
        self.assertTrue(items[0]["by_me"])
        self.assertEqual([(s["code"], s["level"]) for s in items[1]["skills"]], [("OC", "1"), ("KO", "1")])
        self.assertEqual((items[1]["assessed_text"], items[1]["submitted_text"]), ("10-11-2026", "3-11-2026"))
        html = self.html()
        self.assertIn("Beoordeelde evaluaties", html)
        self.assertLess(html.index("Plannen 2"), html.index("OC en KO"))
        self.assertIn("door jou", html)
        self.assertIn('<span class="level assessed-level">1</span>', html)
        self.assertIn('href="/evaluaties/70', html)
        self.assertIn("beoordeeld 20-11-2026", html)

    def test_outside_period_excluded_and_not_counting(self):   # F7, voortgangsregels
        self.add("PL", "assessed", "2026-06-10", "1", rid=50)                        # before the period
        self.add("SW", "assessed", "2026-11-11", "2", rid=51, assessor="Oud Student")
        conn = self.conn()
        with conn:
            conn.execute("INSERT INTO excluded_assessors (name_key, name) VALUES ('oud student', 'Oud Student')")
        conn.close()
        self.add("FO", "assessed", "2026-11-12", None, rid=52, title="Zonder niveau")   # no level: does not count
        self.add("BD", "assessed", "2026-11-13", "2", rid=53, status="not_scored", title="Nog niet af")
        items = {r["request_id"]: r for r in self.assessed()}
        self.assertEqual(set(items), {52, 53})                                         # 50: old; 51: excluded assessor
        self.assertIsNone(items[52]["skills"][0]["level"])
        self.assertFalse(items[52]["skills"][0]["counts"])
        self.assertFalse(items[53]["skills"][0]["counts"])
        html = self.html()
        self.assertIn("zonder niveau", html)
        self.assertIn("telt niet mee", html)

    def test_empty(self):   # F7
        self.assertIn("Nog geen beoordeelde evaluaties in deze semesterperiode.", self.html())
