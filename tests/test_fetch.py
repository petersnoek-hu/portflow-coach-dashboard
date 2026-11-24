"""Tests for fetching evaluations (spec 005). A fake Portflow; no real calls."""

import json
import sqlite3
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timezone
from pathlib import Path

from dashboard import db, portflow_api
from dashboard.skills import NAMES, skill_for_goal_name
from dashboard.portflow_fetch import (
    S_LAST_FETCH_FAILED, Fetcher, is_unchanged, parse_feedback_item, resolve_date, resolve_level,
    reviews_signature, updated_text,
)

NOW = datetime(2026, 11, 9, 13, 32, tzinfo=timezone.utc)
LEVELS = [{"id": "a", "label": "Startniveau"}, {"id": "b", "label": "1"}, {"id": "c", "label": "2"}]


def item(role, level, day, reviewer="Joost Hendriks", rid=1, scored=True):
    return {
        "type": "criterion_evaluation", "role": role, "date": f"{day}T10:00:00.000Z",
        "evaluation": {"level": level, "level_set": LEVELS, "review_request_id": rid,
                       "review_request_title": "OC 1ste evaluatie", "review_request_scored": scored,
                       "comment": "<p>Goed gepland</p>", "reviewer": {"name": reviewer}},
    }


class FakeConnection:
    def __init__(self):
        self.token = "token"
        self.unauthorized = False

    def mark_unauthorized(self):
        self.unauthorized = True
        self.token = None


class FakeApi:
    def __init__(self):
        self.goals_by_portfolio = {}
        self.items = {}
        self.calls = []
        self.invitations = []
        self.shares = []
        self.shares_status = 200
        self.review_lists = {}   # spec 042; without an entry the list fails, so the student is fetched fully

    def goals(self, token, portfolio_id, **retry):
        self.calls.append(("goals", portfolio_id))
        return self.goals_by_portfolio.get(portfolio_id, (200, []))

    def feedback_items(self, token, portfolio_id, goal_id, **retry):
        self.calls.append(("items", portfolio_id, goal_id))
        return self.items.get((portfolio_id, goal_id), (200, []))

    def reviews(self, token, portfolio_id, **retry):
        self.calls.append(("reviews", portfolio_id))
        return self.review_lists.get(portfolio_id, (500, None))

    def received_invitations(self, token, own, **retry):
        return 200, self.invitations

    def shared_with_me(self, token):
        """Spec 015: the shared portfolios (none by default)."""
        return self.shares_status, self.shares


class TestParsing(unittest.TestCase):  # F2
    def test_level_date_and_assessor(self):
        row = parse_feedback_item(item("teacher", "a", "2026-10-01"), "OC", {})
        self.assertEqual((row["kind"], row["level"], row["date"], row["assessor"]),
                         ("assessed", "0", "2026-10-01", "Joost Hendriks"))
        self.assertEqual(row["text"], "<p>Goed gepland</p>")   # spec 037, F1

    def test_self_evaluation_has_no_assessor(self):
        row = parse_feedback_item(item("self", "b", "2026-10-01", reviewer="Student"), "OC", {})
        self.assertEqual((row["kind"], row["assessor"]), ("self", None))

    def test_status_from_received_requests_wins(self):
        row = parse_feedback_item(item("self", "b", "2026-10-01", rid=7, scored=False), "OC", {7: "denied"})
        self.assertEqual(row["review_request_status"], "denied")
        row = parse_feedback_item(item("self", "b", "2026-10-01", rid=8, scored=False), "OC", {})
        self.assertEqual(row["review_request_status"], "not_scored")

    def test_sub_criteria_are_skipped(self):
        self.assertIsNone(parse_feedback_item(dict(item("teacher", "b", "2026-10-01"), type="sub_criterion_evaluation"), "OC", {}))

    def test_helpers(self):
        self.assertIsNone(resolve_level({"level": None, "level_set": LEVELS}))
        self.assertEqual(resolve_date({"evaluation": {"submitted_at": "2026-03-04T00:00:00Z"}}), "2026-03-04")
        self.assertEqual(resolve_date({}), "")

    def test_updated_text(self):  # F8
        self.assertEqual(updated_text(None, NOW), "Nog niet opgehaald")
        self.assertTrue(updated_text(NOW, NOW).startswith("Bijgewerkt om "))
        self.assertIn("Bijgewerkt op", updated_text(datetime(2026, 11, 7, 12, tzinfo=timezone.utc), NOW))


