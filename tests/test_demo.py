"""The demo set must cover the cases of spec 001 (spec 002, F13)."""

import unittest

import tempfile
from pathlib import Path

from dashboard import db, demo, roles
from dashboard.demo import SKILLS, STAFF, STUDENTS

PRODUCT = {"OC", "KO", "JKO", "KPM"}
COACH = {"PL", "BD", "SW", "FO", "PH", "RE"}
SEMESTER_START = "2026-09-01"


def assessed_skills(student):
    return {ev["skill"] for ev in student["evaluations"]}


def levels_per_skill(student):
    result = {}
    for ev in student["evaluations"]:
        result.setdefault(ev["skill"], []).append(ev["level"])
    return result


class TestDemoCoverage(unittest.TestCase):
    def assertSomeStudent(self, condition, message):
        self.assertTrue(any(condition(s) for s in STUDENTS), message)

    def test_semesters(self):
        self.assertSomeStudent(lambda s: s["semester"] == 2, "student in semester 2")
        for semester in (3, 4, 5):
            self.assertSomeStudent(lambda s, n=semester: s["semester"] == n, f"student in semester {semester}")

    def test_grouping_cases(self):
        squads = {s["squad"] for s in STUDENTS if s["squad"]}
        self.assertGreaterEqual(len(squads), 2, "multiple squads")
        self.assertSomeStudent(lambda s: s["squad"] is None and s["semester"], "student without squad")
        self.assertSomeStudent(lambda s: s["semester"] is None, "student without semester")

    def test_cell_cases(self):
        self.assertSomeStudent(lambda s: any(ev["level"] == "0" for ev in s["evaluations"]), "start level")
        self.assertSomeStudent(
            lambda s: any(len(set(levels)) > 1 for levels in levels_per_skill(s).values()), "several levels (1/2)"
        )
        self.assertSomeStudent(
            lambda s: any(len(levels) >= 3 for levels in levels_per_skill(s).values()), "three evaluations (1/1/2)"
        )
        self.assertSomeStudent(lambda s: s["semester"] and s["semester"] >= 3 and len(assessed_skills(s)) < 10,
                               "skill without evaluation")
        self.assertSomeStudent(
            lambda s: any(ev["date"] < SEMESTER_START for ev in s["evaluations"]), "evaluation before the period"
        )

    def test_request_cases(self):
        requests = [r for s in STUDENTS for r in s.get("requests", [])]
        self.assertTrue(any(r["status"] in ("not_started", "in_progress") and len(r["skills"]) < 10 for r in requests),
                        "open request (?)")
        self.assertTrue(any(r["status"] == "denied" for r in requests), "denied request")
        self.assertTrue(any(set(r["skills"]) == set(SKILLS) for r in requests), "full assessment")

    def test_unknown_assessor(self):
        self.assertSomeStudent(
            lambda s: any(ev["assessor"] not in STAFF for ev in s["evaluations"]), "assessor not in staff list"
        )

    def test_signals_and_access(self):
        senior = [s for s in STUDENTS if s["semester"] and s["semester"] >= 3]
        self.assertTrue(any(not (assessed_skills(s) & PRODUCT) for s in senior), "all product skills empty")
        self.assertTrue(any(not (assessed_skills(s) & COACH) for s in senior), "all coach skills empty")
        self.assertTrue(any(len(COACH - assessed_skills(s)) in (4, 5) for s in senior), "4-5 coach skills empty")
        self.assertSomeStudent(lambda s: s.get("has_access") is False, "student without access (n/b)")

    def test_only_known_skills(self):
        for student in STUDENTS:
            self.assertLessEqual(assessed_skills(student), set(SKILLS), student["name"])


if __name__ == "__main__":
    unittest.main()


class TestSharedDemoData(unittest.TestCase):  # spec 002, F18
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "test.sqlite3")
        db.init_db(self.path)
        self.conn = db.connect(self.path)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def count(self, table, where="1"):
        return self.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0]

    def test_empty_dashboard_gets_demo_roles_guilds_semesters(self):
        demo.load_demo_data(self.conn)
        self.assertEqual(self.count("professional_roles", "is_demo = 1 AND description != ''"), 9)
        self.assertEqual(self.count("guilds", "is_demo = 1"), 9)
        self.assertEqual(self.count("semesters", "is_demo = 1"), 8)
        fe = self.conn.execute("SELECT r.color, g.color FROM professional_roles r JOIN guilds g ON g.role_id = r.id "
                               "WHERE r.code = 'FE'").fetchone()
        self.assertEqual(fe[0], fe[1])
        self.assertEqual(dict(demo.demo_counts(self.conn))["Beroepsrollen"], 9)
        demo.remove_demo_data(self.conn)
        for table in ("professional_roles", "guilds", "semesters"):
            self.assertEqual(self.count(table), 0, table)

    def test_existing_roles_are_used_and_unchanged(self):
        roles.add_preset(self.conn)
        self.conn.execute("UPDATE professional_roles SET description = 'Eigen tekst', color = '#000000' WHERE code = 'FE'")
        self.conn.commit()
        demo.load_demo_data(self.conn)
        self.assertEqual(self.count("professional_roles", "is_demo = 1"), 0)
        fe = self.conn.execute("SELECT description, color FROM professional_roles WHERE code = 'FE'").fetchone()
        self.assertEqual(tuple(fe), ("Eigen tekst", "#000000"))
        self.assertEqual(dict(demo.demo_counts(self.conn))["Beroepsrollen"], "gebruikt je bestaande 9")
        demo.remove_demo_data(self.conn)
        self.assertEqual(self.count("professional_roles"), 9)

