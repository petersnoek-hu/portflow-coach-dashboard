"""Tests for fetching evaluations (spec 005). A fake Portflow; no real calls."""

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from dashboard import db
from dashboard.portflow_fetch import (
    S_LAST_FETCH_FAILED, Fetcher, parse_feedback_item, resolve_date, resolve_level, updated_text,
)

NOW = datetime(2026, 11, 9, 13, 32, tzinfo=timezone.utc)
LEVELS = [{"id": "a", "label": "Startniveau"}, {"id": "b", "label": "1"}, {"id": "c", "label": "2"}]


def item(role, level, day, reviewer="Joost Hendriks", rid=1, scored=True):
    return {
        "type": "criterion_evaluation", "role": role, "date": f"{day}T10:00:00.000Z",
        "evaluation": {"level": level, "level_set": LEVELS, "review_request_id": rid,
                       "review_request_title": "OC 1ste evaluatie", "review_request_scored": scored,
                       "comment": "<p>niet bewaren</p>", "reviewer": {"name": reviewer}},
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

    def goals(self, token, portfolio_id, **retry):
        self.calls.append(("goals", portfolio_id))
        return self.goals_by_portfolio.get(portfolio_id, (200, []))

    def feedback_items(self, token, portfolio_id, goal_id, **retry):
        self.calls.append(("items", portfolio_id, goal_id))
        return self.items.get((portfolio_id, goal_id), (200, []))

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
        self.assertNotIn("comment", row)

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


if __name__ == "__main__":
    unittest.main()