class TestGoalNames(unittest.TestCase):  # F14
    def test_spelling_variants_of_a_skill(self):
        for name in ("Overzicht creëren", "Overzicht Creëren", "Overzicht Creëeren", "Overzicht Cre\u0065\u0308ren",
                     "  overzicht   creëren "):
            self.assertEqual(skill_for_goal_name(name), "OC", repr(name))
        for name in ("Pro-actief handelen", "Pro-actief Handelen", "Proactief Handelen"):
            self.assertEqual(skill_for_goal_name(name), "PH", name)
        for name, code in (("Kritisch Oordelen", "KO"), ("Juiste Kennis Ontwikkelen", "JKO"),
                           ("Flexibel Opstellen", "FO"), ("Kwalitatief Product Maken", "KPM")):
            self.assertEqual(skill_for_goal_name(name), code)

    def test_every_skill_and_no_other_goals(self):
        for code, name in NAMES.items():
            self.assertEqual(skill_for_goal_name(name), code)
        for name in ("Onderzoeken - Kritisch denken", "Beroepstaak - Software Realiseren", "Sprint Reflectie",
                     "OC", "", None, "Boodschap delenX", "Plannenmaker", "Reflecterend schrijven"):
            self.assertIsNone(skill_for_goal_name(name), name)

    def test_start_of_the_name_is_enough(self):   # F14, HCAI
        for name, code in (("Boodschap delen (HCAI) - semester 1", "BD"), ("Boodschap Delen(HCAI)", "BD"),
                           ("Plannen - semester 2", "PL"), ("Overzicht Creëeren (HCAI) – semester 1", "OC"),
                           ("Pro-actief handelen: HCAI", "PH"), ("Kwalitatief product maken HCAI s1", "KPM"),
                           ("Samenwerken met andere functies en afdelingen", "SW")):   # chosen by the user
            self.assertEqual(skill_for_goal_name(name), code, name)


class FetchTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database = str(Path(self.tmp.name) / "test.sqlite3")
        db.init_db(self.database)
        db.set_setting(self.database, "portflow_portfolio_id", "500")
        self.api = FakeApi()
        self.connection = FakeConnection()
        self.fetcher = Fetcher(self.database, self.connection, api=self.api, spawn=lambda work: work(),
                               now=lambda: NOW)

    def tearDown(self):
        self.tmp.cleanup()

    def sql(self, query, args=()):
        conn = sqlite3.connect(self.database)
        try:
            with conn:
                return conn.execute(query, args).fetchall()
        finally:
            conn.close()

    def add_student(self, name, portfolios, user_id, demo=False):
        student_id = self.sql("INSERT INTO students (name, portflow_user_id, is_demo) VALUES (?, ?, ?) RETURNING id",
                              (name, user_id, int(demo)))[0][0]
        for portfolio in portfolios:
            self.sql("INSERT INTO student_portfolios (student_id, portfolio_id) VALUES (?, ?)", (student_id, portfolio))
        return student_id

    def skill_goals(self, portfolio):
        goals = [{"id": 1, "name": "Overzicht creëren"}, {"id": 2, "name": "Kwalitatief Product Maken"},
                 {"id": 3, "name": "Semester roadmap"}]
        self.api.goals_by_portfolio[portfolio] = (200, goals)


