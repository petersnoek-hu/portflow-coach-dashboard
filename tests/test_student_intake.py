"""Tests for spec 004 (Studenten toevoegen): the empty state, the chooser and
"Uit Portflow kiezen". No real browser or Portflow calls.
"""

import base64
import json
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from dashboard import create_app
from dashboard import db, portflow_api, student_intake
from dashboard.portflow_login import LoginError
from dashboard.portflow_connection import State


def make_token(expires: datetime) -> str:
    """A fake JWT (not signed) with only an 'exp' claim, like test_portflow.py."""

    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

    return f"{part({'alg': 'none'})}.{part({'exp': int(expires.timestamp())})}.signature"


class FakeApi:
    """Stands in for dashboard.portflow_api: no real network calls in tests."""

    def __init__(self):
        self.valid_tokens: set[str] = set()
        self.shares: list[dict] = []
        self.shares_status = 200

    def check_token(self, token):
        return 200 if token in self.valid_tokens else 401

    def own_portfolio_error(self, token, portfolio_id):
        return None

    def own_name(self, token, portfolio_id):
        return "Anna Coach"

    def shared_with_me(self, token):
        return self.shares_status, self.shares


class StudentIntakeTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "data" / "test.sqlite3"
        self.app = create_app(self.db_path, env_file=Path(self.tmp.name) / ".env")
        self.client = self.app.test_client()
        self.connection = self.app.extensions["portflow"]
        self.api = FakeApi()
        self.connection.api = self.api
        # Never open a real Chrome window from a test: a login attempt fails at once.
        self.connection.capture = self.no_browser
        self.connection.spawn = lambda work: work()

    @staticmethod
    def no_browser(*args, **kwargs):
        raise LoginError("cancelled", "Geen browser in tests.")

    def tearDown(self):
        self.tmp.cleanup()

    @contextmanager
    def db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def connect(self, hours=8.0):
        """Get the connection into State.CONNECTED via the existing paste-token path (F5)."""
        token = make_token(datetime.now(timezone.utc) + timedelta(hours=hours))
        self.api.valid_tokens.add(token)
        error = self.connection.paste_token(token, "23588")
        assert error is None, error

    def add_student(self, name, semester=None, portflow_user_id=None, coach_id=None):
        with self.db() as conn:
            conn.execute(
                "INSERT INTO students (name, semester, portflow_user_id, coach_id) VALUES (?, ?, ?, ?)",
                (name, semester, portflow_user_id, coach_id),
            )

    def fragment_html(self):
        return self.client.get(
            "/studenten/toevoegen/portflow/lijst", query_string={"fragment": "1"}
        ).get_data(as_text=True)


SHARES = [
    {"portfolio_id": 201, "inviter": {"id": 11, "name": "Sem Bakker", "current_role": "student"}},
    {"portfolio_id": 202, "inviter": {"id": 12, "name": "Noor Peters", "current_role": "student"}},
]

SHARES_WITH_DUPLICATE = SHARES + [
    {"portfolio_id": 203, "inviter": {"id": 11, "name": "Sem Bakker", "current_role": "student"}},
    {"portfolio_id": 204, "inviter": {"id": 13, "name": "Een Beoordelaar", "current_role": "coach"}},
]


class TestEmptyState(StudentIntakeTestCase):
    def test_zero_students_shows_empty_state(self):  # F1
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("Nog geen studenten", html)
        self.assertIn('href="/studenten/toevoegen"', html)

    def test_one_student_hides_empty_state_and_shows_permanent_button(self):  # F2
        self.add_student("Lieke Jansen")
        html = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("Nog geen studenten", html)
        self.assertIn("+ Student toevoegen", html)

    def test_permanent_button_also_on_students_page(self):  # F2
        html = self.client.get("/studenten").get_data(as_text=True)
        self.assertIn("+ Student toevoegen", html)


