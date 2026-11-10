"""Tests for the student overview pages (spec 001) and Coaches / Gildemeesters (specs 006, 007)."""

import re
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from dashboard import create_app, db
from dashboard import staff


class PagesTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "data" / "test.sqlite3"
        self.app = create_app(self.db_path, env_file=Path(self.tmp.name) / ".env")
        self.client = self.app.test_client()

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

    def add_roles(self):
        """Spec 008: a new dashboard has no professional roles; add the Open-ICT ones."""
        self.client.post("/beroepsrollen/toevoegen/open-ict")

    def html(self, path, **query):
        return self.client.get(path, query_string=query).get_data(as_text=True)

    def load_demo(self):
        self.client.post("/instellingen/demodata/laden")
        db.set_setting(str(self.db_path), "semester_start", "2026-09-01")
        db.set_setting(str(self.db_path), "semester_end", "2027-01-31")

    @staticmethod
    def rows(html):
        return re.findall(r'class="student-row', html)


class TestStudentTable(PagesTestCase):
    def test_empty_state_without_students(self):  # F20
        html = self.html("/studenten")
        self.assertIn("Nog geen studenten", html)
        self.assertNotIn('id="students"', html)

    def test_columns_in_order_and_all_rows(self):  # F2, F4
        self.load_demo()
        html = self.html("/")
        self.assertEqual(len(self.rows(html)), 14)
        heads = re.findall(r'data-sort="([^"]+)"', html.split("</thead>")[0])
        self.assertEqual(heads[:12], ["name", "profile", "OC", "KO", "JKO", "KPM", "PL", "BD", "SW", "FO", "PH", "RE"])
        self.assertIn('cat-product" data-sort="KPM"', html)
        self.assertIn('cat-social" data-sort="SW"', html)
        self.assertIn('cat-personal" data-sort="RE"', html)

    def test_extra_columns_default_and_kept(self):  # F3
        self.load_demo()
        head = self.html("/").split("</thead>")[0]
        self.assertIn('data-sort="guild_master"', head)
        self.assertNotIn('data-sort="coach"', head)
        self.client.post("/studenten/kolommen", data={"kolom": ["guild_master", "coach"], "next": "/studenten"})
        fresh = create_app(self.db_path).test_client()  # as after a restart
        head = fresh.get("/").get_data(as_text=True).split("</thead>")[0]
        self.assertIn('data-sort="coach"', head)

    def test_cells_labels_and_markers(self):  # F5, F6, F10, F11, F12
        self.load_demo()
        html = self.html("/")
        self.assertIn('<span class="role-label">SM</span>', html)
        self.assertIn("Assessment ingeleverd", html)
        self.assertIn("portfolio niet gedeeld", html)
        self.assertNotIn("Product nog leeg", html)       # no signal labels (spec 001, F12 changed)
        self.assertNotIn("Coach nog leeg", html)
        self.assertNotIn("04 Horizon · Sem", html)            # no project in the subline (F2 changed)
        self.assertNotIn("Horizon · Sem 3", html)
        self.assertIn('level level-n2', html)
        self.assertIn('<b class="pending">?</b>', html)

    def test_groups_and_last_groups(self):  # F16
        self.load_demo()
        html = self.html("/")
        titles = re.findall(r'class="group-title">([^<]+)<', html)
        self.assertEqual(titles[-2:], ["Zonder project", "Nog in te delen"])

    def test_no_grouping(self):  # F16 "Niet groeperen"
        self.load_demo()
        for path in ("/", "/studenten"):
            html = self.html(path, groep="none")
            self.assertNotIn('class="group-header"', html)
            self.assertEqual(len(self.rows(html)), 14)
            self.assertIn('<option value="none" selected>Niet groeperen</option>', html)
        names = re.findall(r'data-sort-name="([^"]+)"', self.html("/studenten", groep="none"))
        self.assertEqual(names, sorted(names))

    def test_filters(self):  # F13, F14, F15
        self.load_demo()
        # Demo set: 8 students with a signal, 4 in semester 3; Marieke Ploeg coaches 8.
        self.assertEqual(len(self.rows(self.html("/studenten", aansporen="1"))), 8)
        self.assertEqual(len(self.rows(self.html("/studenten", semester="3"))), 4)
        db.set_setting(str(self.db_path), "portflow_user_name", "Marieke Ploeg")
        self.assertEqual(len(self.rows(self.html("/studenten", wie="coach"))), 8)
        self.assertEqual(len(self.rows(self.html("/studenten", wie="coach", semester="3"))), 4)
        self.assertEqual(len(self.rows(self.html("/studenten", wie="coach", semester="5", aansporen="1"))), 2)
        self.assertEqual(len(self.rows(self.html("/studenten", wie="gilde"))), 0)

    def test_overview_shows_full_table(self):  # F1 (changed): all students, no link
        self.load_demo()
        html = self.html("/")
        self.assertEqual(len(self.rows(html)), 14)
        self.assertIn("14 van 14 studenten", html)
        self.assertNotIn("Alle studenten bekijken", html)
        self.assertIn('class="level level-', html)

    def test_legend_colours_on_and_off(self):  # F23
        self.load_demo()
        html = self.html("/")
        self.assertEqual(len(re.findall(r'name="kleur" value="(n0|n1|n2|pending)" checked', html)), 4)
        self.assertNotIn("colour-off-", html)
        self.client.post("/studenten/kleuren", data={"kleur": ["n1", "n2", "pending"], "next": "/"})
        fresh = create_app(self.db_path).test_client()   # the choice is kept
        html = fresh.get("/").get_data(as_text=True)
        self.assertIn("colour-off-n0", html)
        self.assertNotIn('value="n0" checked', html)
        self.assertIn('value="n1" checked', html)

    def test_custom_value_percentage(self):  # F8
        self.load_demo()
        with self.db() as conn:
            column = conn.execute("SELECT id FROM custom_columns WHERE type = 'percentage'").fetchone()["id"]
            student = conn.execute("SELECT id FROM students WHERE name = 'Iris Bouma'").fetchone()["id"]
        self.client.post(f"/studenten/{student}/kolom/{column}", data={"waarde": "75", "next": "/studenten"})
        response = self.client.post(f"/studenten/{student}/kolom/{column}", data={"waarde": "120", "next": "/studenten"})
        self.assertIn("fout=", response.headers["Location"])
        with self.db() as conn:
            value = conn.execute("SELECT value FROM custom_values WHERE student_id = ? AND column_id = ?",
                                 (student, column)).fetchone()["value"]
        self.assertEqual(value, "75")

    def test_semester_period_setting(self):  # F22
        html = self.html("/instellingen")
        self.assertIn("Semesterperiode", html)
        self.assertIn("vooringevuld", html)
        response = self.client.post("/instellingen/semesterperiode", data={"start": "2027-02-01", "end": "2026-09-01"})
        self.assertIn("fout=", response.headers["Location"])
        self.client.post("/instellingen/semesterperiode", data={"start": "2026-02-01", "end": "2026-08-31"})
        self.assertIn('value="2026-02-01"', self.html("/instellingen"))