class TestFetchRound(FetchTestCase):
    def test_only_skill_goals_and_no_demo_students(self):  # F1
        self.add_student("Sem Bakker", [101], 11)
        self.add_student("Demo Student", [102], 12, demo=True)
        self.skill_goals(101)
        self.assertTrue(self.fetcher.start())
        self.assertEqual(sorted(c for c in self.api.calls if c[0] == "items"), [("items", 101, 1), ("items", 101, 2)])
        self.assertNotIn(("goals", 102), self.api.calls)

    def test_old_and_new_goals_of_one_skill_both_count_once(self):  # F14
        student = self.add_student("Sem Bakker", [101], 11)
        self.api.goals_by_portfolio[101] = (200, [{"id": 1, "name": "Kritisch oordelen"}, {"id": 2, "name": "Kritisch Oordelen"},
                                                  {"id": 3, "name": "Proactief Handelen"}])
        self.api.items[(101, 1)] = (200, [item("coach", "b", "2026-06-01")])
        self.api.items[(101, 2)] = (200, [item("assessor", "c", "2026-11-16", rid=2)])
        self.api.items[(101, 3)] = (200, [item("coach", "b", "2026-11-10", rid=3)])
        self.fetcher.start()
        self.assertEqual(self.sql("SELECT skill, level FROM evaluations WHERE student_id = ? ORDER BY date", (student,)),
                         [("KO", "1"), ("PH", "1"), ("KO", "2")])

    def test_all_assessors_are_stored(self):  # F2
        student = self.add_student("Sem Bakker", [101], 11)
        self.skill_goals(101)
        self.api.items[(101, 1)] = (200, [item("teacher", "b", "2026-10-01", reviewer="Onbekende Beoordelaar")])
        self.fetcher.start()
        self.assertEqual(self.sql("SELECT skill, assessor FROM evaluations WHERE student_id = ?", (student,)),
                         [("OC", "Onbekende Beoordelaar")])

    def test_new_data_replaces_old(self):  # F4
        student = self.add_student("Sem Bakker", [101], 11)
        self.skill_goals(101)
        self.api.items[(101, 1)] = (200, [item("teacher", "b", "2026-10-01")])
        self.fetcher.start()
        self.api.items[(101, 1)] = (200, [])
        self.fetcher.start()
        self.assertEqual(self.sql("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (student,)), [(0,)])

    def test_404_marks_no_access_and_200_clears_it(self):  # F10
        student = self.add_student("Sem Bakker", [101], 11)
        self.api.goals_by_portfolio[101] = (404, None)
        self.fetcher.start()
        self.assertEqual(self.sql("SELECT has_access FROM students WHERE id = ?", (student,)), [(0,)])
        self.skill_goals(101)
        self.fetcher.start()
        self.assertEqual(self.sql("SELECT has_access FROM students WHERE id = ?", (student,)), [(1,)])

    def test_401_stops_and_keeps_data(self):  # F11
        student = self.add_student("Sem Bakker", [101], 11)
        self.skill_goals(101)
        self.api.items[(101, 1)] = (200, [item("teacher", "b", "2026-10-01")])
        self.fetcher.start()
        self.api.goals_by_portfolio[101] = (401, None)
        self.connection.token = "token"
        self.fetcher.start()
        self.assertTrue(self.connection.unauthorized)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (student,)), [(1,)])

    def test_other_errors_keep_old_data_and_are_reported(self):  # F12
        ok = self.add_student("Sem Bakker", [101], 11)
        bad = self.add_student("Noor Peters", [102], 12)
        self.skill_goals(101)
        self.skill_goals(102)
        self.api.items[(102, 1)] = (200, [item("teacher", "b", "2026-10-01")])
        self.fetcher.start()
        self.api.goals_by_portfolio[102] = (500, None)
        self.fetcher.start()
        self.assertEqual(json.loads(db.get_setting(self.database, S_LAST_FETCH_FAILED)), ["Noor Peters"])
        self.assertEqual(self.sql("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (bad,)), [(1,)])
        self.assertIsNotNone(self.sql("SELECT fetched_at FROM students WHERE id = ?", (ok,))[0][0])
        self.assertIn("Bijgewerkt om", self.fetcher.status()["text"])

    def test_not_connected_does_not_start(self):  # F13
        self.connection.token = None
        self.assertFalse(self.fetcher.start())
        self.assertFalse(self.fetcher.status()["can_start"])

    def test_one_round_at_a_time(self):  # F6
        held = []
        self.fetcher.spawn = held.append
        self.assertTrue(self.fetcher.start())
        self.assertFalse(self.fetcher.start())
        self.assertIn("Ophalen", self.fetcher.status()["text"])
        held[0]()
        self.assertFalse(self.fetcher.status()["running"])


def review(rid, updated="2026-11-01T10:00:00.000Z"):
    return {"id": rid, "updated_at": updated, "role": "coach"}


class TestSignature(unittest.TestCase):  # spec 042
    def test_signature_changes_on_add_edit_and_remove(self):
        base = reviews_signature([review(1), review(2)])
        self.assertEqual(base, reviews_signature([review(2), review(1)]))   # order does not matter
        self.assertNotEqual(base, reviews_signature([review(1), review(2), review(3)]))
        self.assertNotEqual(base, reviews_signature([review(1), review(2, "2026-11-20T09:00:00.000Z")]))
        self.assertNotEqual(base, reviews_signature([review(1)]))

    def test_unusable_list_has_no_signature(self):  # F2
        self.assertIsNone(reviews_signature(None))
        self.assertIsNone(reviews_signature([{"updated_at": "x"}]))

    def test_is_unchanged(self):
        sig = reviews_signature([review(1)])
        student = {"fetched_at": "2026-11-09", "portfolios": [101], "signatures": {101: sig}}
        self.assertTrue(is_unchanged(student, {101: sig}))
        self.assertFalse(is_unchanged(dict(student, fetched_at=None), {101: sig}))   # never fetched
        self.assertFalse(is_unchanged(student, {101: None}))                         # list failed
        self.assertFalse(is_unchanged(dict(student, signatures={101: None}), {101: None}))


class TestReviewsPaging(unittest.TestCase):  # spec 042
    def test_a_short_page_is_the_last(self):
        full = [{"id": i} for i in range(50)]
        pages = [(200, full), (200, [{"id": 50}])]
        with mock.patch.object(portflow_api, "_get_json_with_retry", side_effect=pages) as get:
            status, items = portflow_api.reviews("t", 101)
        self.assertEqual((status, len(items), get.call_count), (200, 51, 2))   # no call for an empty page

    def test_every_list_stops_at_a_short_page(self):  # also goals, feedback items, collections, ...
        with mock.patch.object(portflow_api, "_get_json_with_retry", return_value=(200, [{"id": 1}])) as get:
            self.assertEqual(portflow_api.goals("t", 101), (200, [{"id": 1}]))
        self.assertEqual(get.call_count, 1)

    def test_evaluations_are_indexed(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = str(Path(tmp) / "test.sqlite3")
            db.init_db(database)
            conn = sqlite3.connect(database)
            plan = " ".join(str(r) for r in conn.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM evaluations WHERE student_id = 1 AND review_request_id = 2"))
            conn.close()
        self.assertIn("USING INDEX", plan)

    def test_an_error_gives_none(self):
        with mock.patch.object(portflow_api, "_get_json_with_retry", return_value=(500, None)):
            self.assertEqual(portflow_api.reviews("t", 101), (500, None))


class TestSkipUnchanged(FetchTestCase):  # spec 042
    def setUp(self):
        super().setUp()
        self.sem = self.add_student("Sem Bakker", [101], 11)
        self.noor = self.add_student("Noor Peters", [102], 12)
        for portfolio in (101, 102):
            self.skill_goals(portfolio)
            self.api.review_lists[portfolio] = (200, [review(1), review(2)])
        self.api.items[(101, 1)] = (200, [item("teacher", "b", "2026-10-01")])
        self.api.items[(102, 1)] = (200, [item("self", "b", "2026-10-01", rid=7, scored=False)])
        self.fetcher.start()   # first round: everyone fully, fingerprints stored
        self.api.calls.clear()

    def full_fetches(self):
        return sorted({c[1] for c in self.api.calls if c[0] == "goals"})

    def test_only_changed_students_are_fetched(self):  # F1
        self.api.review_lists[102] = (200, [review(1), review(2, "2026-11-20T09:00:00.000Z")])
        self.fetcher.start()
        self.assertEqual(self.full_fetches(), [102])
        self.assertIn(("reviews", 101), self.api.calls)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (self.sem,)), [(1,)])

    def test_nothing_changed_means_one_call_per_portfolio(self):  # F1, F4
        self.fetcher.start()
        self.assertEqual(sorted(self.api.calls), [("reviews", 101), ("reviews", 102)])
        self.assertEqual((self.fetcher.done, self.fetcher.total, self.fetcher.skipped), (2, 2, 2))

    def test_removed_review_fetches_and_removes(self):  # F1
        self.api.review_lists[101] = (200, [review(1)])
        self.api.items[(101, 1)] = (200, [])
        self.fetcher.start()
        self.assertEqual(self.full_fetches(), [101])
        self.assertEqual(self.sql("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (self.sem,)), [(0,)])

    def test_failing_review_list_fetches_fully(self):  # F2
        self.api.review_lists[101] = (500, None)
        self.fetcher.start()
        self.assertEqual(self.full_fetches(), [101])

    def test_unauthorized_review_list_stops_the_round(self):  # F2, spec 005 F11
        self.api.review_lists[101] = (401, None)
        self.fetcher.start()
        self.assertTrue(self.connection.unauthorized)

    def test_failed_fetch_clears_nothing_and_is_tried_again(self):  # spec 005 F4, F12
        self.api.review_lists[101] = (200, [review(1), review(3)])
        self.api.goals_by_portfolio[101] = (500, None)
        self.fetcher.start()
        self.api.goals_by_portfolio.pop(101); self.skill_goals(101)
        self.api.calls.clear()
        self.fetcher.start()
        self.assertEqual(self.full_fetches(), [101])

    def test_shift_click_fetches_everyone(self):  # F3
        self.fetcher.start(full=True)
        self.assertEqual(self.full_fetches(), [101, 102])

    def test_relinked_student_is_fetched_fully(self):  # F1: no fetched_at
        self.sql("UPDATE students SET fetched_at = NULL WHERE id = ?", (self.noor,))
        self.fetcher.start()
        self.assertEqual(self.full_fetches(), [102])

    def test_text_tells_how_many_were_new(self):  # F4
        self.assertTrue(self.fetcher.status()["text"].endswith(" · 2 nieuw"))   # first round: everyone
        self.api.review_lists[102] = (200, [review(1), review(3)])
        self.fetcher.start()
        self.assertTrue(self.fetcher.status()["text"].endswith(" · 1 nieuw"))
        self.fetcher.start()
        self.assertTrue(self.fetcher.status()["text"].endswith(" · niets nieuw"))
        self.fetcher.start(full=True)
        self.assertNotIn("nieuw", self.fetcher.status()["text"])

    def test_progress_text_while_checking(self):  # F4
        held = []
        self.fetcher.spawn = held.append
        self.fetcher.start()
        self.fetcher.total, self.fetcher.done = 30, 12
        self.assertEqual(self.fetcher.status()["text"], "Controleren… 12 van 30")
        held[0]()
        self.fetcher.start(full=True)
        self.fetcher.total, self.fetcher.done = 30, 4
        self.assertEqual(self.fetcher.status()["text"], "Ophalen… 4 van 30 studenten")
        held[1]()

    def test_denied_request_is_updated_for_a_skipped_student(self):  # F5
        self.api.invitations = [{"review_request_id": 7, "status": "denied"}]
        self.fetcher.start()
        self.assertEqual(self.full_fetches(), [])
        self.assertEqual(self.sql("SELECT review_request_status FROM evaluations WHERE student_id = ?", (self.noor,)),
                         [("denied",)])


if __name__ == "__main__":
    unittest.main()
