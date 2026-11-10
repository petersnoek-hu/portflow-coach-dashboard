"""Tests for the progress rules (docs/voortgangsregels.md, spec 001 F6, F7, F10, F12, F18, F22)."""

import unittest
from datetime import date

from dashboard.progress import default_semester_period, student_progress
from dashboard.skills import SKILLS

PERIOD = (date(2026, 9, 1), date(2027, 1, 31))
KNOWN = {"Joost Hendriks", "Marieke Ploeg"}


def assessed(skill, level, day, assessor="Joost Hendriks", status="scored", rid=None):
    return {"skill": skill, "kind": "assessed", "level": level, "date": day, "assessor": assessor,
            "review_request_id": rid, "review_request_title": None, "review_request_status": status}


def self_eval(skill, day, rid=1, title="Verzoek", status="not_scored"):
    return {"skill": skill, "kind": "self", "level": "1", "date": day, "assessor": None,
            "review_request_id": rid, "review_request_title": title, "review_request_status": status}


def progress(rows, semester=3, **kwargs):
    return student_progress(rows, semester=semester, known_assessors=KNOWN, period=PERIOD, **kwargs)


class TestCells(unittest.TestCase):  # F6, F7
    def test_two_evaluations_chronological(self):
        cell = progress([assessed("OC", "2", "2026-10-20"), assessed("OC", "1", "2026-09-20")]).cells["OC"]
        self.assertEqual(cell.text, "1/2")
        self.assertEqual(cell.colour, "n2")

    def test_start_level_shows_as_zero(self):
        cell = progress([assessed("OC", "0", "2026-09-20"), assessed("OC", "2", "2026-10-20")]).cells["OC"]
        self.assertEqual(cell.text, "0/2")
        self.assertEqual(cell.highest, 2)

    def test_open_request_adds_question_mark_with_colour_of_achieved(self):
        cell = progress([assessed("SW", "1", "2026-09-20"), self_eval("SW", "2026-10-25")]).cells["SW"]
        self.assertEqual(cell.text, "1/?")
        self.assertEqual(cell.colour, "n1")
        self.assertIsNotNone(cell.pending)

    def test_three_evaluations_get_two_plus_colour(self):
        rows = [assessed("SW", "1", "2026-09-10"), assessed("SW", "1", "2026-10-01"), assessed("SW", "2", "2026-10-29")]
        cell = progress(rows).cells["SW"]
        self.assertEqual(cell.text, "1/1/2")
        self.assertEqual(cell.colour, "n2")

    def test_denied_request_gives_no_question_mark(self):
        cell = progress([self_eval("PL", "2026-10-30", status="denied")]).cells["PL"]
        self.assertIsNone(cell.pending)
        self.assertEqual(cell.text, "-/-")

    def test_answered_request_gives_no_question_mark(self):
        rows = [self_eval("PL", "2026-10-01"), assessed("PL", "1", "2026-10-03", status="scored")]
        self.assertIsNone(progress(rows).cells["PL"].pending)

    def test_only_newest_open_request_counts(self):
        rows = [self_eval("PL", "2026-10-01", rid=1, title="Oud"), self_eval("PL", "2026-10-20", rid=2, title="Nieuw")]
        self.assertEqual(progress(rows).cells["PL"].pending.title, "Nieuw")

    def test_semester_three_without_evaluation(self):
        cell = progress([], semester=3).cells["OC"]
        self.assertEqual((cell.text, cell.colour), ("-/-", "n0"))

    def test_semester_two_without_evaluation_is_grey(self):
        cell = progress([], semester=2).cells["OC"]
        self.assertEqual((cell.text, cell.colour), ("", "grey"))

    def test_unknown_semester_without_evaluation_is_grey(self):
        cell = progress([], semester=None).cells["OC"]
        self.assertEqual((cell.text, cell.colour), ("", "grey"))

    def test_unknown_assessor_is_hidden(self):
        cell = progress([assessed("BD", "3", "2026-10-21", assessor="Kevin Brandsma")]).cells["BD"]
        self.assertEqual(cell.text, "-/-")

    def test_assessor_names_compare_without_case_and_spaces(self):
        cell = progress([assessed("BD", "2", "2026-10-21", assessor=" joost  hendriks")]).cells["BD"]
        self.assertEqual(cell.text, "2")

    def test_evaluation_before_semester_period_is_hidden(self):
        cell = progress([assessed("OC", "1", "2026-05-12"), assessed("OC", "2", "2026-09-24")]).cells["OC"]
        self.assertEqual(cell.text, "2")

    def test_own_start_date_replaces_period_start(self):
        cell = progress([assessed("OC", "1", "2026-09-10")], start_date="2026-10-01").cells["OC"]
        self.assertEqual(cell.text, "-/-")

    def test_evaluation_without_date_counts(self):
        self.assertEqual(progress([assessed("OC", "1", "")]).cells["OC"].text, "1")

    def test_evaluation_without_level_or_unscored_request_does_not_count(self):
        rows = [assessed("OC", None, "2026-10-01"), assessed("KO", "1", "2026-10-01", status="not_scored")]
        result = progress(rows)
        self.assertEqual(result.cells["OC"].text, "-/-")
        self.assertEqual(result.cells["KO"].text, "-/-")

    def test_no_access_shows_nb(self):  # F11
        result = progress([assessed("OC", "1", "2026-10-01")], has_access=False)
        self.assertEqual([c.text for c in result.cells.values()], ["n/b"] * 10)
        self.assertEqual(result.signals, [])


