"""Tests for importing students from Excel (spec 013). Files are made in the test; all names are invented."""

import io
import re
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from dashboard import create_app, excel_import
from dashboard.xlsx_reader import NotAnXlsx, read_workbook
from tests.xlsx_maker import make_xlsx

HEADER = ["Nummer", "Naam", "Project", "Coach", "Herkomst", "Semester", "Gilde", "Eventueel 2e gilde", "Discord"]
ROWS = [
    [1000001, "Anna de Boer", "02 - Opdrachtgever Spelleren", "Marieke", "Extern", "Semester 3", "Front-end developer (FE)", "", "anna_db"],
    [1000002, "Bram Visser", "05 - Iets met AI", "Stage", "Open ICT jaar 1", "Semester 4 (her)", "Game developer (GD)", "Cybersecurity engineer (CS)", ""],
    [1000003, "Cas Jansen", "21 - Bestaat niet", "Onbekend", "", "Semester 3", "ja", "", ""],
    ["", "", "", "", "", "", "", "", ""],
    [1000004, "Dewi Smit", "", "#N/A", "", "", "#N/A", "", ""],
]


class ImportTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "data" / "test.sqlite3"
        self.app = create_app(self.db_path, env_file=Path(self.tmp.name) / ".env")
        self.client = self.app.test_client()
        self.client.post("/beroepsrollen/toevoegen/open-ict")
        self.client.post("/semesters/toevoegen/open-ict")
        self.client.post("/projecten/nieuw/open-ict")
        with self.db() as conn:
            conn.execute("INSERT INTO staff (name, is_coach) VALUES ('Marieke Ploeg', 1), ('Ruben Smit', 1), "
                         "('Ruben de Wit', 1)")

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

    def upload(self, data: bytes, name="studenten.xlsx"):
        return self.client.post("/studenten/toevoegen/excel", data={"bestand": (io.BytesIO(data), name)},
                                content_type="multipart/form-data")

    def preview(self, sheets):
        response = self.upload(make_xlsx(sheets))
        self.assertEqual(response.status_code, 302, response.get_data(as_text=True)[:300])
        location = response.headers["Location"]
        return location, self.client.get(location, follow_redirects=True).get_data(as_text=True)

    def key(self, location):
        return location.rstrip("/").split("/")[-1].split("?")[0]


class TestReader(unittest.TestCase):
    def test_reads_values_numbers_errors_and_hidden(self):
        data = make_xlsx({"Lijst": [["Naam", "Nummer"], ["Anna de Boer", 1000001.0], ["#N/A", ""]],
                          "~Verborgen": [["x", "y"], ["1", "2"]]})
        sheets = read_workbook(data)
        self.assertEqual([s.name for s in sheets], ["Lijst", "Verborgen"])
        self.assertEqual(sheets[0].rows[1], ["Anna de Boer", "1000001"])
        self.assertEqual(sheets[0].rows[2][0], "#N/A")
        self.assertTrue(sheets[1].hidden)

    def test_broken_file(self):  # F2
        with self.assertRaises(NotAnXlsx):
            read_workbook(b"dit is geen zip")


class TestRecognising(unittest.TestCase):  # F4, F5
    def test_header_not_on_first_row_and_any_order(self):
        rows = [["Studenten sept 2026", ""], ["", ""], ["Gilde", "naam ", "STUDENT-NUMMER", "Opmerking"]]
        index = excel_import.find_header(rows)
        self.assertEqual(index, 2)
        self.assertEqual(excel_import.auto_mapping(rows[index]), ["primary_role", "name", "student_number", "note"])

    def test_mapping_rules(self):
        self.assertEqual(excel_import.mapping_error(["note", "unused"]), "Koppel een kolom aan Naam.")
        self.assertIn("meer dan één kolom", excel_import.mapping_error(["name", "coach", "coach"]))
        self.assertIsNone(excel_import.mapping_error(["name", "note", "note"]))


