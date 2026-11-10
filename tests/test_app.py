"""Tests for the shell (spec 002). Run with: python -m unittest"""

import re
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from app import port_is_free
from dashboard import create_app
from dashboard.routes import PAGES, dutch_date, greeting


class ShellTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "data" / "test.sqlite3"
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    @contextmanager
    def db(self):
        """Open the test database, commit and always close it."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()


class TestPages(ShellTestCase):
    def test_database_is_created_without_guilds(self):  # F3; spec 018
        self.assertTrue(self.db_path.exists())
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM guilds").fetchone()[0], 0)
            self.assertIsNone(conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'professional_roles'").fetchone())
            conn.execute("INSERT INTO guilds (code, name, role_name) VALUES ('FE', 'Front-end gilde', 'Front-end developer')")
        create_app(self.db_path)  # a second start reuses the database and adds no guilds
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM guilds").fetchone()[0], 1)

    def test_every_page_loads_with_shell(self):  # F5, F7, F8, F9
        with self.db() as conn:  # a student, so Overzicht shows its placeholder (spec 004, F1)
            conn.execute("INSERT INTO students (name) VALUES ('Verzonnen Student')")
        for page in PAGES:
            with self.subTest(page=page["label"]):
                response = self.client.get(page["path"])
                html = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn("portflow", html)
                self.assertIn("Niet verbonden", html)
                self.assertIn("Gebruiker", html)
                self.assertIn('aria-current="page"', html)
                self.assertRegex(html, rf'is-active"\s+href="{re.escape(page["path"])}"')
                self.assertIn(page["intro"], html)
                if page["placeholder"]:
                    self.assertIn(page["placeholder"], html)

    def test_management_menu_group(self):  # F17
        html = self.client.get("/").get_data(as_text=True)
        group = re.search(r'<details class="nav-group"([^>]*)>(.*?)</details>', html, re.S)
        self.assertNotIn("open", group.group(1))
        self.assertIn("Beheer", group.group(2))
        order = re.findall(r'href="(/[a-z]+)"', group.group(2))
        self.assertEqual(order, ["/semesters", "/gildes", "/gildemeesters", "/coaches", "/projecten",
                                 "/kolommen"])
        outside = html.replace(group.group(0), "")
        for path in ("/", "/studenten", "/evaluaties", "/instellingen"):
            self.assertIn(f'href="{path}"', outside)
        html = self.client.get("/gildes").get_data(as_text=True)
        group = re.search(r'<details class="nav-group"([^>]*)>(.*?)</details>', html, re.S)
        self.assertIn("open", group.group(1))
        self.assertIn('aria-current="page"', group.group(2))

    def test_no_external_resources(self):  # F14
        html = self.client.get("/").get_data(as_text=True)
        css = (Path(self.app.static_folder) / "app.css").read_text()
        self.assertNotRegex(html, r'(src|href)="https?://')
        self.assertNotIn("http", css)

    def test_overview_header_in_dutch(self):
        self.assertEqual(dutch_date(datetime(2026, 11, 9)), "maandag 9 november")
        self.assertEqual(greeting(datetime(2026, 11, 9, 9)), "Goedemorgen")
        self.assertEqual(greeting(datetime(2026, 11, 9, 14)), "Goedemiddag")
        self.assertEqual(greeting(datetime(2026, 11, 9, 20)), "Goedenavond")

    def test_requests_from_other_hosts_or_sites_are_refused(self):
        self.assertEqual(self.client.get("/", headers={"Host": "evil.example"}).status_code, 400)
        response = self.client.post("/instellingen/demodata/laden", headers={"Origin": "https://evil.example"})
        self.assertEqual(response.status_code, 403)


class TestDemoData(ShellTestCase):
    def add_real_student(self):
        with self.db() as conn:
            conn.execute("INSERT INTO students (name, semester) VALUES ('Echte Student', 3)")

    def test_load_shows_counts_and_banner(self):  # F10, F12
        self.assertNotIn("Je bekijkt demodata", self.client.get("/").get_data(as_text=True))
        response = self.client.post("/instellingen/demodata/laden", follow_redirects=True)
        html = response.get_data(as_text=True)
        self.assertIn("Je bekijkt demodata", html)
        self.assertRegex(html, r"Studenten</th><td>\d+")
        self.assertRegex(html, r"Demodata laden\s*</button>")
        self.assertIn("disabled", html)

    def test_loading_twice_adds_nothing(self):  # F10
        self.client.post("/instellingen/demodata/laden")
        with self.db() as conn:
            before = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        self.client.post("/instellingen/demodata/laden")
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM students").fetchone()[0], before)

    def test_remove_asks_for_confirmation_first(self):  # F11
        self.client.post("/instellingen/demodata/laden")
        html = self.client.get("/instellingen?bevestig=demodata-verwijderen").get_data(as_text=True)
        self.assertIn("Alle demodata verwijderen?", html)
        self.assertIn("Annuleren", html)

    def test_remove_keeps_real_records(self):  # F11, F12
        self.add_real_student()
        with self.db() as conn:  # a real guild stays; the demo only removes the guilds it added
            conn.execute("INSERT INTO guilds (code, name, role_name) VALUES ('FE', 'Front-end gilde', 'Front-end developer')")
        self.client.post("/instellingen/demodata/laden")
        response = self.client.post("/instellingen/demodata/verwijderen", follow_redirects=True)
        self.assertNotIn("Je bekijkt demodata", response.get_data(as_text=True))
        with self.db() as conn:
            names = [row[0] for row in conn.execute("SELECT name FROM students")]
            for table in ("squads", "staff", "evaluations"):
                self.assertEqual(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0, table)
            self.assertEqual([r[0] for r in conn.execute("SELECT code FROM guilds")], ["FE"])
        self.assertEqual(names, ["Echte Student"])


class TestStart(unittest.TestCase):
    def test_port_in_use_is_detected(self):  # F4
        import socket

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            sock.listen()
            self.assertFalse(port_is_free(sock.getsockname()[1]))


if __name__ == "__main__":
    unittest.main()
