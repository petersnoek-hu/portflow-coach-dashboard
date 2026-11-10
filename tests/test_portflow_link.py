"""Tests for linking students to Portflow (spec 015). A fake Portflow; all names are invented."""

import base64
import json
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dashboard import create_app, db, portflow_link
from dashboard.portflow_fetch import S_UNLINKED, Fetcher


def share(user_id, name, portfolio_id):
    return {"portfolio_id": portfolio_id, "inviter": {"id": user_id, "name": name, "current_role": "student"}}


SHARES = [share(11, "Anna de Böer", 101), share(11, "Anna de Böer", 102), share(12, "Bram Visser", 103),
          share(13, "Cas Jansen", 104), share(14, "Cas Jansen", 105)]


def make_token(hours=8):
    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    exp = datetime.now(timezone.utc) + timedelta(hours=hours)
    return f"{part({'alg': 'none'})}.{part({'exp': int(exp.timestamp())})}.sig"


class FakeApi:
    def __init__(self):
        self.shares, self.status, self.valid = list(SHARES), 200, set()

    def shared_with_me(self, token):
        return self.status, self.shares

    def check_token(self, token):
        return 200 if token in self.valid else 401

    def own_portfolio_error(self, token, portfolio_id):
        return None

    def own_name(self, token, portfolio_id):
        return "Marieke Ploeg"

    def goals(self, token, portfolio_id, **retry):
        return 200, []

    def feedback_items(self, token, portfolio_id, goal_id, **retry):
        return 200, []

    def received_invitations(self, token, own, **retry):
        return 200, []


class LinkTestCase(unittest.TestCase):
    def setUp(self):
        portflow_link.clear_cache()
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.db_path = base / "data" / "test.sqlite3"
        self.app = create_app(self.db_path, env_file=base / ".env")
        self.client = self.app.test_client()
        self.connection = self.app.extensions["portflow"]
        self.connection.profile_dir = base / "profile"
        self.api = FakeApi()
        self.connection.api = self.api
        self.app.extensions["fetcher"].api = self.api
        self.app.extensions["fetcher"].spawn = lambda work: work()

    def tearDown(self):
        portflow_link.clear_cache()
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

    def connect(self):
        token = make_token()
        self.api.valid.add(token)
        self.assertIsNone(self.connection.paste_token(token, "23588"))

    def add(self, name, user_id=None):
        with self.db() as conn:
            return conn.execute("INSERT INTO students (name, portflow_user_id) VALUES (?, ?) RETURNING id",
                                (name, user_id)).fetchone()[0]

    def link_of(self, student_id):
        with self.db() as conn:
            user = conn.execute("SELECT portflow_user_id FROM students WHERE id = ?", (student_id,)).fetchone()[0]
            portfolios = [r[0] for r in conn.execute(
                "SELECT portfolio_id FROM student_portfolios WHERE student_id = ? ORDER BY portfolio_id", (student_id,))]
        return user, portfolios


class TestAutoLink(LinkTestCase):  # F1
    def test_unique_name_without_case_spaces_and_accents(self):
        anna = self.add("anna  de boer")
        with self.db() as conn:
            linked, unresolved = portflow_link.auto_link(conn, portflow_link.student_intake.group_shared_students(SHARES))
        self.assertEqual(linked, 1)
        self.assertEqual(self.link_of(anna), (11, [101, 102]))

    def test_two_portflow_students_with_the_same_name_are_not_linked(self):
        cas = self.add("Cas Jansen")
        with self.db() as conn:
            _, unresolved = portflow_link.auto_link(conn, portflow_link.student_intake.group_shared_students(SHARES))
        self.assertEqual(self.link_of(cas), (None, []))
        self.assertEqual(unresolved, ["Cas Jansen"])

    def test_already_linked_portflow_student_is_not_used_twice(self):
        self.add("Bram Visser", user_id=12)
        second = self.add("Bram Visser")
        with self.db() as conn:
            portflow_link.auto_link(conn, portflow_link.student_intake.group_shared_students(SHARES))
        self.assertEqual(self.link_of(second), (None, []))


class TestWhenLinking(LinkTestCase):
    def test_refresh_links_first_and_reports_unlinked(self):  # F2, F4
        anna, cas = self.add("Anna de Boer"), self.add("Cas Jansen")
        self.connect()
        self.assertTrue(self.app.extensions["fetcher"].start())
        self.assertEqual(self.link_of(anna)[0], 11)
        self.assertEqual(json.loads(db.get_setting(str(self.db_path), S_UNLINKED)), ["Cas Jansen"])
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("1 niet gekoppeld", html)
        self.assertIn("Niet gekoppeld aan Portflow: Cas Jansen", html)

    def test_refresh_continues_when_shared_list_fails(self):  # F2
        self.add("Anna de Boer")
        self.connect()
        self.api.status = 500
        self.assertTrue(self.app.extensions["fetcher"].start())
        self.assertIsNotNone(db.get_setting(str(self.db_path), "fetch_last_finished"))

    def test_after_excel_import(self):  # F3
        from tests.xlsx_maker import make_xlsx
        import io
        self.connect()
        response = self.client.post("/studenten/toevoegen/excel", content_type="multipart/form-data",
                                    data={"bestand": (io.BytesIO(make_xlsx({"Lijst": [["Naam"], ["Anna de Boer"]]})), "a.xlsx")})
        key = response.headers["Location"].rstrip("/").split("/")[-1]
        response = self.client.post(f"/studenten/toevoegen/excel/{key}/importeren", data={"nieuw": ["2"]})
        self.assertIn("1+gekoppeld+aan+Portflow", response.headers["Location"])
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT portflow_user_id FROM students").fetchone()[0], 11)


class TestManualLink(LinkTestCase):  # F5
    def test_choose_and_unlink(self):
        cas = self.add("Cas Jansen")
        with self.db() as conn:
            conn.execute("INSERT INTO evaluations (student_id, skill, kind, level, date) VALUES (?, 'OC', 'assessed', '1', '')", (cas,))
        self.connect()
        html = self.client.get(f"/studenten/{cas}/bewerken").get_data(as_text=True)
        self.assertIn('<option value="14"', html)
        self.client.post(f"/studenten/{cas}/bewerken", data={"name": "Cas Jansen", "portflow": "14"})
        self.assertEqual(self.link_of(cas), (14, [105]))
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0], 0)
        self.client.post(f"/studenten/{cas}/bewerken", data={"name": "Cas Jansen", "portflow": "geen"})
        self.assertEqual(self.link_of(cas), (None, []))

    def test_without_connection(self):
        cas = self.add("Cas Jansen")
        html = self.client.get(f"/studenten/{cas}/bewerken").get_data(as_text=True)
        self.assertIn("Verbind met Portflow om te koppelen.", html)
        self.assertNotIn('name="portflow"', html)


if __name__ == "__main__":
    unittest.main()
