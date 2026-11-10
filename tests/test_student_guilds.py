"""Tests for the guilds of a student (spec 016, spec 018). All names are invented."""

import re
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from dashboard import create_app, db, staff


class GuildsTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "data" / "test.sqlite3"
        self.app = create_app(self.db_path, env_file=Path(self.tmp.name) / ".env")
        self.client = self.app.test_client()
        self.client.post("/gildes/toevoegen/open-ict")
        self.client.post("/semesters/toevoegen/open-ict")
        with self.db() as conn:
            staff.add(conn, ["Anna Gilde", "Bas Gilde"], "guild_master")
            self.fe, self.ux = (conn.execute("SELECT id FROM guilds WHERE code = ?", (c,)).fetchone()[0]
                                for c in ("FE", "UX"))
            self.anna, self.bas = (conn.execute("SELECT id FROM staff WHERE name = ?", (n,)).fetchone()[0]
                                   for n in ("Anna Gilde", "Bas Gilde"))
            self.student = conn.execute("INSERT INTO students (name, semester) VALUES ('Eva Kok', 3) RETURNING id").fetchone()[0]

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

    def guilds(self):
        with self.db() as conn:
            return sorted(tuple(r) for r in conn.execute(
                "SELECT guild_id, guild_master_id FROM student_guilds WHERE student_id = ?", (self.student,)))

    def save(self, roles, masters):
        return self.client.post(f"/studenten/{self.student}/bewerken",
                                data={"name": "Eva Kok", "semester": "3", "guild": roles, "guild_master": masters})


class TestGuilds(GuildsTestCase):
    def test_edit_two_guilds_each_with_a_guild_master(self):  # F1, F4
        self.save([str(self.fe), str(self.ux), ""], [str(self.anna), str(self.bas), ""])
        self.assertEqual(self.guilds(), sorted([(self.fe, self.anna), (self.ux, self.bas)]))
        self.save([str(self.ux), ""], [str(self.bas), ""])          # FE removed
        self.assertEqual(self.guilds(), [(self.ux, self.bas)])
        html = self.client.get(f"/studenten/{self.student}/bewerken").get_data(as_text=True)
        self.assertIn("Gildes", html)
        self.assertNotIn("Primaire beroepsrol", html)

    def test_same_role_twice_is_refused(self):  # F1, F4
        html = self.save([str(self.fe), str(self.fe)], ["", ""]).get_data(as_text=True)
        self.assertIn("FE staat er twee keer in.", html)
        self.assertEqual(self.guilds(), [])

    def test_unassigned_without_guild(self):  # F2
        titles = re.findall(r'class="group-title">([^<]+)<', self.client.get("/studenten").get_data(as_text=True))
        self.assertEqual(titles, ["Nog in te delen"])
        self.save([str(self.fe)], [""])
        titles = re.findall(r'class="group-title">([^<]+)<', self.client.get("/studenten").get_data(as_text=True))
        self.assertNotIn("Nog in te delen", titles)

    def test_my_guild_students_and_filter(self):  # F5, F6
        self.save([str(self.fe), str(self.ux)], ["", str(self.bas)])
        db.set_setting(str(self.db_path), "portflow_user_name", "Bas Gilde")
        html = self.client.get("/studenten?wie=gilde").get_data(as_text=True)
        self.assertIn("Eva Kok", html)
        self.assertIn(">FE, UX<", html)
        self.assertIn(f'Eva Kok', self.client.get(f"/studenten?gilde={self.ux}").get_data(as_text=True))
        grouped = self.client.get("/?groep=guild").get_data(as_text=True)
        self.assertEqual(grouped.count('data-sort-name="eva kok"'), 2)
        self.assertNotIn('value="role"', grouped)        # "Groeperen: Beroepsrol" is gone

    def test_guild_master_card_and_remove_role(self):  # F7
        self.save([str(self.fe), str(self.ux)], [str(self.anna), str(self.anna)])
        self.assertIn("1 student", self.client.get("/gildemeesters").get_data(as_text=True))
        self.client.post(f"/gildemeesters/{self.anna}/verwijderen")
        self.assertEqual(self.guilds(), sorted([(self.fe, None), (self.ux, None)]))

    def test_migration_of_old_fields(self):  # spec 016 F3, spec 018 F9
        """A database from before spec 016 and 018: roles, guilds per role, primary and secondary roles."""
        old = Path(self.tmp.name) / "old.sqlite3"
        conn = sqlite3.connect(old)
        conn.executescript("""
            CREATE TABLE professional_roles (id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '', color TEXT NOT NULL DEFAULT '#909DB9', is_demo INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE guilds (id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
                role_id INTEGER NOT NULL UNIQUE REFERENCES professional_roles(id) ON DELETE CASCADE,
                color TEXT NOT NULL DEFAULT '#909DB9', is_demo INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE staff (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
            CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT NOT NULL, semester INTEGER,
                primary_role_id INTEGER REFERENCES professional_roles(id) ON DELETE SET NULL,
                guild_master_id INTEGER REFERENCES staff(id) ON DELETE SET NULL,
                has_access INTEGER NOT NULL DEFAULT 1, is_demo INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE student_guilds (student_id INTEGER NOT NULL, role_id INTEGER NOT NULL
                REFERENCES professional_roles(id) ON DELETE CASCADE, guild_master_id INTEGER, PRIMARY KEY (student_id, role_id));
            CREATE TABLE student_secondary_roles (student_id INTEGER, role_id INTEGER);
            INSERT INTO professional_roles (id, code, name, description, color) VALUES
                (1, 'FE', 'Front-end developer', 'Bouwt interfaces', '#7D6BA8'), (2, 'GD', 'Game developer', '', '#B58A4A');
            INSERT INTO guilds (id, code, name, role_id, color) VALUES (7, 'FE', 'Front-end gilde', 1, '#123456');
            INSERT INTO staff (id, name) VALUES (5, 'Anna Gilde');
            INSERT INTO students (id, name, semester, primary_role_id, guild_master_id) VALUES (1, 'Eva Kok', 3, 1, 5);
            INSERT INTO student_secondary_roles VALUES (1, 2);
        """)
        conn.commit()
        conn.close()
        create_app(old)
        conn = sqlite3.connect(old)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            rows = {r["code"]: tuple(r)[1:] for r in conn.execute(
                "SELECT code, id, name, role_name, description, color FROM guilds ORDER BY code")}
            self.assertEqual(rows["FE"], (7, "Front-end gilde", "Front-end developer", "Bouwt interfaces", "#123456"))
            gd = rows["GD"]   # a role without a guild becomes a guild, named after the Open-ICT list
            self.assertEqual(gd[1:], ("Game development gilde", "Game developer", "", "#B58A4A"))
            links = sorted(tuple(r) for r in conn.execute("SELECT guild_id, guild_master_id FROM student_guilds"))
            self.assertEqual(links, sorted([(7, 5), (gd[0], None)]))
            for table in ("professional_roles", "student_secondary_roles"):
                self.assertIsNone(conn.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (table,)).fetchone())
            self.assertNotIn("primary_role_id", {r["name"] for r in conn.execute("PRAGMA table_info(students)")})
            conn.execute("UPDATE students SET semester = 4")   # students can be changed again
            conn.commit()
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()