class TestStaffPages(PagesTestCase):
    def setUp(self):
        super().setUp()
        self.add_roles()

    def test_menu_items(self):  # 006 F1, 007 F1
        html = self.html("/")
        # Under Beheer (spec 002, F17): ... Gildes, Gildemeesters, Coaches, Projecten.
        self.assertLess(html.index('href="/gildemeesters"'), html.index('href="/coaches"'))
        self.assertLess(html.index('href="/coaches"'), html.index('href="/projecten"'))
        self.assertIn("Nog geen gildemeesters", self.html("/gildemeesters"))

    def test_add_by_names_skips_duplicates_and_warns_for_unknown(self):  # 006 F6
        html = self.client.post("/gildemeesters/toevoegen/namen", data={"namen": "A. Gilde\na. gilde \n\n"}).get_data(as_text=True)
        self.assertIn("Nog geen evaluaties van deze naam gevonden", html)
        self.client.post("/gildemeesters/toevoegen/namen", data={"namen": "A. Gilde\na. gilde \n\n", "toch": "1"})
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM staff WHERE is_guild_master = 1").fetchone()[0], 1)

    def test_candidates_sorted_per_role(self):  # 006 F5, 007 F3
        with self.db() as conn:
            student = conn.execute("INSERT INTO students (name) VALUES ('Sem Bakker') RETURNING id").fetchone()[0]
            for skill in ["OC", "KO", "JKO", "KPM", "OC"]:
                conn.execute("INSERT INTO evaluations (student_id, skill, kind, level, date, assessor) "
                             "VALUES (?, ?, 'assessed', '1', '2026-10-01', 'A. Gilde')", (student, skill))
            for skill in ["PL", "BD", "SW", "FO", "PH", "RE", "PL"]:
                conn.execute("INSERT INTO evaluations (student_id, skill, kind, level, date, assessor) "
                             "VALUES (?, ?, 'assessed', '1', '2026-10-01', 'B. Coach')", (student, skill))
            self.assertEqual(staff.candidates(conn, "guild_master")[0]["name"], "A. Gilde")
            self.assertEqual(staff.candidates(conn, "coach")[0]["name"], "B. Coach")
        self.client.post("/gildemeesters/toevoegen/portflow", data={"naam": ["A. Gilde"]})
        self.assertIn("A. Gilde", self.html("/gildemeesters"))
        self.assertIn("Al gildemeester", self.html("/gildemeesters/toevoegen/portflow"))

    def test_one_person_two_roles(self):  # 006 F10, 007 F4
        with self.db() as conn:
            staff.add(conn, ["A. de Vries"], "coach")
            staff.add(conn, ["a. de vries"], "guild_master")
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM staff").fetchone()[0], 1)
        self.assertIn("Ook coach", self.html("/gildemeesters"))
        self.assertIn("Ook gildemeester", self.html("/coaches"))

    def test_remove_role_empties_field_and_keeps_other_role(self):  # 006 F8
        with self.db() as conn:
            staff.add(conn, ["A. de Vries"], "coach")
            staff.add(conn, ["A. de Vries"], "guild_master")
            person = conn.execute("SELECT id FROM staff").fetchone()["id"]
            student = conn.execute("INSERT INTO students (name, coach_id) VALUES ('Sem Bakker', ?) RETURNING id", (person,)).fetchone()[0]
            role = conn.execute("SELECT id FROM professional_roles WHERE code = 'FE'").fetchone()[0]
            conn.execute("INSERT INTO student_guilds (student_id, role_id, guild_master_id) VALUES (?, ?, ?)", (student, role, person))
        self.assertIn("is bij 1 student ingevuld", self.html("/gildemeesters", verwijder=person))
        self.client.post(f"/gildemeesters/{person}/verwijderen")
        with self.db() as conn:
            student = conn.execute("SELECT s.coach_id, g.guild_master_id FROM students s JOIN student_guilds g ON g.student_id = s.id").fetchone()
            row = conn.execute("SELECT is_coach, is_guild_master FROM staff").fetchone()
        self.assertEqual((student["coach_id"], student["guild_master_id"]), (person, None))
        self.assertEqual((row["is_coach"], row["is_guild_master"]), (1, 0))

    def test_edit_name_and_guilds(self):  # 006 F7
        with self.db() as conn:
            staff.add(conn, ["A Gilde", "B. Ander"], "guild_master")
            person = conn.execute("SELECT id FROM staff WHERE name = 'A Gilde'").fetchone()["id"]
            role = conn.execute("SELECT id FROM professional_roles WHERE code = 'FE'").fetchone()["id"]
            frontend = conn.execute("INSERT INTO guilds (code, name, role_id) VALUES ('FE', 'Front-end gilde', ?) "
                                    "RETURNING id", (role,)).fetchone()["id"]
        html = self.client.post(f"/gildemeesters/{person}/bewerken", data={"naam": "B. Ander"}).get_data(as_text=True)
        self.assertIn("staat al iemand", html)
        self.client.post(f"/gildemeesters/{person}/bewerken", data={"naam": "A. Gilde", "gilde": [str(frontend)]})
        html = self.html("/gildemeesters")
        self.assertIn("A. Gilde", html)
        self.assertIn('tag-guild" title="Front-end gilde"', html)

    def test_open_ict_guild_masters_preset(self):  # 006 F11
        preset = staff.read_preset()
        self.assertEqual(len(preset), 16)
        self.assertIn(("Peter Snoek", "FE"), preset)
        self.assertIn("<h2>Open-ICT-gildemeesters toevoegen</h2>", self.html("/gildemeesters/toevoegen"))
        self.assertNotIn("Open-ICT-gildemeesters", self.html("/coaches/toevoegen"))
        with self.db() as conn:
            staff.add(conn, ["Peter Snoek"], "coach")
        response = self.client.post("/gildemeesters/toevoegen/open-ict")
        self.assertIn("toegevoegd=16", response.headers["Location"])
        self.client.post("/gildemeesters/toevoegen/open-ict")  # twice: no duplicates
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM staff WHERE is_guild_master = 1").fetchone()[0], 16)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM staff_guilds").fetchone()[0], 16)
            # F11 with guilds: the missing Open-ICT guilds were added first (all 9 codes occur).
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM guilds").fetchone()[0], 9)
            peter = conn.execute("SELECT s.is_coach, g.code FROM staff s JOIN staff_guilds sg ON sg.staff_id = s.id "
                                 "JOIN guilds g ON g.id = sg.guild_id WHERE s.name = 'Peter Snoek'").fetchone()
        self.assertEqual((peter["is_coach"], peter["code"]), (1, "FE"))

    def test_preset_skips_unknown_guild_code(self):  # 006 F11
        with self.db() as conn:
            staff.add_guild_masters_with_guilds(conn, [("A. Gilde", "XX")])
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM staff_guilds").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM staff WHERE is_guild_master = 1").fetchone()[0], 1)

    def test_user_added_as_coach_only_once(self):  # 007 F2a
        path = str(self.db_path)
        db.add_user_as_coach(path, "Anna van der Berg")
        with self.db() as conn:
            row = conn.execute("SELECT id, is_coach, is_guild_master FROM staff").fetchone()
        self.assertEqual((row["is_coach"], row["is_guild_master"]), (1, 0))
        self.client.post(f"/coaches/{row['id']}/verwijderen")
        db.add_user_as_coach(path, "Anna van der Berg")
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM staff").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()


