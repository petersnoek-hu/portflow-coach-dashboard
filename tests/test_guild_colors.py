"""Spec 006, F14 (2026-11-23): the Open-ICT guilds get the LEF colours from docs/gildes-openict.md."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from dashboard import db, guilds


class GuildColorsCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        db.init_db(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def colors(self):
        conn = sqlite3.connect(self.db_path)
        try:
            return dict(conn.execute("SELECT code, color FROM guilds"))
        finally:
            conn.close()

    def test_preset_has_a_lef_colour_for_every_guild(self):
        colors = guilds.preset_colors()
        self.assertEqual(set(colors), {code for code, _, _ in guilds.read_preset()})
        self.assertEqual((colors["BE"], colors["FE"], colors["UX"]), ("#B71C1C", "#D35400", "#880E4F"))

    def test_add_preset_uses_the_lef_colours(self):
        conn = db.connect(self.db_path)
        try:
            guilds.add_preset(conn)
        finally:
            conn.close()
        self.assertEqual(self.colors()["CI"], "#59C759")

    def test_existing_default_colours_are_replaced_once(self):
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute("INSERT INTO guilds (code, name, color) VALUES ('BE', 'Back-end gilde', '#909DB9'), "
                         "('FE', 'Front-end gilde', '#123456'), ('XY', 'Eigen gilde', '#909DB9')")
            conn.execute("DELETE FROM settings WHERE key = 'guild_colors_lef'")   # as in a database from before
        conn.close()
        db.init_db(self.db_path)
        self.assertEqual(self.colors(), {"BE": "#B71C1C", "FE": "#123456", "XY": "#909DB9"})   # own colour kept

        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute("UPDATE guilds SET color = '#909DB9' WHERE code = 'BE'")   # chosen by the user later
        conn.close()
        db.init_db(self.db_path)
        self.assertEqual(self.colors()["BE"], "#909DB9")   # only once

    def test_text_stays_readable(self):
        self.assertEqual(guilds.text_color("#59C759"), "#1f1f1f")   # LEF green of CI: dark text
        for color in ("#B71C1C", "#001F3F", "#880E4F", "#909DB9"):
            self.assertEqual(guilds.text_color(color), "#fff", color)


if __name__ == "__main__":
    unittest.main()