class TestChooser(StudentIntakeTestCase):
    def test_shows_four_methods_two_disabled(self):  # F3; Excel works since spec 013
        html = self.client.get("/studenten/toevoegen").get_data(as_text=True)
        for title in ("Uit Portflow kiezen", "Excelbestand uploaden", "Namen typen of plakken",
                      "CSV of Excelcellen plakken"):
            self.assertIn(title, html)
        self.assertEqual(html.count("Binnenkort beschikbaar"), 2)

    def test_back_without_confirming_adds_nothing(self):  # F4
        self.client.get("/studenten/toevoegen")
        self.client.get("/studenten/toevoegen/portflow")
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM students").fetchone()[0], 0)


class TestPortflowEntry(StudentIntakeTestCase):
    def test_not_connected_shows_connect_panel(self):  # F5
        html = self.client.get("/studenten/toevoegen/portflow").get_data(as_text=True)
        self.assertIn("Verbinden met Portflow", html)
        self.assertIn('action="/portflow/verbinden"', html)

    def test_start_begins_login_when_not_connected(self):  # F5
        response = self.client.post("/studenten/toevoegen/portflow/starten")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/studenten/toevoegen/portflow", response.headers["Location"])

    def test_start_skips_reconnecting_when_already_connected(self):  # F5
        self.connect()
        before = self.connection.state
        self.client.post("/studenten/toevoegen/portflow/starten")
        self.assertEqual(self.connection.state, before)

    def test_connected_shows_loading_shell_not_the_list_yet(self):  # F6 (technical: loading indicator)
        self.connect()
        self.api.shares = SHARES
        html = self.client.get("/studenten/toevoegen/portflow").get_data(as_text=True)
        self.assertIn("portflow-list-loading", html)
        self.assertIn("fragment=1", html)
        self.assertNotIn("Sem Bakker", html)

    def test_needs_login_with_valid_token_goes_straight_to_loading(self):  # F5
        self.connect()
        self.connection.state = State.NEEDS_LOGIN
        html = self.client.get("/studenten/toevoegen/portflow").get_data(as_text=True)
        self.assertIn("portflow-list-loading", html)
        self.assertNotIn("Verbinden met Portflow", html)


class TestPortflowList(StudentIntakeTestCase):
    """GET /studenten/toevoegen/portflow/lijst: the actual (slow) share fetch."""

    def test_full_page_without_fragment_param_includes_shell(self):
        self.connect()
        self.api.shares = SHARES
        html = self.client.get("/studenten/toevoegen/portflow/lijst").get_data(as_text=True)
        self.assertIn("<html", html)
        self.assertIn("Sem Bakker", html)

    def test_fragment_param_returns_bare_fragment(self):
        self.connect()
        self.api.shares = SHARES
        html = self.fragment_html()
        self.assertNotIn("<html", html)
        self.assertIn("Sem Bakker", html)

    def test_lists_grouped_students(self):  # F6, F9
        self.connect()
        self.api.shares = SHARES_WITH_DUPLICATE
        html = self.fragment_html()
        self.assertIn("Sem Bakker", html)
        self.assertIn("Noor Peters", html)
        self.assertNotIn("Een Beoordelaar", html)  # not a student
        self.assertEqual(html.count('name="portflow_user_id"'), 2)  # Sem's 2 shares -> 1 row

    def test_already_tracked_student_is_disabled(self):  # F10
        self.connect()
        self.api.shares = SHARES
        self.add_student("Sem Bakker", portflow_user_id=11)
        html = self.fragment_html()
        self.assertIn("Al gevolgd", html)
        self.assertRegex(html, r'value="11"\s+disabled')

    def test_unlinked_student_with_same_name_is_flagged_but_selectable(self):  # F10
        self.connect()
        self.api.shares = SHARES
        self.add_student("sem   bakker")  # same name, different case/spacing, no Portflow link
        html = self.fragment_html()
        self.assertIn("Mogelijk al gevolgd (zelfde naam)", html)
        self.assertNotRegex(html, r'value="11"\s+disabled')  # still selectable

    def test_unauthorized_marks_connection_expired(self):  # F7
        self.connect()
        self.api.shares_status = 401
        html = self.fragment_html()
        self.assertEqual(str(self.connection.state), "expired")
        self.assertIn("Opnieuw inloggen", html)

    def test_unreachable_shows_retry_message(self):  # F7
        self.connect()
        self.api.shares_status = 0
        html = self.fragment_html()
        self.assertIn("niet bereikbaar", html.lower())

    def test_empty_share_list_shows_explanation(self):  # F8
        self.connect()
        self.api.shares = []
        html = self.fragment_html()
        self.assertIn("nog geen gedeelde portfolio", html.lower())

    def test_shows_coach_checkbox_checked_by_default(self):  # F11
        self.connect()
        self.api.shares = SHARES
        html = self.fragment_html()
        self.assertRegex(html, r'name="coach" value="1" checked')
        self.assertIn("Ik ben hun coach", html)