class TestGuilds(PagesTestCase):  # spec 006, F12-F19
    def setUp(self):
        super().setUp()
        self.add_roles()

    def role_id(self, code):
        with self.db() as conn:
            return conn.execute("SELECT id FROM professional_roles WHERE code = ?", (code,)).fetchone()["id"]

    def test_menu_and_empty_start(self):  # F12, F13
        html = self.html("/gildes")
        self.assertLess(html.index('href="/gildes"'), html.index('href="/gildemeesters"'))
        self.assertLess(html.index('href="/gildes"'), html.index('href="/kolommen"'))
        self.assertIn("Nog geen gildes.", html)

    def test_open_ict_guilds_twice(self):  # F14
        self.assertIn("toegevoegd=9", self.client.post("/gildes/toevoegen/open-ict").headers["Location"])
        self.assertIn("toegevoegd=0", self.client.post("/gildes/toevoegen/open-ict").headers["Location"])
        html = self.html("/gildes")
        self.assertIn("Front-end gilde", html)
        self.assertIn("Front-end developer", html)

    def test_validation(self):  # F15
        fe = str(self.role_id("FE"))
        for code in ("F", "FRON", "F1"):
            html = self.client.post("/gildes/nieuw", data={"code": code, "naam": "X", "rol": fe}).get_data(as_text=True)
            self.assertIn("2 of 3 letters", html)
        self.client.post("/gildes/nieuw", data={"code": "fe", "naam": "Front-end gilde", "rol": fe, "kleur": "#123456"})
        html = self.client.post("/gildes/nieuw", data={"code": "FE", "naam": "Ander", "rol": str(self.role_id("BE"))}).get_data(as_text=True)
        self.assertIn("al een gilde met de code FE", html)
        html = self.client.post("/gildes/nieuw", data={"code": "FX", "naam": "Ander", "rol": fe}).get_data(as_text=True)
        self.assertIn("heeft al een gilde", html)
        with self.db() as conn:
            row = conn.execute("SELECT code, color FROM guilds").fetchone()
        self.assertEqual((row["code"], row["color"]), ("FE", "#123456"))

    def test_edit_and_delete_keeps_guild_masters(self):  # F16, F17
        self.client.post("/gildes/toevoegen/open-ict")
        with self.db() as conn:
            staff.add(conn, ["A. Gilde", "B. Gilde"], "guild_master")
            guild = conn.execute("SELECT id FROM guilds WHERE code = 'FE'").fetchone()["id"]
            for person in conn.execute("SELECT id FROM staff").fetchall():
                conn.execute("INSERT INTO staff_guilds (staff_id, guild_id) VALUES (?, ?)", (person["id"], guild))
        self.client.post(f"/gildes/{guild}/bewerken", data={"code": "FE", "naam": "Gilde front-end",
                                                            "rol": str(self.role_id("FE")), "kleur": "#909DB9"})
        self.assertIn("Gilde front-end", self.html("/gildemeesters"))
        self.assertIn("heeft 2 gildemeesters", self.html("/gildes", verwijder=guild))
        self.client.post(f"/gildes/{guild}/verwijderen")
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM staff WHERE is_guild_master = 1").fetchone()[0], 2)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM staff_guilds").fetchone()[0], 0)

    def test_guild_master_chooses_from_guilds(self):  # F18
        self.client.post("/gildes/toevoegen/open-ict")
        with self.db() as conn:
            staff.add(conn, ["A. Gilde"], "guild_master")
            person = conn.execute("SELECT id FROM staff").fetchone()["id"]
        html = self.html(f"/gildemeesters/{person}/bewerken")
        self.assertIn("FE · Front-end gilde", html)

    def test_group_by_guild(self):  # F19
        self.load_demo()
        with self.db() as conn:
            conn.execute("DELETE FROM guilds")
        titles = re.findall(r'class="group-title">([^<]+)<', self.html("/studenten", groep="guild"))
        self.assertIn("FE", titles)                    # spec 016: grouped on the codes of the student's guilds
        self.assertEqual(titles[-1], "Nog in te delen")
        self.client.post("/gildes/toevoegen/open-ict")
        html = self.html("/studenten", groep="guild")
        self.assertIn('class="group-title">FE<', html)
        self.assertIn("Front-end gilde", html)
        # Julia Meijer has CI and CS: she is in both groups
        self.assertEqual(html.count('data-sort-name="julia meijer"'), 2)

    def test_old_guild_links_lapse_on_migration(self):
        with self.db() as conn:
            conn.execute("DROP TABLE staff_guilds")
            conn.execute("CREATE TABLE staff_guilds (staff_id INTEGER, role_id INTEGER)")
            conn.execute("INSERT INTO staff_guilds VALUES (1, 1)")
        create_app(self.db_path)
        with self.db() as conn:
            columns = {r["name"] for r in conn.execute("PRAGMA table_info(staff_guilds)")}
            self.assertEqual(columns, {"staff_id", "guild_id"})
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM staff_guilds").fetchone()[0], 0)


