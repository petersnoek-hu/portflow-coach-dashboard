"""Tests for spec 019 (eenvoudige start): all shared students, hiding, the semester list in the
table, assessors and fetching. A fake Portflow; all names are invented."""

import base64
import json
import re
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dashboard import create_app, db, portflow_link, staff

LEVELS = [{"id": "a", "label": "Startniveau"}, {"id": "b", "label": "1"}, {"id": "c", "label": "2"}]
GOALS = [{"id": 1, "name": "Overzicht creëren"}, {"id": 2, "name": "Samenwerken"}]   # OC, SW


def share(user_id, name, portfolio_id):
    return {"portfolio_id": portfolio_id, "inviter": {"id": user_id, "name": name, "current_role": "student"}}


def item(level, day, reviewer):
    return {"type": "criterion_evaluation", "role": "teacher", "date": f"{day}T10:00:00.000Z",
            "evaluation": {"level": level, "level_set": LEVELS, "review_request_id": 1,
                           "review_request_title": "Evaluatie", "review_request_scored": True,
                           "reviewer": {"name": reviewer}}}


def make_token(hours=8):
    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    exp = datetime.now(timezone.utc) + timedelta(hours=hours)
    return f"{part({'alg': 'none'})}.{part({'exp': int(exp.timestamp())})}.sig"


class FakeApi:
    def __init__(self):
        self.shares = [share(11, "Anna de Boer", 101), share(11, "Anna de Boer", 102),
                       share(12, "Bram Visser", 103), share(13, "Cas Jansen", 104)]
        self.valid = set()
        self.fetched = []   # portfolio ids whose goals were asked for
        # OC by a guild master, SW by a coach; evaluations in the running semester period.
        today = datetime.now().date().isoformat()
        self.items = {1: [item("c", today, "Gerrit Gildemeester")], 2: [item("b", today, "Carla Coach")]}

    def shared_with_me(self, token):
        return 200, self.shares

    def check_token(self, token):
        return 200 if token in self.valid else 401

    def own_portfolio_error(self, token, portfolio_id):
        return None

    def own_name(self, token, portfolio_id):
        return "Marieke Ploeg"

    def goals(self, token, portfolio_id, **retry):
        self.fetched.append(portfolio_id)
        return 200, GOALS

    def feedback_items(self, token, portfolio_id, goal_id, **retry):
        return 200, self.items.get(goal_id, [])

    def reviews(self, token, portfolio_id, **retry):
        return 500, None   # spec 042: no review list, so every student is fetched fully

    def received_invitations(self, token, own, **retry):
        return 200, []


class SimpleStartCase(unittest.TestCase):
    def setUp(self):
        portflow_link.clear_cache()
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.db_path = base / "data" / "test.sqlite3"
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()
        self.connection = self.app.extensions["portflow"]
        self.connection.profile_dir = base / "profile"
        self.api = FakeApi()
        self.connection.api = self.api
        self.fetcher = self.app.extensions["fetcher"]
        self.fetcher.api = self.api
        self.fetcher.spawn = lambda work: work()

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

    def names(self, html):
        return re.findall(r'data-sort-name="([^"]+)"', html)

    def html(self, path="/", **query):
        return self.client.get(path, query_string=query).get_data(as_text=True)

    def add(self, name, **fields):
        columns = ["name", *fields]
        with self.db() as conn:
            return conn.execute(f"INSERT INTO students ({', '.join(columns)}) VALUES ({', '.join('?' * len(columns))}) "
                                "RETURNING id", (name, *fields.values())).fetchone()[0]


class TestFirstStart(SimpleStartCase):
    def test_connecting_adds_all_shared_students_with_their_levels(self):   # F1, F2, F10
        self.connect()
        html = self.html()
        self.assertEqual(self.names(html), ["anna de boer", "bram visser", "cas jansen"])
        self.assertIn("3 van 3 studenten", html)
        # Every assessor counts, also without being on Coaches or Gildemeesters (F10).
        self.assertIn('aria-label="OC: 2"', html)
        self.assertIn('aria-label="SW: 1"', html)
        self.assertEqual(sorted(self.api.fetched), [101, 102, 103, 104])

    def test_assessors_are_added_with_their_role(self):   # F11
        self.connect()
        with self.db() as conn:
            people = {r["name"]: (r["is_coach"], r["is_guild_master"]) for r in conn.execute("SELECT * FROM staff")}
        self.assertEqual(people, {"Marieke Ploeg": (1, 0), "Gerrit Gildemeester": (1, 1), "Carla Coach": (1, 0)})
        self.fetcher.start()   # a second round adds nobody twice
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM staff").fetchone()[0], 3)

    def test_no_grouping_while_nothing_is_assigned(self):   # F8
        self.connect()
        html = self.html()
        self.assertNotIn('class="group-header"', html)
        self.assertIn('<option value="none" selected>Niet groeperen</option>', html)
        with self.db() as conn:
            conn.execute("UPDATE students SET semester = 2 WHERE name = 'Bram Visser'")
        html = self.html()
        self.assertIn('class="group-header"', html)
        self.assertIn('<option value="squad" selected>Groeperen: Project</option>', html)
        self.assertNotIn('class="group-header"', self.html(groep="none"))   # the user's own choice counts

    def test_second_connection_does_not_start_a_round(self):   # F2: only the very first time
        self.connect()
        self.api.fetched.clear()
        self.connect()
        self.assertEqual(self.api.fetched, [])