class TestManualAdd(GuildsTestCase):  # spec 017
    def test_card_and_form(self):  # F1, F2
        html = self.client.get("/studenten/toevoegen").get_data(as_text=True)
        self.assertIn('href="/studenten/toevoegen/handmatig"', html)
        self.assertEqual(html.count("Binnenkort beschikbaar"), 2)
        form = self.client.get("/studenten/toevoegen/handmatig").get_data(as_text=True)
        for field in ('name="name"', 'name="student_number"', 'name="semester"', 'name="guild"', 'name="coach_id"', 'name="notes"'):
            self.assertIn(field, form)
        self.assertNotIn("Student niet meer volgen", form)
        self.assertNotIn('name="portflow"', form)

    def test_name_required_and_form_kept(self):  # F2
        html = self.client.post("/studenten/toevoegen/handmatig", data={"name": " ", "student_number": "9000001"}).get_data(as_text=True)
        self.assertIn("Vul een naam in.", html)
        self.assertIn('value="9000001"', html)

    def test_add_with_guild_and_message(self):  # F4
        response = self.client.post("/studenten/toevoegen/handmatig", data={
            "name": "Tim Vos", "semester": "3", "guild": [str(self.fe), ""], "guild_master": [str(self.anna), ""]})
        self.assertIn("Tim+Vos+toegevoegd", response.headers["Location"])
        self.assertIn("Klik+op+Verversen", response.headers["Location"])   # not connected
        with self.db() as conn:
            sid = conn.execute("SELECT id FROM students WHERE name = 'Tim Vos'").fetchone()[0]
            guilds = [tuple(r) for r in conn.execute("SELECT guild_id, guild_master_id FROM student_guilds WHERE student_id = ?", (sid,))]
        self.assertEqual(guilds, [(self.fe, self.anna)])
        titles = re.findall(r'class="group-title">([^<]+)<', self.client.get("/studenten").get_data(as_text=True))
        self.assertIn("Zonder project", titles)       # Tim is assigned (semester + guild), Eva is not

    def test_same_name_warns_and_number_refused(self):  # F3
        html = self.client.post("/studenten/toevoegen/handmatig", data={"name": "eva  kók"}).get_data(as_text=True)
        self.assertIn("Er is al een student met deze naam", html)
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM students").fetchone()[0], 1)
        self.client.post("/studenten/toevoegen/handmatig", data={"name": "eva kók", "toch": "1"})
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM students").fetchone()[0], 2)
            conn.execute("UPDATE students SET student_number = '9000001' WHERE id = ?", (self.student,))
        html = self.client.post("/studenten/toevoegen/handmatig", data={"name": "Lars Koster", "student_number": "9000001"}).get_data(as_text=True)
        self.assertIn("Dit studentnummer hoort al bij Eva Kok.", html)