class TestRoles(PagesTestCase):  # spec 008
    def test_empty_page_and_open_ict_twice(self):  # F1, F4, F5
        html = self.html("/beroepsrollen")
        self.assertIn("Nog geen beroepsrollen.", html)
        self.assertIn("Opleidingsprofiel", html)
        self.assertIn("toegevoegd=9", self.client.post("/beroepsrollen/toevoegen/open-ict").headers["Location"])
        self.assertIn("toegevoegd=0", self.client.post("/beroepsrollen/toevoegen/open-ict").headers["Location"])
        html = self.html("/beroepsrollen")
        self.assertIn("Front-end developer", html)
        self.assertIn("Een student kan een of meer gildes hebben", html)

    def test_validation_and_edit(self):  # F6, F7
        for code in ("F", "FRON", "F1"):
            html = self.client.post("/beroepsrollen/nieuw", data={"code": code, "naam": "X"}).get_data(as_text=True)
            self.assertIn("2 of 3 letters", html)
        self.client.post("/beroepsrollen/nieuw", data={"code": "fe", "naam": "Front-end developer", "kleur": "#123456"})
        html = self.client.post("/beroepsrollen/nieuw", data={"code": "FE", "naam": "Ander"}).get_data(as_text=True)
        self.assertIn("al een beroepsrol met de code FE", html)
        with self.db() as conn:
            role = conn.execute("SELECT * FROM professional_roles").fetchone()
        self.assertEqual((role["code"], role["color"]), ("FE", "#123456"))
        self.client.post(f"/beroepsrollen/{role['id']}/bewerken",
                         data={"code": "FE", "naam": "Frontend developer", "beschrijving": "Bouwt interfaces", "kleur": "#123456"})
        html = self.html("/beroepsrollen")
        self.assertIn("Frontend developer", html)
        self.assertIn("Bouwt interfaces", html)

    def test_counts_and_delete(self):  # F2, F3, F8
        self.add_roles()
        self.client.post("/gildes/toevoegen/open-ict")
        with self.db() as conn:
            fe = conn.execute("SELECT id FROM professional_roles WHERE code = 'FE'").fetchone()["id"]
            ux = conn.execute("SELECT id FROM professional_roles WHERE code = 'UX'").fetchone()["id"]
            for name in ("Sem Bakker", "Noor Peters", "Lars Koster"):
                sid = conn.execute("INSERT INTO students (name, semester) VALUES (?, 3) RETURNING id", (name,)).fetchone()[0]
                conn.execute("INSERT INTO student_guilds (student_id, role_id) VALUES (?, ?)", (sid, fe))
            other = conn.execute("INSERT INTO students (name, semester) VALUES ('Iris Bouma', 3) RETURNING id").fetchone()["id"]
            conn.execute("INSERT INTO student_guilds (student_id, role_id) VALUES (?, ?), (?, ?)", (other, ux, other, fe))
        html = self.html("/beroepsrollen")
        self.assertIn("<strong>4</strong> Studenten gekoppeld", html)
        self.assertIn("4 studenten", html)                    # FE
        confirm = self.html("/beroepsrollen", verwijder=fe)
        self.assertIn("Bij 4 studenten verdwijnt dit gilde; 3 van hen hebben geen ander gilde", confirm)
        self.assertIn("Het Front-end gilde wordt ook verwijderd", confirm)
        self.client.post(f"/beroepsrollen/{fe}/verwijderen")
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM student_guilds").fetchone()[0], 1)   # Iris keeps UX
            self.assertIsNone(conn.execute("SELECT 1 FROM guilds WHERE code = 'FE'").fetchone())
        titles = re.findall(r'class="group-title">([^<]+)<', self.html("/studenten"))
        self.assertIn("Nog in te delen", titles)

    def test_guild_pages_hint_without_roles(self):  # F10
        self.assertIn("Voeg eerst beroepsrollen toe", self.html("/gildes/toevoegen"))
        self.assertIn("Voeg eerst beroepsrollen toe", self.html("/gildes/nieuw"))
        self.add_roles()
        self.assertNotIn("Voeg eerst beroepsrollen toe", self.html("/gildes/toevoegen"))