class TestNewShares(SimpleStartCase):
    def test_new_share_appears_and_hidden_student_stays_hidden(self):   # F3
        self.connect()
        with self.db() as conn:
            conn.execute("UPDATE students SET is_hidden = 1 WHERE name = 'Bram Visser'")
        self.api.shares.append(share(14, "Daan Smit", 105))
        self.fetcher.start()
        self.assertEqual(self.names(self.html()), ["anna de boer", "cas jansen", "daan smit"])
        self.assertEqual(len(self.names(self.html(wie="alle"))), 4)

    def test_name_shared_twice_is_not_added_while_unlinked(self):   # spec 015, F4 stays
        self.add("Eva Bos")
        self.api.shares += [share(15, "Eva Bos", 106), share(16, "Eva Bos", 107)]
        self.connect()
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM students WHERE name = 'Eva Bos'").fetchone()[0], 1)


class TestHiding(SimpleStartCase):
    def setUp(self):
        super().setUp()
        self.ids = [self.add(n) for n in ("Anna de Boer", "Bram Visser", "Cas Jansen")]

    def test_hide_and_show(self):   # F4, F5, F6
        response = self.client.post(f"/studenten/{self.ids[1]}/verbergen", headers={"X-Requested-With": "fetch"})
        self.assertEqual(response.status_code, 204)
        html = self.html()
        self.assertEqual(self.names(html), ["anna de boer", "cas jansen"])
        self.assertIn("2 van 3 studenten", html)
        self.assertIn('<option value="zichtbaar" selected>Alle studenten die ik niet heb verborgen</option>', html)
        html = self.html(wie="alle")
        self.assertIn("3 van 3 studenten", html)
        self.assertEqual(html.count("is-hidden-student"), 1)
        self.client.post(f"/studenten/{self.ids[1]}/tonen", data={"next": "/?wie=alle"})
        self.assertEqual(len(self.names(self.html())), 3)

    def test_all_students_filters_nothing(self):   # F6: "Alle studenten", added 2026-11-11
        self.client.post(f"/studenten/{self.ids[1]}/verbergen", headers={"X-Requested-With": "fetch"})
        html = self.html(wie="iedereen")
        self.assertEqual(len(self.names(html)), 3)
        self.assertIn("3 van 3 studenten", html)
        self.assertEqual(html.count("is-hidden-student"), 1)   # dimmed, with the eye icons (2026-11-19)
        self.assertIn("/verbergen", html)
        self.assertIn("/tonen", html)
        options = re.findall(r'<option value="([a-z]+)"[^>]*>', html.split('name="wie"')[1].split("</select>")[0])
        self.assertEqual(options[0], "iedereen")

    def test_without_javascript_back_to_the_table(self):
        response = self.client.post(f"/studenten/{self.ids[0]}/verbergen", data={"next": "/?wie=alle"})
        self.assertEqual(response.headers["Location"], "/?wie=alle")
        self.assertEqual(self.client.post("/studenten/999/verbergen").status_code, 404)

    def test_eye_icon_with_every_choice(self):   # F6 (changed 2026-11-19)
        with self.db() as conn:
            coach = conn.execute("INSERT INTO staff (name, is_coach) VALUES ('Marieke Ploeg', 1) RETURNING id").fetchone()[0]
            conn.execute("UPDATE students SET coach_id = ?, is_hidden = 1 WHERE id = ?", (coach, self.ids[0]))
        db.set_setting(str(self.db_path), "portflow_user_name", "Marieke Ploeg")
        html = self.html(wie="coach")
        self.assertEqual(self.names(html), ["anna de boer"])
        self.assertIn("is-hidden-student", html)            # dimmed, with "Weer tonen"
        self.assertIn("Weer tonen in dit overzicht", html)
        self.assertIn("Verbergen in dit overzicht", self.html(wie="iedereen"))

    def test_all_hidden(self):
        for student_id in self.ids:
            self.client.post(f"/studenten/{student_id}/verbergen")
        self.assertIn("Je hebt alle studenten verborgen", self.html())