class TestSubmit(StudentIntakeTestCase):
    def test_confirm_adds_selected_students_with_user_as_coach_by_default(self):  # F11, F12
        self.connect()
        self.api.shares = SHARES
        response = self.client.post(
            "/studenten/toevoegen/portflow",
            data={"portflow_user_id": ["11"], "coach": "1"},
            follow_redirects=False,
        )
        self.assertIn("toegevoegd=1", response.headers["Location"])
        self.assertIn("gekoppeld=0", response.headers["Location"])
        with self.db() as conn:
            row = conn.execute(
                "SELECT s.name, s.semester, (SELECT COUNT(*) FROM student_guilds g WHERE g.student_id = s.id), "
                "s.portflow_user_id, st.name FROM students s JOIN staff st ON st.id = s.coach_id WHERE s.name = ?",
                ("Sem Bakker",),
            ).fetchone()
            self.assertEqual(tuple(row), ("Sem Bakker", None, 0, 11, "Anna Coach"))
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM students WHERE name = 'Noor Peters'").fetchone()[0], 0
            )

    def test_unchecking_coach_leaves_coach_empty(self):  # F11
        self.connect()
        self.api.shares = SHARES
        self.client.post("/studenten/toevoegen/portflow", data={"portflow_user_id": ["11"]})  # no "coach" field
        with self.db() as conn:
            coach_id = conn.execute("SELECT coach_id FROM students WHERE name = 'Sem Bakker'").fetchone()[0]
        self.assertIsNone(coach_id)

    def test_stores_all_shared_portfolios_of_one_student(self):  # F6, F11
        self.connect()
        self.api.shares = SHARES_WITH_DUPLICATE
        self.client.post("/studenten/toevoegen/portflow", data={"portflow_user_id": ["11"]})
        with self.db() as conn:
            student_id = conn.execute("SELECT id FROM students WHERE name = 'Sem Bakker'").fetchone()[0]
            portfolio_ids = {
                row[0] for row in conn.execute(
                    "SELECT portfolio_id FROM student_portfolios WHERE student_id = ?", (student_id,)
                )
            }
        self.assertEqual(portfolio_ids, {201, 203})

    def test_links_existing_unlinked_student_with_same_name_instead_of_duplicating(self):  # F10
        self.connect()
        self.api.shares = SHARES
        self.add_student("sem bakker", semester=3, coach_id=None)
        response = self.client.post(
            "/studenten/toevoegen/portflow", data={"portflow_user_id": ["11"]}, follow_redirects=False
        )
        self.assertIn("toegevoegd=0", response.headers["Location"])
        self.assertIn("gekoppeld=1", response.headers["Location"])
        with self.db() as conn:
            rows = conn.execute("SELECT name, semester, portflow_user_id FROM students").fetchall()
        self.assertEqual([tuple(r) for r in rows], [("sem bakker", 3, 11)])  # linked, not duplicated; semester kept

    def test_confirmation_message_mentions_added_and_linked(self):  # F12
        self.connect()
        self.api.shares = SHARES
        self.add_student("sem bakker")  # will be linked, not added
        response = self.client.post(
            "/studenten/toevoegen/portflow",
            data={"portflow_user_id": ["11", "12"]},
            follow_redirects=True,
        )
        html = response.get_data(as_text=True)
        self.assertIn("1 student toegevoegd", html)
        self.assertIn("1 bestaande student gekoppeld", html)
        self.assertIn("Nog in te delen", html)

    def test_cannot_add_already_tracked_student_twice(self):  # F10
        self.connect()
        self.api.shares = SHARES
        self.add_student("Sem Bakker", portflow_user_id=11)
        self.client.post("/studenten/toevoegen/portflow", data={"portflow_user_id": ["11", "12"]})
        with self.db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM students WHERE portflow_user_id = 11").fetchone()[0]
        self.assertEqual(count, 1)

    def test_nothing_selected_adds_nothing(self):
        self.connect()
        self.api.shares = SHARES
        response = self.client.post("/studenten/toevoegen/portflow", data={}, follow_redirects=False)
        self.assertIn("toegevoegd=0", response.headers["Location"])
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM students").fetchone()[0], 0)