class TestSemesters(PagesTestCase):  # spec 009
    def add_student(self, name, semester):
        with self.db() as conn:
            conn.execute("INSERT INTO students (name, semester) VALUES (?, ?)", (name, semester))

    def semester_id(self, number):
        with self.db() as conn:
            return conn.execute("SELECT id FROM semesters WHERE number = ?", (number,)).fetchone()["id"]

    def test_empty_page(self):  # F1, F4
        html = self.html("/semesters")
        self.assertIn("Nog geen semesters.", html)
        self.assertIn("+ Semester toevoegen", html)

    def test_open_ict_semesters_twice_and_fields(self):  # F5, F6
        self.assertIn("toegevoegd=8", self.client.post("/semesters/toevoegen/open-ict").headers["Location"])
        self.assertIn("toegevoegd=0", self.client.post("/semesters/toevoegen/open-ict").headers["Location"])
        with self.db() as conn:
            three = dict(conn.execute("SELECT * FROM semesters WHERE number = 3").fetchone())
            six = conn.execute("SELECT osiris_code FROM semesters WHERE number = 6").fetchone()[0]
            eight = dict(conn.execute("SELECT * FROM semesters WHERE number = 8").fetchone())
        self.assertEqual((three["osiris_code"], three["min_level"], three["kpm_level"], three["mastery"]),
                         ("TICT-OV2SE3-26", "4 op 2, 6 op 1", "Minimaal KPM op 1", "Probleemgericht"))
        self.assertEqual(six, "TICT-OV3SE6-26")
        self.assertEqual((eight["min_level"], eight["kpm_level"]), ("", "BOKSA"))

    def test_cards_summary_and_phase(self):  # F2, F3, F9
        self.client.post("/semesters/toevoegen/open-ict")
        for name, semester in (("Sem Bakker", 3), ("Noor Peters", 3), ("Lars Koster", 4), ("Iris Bouma", 5)):
            self.add_student(name, semester)
        html = self.html("/semesters")
        self.assertIn("verdeeld over 3 actieve semesters", html)
        self.assertIn("<strong>4 studenten</strong>", html)
        card7 = html.split("Semester 7</h2>")[0].rsplit('class="eyebrow">', 1)[1]
        self.assertTrue(card7.startswith("Hoofdfase"))
        card8 = html.split("Semester 8</h2>")[0].rsplit('class="eyebrow">', 1)[1]
        self.assertTrue(card8.startswith("Afstudeerfase"))

    def test_validation(self):  # F7
        for number in ("0", "9", "drie", ""):
            html = self.client.post("/semesters/nieuw", data={"number": number}).get_data(as_text=True)
            self.assertIn("1 tot en met 8", html)
        self.client.post("/semesters/nieuw", data={"number": "3", "osiris_code": "TICT-OV2SE3-26"})
        html = self.client.post("/semesters/nieuw", data={"number": "3"}).get_data(as_text=True)
        self.assertIn("Semester 3 bestaat al", html)

    def test_edit_moves_students(self):  # F8
        self.client.post("/semesters/nieuw", data={"number": "6"})
        self.add_student("Sem Bakker", 6)
        self.client.post(f"/semesters/{self.semester_id(6)}/bewerken",
                         data={"number": "7", "min_level": "5 op 3, 5 op 2"})
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT semester FROM students").fetchone()[0], 7)
        self.assertIn("5 op 3, 5 op 2", self.html("/semesters"))

    def test_delete_moves_students_to_unassigned(self):  # F10
        self.client.post("/semesters/toevoegen/open-ict")
        for name in ("Sem Bakker", "Noor Peters", "Lars Koster", "Iris Bouma"):
            self.add_student(name, 3)
        three = self.semester_id(3)
        self.assertIn("zitten 4 studenten", self.html("/semesters", verwijder=three))
        self.client.post(f"/semesters/{three}/verwijderen")
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM students WHERE semester IS NULL").fetchone()[0], 4)
            self.assertIsNone(conn.execute("SELECT 1 FROM semesters WHERE number = 3").fetchone())


