"""Tests for the Portflow connection (spec 003). No real browser or Portflow calls."""

import base64
import json
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dashboard import create_app, db
from dashboard.portflow_connection import (
    S_PORTFOLIO_ID, PortflowConnection, State, initials, local_time, remaining,
)
from dashboard.portflow_login import CaptureResult, LoginError
from dashboard.portflow_token import ENV_KEY, TokenStore, decode_payload, expires_at

NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def make_token(expires: datetime) -> str:
    """A fake JWT (not signed) with only an 'exp' claim."""
    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

    return f"{part({'alg': 'none'})}.{part({'exp': int(expires.timestamp()), 'sub': 1})}.signature"


class FakeApi:
    def __init__(self):
        self.valid = set()
        self.status_for_unknown = 401

    def check_token(self, token):
        return 200 if token in self.valid else self.status_for_unknown

    def own_name(self, token, portfolio_id):
        return "Anna van der Berg"

    def own_portfolio_error(self, token, portfolio_id):
        return None if portfolio_id == "23588" else "Niet je eigen portfolio."


class FakeBrowser:
    """Stands in for portflow_login.capture_token. `script` lists what each call returns."""

    def __init__(self):
        self.script = []
        self.calls = []

    def __call__(self, canvas_url, profile_dir, *, headless, timeout_s, validate, cancel):
        self.calls.append("headless" if headless else "visible")
        outcome = self.script.pop(0)
        if isinstance(outcome, LoginError):
            raise outcome
        assert validate(outcome.token)
        return outcome


class ConnectionTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.database = str(self.dir / "test.sqlite3")
        db.init_db(self.database)
        self.store = TokenStore(self.dir / ".env")
        self.api = FakeApi()
        self.browser = FakeBrowser()
        self.clock = [NOW]
        self.conn = PortflowConnection(
            self.database, self.store, self.dir / "profile",
            capture=self.browser, api=self.api, now=lambda: self.clock[0], spawn=lambda work: work(),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def fresh_token(self, hours=8.0):
        token = make_token(self.clock[0] + timedelta(hours=hours))
        self.api.valid.add(token)
        return token

    def ok(self, hours=8.0, portfolio_id="23588"):
        return CaptureResult(token=self.fresh_token(hours), portfolio_id=portfolio_id)

    @staticmethod
    def fail(kind="closed"):
        return LoginError(kind, "Inloggen is niet afgerond.")


class TestToken(ConnectionTestCase):
    def test_expiry_from_jwt(self):
        token = make_token(NOW + timedelta(hours=8))
        self.assertEqual(expires_at(token), NOW + timedelta(hours=8))
        self.assertIsNone(decode_payload("geen-token"))

    def test_store_keeps_other_lines(self):
        (self.dir / ".env").write_text("OTHER=1\n")
        self.store.save("abc.def.ghi")
        self.assertEqual(self.store.read(), "abc.def.ghi")
        self.store.save("new.token.value")
        text = (self.dir / ".env").read_text()
        self.assertEqual(text.count(ENV_KEY), 1)
        self.assertIn("OTHER=1", text)
        self.store.delete()
        self.assertIsNone(self.store.read())
        self.assertIn("OTHER=1", (self.dir / ".env").read_text())

    def test_display_helpers(self):
        self.assertEqual(initials("Anna van der Berg"), "AB")
        self.assertEqual(remaining(NOW + timedelta(hours=3, minutes=12), NOW), "nog 3 u 12 min")
        self.assertRegex(local_time(NOW, NOW), r"^\d\d:\d\d$")
        self.assertRegex(local_time(NOW + timedelta(days=2), NOW), r"^\d+ nov \d\d:\d\d$")


class TestConnect(ConnectionTestCase):
    def test_connect_saves_token_name_and_staff(self):  # F1, F2
        self.browser.script = [self.ok()]
        self.conn.connect()
        self.assertEqual(self.conn.state, State.CONNECTED)
        self.assertEqual(self.browser.calls, ["visible"])
        self.assertIsNotNone(self.store.read())
        self.assertEqual(self.conn.user_name, "Anna van der Berg")
        conn = db.connect(self.database)
        names = [r["name"] for r in conn.execute("SELECT name FROM staff")]
        conn.close()
        self.assertIn("Anna van der Berg", names)

    def test_only_one_attempt_at_a_time(self):  # F3
        started = threading.Event()
        release = threading.Event()
        threads = []

        def slow_browser(*args, **kwargs):
            started.set()
            release.wait(2)
            return self.ok()

        self.conn.capture = slow_browser
        self.conn.spawn = lambda work: threads.append(threading.Thread(target=work)) or threads[-1].start()
        self.conn.connect()
        started.wait(2)
        self.assertEqual(self.conn.state, State.LOGGING_IN)
        self.conn.connect()  # ignored
        self.assertEqual(len(threads), 1)
        release.set()
        threads[0].join(2)
        self.assertEqual(self.conn.state, State.CONNECTED)

    def test_closed_window_returns_to_previous_state(self):  # F4
        self.browser.script = [self.fail("closed")]
        self.conn.connect()
        self.assertEqual(self.conn.state, State.DISCONNECTED)
        self.assertIn("niet afgerond", self.conn.message)


class TestPaste(ConnectionTestCase):
    def test_paste_valid_token(self):  # F5
        self.assertIsNone(self.conn.paste_token(self.fresh_token(), "23588"))
        self.assertEqual(self.conn.state, State.CONNECTED)

    def test_paste_rejections(self):  # F5
        self.assertIn("geen Portflow-token", self.conn.paste_token("rommel"))
        expired = make_token(NOW - timedelta(minutes=1))
        self.assertIn("verlopen", self.conn.paste_token(expired, "23588"))
        unknown = make_token(NOW + timedelta(hours=8))
        self.assertIn("accepteert", self.conn.paste_token(unknown, "23588"))
        self.assertIn("portfolio-id", self.conn.paste_token(self.fresh_token()))
        self.assertIn("eigen portfolio", self.conn.paste_token(self.fresh_token(), "999"))
        self.assertEqual(self.conn.state, State.DISCONNECTED)

    def test_known_portfolio_id_is_reused(self):  # F5
        db.set_setting(self.database, S_PORTFOLIO_ID, "23588")
        self.assertIsNone(self.conn.paste_token(self.fresh_token()))


class TestStartUp(ConnectionTestCase):
    def test_valid_token_connects_without_window(self):  # F6
        self.store.save(self.fresh_token())
        self.conn.start_up()
        self.assertEqual(self.conn.state, State.CONNECTED)
        self.assertEqual(self.browser.calls, [])

    def test_no_token_opens_login_window(self):  # F6
        self.browser.script = [self.ok()]
        self.conn.start_up()
        self.assertEqual(self.browser.calls, ["visible"])
        self.assertEqual(self.conn.state, State.CONNECTED)

    def test_expired_token_refreshes_first(self):  # F6, F7
        self.store.save(make_token(NOW - timedelta(hours=1)))
        self.browser.script = [self.ok()]
        self.conn.start_up()
        self.assertEqual(self.browser.calls, ["visible"])  # visible refresh is the default
        self.assertEqual(self.conn.state, State.CONNECTED)


class TestRefresh(ConnectionTestCase):
    def connected(self, hours=8.0):
        self.store.save(self.fresh_token(hours))
        self.conn.start_up()
        self.assertEqual(self.conn.state, State.CONNECTED)

    def test_refresh_one_hour_before_expiry(self):  # F7
        self.conn.save_settings("", always_visible=False)
        self.connected(hours=8)
        self.conn.tick()
        self.assertEqual(self.browser.calls, [])
        self.clock[0] += timedelta(hours=7, minutes=1)
        self.browser.script = [self.ok()]
        self.conn.tick()
        self.assertEqual(self.browser.calls, ["headless"])
        self.assertEqual(self.conn.state, State.CONNECTED)
        self.assertEqual(self.conn.expires, self.clock[0] + timedelta(hours=8))
        self.assertEqual(self.conn.status()["last_refresh_kind"], "automatisch")

    def test_visible_by_default(self):  # F8
        self.connected(hours=0.5)
        self.browser.script = [self.ok()]
        self.conn.tick()
        self.assertEqual(self.browser.calls, ["visible"])

    def test_visible_fallback_when_headless_fails(self):  # F8
        self.conn.save_settings("", always_visible=False)
        self.connected(hours=0.5)
        self.browser.script = [self.fail(), self.ok()]
        self.conn.tick()
        self.assertEqual(self.browser.calls, ["headless", "visible"])
        self.assertEqual(self.conn.state, State.CONNECTED)

    def test_always_visible_skips_headless(self):  # F8
        self.conn.save_settings("https://canvas.example/tool", always_visible=True)
        self.connected(hours=0.5)
        self.browser.script = [self.ok()]
        self.conn.tick()
        self.assertEqual(self.browser.calls, ["visible"])

    def test_no_automatic_windows_after_failure(self):  # F9
        self.connected(hours=0.5)
        self.browser.script = [self.fail()]
        self.conn.tick()
        self.assertEqual(self.conn.state, State.NEEDS_LOGIN)
        self.clock[0] += timedelta(minutes=20)
        self.conn.tick()
        self.assertEqual(self.browser.calls, ["visible"])  # no new pop-up; the user clicks

    def test_needs_login_and_retry_interval(self):  # F9 (headless setting)
        self.conn.save_settings("", always_visible=False)
        self.connected(hours=0.5)
        self.browser.script = [self.fail(), self.fail()]
        self.conn.tick()
        self.assertEqual(self.conn.state, State.NEEDS_LOGIN)
        self.assertTrue(self.conn.status()["sub"].startswith("verloopt om"))
        self.clock[0] += timedelta(minutes=10)
        self.conn.tick()
        self.assertEqual(len(self.browser.calls), 2)  # no new attempt within 15 minutes
        self.clock[0] += timedelta(minutes=6)
        self.browser.script = [self.fail()]
        self.conn.tick()
        self.assertEqual(self.browser.calls[2:], ["headless"])  # retries do not pop up a window

    def test_expired_and_unauthorized(self):  # F10
        self.conn.save_settings("", always_visible=False)
        self.connected(hours=0.5)
        self.browser.script = [self.fail(), self.fail()]
        self.conn.tick()
        self.clock[0] += timedelta(minutes=31)
        self.browser.script = [self.fail()]
        self.conn.tick()
        self.assertEqual(self.conn.state, State.EXPIRED)
        self.assertIsNone(self.conn.token)

        other = PortflowConnection(self.database, self.store, self.dir / "p", capture=self.browser,
                                   api=self.api, now=lambda: self.clock[0], spawn=lambda w: w())
        other.store.save(self.fresh_token())
        other.start_up()
        other.mark_unauthorized()
        self.assertEqual(other.state, State.EXPIRED)

    def test_disconnect_removes_token(self):  # F11
        self.connected()
        self.conn.disconnect()
        self.assertEqual(self.conn.state, State.DISCONNECTED)
        self.assertIsNone(self.store.read())


class TestStatusDisplay(ConnectionTestCase):
    def test_every_state_has_dot_label_and_sub(self):  # F12
        expected = {
            State.DISCONNECTED: ("grey", "Niet verbonden", ""),
            State.LOGGING_IN: ("blue", "Inloggen…", "Log in in het Chrome-venster"),
            State.CONNECTED: ("green", "Verbonden", "tot "),
            State.REFRESHING: ("green", "Verversen…", ""),
            State.NEEDS_LOGIN: ("orange", "Opnieuw inloggen nodig", "verloopt om "),
            State.EXPIRED: ("red", "Verlopen", "sinds "),
        }
        self.conn._set_token(self.fresh_token(), NOW + timedelta(hours=8))
        for state, (dot, label, sub) in expected.items():
            with self.subTest(state=state):
                self.conn.state = state
                status = self.conn.status()
                self.assertEqual((status["dot"], status["label"]), (dot, label))
                self.assertTrue(status["sub"].startswith(sub))

    def test_status_never_contains_token(self):
        token = self.fresh_token()
        self.conn.paste_token(token, "23588")
        self.assertNotIn(token, json.dumps(self.conn.status()))


class TestRoutes(ConnectionTestCase):
    def setUp(self):
        super().setUp()
        self.app = create_app(self.database, env_file=self.dir / ".env")
        self.app.extensions["portflow"] = self.conn
        self.client = self.app.test_client()

    def test_status_endpoint(self):  # F14
        token = self.fresh_token()
        self.conn.paste_token(token, "23588")
        response = self.client.get("/portflow/status")
        data = response.get_json()
        self.assertEqual(data["state"], "connected")
        self.assertIn("Verbonden", data["status_html"])
        self.assertIn("Anna van der Berg", data["user_html"])
        self.assertNotIn(token, response.get_data(as_text=True))

    def test_panel_and_buttons_per_state(self):  # F12, F13
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("Verbinden met Portflow", html)
        self.assertIn("Token plakken", html)
        self.conn.paste_token(self.fresh_token(), "23588")
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("Ingelogd als", html)
        self.assertIn("Verbinding verbreken", html)
        self.assertIn("AB", html)  # initials in the sidebar

    def test_expired_banner(self):  # F10
        self.conn._set_token(self.fresh_token(), NOW - timedelta(minutes=1))
        self.conn.state = State.EXPIRED
        html = self.client.get("/studenten").get_data(as_text=True)
        self.assertIn("Je Portflow-verbinding is verlopen", html)

    def test_connect_route_redirects_back_with_panel_open(self):  # F1
        self.browser.script = [self.ok(), self.ok()]
        response = self.client.post("/portflow/verbinden", data={"next": "/projecten"})
        self.assertEqual(response.headers["Location"], "/projecten?portflow=open")
        response = self.client.post("/portflow/verbinden", data={"next": "//evil.example"})
        self.assertEqual(response.headers["Location"], "/?portflow=open")

    def test_paste_route_shows_error_in_open_panel(self):  # F5
        response = self.client.post("/portflow/token", data={"token": "rommel", "next": "/"}, follow_redirects=True)
        html = response.get_data(as_text=True)
        self.assertIn("geen Portflow-token", html)
        self.assertRegex(html, r'id="portflow-status"[^>]*\sopen')

    def test_settings_section_and_disconnect(self):  # F11, F15
        self.client.post("/portflow/instellingen", data={"canvas_url": "https://canvas.example/tool", "always_visible": "1"})
        html = self.client.get("/instellingen").get_data(as_text=True)
        self.assertIn("Portflow-koppeling", html)
        self.assertIn('value="https://canvas.example/tool"', html)
        self.assertIn("checked", html)
        self.client.post("/portflow/instellingen", data={"canvas_url": "https://canvas.example/tool"})
        self.assertFalse(self.conn.always_visible)
        self.conn.paste_token(self.fresh_token(), "23588")
        html = self.client.get("/instellingen?bevestig=verbinding-verbreken").get_data(as_text=True)
        self.assertIn("Verbinding met Portflow verbreken?", html)
        self.client.post("/portflow/verbreken")
        self.assertEqual(self.conn.state, State.DISCONNECTED)



class TestLoginModule(unittest.TestCase):
    def test_missing_playwright_gives_instructions(self):  # F16
        from unittest import mock

        from dashboard import portflow_login

        with mock.patch.object(portflow_login, "playwright_available", return_value=False):
            with self.assertRaises(LoginError) as caught:
                portflow_login.capture_token("https://x", Path("/tmp/none"), headless=False, timeout_s=1,
                                             validate=lambda t: True, cancel=threading.Event())
        self.assertEqual(caught.exception.kind, "playwright_missing")
        self.assertIn("pip install", caught.exception.message)


if __name__ == "__main__":
    unittest.main()