class TestGroupSharedStudents(unittest.TestCase):
    def test_groups_by_inviter_and_filters_on_role(self):  # F6
        result = student_intake.group_shared_students(SHARES_WITH_DUPLICATE)
        by_id = {c["portflow_user_id"]: c for c in result}
        self.assertEqual(set(by_id), {11, 12})
        self.assertEqual(by_id[11]["portfolio_ids"], [201, 203])
        self.assertEqual(by_id[11]["name"], "Sem Bakker")
        self.assertEqual(by_id[11]["initials"], "SB")

    def test_sorted_by_name(self):
        result = student_intake.group_shared_students(SHARES)
        self.assertEqual([c["name"] for c in result], ["Noor Peters", "Sem Bakker"])


class TestNormalizeName(unittest.TestCase):
    def test_ignores_case_and_extra_whitespace(self):
        self.assertEqual(student_intake.normalize_name("  Sem   Bakker "), student_intake.normalize_name("sem bakker"))


class TestSharedWithMe(unittest.TestCase):
    """dashboard.portflow_api.shared_with_me: pagination (always <=20/page) and retry
    (architectuur.md#portflow-api)."""

    def test_paginates_to_an_empty_page_not_a_short_one(self):
        # The real endpoint caps at 20 per page regardless of the requested per_page (50),
        # so a full page of 20 must NOT be treated as "the last page".
        pages = {1: [{"id": "a"}] * 20, 2: [{"id": "b"}] * 20, 3: [{"id": "c"}] * 5, 4: []}

        def fake_get_json(path, token, timeout=15):
            page = int(path.split("page=")[1].split("&")[0])
            return 200, pages[page]

        with patch.object(portflow_api, "get_json", side_effect=fake_get_json):
            status, items = portflow_api.shared_with_me("t")
        self.assertEqual(status, 200)
        self.assertEqual(len(items), 45)

    def test_retries_other_errors_then_succeeds(self):
        calls = {"n": 0}

        def fake_get_json(path, token, timeout=15):
            calls["n"] += 1
            return (200, []) if calls["n"] >= 3 else (500, None)

        with patch.object(portflow_api, "get_json", side_effect=fake_get_json), \
             patch.object(portflow_api.time, "sleep"):
            status, items = portflow_api.shared_with_me("t", retries=3, retry_delay_s=0)
        self.assertEqual((status, items), (200, []))
        self.assertEqual(calls["n"], 3)

    def test_401_and_404_are_not_retried(self):
        for code in (401, 404):
            with self.subTest(code=code):
                calls = {"n": 0}

                def fake_get_json(path, token, timeout=15, code=code):
                    calls["n"] += 1
                    return code, None

                with patch.object(portflow_api, "get_json", side_effect=fake_get_json):
                    status, items = portflow_api.shared_with_me("t")
                self.assertEqual(status, code)
                self.assertIsNone(items)
                self.assertEqual(calls["n"], 1)