class TestStudentList(PagesTestCase):  # spec 010
    def test_columns_and_values_without_progress(self):  # F1, F4
        self.load_demo()
        html = self.html("/studenten")
        self.assertIn("Alle studenten die je volgt, met hun indeling.", html)
        heads = re.findall(r'<button type="button">([^<]+)</button></th>', html.split("</thead>")[0])
        self.assertEqual(heads, ["Student", "Semester", "Project", "Invulling", "Rol", "Gilde",
                                 "Coach", "Gildemeester", "Portflow"])
        self.assertNotIn('class="level level-', html)
        self.assertNotIn("Product nog leeg</span>", html.split("</thead>")[1])
        row = re.search(r'data-sort-name="lieke jansen">(.*?)</tr>', html, re.S).group(1)
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        self.assertEqual(cells, ["3", "04 Horizon", "Open projecten", "SM", "FE",
                                 "Marieke Ploeg", "Joost Hendriks", "Niet gekoppeld"])
        self.assertIn('title="scrum master">SM<', row)
        julia = re.search(r'data-sort-name="julia meijer">(.*?)</tr>', html, re.S).group(1)
        self.assertIn(">CI, CS<", julia)                     # spec 016: all guild codes

    def test_portflow_column(self):  # F1
        with self.db() as conn:
            conn.execute("INSERT INTO students (name, portflow_user_id) VALUES ('Sem Bakker', 11)")
            conn.execute("INSERT INTO students (name, portflow_user_id, has_access) VALUES ('Noor Peters', 12, 0)")
        html = self.html("/studenten")
        self.assertIn("Gekoppeld</td>", html)
        self.assertIn("Portfolio niet gedeeld", html)

    def test_filters_shared_with_overview(self):  # F2
        self.load_demo()
        db.set_setting(str(self.db_path), "portflow_user_name", "Marieke Ploeg")
        self.assertEqual(len(self.rows(self.html("/studenten", wie="coach", semester="3"))), 4)
        self.assertIn("4 van 14 studenten", self.html("/studenten", wie="coach", semester="3"))
        self.assertIn('id="table-search"', self.html("/studenten"))

    def test_empty_state(self):  # F3
        self.assertIn("Nog geen studenten", self.html("/studenten"))