class TestSemesterInTable(SimpleStartCase):
    def test_semester_is_text_on_overzicht(self):   # F7, changed 2026-11-18: no list any more
        student = self.add("Anna de Boer")
        self.assertNotIn("semester-pick", self.html())
        self.client.post(f"/studenten/{student}/veld/semester", data={"waarde": "5"})   # at Beheer › Studenten
        self.assertRegex(self.html(), r'<span class="student-sub">\s*Sem 5')


class TestEmptyColumns(SimpleStartCase):
    def test_empty_extra_column_is_not_shown(self):   # F9
        student = self.add("Anna de Boer")
        self.assertNotIn('data-sort="guild_master"', self.html())
        self.client.post("/gildes/toevoegen/open-ict")
        with self.db() as conn:
            master = conn.execute("INSERT INTO staff (name, is_guild_master) VALUES ('Gerrit Gildemeester', 1) "
                                  "RETURNING id").fetchone()[0]
            conn.execute("INSERT INTO student_guilds (student_id, guild_id, guild_master_id) "
                         "SELECT ?, id, ? FROM guilds LIMIT 1", (student, master))
        self.assertIn('data-sort="guild_master"', self.html())

    def test_own_choice_counts(self):   # F9: a column switched on stays, also when empty
        self.add("Anna de Boer")
        self.client.post("/studenten/kolommen", data={"kolom": ["track"], "next": "/"})
        html = self.html()
        self.assertIn('data-sort="track"', html)
        self.assertNotIn('data-sort="guild_master"', html)


class TestAssessors(SimpleStartCase):
    def setUp(self):
        super().setUp()
        self.student = self.add("Anna de Boer", semester=3)
        with self.db() as conn:
            conn.execute("INSERT INTO evaluations (student_id, skill, kind, level, date, assessor) "
                         "VALUES (?, 'OC', 'assessed', '2', '', 'Kevin Brandsma')", (self.student,))
            self.kevin = conn.execute("INSERT INTO staff (name, is_coach) VALUES ('Kevin Brandsma', 1) RETURNING id").fetchone()[0]

    def test_exclude_on_the_edit_page(self):   # F12
        self.assertIn('aria-label="OC: 2"', self.html())
        self.client.post(f"/coaches/{self.kevin}/bewerken", data={"voornaam": "Kevin", "achternaam": "Brandsma",
                                                                  "uitsluiten": "1"})
        self.assertIn('aria-label="OC: -/-"', self.html())
        self.assertIn("Telt niet mee", self.html("/coaches"))
        self.assertIn('name="uitsluiten" value="1" checked', self.html(f"/coaches/{self.kevin}/bewerken"))
        self.client.post(f"/coaches/{self.kevin}/bewerken", data={"voornaam": "Kevin", "achternaam": "Brandsma"})
        self.assertIn('aria-label="OC: 2"', self.html())

    def test_removed_assessor_stays_excluded_and_is_not_added_again(self):   # F13
        self.client.post(f"/coaches/{self.kevin}/verwijderen")
        self.assertIn('aria-label="OC: -/-"', self.html())
        with self.db() as conn:
            self.assertEqual(staff.add_found_assessors(conn), 0)
            self.assertFalse(conn.execute("SELECT 1 FROM staff WHERE name = 'Kevin Brandsma'").fetchone())
            staff.add(conn, ["Kevin Brandsma"], "coach")   # adding yourself makes them count again
        self.assertIn('aria-label="OC: 2"', self.html())

    def test_removing_the_user_does_not_exclude_their_evaluations(self):
        db.set_setting(str(self.db_path), "portflow_user_name", "Kevin Brandsma")
        self.client.post(f"/coaches/{self.kevin}/verwijderen")
        self.assertIn('aria-label="OC: 2"', self.html())


