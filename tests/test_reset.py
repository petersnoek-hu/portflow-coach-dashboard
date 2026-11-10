"""Tests for Alles verwijderen (spec 014). Uses a temporary database, .env and browser profile."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import create_app
from dashboard.portflow_token import TokenStore


class ResetTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.db_path = base / "data" / "test.sqlite3"
        self.env = base / ".env"
        self.app = create_app(self.db_path, env_file=self.env)
        self.client = self.app.test_client()
        self.connection = self.app.extensions["portflow"]
        self.profile = base / "data" / "browser-profile"
        self.connection.profile_dir = self.profile   # never the real browser profile
        self.profile.mkdir(parents=True)
        (self.profile / "Cookies").write_text("verzonnen")
        TokenStore(self.env).save("verzonnen.token.waarde")
        self.client.post("/instellingen/demodata/laden")
        self.client.post("/instellingen/semesterperiode", data={"start": "2026-09-01", "end": "2027-01-31"})

    def tearDown(self):
        self.tmp.cleanup()

    def count(self, table):
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        finally:
            conn.close()

    def settings(self, **query):
        return self.client.get("/instellingen", query_string=query).get_data(as_text=True)


class TestReset(ResetTestCase):
    def test_block_and_first_confirmation(self):  # F1, F2
        self.assertIn("Alles verwijderen…", self.settings())
        html = self.settings(bevestig="alles-verwijderen")
        self.assertIn("Alle gegevens verwijderen?", html)
        self.assertIn("14 studenten", html)
        self.assertIn("HU-login in het browserprofiel", html)
        self.assertEqual(self.count("students"), 14)   # nothing deleted yet

    def test_second_confirmation_needs_the_word(self):  # F3
        self.assertIn('name="bevestiging"', self.settings(bevestig="alles-verwijderen-2"))
        for word in ("", "verwijder", "ja"):
            response = self.client.post("/instellingen/alles-verwijderen", data={"bevestiging": word})
            self.assertIn("bevestig=alles-verwijderen-2", response.headers["Location"])
        self.assertEqual(self.count("students"), 14)

    def test_reset_with_backup_and_start_state(self):  # F4, F5, F6
        response = self.client.post("/instellingen/alles-verwijderen", data={"bevestiging": " verwijderen "})
        self.assertIn("melding=", response.headers["Location"])
        for table in ("students", "evaluations", "squads", "semesters", "professional_roles", "guilds", "staff",
                      "custom_columns", "settings"):
            self.assertEqual(self.count(table), 0, table)
        backups = list((self.db_path.parent / "reservekopieen").glob("dashboard-*.sqlite3"))
        self.assertEqual(len(backups), 1)
        copy = sqlite3.connect(backups[0])
        try:
            self.assertEqual(copy.execute("SELECT COUNT(*) FROM students").fetchone()[0], 14)
        finally:
            copy.close()
        self.assertIsNone(TokenStore(self.env).read())
        self.assertFalse(self.profile.exists())
        html = self.client.get(response.headers["Location"]).get_data(as_text=True)
        self.assertIn("Alle gegevens zijn verwijderd.", html)
        self.assertIn("Nog geen studenten", html)
        self.assertIn("Niet verbonden", html)

    def test_blocked_while_fetching(self):  # F7
        self.app.extensions["fetcher"].running = True
        self.assertIn("Wacht tot het inloggen of ophalen klaar is.", self.settings())
        response = self.client.post("/instellingen/alles-verwijderen", data={"bevestiging": "VERWIJDEREN"})
        self.assertIn("reset_fout=", response.headers["Location"])
        self.assertEqual(self.count("students"), 14)
        self.assertTrue(self.profile.exists())


if __name__ == "__main__":
    unittest.main()