class TestStudentEdit(PagesTestCase):  # spec 011
    def setUp(self):
        super().setUp()
        self.load_demo()
        with self.db() as conn:
            self.iris = conn.execute("SELECT id FROM students WHERE name = 'Iris Bouma'").fetchone()["id"]
            self.fe = conn.execute("SELECT id FROM professional_roles WHERE code = 'FE'").fetchone()["id"]
            self.ux = conn.execute("SELECT id FROM professional_roles WHERE code = 'UX'").fetchone()["id"]
            self.coach = conn.execute("SELECT id FROM staff WHERE name = 'Marieke Ploeg'").fetchone()["id"]

    def test_name_links_to_edit_page_keeping_filters(self):  # F1
        html = self.html("/studenten", semester="3")
        self.assertIn("/bewerken?terug=/studenten?semester%3D3", html)
        page = self.html(f"/studenten/{self.iris}/bewerken")
        self.assertIn("Student bewerken", page)
        self.assertIn('value="Iris Bouma"', page)

    def test_prefilled_values(self):  # F2, F3
        with self.db() as conn:
            lieke = conn.execute("SELECT id FROM students WHERE name = 'Lieke Jansen'").fetchone()["id"]
        page = self.html(f"/studenten/{lieke}/bewerken")
        self.assertRegex(page, r'<option value="3" selected>Semester 3')
        self.assertRegex(page, r'<option value="SM" selected>SM · scrum master')
        self.assertRegex(page, rf'<option value="{self.coach}" selected>Marieke Ploeg')
        self.assertIn("Niet gekoppeld", page)

    def test_save_moves_student_out_of_unassigned(self):  # F4
        gm = self.coach   # any guild master; Marieke is a coach, so make her a guild master too
        with self.db() as conn:
            conn.execute("UPDATE staff SET is_guild_master = 1 WHERE id = ?", (gm,))
        data = {"name": "Iris Bouma", "semester": "3", "coach_id": str(self.coach),
                "guild_role": [str(self.fe), str(self.ux), ""], "guild_master": [str(gm), "", ""],
                "terug": "/studenten?semester=3"}
        response = self.client.post(f"/studenten/{self.iris}/bewerken", data=data)
        self.assertTrue(response.headers["Location"].startswith("/studenten?semester=3&melding="))
        with self.db() as conn:
            row = conn.execute("SELECT semester, coach_id FROM students WHERE id = ?", (self.iris,)).fetchone()
            guilds = sorted(tuple(r) for r in conn.execute(
                "SELECT role_id, guild_master_id FROM student_guilds WHERE student_id = ?", (self.iris,)))
        self.assertEqual(tuple(row), (3, self.coach))
        self.assertEqual(guilds, sorted([(self.fe, gm), (self.ux, None)]))   # spec 016: each guild its own guild master
        html = self.html("/studenten", melding="Gegevens van Iris Bouma opgeslagen.")
        self.assertIn("Gegevens van Iris Bouma opgeslagen.", html)
        unassigned = html.split('class="group-title">Nog in te delen<')
        self.assertTrue(len(unassigned) == 1 or "Iris Bouma" not in unassigned[1])

    def test_validation_keeps_form(self):  # F5
        html = self.client.post(f"/studenten/{self.iris}/bewerken",
                                data={"name": " ", "student_number": "123456"}).get_data(as_text=True)
        self.assertIn("Vul een naam in.", html)
        self.assertIn('value="123456"', html)
        html = self.client.post(f"/studenten/{self.iris}/bewerken",
                                data={"name": "Iris Bouma", "semester": "9"}).get_data(as_text=True)
        self.assertIn("Kies een semester uit de lijst.", html)

    def test_unsafe_back_path_is_ignored(self):
        response = self.client.post(f"/studenten/{self.iris}/bewerken",
                                    data={"name": "Iris Bouma", "terug": "https://example.com/"})
        self.assertTrue(response.headers["Location"].startswith("/studenten?melding="))

    def test_stop_following(self):  # F6
        with self.db() as conn:
            sem = conn.execute("SELECT id FROM students WHERE name = 'Sem Bakker'").fetchone()["id"]
        self.assertIn("Sem Bakker niet meer volgen?", self.html(f"/studenten/{sem}/bewerken", bevestig="verwijderen"))
        response = self.client.post(f"/studenten/{sem}/verwijderen", data={"terug": "/studenten"})
        self.assertIn("melding=", response.headers["Location"])
        with self.db() as conn:
            self.assertIsNone(conn.execute("SELECT 1 FROM students WHERE id = ?", (sem,)).fetchone())
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (sem,)).fetchone()[0], 0)


