"""Tests for spec 044: the colour scheme of the level labels. Invented names."""
import re
import unittest
from datetime import date

from dashboard import overview, progress
from tests.test_student_page import StudentPageCase

PERIOD = (date(2026, 9, 1), date(2027, 1, 31))


def row(skill, kind, day, level=None, rid=None, assessor="Joost Visser", status="scored"):
    return {"skill": skill, "kind": kind, "level": level, "date": day, "assessor": None if kind == "self" else assessor,
            "review_request_id": rid, "review_request_status": status, "review_request_title": "Peilmoment"}


class TestMoments(unittest.TestCase):   # F4-F6
    def cell(self, rows, **kw):
        return progress.student_progress(rows, semester=3, period=PERIOD, **kw).cells["PL"]

    def test_acceptance(self):   # F4 acceptance
        cell = self.cell([row("PL", "assessed", "2026-10-01", None, 1), row("PL", "assessed", "2026-11-20", "3", 2)])
        self.assertEqual([(s["kind"], s["text"]) for s in cell.slots], [("pm1", "–"), ("pm2", "3"), ("empty", "")])
        self.assertEqual(cell.count, 1)                                  # F6: only the one with a level counts
        self.assertEqual(cell.text, "3")

    def test_pending_on_the_next_place_and_a_fourth(self):
        rows = [row("PL", "assessed", f"2026-10-0{i}", "3", i) for i in range(1, 4)]
        rows += [row("PL", "self", "2026-11-01", "3", 9, status="submitted")]
        cell = self.cell(rows)
        self.assertEqual([s["kind"] for s in cell.slots], ["pm1", "pm2", "pm3", "pending"])
        cell = self.cell([row("PL", "assessed", f"2026-10-0{i}", "4", i) for i in range(1, 6)])
        self.assertEqual([s["kind"] for s in cell.slots], ["pm1", "pm2", "pm3", "pm4", "pm4"])   # fifth: colour of the fourth

    def test_excluded_or_outside_the_period_is_no_moment(self):
        rows = [row("PL", "assessed", "2026-06-01", None, 1),                    # before the period
                row("PL", "assessed", "2026-10-01", None, 2, assessor="Oud Student")]
        cell = self.cell(rows, excluded_assessors={"Oud Student"})
        self.assertEqual([s["kind"] for s in cell.slots], ["empty", "empty", "empty"])


class TestScheme(StudentPageCase):   # F1-F3
    def scheme(self, key):
        return self.client.post("/instellingen/kleuren", data={"schema": key})

    def test_choice_in_settings(self):   # F1
        html = self.html("/instellingen")
        self.assertIn("Kleuren in de tabellen", html)
        self.assertRegex(html, r'value="openict"\s+checked')                     # the default
        response = self.scheme("hcai")
        self.assertTrue(response.headers["Location"].endswith("/instellingen?kleuren=ok#kleuren"))
        self.assertRegex(self.html("/instellingen"), r'value="hcai"\s+checked')
        self.assertEqual(self.scheme("regenboog").status_code, 400)
        self.assertIn('<body class="scheme-hcai">', self.html("/"))

    def test_hcai_cells_everywhere(self):   # F2, F4
        self.add("PL", "assessed", "2026-10-01", None, rid=1)
        self.add("PL", "assessed", "2026-11-20", "3", rid=2)
        self.scheme("hcai")
        for path in ("/", "/studenten/1", "/evaluaties"):
            html = self.html(path)
            self.assertIn('class="moment moment-pm1">–</span><span class="moment moment-pm2">3</span>'
                          '<span class="moment moment-empty"></span>', html, path)
        self.assertIn("geen niveau ingevuld (startniveau, 1 of 2)", self.html("/"))

    def test_legend_follows_the_scheme(self):   # F3
        self.scheme("hcai")
        html = self.html("/")
        self.assertIn("1e peilmoment", html)
        self.assertNotIn("0 evaluaties", html)
        self.scheme("blue")
        html = self.html("/")
        self.assertIn('value="pending"', html)
        self.assertNotIn('value="n0"', html)
        self.scheme("none")
        self.assertIn("Geen kleuren (Instellingen", self.html("/"))

    def test_ticks_per_scheme_are_kept(self):   # F3 with spec 001, F23
        conn = self.conn()
        overview.save_colours_on(conn, ["n1", "n2", "pending"], ["n0", "n1", "n2", "pending"])   # n0 off
        overview.save_colours_on(conn, ["pm2", "pm3", "pm4", "pending"], ["pm1", "pm2", "pm3", "pm4", "pending"])
        self.assertEqual(sorted(overview.colours_off(conn)), ["n0", "pm1"])
        conn.close()
        self.scheme("hcai")
        self.client.post("/studenten/kleuren", data={"kleur": ["pm1", "pm2", "pm3", "pm4", "pending"]})
        conn = self.conn()
        self.assertEqual(overview.colours_off(conn), ["n0"])                     # the Open-ICT choice stays
        conn.close()


if __name__ == "__main__":
    unittest.main()