class TestAddOrLinkStudentsFromPortflow(StudentIntakeTestCase):
    def test_adds_name_and_portfolios_only_without_coach(self):  # F11
        with self.db() as conn:
            added, linked = student_intake.add_or_link_students_from_portflow(
                conn, [{"name": "Sem Bakker", "portflow_user_id": 11, "portfolio_ids": [201, 203]}]
            )
            self.assertEqual((added, linked), (1, 0))
            row = conn.execute(
                "SELECT semester, squad_id, coach_id, (SELECT COUNT(*) FROM student_guilds) FROM students "
                "WHERE name = 'Sem Bakker'"
            ).fetchone()
            self.assertEqual(tuple(row), (None, None, None, 0))
            portfolios = {r[0] for r in conn.execute("SELECT portfolio_id FROM student_portfolios")}
            self.assertEqual(portfolios, {201, 203})

    def test_adds_with_coach_when_given(self):  # F11
        with self.db() as conn:
            conn.execute("INSERT INTO staff (name) VALUES ('Anna Coach')")
            coach_id = conn.execute("SELECT id FROM staff WHERE name = 'Anna Coach'").fetchone()[0]
            student_intake.add_or_link_students_from_portflow(
                conn, [{"name": "Sem Bakker", "portflow_user_id": 11, "portfolio_ids": []}], coach_id=coach_id
            )
            self.assertEqual(
                conn.execute("SELECT coach_id FROM students WHERE name = 'Sem Bakker'").fetchone()[0], coach_id
            )

    def test_links_instead_of_duplicating_same_name(self):  # F10
        self.add_student("sem bakker", semester=4)
        with self.db() as conn:
            added, linked = student_intake.add_or_link_students_from_portflow(
                conn, [{"name": "Sem Bakker", "portflow_user_id": 11, "portfolio_ids": [201]}]
            )
            self.assertEqual((added, linked), (0, 1))
            rows = conn.execute("SELECT name, semester, portflow_user_id FROM students").fetchall()
            self.assertEqual([tuple(r) for r in rows], [("sem bakker", 4, 11)])

    def test_tracked_portflow_ids(self):  # F10
        self.add_student("Sem Bakker", portflow_user_id=11)
        self.add_student("Zonder koppeling")
        with self.db() as conn:
            self.assertEqual(student_intake.tracked_portflow_ids(conn), {11})

    def test_unlinked_students_by_name_prefers_lowest_id(self):  # F10
        self.add_student("Sem Bakker")
        self.add_student("sem   bakker")
        self.add_student("Sem Bakker", portflow_user_id=99)  # already linked: excluded
        with self.db() as conn:
            first_id = conn.execute("SELECT MIN(id) FROM students").fetchone()[0]
            matches = student_intake.unlinked_students_by_name(conn)
        self.assertEqual(matches, {"sem bakker": first_id})

    def test_unlinked_students_by_name_ignores_demo_students(self):  # F10
        with self.db() as conn:
            conn.execute("INSERT INTO students (name, is_demo) VALUES ('Sem Bakker', 1)")
            matches = student_intake.unlinked_students_by_name(conn)
        self.assertEqual(matches, {})


class TestMigration(unittest.TestCase):
    """A database created before spec 004 gets the new column without losing data."""

    def test_adds_column_to_existing_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "test.sqlite3")
            conn = sqlite3.connect(path)
            with conn:
                conn.execute(
                    "CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT NOT NULL, semester INTEGER)"
                )
                conn.execute("INSERT INTO students (name, semester) VALUES ('Oud Studentje', 2)")
            conn.close()

            db.init_db(path)
            db.init_db(path)  # idempotent: running it twice must not fail or duplicate data

            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT name, semester, portflow_user_id FROM students").fetchone()
            conn.close()
        self.assertEqual((row["name"], row["semester"], row["portflow_user_id"]), ("Oud Studentje", 2, None))


if __name__ == "__main__":
    unittest.main()