class TestVisibleFetch(SimpleStartCase):
    def ids(self):
        with self.db() as conn:
            return {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM students")}

    def test_only_the_students_on_the_screen(self):   # spec 041, F1-F3, F5
        self.connect()   # first round: everyone (F6)
        ids = self.ids()
        with self.db() as conn:
            conn.execute("UPDATE students SET is_hidden = 1 WHERE name = 'Cas Jansen'")
        self.api.fetched.clear()
        self.client.post("/portflow/verversen", data={"student": [str(ids["Bram Visser"])], "scherm": "1"})
        self.assertEqual(self.api.fetched, [103])               # Anna is not on the screen
        self.api.fetched.clear()
        self.api.shares.append(share(14, "Daan Smit", 105))   # a new share is fetched too, after the screen (F5)
        self.client.post("/portflow/verversen", data={"student": [str(ids["Bram Visser"])], "scherm": "1"})
        self.assertEqual(self.api.fetched, [103, 105])
        self.api.fetched.clear()
        self.client.post("/portflow/verversen", data={"student": [str(ids["Cas Jansen"])], "scherm": "1"})   # hidden but on the screen
        self.assertEqual(self.api.fetched, [104])
        self.api.fetched.clear()
        self.client.post("/portflow/verversen", data={"scherm": "1"})   # a screen without students: only the lists
        self.assertEqual(self.api.fetched, [])


    def test_page_without_students_fetches_everyone(self):   # spec 041, F4 (spec 019, F14)
        self.connect()
        ids = self.ids()
        with self.db() as conn:
            conn.execute("UPDATE students SET is_hidden = 1 WHERE name = 'Cas Jansen'")
        self.api.fetched.clear()
        self.client.post("/portflow/verversen", data={"student": [str(ids["Bram Visser"])]})
        self.assertEqual(self.api.fetched[0], 103)
        self.assertEqual(sorted(self.api.fetched), [101, 102, 103])
        self.api.fetched.clear()
        self.client.post("/portflow/verversen")
        self.assertEqual(sorted(self.api.fetched), [101, 102, 103])

    def test_first_round_fetches_everyone_even_from_a_screen(self):   # spec 041, F6
        self.api.fetched.clear()
        self.connect()
        self.assertEqual(sorted(set(self.api.fetched)), [101, 102, 103, 104])

    def test_started_from_app_js_the_page_stays(self):   # spec 041, F7
        self.connect()
        response = self.client.post("/portflow/verversen", data={"scherm": "1"}, headers={"X-Requested-With": "fetch"})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.post("/portflow/verversen", data={"scherm": "1"}).status_code, 302)   # without JavaScript

    def test_button_shows_only_the_time(self):   # spec 041, F8 (changed 2026-11-23: no number)
        self.connect()
        ids = self.ids()
        self.client.post("/portflow/verversen", data={"student": [str(ids["Bram Visser"])], "scherm": "1"})
        html = self.client.get("/portflow/status").get_json()["refresh_html"]
        self.assertIn("Bijgewerkt om", html)
        self.assertNotIn("student bijgewerkt", html)

    def test_pages_mark_their_students_and_live_parts(self):   # spec 041, F1-F3, F7
        self.connect()
        sid = self.ids()["Bram Visser"]
        for path, query in (("/evaluaties", {"wie": "iedereen"}), (f"/studenten/{sid}", {}), ("/", {})):
            with self.subTest(path=path):
                html = self.html(path, **query)
                self.assertIn(f'data-student-id="{sid}"', html)
                self.assertIn(f'data-live="cell-{sid}-OC"', html)
                self.assertNotIn("data-reload-after-fetch", html)
                self.assertNotIn("data-reload-when-fetched", html)
        self.assertIn('data-live="to-review"', self.html("/evaluaties"))
        self.assertIn('data-live="weeks"', self.html(f"/studenten/{sid}"))
        self.assertIn('data-live="student-open"', self.html(f"/studenten/{sid}"))
        self.assertIn('data-live="nav-count"', self.html("/instellingen"))

    def test_status_tells_which_students_are_done(self):   # spec 039, spec 041, F7
        self.connect()
        sid = self.ids()["Bram Visser"]
        self.client.post("/portflow/verversen", data={"student": [str(sid)], "scherm": "1"})
        first = self.client.get("/portflow/status").get_json()
        self.assertEqual(first["fetch_students"], [sid])
        self.assertTrue(first["fetch_round"])
        self.client.post("/portflow/verversen")
        self.assertNotEqual(self.client.get("/portflow/status").get_json()["fetch_round"], first["fetch_round"])


class TestMigration(unittest.TestCase):
    def test_existing_students_become_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "old.sqlite3")
            conn = sqlite3.connect(path)
            conn.execute("CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT NOT NULL, semester INTEGER, "
                         "is_demo INTEGER NOT NULL DEFAULT 0)")
            conn.execute("INSERT INTO students (name) VALUES ('Anna de Boer')")
            conn.commit()
            conn.close()
            db.init_db(path)
            conn = db.connect(path)
            try:
                self.assertEqual(conn.execute("SELECT is_hidden FROM students").fetchone()[0], 0)
                self.assertTrue(conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'excluded_assessors'").fetchone())
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