class TestFullAssessment(unittest.TestCase):  # F10
    def test_request_with_all_ten_skills_gives_marker_and_no_question_marks(self):
        result = progress([self_eval(skill, "2026-11-06", rid=9) for skill in SKILLS])
        self.assertTrue(result.full_assessment)
        self.assertFalse(any(cell.pending for cell in result.cells.values()))

    def test_request_with_some_skills_is_not_a_full_assessment(self):
        result = progress([self_eval(skill, "2026-11-06", rid=9) for skill in SKILLS[:4]])
        self.assertFalse(result.full_assessment)
        self.assertEqual(sum(1 for c in result.cells.values() if c.pending), 4)


class TestSignals(unittest.TestCase):  # F12
    COACH = [assessed(s, "1", "2026-10-01", "Marieke Ploeg") for s in ["PL", "BD", "SW", "FO", "PH", "RE"]]
    PRODUCT = [assessed(s, "1", "2026-10-01") for s in ["OC", "KO", "JKO", "KPM"]]

    def test_product_empty_is_red(self):
        self.assertEqual(progress(self.COACH, semester=4).signals, [("red", "Product nog leeg")])

    def test_five_of_six_coach_skills_empty_is_yellow(self):
        self.assertEqual(progress(self.PRODUCT + self.COACH[:1], semester=4).signals, [("yellow", "Coach nog leeg")])

    def test_all_coach_skills_empty_is_orange(self):
        self.assertEqual(progress(self.PRODUCT, semester=4).signals, [("orange", "Coach nog leeg")])

    def test_open_request_does_not_count_as_filled(self):
        rows = self.COACH + [self_eval("OC", "2026-10-20")]
        self.assertIn(("red", "Product nog leeg"), progress(rows, semester=3).signals)

    def test_no_signals_in_semester_two_or_unknown(self):
        self.assertEqual(progress([], semester=2).signals, [])
        self.assertEqual(progress([], semester=None).signals, [])


class TestSortKey(unittest.TestCase):  # F18
    def test_empty_first_then_one_evaluation_lowest_level_first(self):
        cells = [
            progress([assessed("OC", "1", "2026-10-01"), assessed("OC", "2", "2026-10-20")]).cells["OC"],
            progress([assessed("OC", "2", "2026-10-01")]).cells["OC"],
            progress([]).cells["OC"],
            progress([assessed("OC", "1", "2026-10-01")]).cells["OC"],
        ]
        ordered = [c.text for c in sorted(cells, key=lambda c: c.sort_key)]
        self.assertEqual(ordered, ["-/-", "1", "2", "1/2"])


class TestSemesterPeriod(unittest.TestCase):  # F22
    def test_running_semester(self):
        self.assertEqual(default_semester_period(date(2026, 11, 9)), (date(2026, 9, 1), date(2027, 1, 31)))
        self.assertEqual(default_semester_period(date(2027, 1, 15)), (date(2026, 9, 1), date(2027, 1, 31)))
        self.assertEqual(default_semester_period(date(2027, 3, 10)), (date(2027, 2, 1), date(2027, 8, 31)))


if __name__ == "__main__":
    unittest.main()
