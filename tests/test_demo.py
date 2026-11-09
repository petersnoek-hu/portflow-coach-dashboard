"""The demo set must cover the cases of spec 001 (spec 002, F13)."""

import unittest

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