class TestImportPages(ImportTestCase):
    def test_card_is_active_and_upload_page(self):  # F1
        self.assertIn('href="/studenten/toevoegen/excel"', self.client.get("/studenten/toevoegen").get_data(as_text=True))
        self.assertIn('type="file"', self.client.get("/studenten/toevoegen/excel").get_data(as_text=True))

    def test_wrong_file(self):  # F2
        html = self.upload(b"geen excel", "lijst.txt").get_data(as_text=True)
        self.assertIn("geen Excelbestand (.xlsx)", html)

    def test_preview_counts_conversions_and_warnings(self):  # F6, F7
        with self.db() as conn:  # an existing student with another project and an empty semester
            two = conn.execute("SELECT id FROM squads WHERE number = '01'").fetchone()["id"]
            conn.execute("INSERT INTO students (name, squad_id) VALUES ('Dewi Smit', ?)", (two,))
        _, html = self.preview({"Draaitabel": [["Rijlabels", "Totaal"], ["x", "1"]], "Studenten": [HEADER] + ROWS})
        self.assertIn("<strong>3</strong> nieuw", html)       # Anna, Bram, Cas
        self.assertIn("<strong>1</strong> aanvullen", html)   # Dewi gets her student number
        self.assertIn("<strong>0</strong> overgeslagen", html)  # an empty row is not listed
        self.assertIn("Semester: semester 3", html)
        self.assertIn("Project: 02 Gamified Learning", html)
        self.assertIn("Coach: Marieke Ploeg", html)          # first name, one match
        self.assertIn("Invulling: Stage", html)              # "Stage" in the coach column
        self.assertIn("Semester: semester 4", html)          # "Semester 4 (her)"
        self.assertIn("Gilde: GD, CS", html)                 # spec 016: all guild columns together
        self.assertIn("Project 21 bestaat niet", html)
        self.assertIn("Coach &#39;Onbekend&#39; niet gevonden", html)
        self.assertIn("Gilde &#39;ja&#39; niet herkend", html)

    def test_existing_student_fill_change_and_import(self):  # F6, F8, F10, F11
        with self.db() as conn:
            one = conn.execute("SELECT id FROM squads WHERE number = '01'").fetchone()["id"]
            conn.execute("INSERT INTO students (name, squad_id, notes) VALUES ('anna  de boer', ?, 'Discord: anna_db')", (one,))
        location, html = self.preview({"Studenten": [HEADER] + ROWS[:1]})
        self.assertIn("<strong>1</strong> aanvullen", html)
        self.assertIn("+ Studentnummer: 1000001", html)
        self.assertIn("Project: 01 Van data mess to FAIR succes → <strong>02 Gamified Learning</strong>", html)
        self.assertIn("+ 1 notitieregel", html)              # Herkomst; Discord was already there
        key = self.key(location)
        response = self.client.post(f"/studenten/toevoegen/excel/{key}/importeren", data={"overnemen": ["2:squad"]})
        self.assertIn("melding=", response.headers["Location"])
        with self.db() as conn:
            row = dict(conn.execute("SELECT s.*, q.number AS squad_number FROM students s "
                                    "JOIN squads q ON q.id = s.squad_id").fetchone())
        self.assertEqual((row["student_number"], row["semester"], row["squad_number"]), ("1000001", 3, "02"))
        self.assertEqual(row["notes"].splitlines(), ["Discord: anna_db", "Herkomst: Extern"])

    def test_change_not_ticked_keeps_old_value(self):  # F6
        with self.db() as conn:
            one = conn.execute("SELECT id FROM squads WHERE number = '01'").fetchone()["id"]
            conn.execute("INSERT INTO students (name, squad_id) VALUES ('Anna de Boer', ?)", (one,))
        location, _ = self.preview({"Studenten": [HEADER] + ROWS[:1]})
        self.client.post(f"/studenten/toevoegen/excel/{self.key(location)}/importeren", data={})
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT squad_id FROM students").fetchone()[0], one)

    def test_new_students_selection_default_coach_and_twice(self):  # F8, F9, F11
        location, _ = self.preview({"Studenten": [HEADER] + ROWS})
        coach = self.coach_id("Ruben Smit")
        self.client.post(f"/studenten/toevoegen/excel/{self.key(location)}/importeren",
                         data={"nieuw": ["2", "3", "5"], "coach": str(coach)})   # not Cas (row 4)
        with self.db() as conn:
            students = {r["name"]: dict(r) for r in conn.execute("SELECT * FROM students")}
            guilds = [tuple(r) for r in conn.execute(
                "SELECT s.name, r.code, sg.guild_master_id FROM student_guilds sg JOIN students s ON s.id = sg.student_id "
                "JOIN professional_roles r ON r.id = sg.role_id ORDER BY s.name, r.code")]
        self.assertEqual(sorted(students), ["Anna de Boer", "Bram Visser", "Dewi Smit"])
        self.assertEqual(students["Anna de Boer"]["coach_id"], self.coach_id("Marieke Ploeg"))
        self.assertEqual(students["Bram Visser"]["coach_id"], coach)         # no coach in the file -> default
        self.assertEqual(students["Bram Visser"]["track"], "Stage")
        self.assertEqual(guilds, [("Anna de Boer", "FE", None), ("Bram Visser", "CS", None), ("Bram Visser", "GD", None)])
        self.assertEqual(students["Anna de Boer"]["notes"].splitlines(), ["Herkomst: Extern", "Discord: anna_db"])
        location, html = self.preview({"Studenten": [HEADER] + ROWS})       # the same file again
        self.assertIn("<strong>1</strong> nieuw", html)        # Cas, not ticked the first time
        self.assertIn("<strong>3</strong> ongewijzigd", html)
        self.client.post(f"/studenten/toevoegen/excel/{self.key(location)}/importeren", data={})
        with self.db() as conn:
            notes = conn.execute("SELECT notes FROM students WHERE name = 'Anna de Boer'").fetchone()[0]
        self.assertEqual(notes.splitlines(), ["Herkomst: Extern", "Discord: anna_db"])   # no double lines

    def coach_id(self, name):
        with self.db() as conn:
            return conn.execute("SELECT id FROM staff WHERE name = ?", (name,)).fetchone()[0]

    def test_existing_student_gets_extra_guild_and_empty_guild_master_filled(self):  # spec 016, F8
        with self.db() as conn:
            conn.execute("INSERT INTO staff (name, is_guild_master) VALUES ('Joost Hendriks', 1)")
            fe = conn.execute("SELECT id FROM professional_roles WHERE code = 'FE'").fetchone()[0]
            sid = conn.execute("INSERT INTO students (name) VALUES ('Eva Kok') RETURNING id").fetchone()[0]
            conn.execute("INSERT INTO student_guilds (student_id, role_id) VALUES (?, ?)", (sid, fe))
        location, html = self.preview({"Studenten": [["Naam", "Gilde", "Eventueel 2e gilde", "Gildemeester"],
                                                      ["Eva Kok", "Front-end developer (FE)", "UI/UX Designer (UX)", "Joost"]]})
        self.assertIn("+ Gildemeester bij FE: Joost Hendriks", html)
        self.assertIn("+ Gilde: UX", html)
        self.client.post(f"/studenten/toevoegen/excel/{self.key(location)}/importeren", data={})
        with self.db() as conn:
            rows = [tuple(r) for r in conn.execute(
                "SELECT r.code, st.name FROM student_guilds sg JOIN professional_roles r ON r.id = sg.role_id "
                "LEFT JOIN staff st ON st.id = sg.guild_master_id ORDER BY r.code")]
        self.assertEqual(rows, [("FE", "Joost Hendriks"), ("UX", None)])

    def test_first_name_without_accents(self):  # F7
        with self.db() as conn:
            conn.execute("INSERT INTO staff (name, is_coach) VALUES ('Andre Kok', 1)")
        _, html = self.preview({"Studenten": [["Naam", "Coach"], ["Eva Kok", "André"]]})
        self.assertIn("Coach: Andre Kok", html)

    def ticked(self, html):
        return re.findall(r'name="nieuw" value="(\d+)" checked', html)

    def test_only_rows_with_users_name_are_ticked(self):  # F6
        from dashboard import db
        db.set_setting(str(self.db_path), "portflow_user_name", "Marieke Ploeg")
        rows = [["Naam", "Coach", "Opmerking"],
                ["Eva Kok", "marieke", ""],                      # first name: ticked
                ["Tim Vos", "Ruben Smit", "Marieke Ploeg"],      # full name in another column: ticked
                ["Fleur Bos", "Ruben Smit", "Gesprek met Marieke"],  # in a sentence: not ticked
                ["Jesse Peters", "Mariek", ""]]                  # a different name: not ticked
        _, html = self.preview({"Studenten": rows})
        self.assertEqual(self.ticked(html), ["2", "3"])
        self.assertIn("Jouw naam in kolom Coach", html)
        self.assertIn("Jouw naam in kolom Opmerking", html)
        self.assertIn("Importeren (2 toevoegen", html)

    def test_all_ticked_when_user_unknown(self):  # F6
        _, html = self.preview({"Studenten": [["Naam", "Coach"], ["Eva Kok", "Marieke"], ["Tim Vos", ""]]})
        self.assertEqual(self.ticked(html), ["2", "3"])
        self.assertIn("alle nieuwe studenten aangevinkt", html)

    def test_ambiguous_first_name(self):  # F7
        _, html = self.preview({"Studenten": [["Naam", "Coach"], ["Eva Kok", "Ruben"]]})
        self.assertIn("past bij meer dan één persoon", html)

    def test_unknown_columns_ask_for_mapping(self):  # F5
        location, html = self.preview({"Blad1": [["Leerling", "Groep"], ["Eva Kok", "02"]]})
        self.assertIn("Kolommen koppelen", html)
        key = self.key(location)
        mapping_url = f"/studenten/toevoegen/excel/{key}/koppelen"
        html = self.client.post(mapping_url, data={"kopregel": "1", "kolom0": "note", "kolom1": "squad"}).get_data(as_text=True)
        self.assertIn("Koppel een kolom aan Naam.", html)
        response = self.client.post(mapping_url, data={"kopregel": "1", "kolom0": "name", "kolom1": "squad"})
        html = self.client.get(response.headers["Location"]).get_data(as_text=True)
        self.assertIn("Eva Kok", html)
        self.assertIn("Project: 02 Gamified Learning", html)

    def test_skipped_rows(self):  # F6
        _, html = self.preview({"Studenten": [["Naam", "Nummer"], ["Eva Kok", 1], ["", 2], ["Eva Kok", 1]]})
        self.assertIn("Geen naam", html)
        self.assertIn("Staat al eerder in het bestand", html)

    def test_cancel_saves_nothing(self):  # F11
        location, _ = self.preview({"Studenten": [HEADER] + ROWS})
        self.client.post(f"/studenten/toevoegen/excel/{self.key(location)}/annuleren")
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM students").fetchone()[0], 0)
        self.assertEqual(self.client.get(location).status_code, 404)   # the rows are gone

    def test_notes_on_edit_page(self):  # F12
        with self.db() as conn:
            student = conn.execute("INSERT INTO students (name) VALUES ('Eva Kok') RETURNING id").fetchone()[0]
        self.client.post(f"/studenten/{student}/bewerken", data={"name": "Eva Kok", "notes": "Discord: eva\nHerkomst: Extern"})
        html = self.client.get(f"/studenten/{student}/bewerken").get_data(as_text=True)
        self.assertIn("Discord: eva\nHerkomst: Extern</textarea>", html)


if __name__ == "__main__":
    unittest.main()