class TestProjects(PagesTestCase):  # spec 012
    def project_id(self, number):
        with self.db() as conn:
            return conn.execute("SELECT id FROM squads WHERE number = ?", (number,)).fetchone()["id"]

    def test_empty_page_and_without_project_bar(self):  # F1, F4
        with self.db() as conn:
            conn.execute("INSERT INTO students (name) VALUES ('Sem Bakker')")
        html = self.html("/projecten")
        self.assertIn("Nog geen projecten.", html)
        self.assertIn("+ Nieuw project", html)
        self.assertIn("Zonder project", html)
        self.assertIn("1 student</strong>", html)

    def test_open_ict_projects_twice_and_colours(self):  # F5, F6
        self.assertIn("toegevoegd=19", self.client.post("/projecten/nieuw/open-ict").headers["Location"])
        self.assertIn("toegevoegd=0", self.client.post("/projecten/nieuw/open-ict").headers["Location"])
        with self.db() as conn:
            numbers = [r[0] for r in conn.execute("SELECT number FROM squads ORDER BY number")]
            colours = [r[0] for r in conn.execute("SELECT color FROM squads ORDER BY number")]
            two = dict(conn.execute("SELECT * FROM squads WHERE number = '02'").fetchone())
        self.assertNotIn("09", numbers)
        self.assertEqual((numbers[0], numbers[-1], len(numbers)), ("01", "20", 19))
        self.assertNotEqual(colours[0], colours[1])
        self.assertEqual((two["name"], two["client"], two["full_name"]),
                         ("Gamified Learning", "Condor Arnhem OT", "02 Gamified Learning"))

    def test_cards_and_summary(self):  # F2, F3
        self.client.post("/projecten/nieuw/open-ict")
        with self.db() as conn:
            for name in ("Sem Bakker", "Noor Peters"):
                conn.execute("INSERT INTO students (name, squad_id) VALUES (?, ?)", (name, self.project_id("02")))
            conn.execute("INSERT INTO students (name) VALUES ('Lars Koster')")
        html = self.html("/projecten")
        self.assertIn("<strong>1</strong> actief project", html)
        self.assertIn("<strong>2</strong> studenten", html)
        self.assertIn("<strong>1</strong> zonder project", html)
        self.assertIn(">GL</span>", html)
        self.assertIn(">BE</span>", html)  # one word: "Beheerteam"
        self.assertIn("02 Gamified Learning", html)
        self.assertIn("Condor Arnhem OT", html)
        self.assertIn("Project toevoegen", html)

    def test_validation_and_number_padding(self):  # F5, F7
        for number in ("123", "a1"):
            html = self.client.post("/projecten/handmatig", data={"nummer": number, "naam": "X"}).get_data(as_text=True)
            self.assertIn("1 of 2 cijfers", html)
        self.assertIn("Vul een naam in.", self.client.post("/projecten/handmatig", data={"naam": " "}).get_data(as_text=True))
        self.client.post("/projecten/handmatig", data={"nummer": "2", "naam": "Gamified Learning", "kleur": "#123456"})
        html = self.client.post("/projecten/handmatig", data={"nummer": "02", "naam": "Ander"}).get_data(as_text=True)
        self.assertIn("al een project met nummer 02", html)
        self.client.post("/projecten/handmatig", data={"naam": "Stage"})  # no number is fine
        with self.db() as conn:
            rows = [tuple(r) for r in conn.execute("SELECT number, full_name, color FROM squads ORDER BY id")]
        self.assertEqual(rows[0], ("02", "02 Gamified Learning", "#123456"))
        self.assertEqual(rows[1][:2], (None, "Stage"))

    def test_edit_shows_everywhere(self):  # F8
        self.load_demo()
        self.client.post("/projecten/handmatig", data={"nummer": "02", "naam": "Gamified Learning"})
        with self.db() as conn:
            conn.execute("UPDATE students SET squad_id = ? WHERE name = 'Iris Bouma'", (self.project_id("02"),))
        self.client.post(f"/projecten/{self.project_id('02')}/bewerken",
                         data={"nummer": "02", "naam": "Gamified Learning 2", "opdrachtgever": "Condor", "kleur": "#123456"})
        for path in ("/projecten", "/", "/studenten"):
            self.assertIn("02 Gamified Learning 2", self.html(path), path)

    def test_delete_moves_students_without_project(self):  # F9
        self.client.post("/projecten/nieuw/open-ict")
        two = self.project_id("02")
        with self.db() as conn:
            for name in ("Sem Bakker", "Noor Peters", "Lars Koster"):
                conn.execute("INSERT INTO students (name, squad_id) VALUES (?, ?)", (name, two))
        self.assertIn("zitten 3 studenten", self.html("/projecten", verwijder=two))
        self.client.post(f"/projecten/{two}/verwijderen")
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM students WHERE squad_id IS NULL").fetchone()[0], 3)
        self.assertIn("3 studenten</strong>", self.html("/projecten"))

    def test_migration_takes_number_from_full_name(self):
        with self.db() as conn:
            conn.execute("DROP TABLE squads")
            conn.execute("CREATE TABLE squads (id INTEGER PRIMARY KEY, name TEXT NOT NULL, full_name TEXT NOT NULL, "
                         "color TEXT NOT NULL DEFAULT '#909DB9', is_demo INTEGER NOT NULL DEFAULT 0)")
            conn.execute("INSERT INTO squads (name, full_name) VALUES ('Horizon', '04 Horizon'), ('Stage', 'Stage')")
        create_app(self.db_path)
        with self.db() as conn:
            rows = [tuple(r) for r in conn.execute("SELECT number, name, client FROM squads ORDER BY id")]
        self.assertEqual(rows, [("04", "Horizon", ""), (None, "Stage", "")])
