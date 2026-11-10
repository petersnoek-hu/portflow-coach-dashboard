"""The Portflow connection: one state machine for spec 003 (F1-F17).

States (spec 003, F12):
    disconnected -> logging_in -> connected -> refreshing -> connected
                                            -> needs_login -> expired
Everything that touches the browser runs in a background thread; the web
pages only read `status()`. The token itself never leaves this module and the
TokenStore.
"""

import threading
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Callable

from . import db, portflow_api, portflow_login
from .portflow_login import DEFAULT_CANVAS_URL, CaptureResult, LoginError
from .portflow_token import TokenStore, decode_payload, expires_at

REFRESH_BEFORE = timedelta(hours=1)       # F7
RETRY_INTERVAL = timedelta(minutes=15)    # F9
VISIBLE_TIMEOUT_S = 300                   # F4
HEADLESS_TIMEOUT_S = 60                   # F7

MONTHS = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]


class State(StrEnum):
    DISCONNECTED = "disconnected"
    LOGGING_IN = "logging_in"
    CONNECTED = "connected"
    REFRESHING = "refreshing"
    NEEDS_LOGIN = "needs_login"
    EXPIRED = "expired"


# Dot colour, text and whether the dot pulses (spec 003, F12).
DISPLAY = {
    State.DISCONNECTED: ("grey", "Niet verbonden", False),
    State.LOGGING_IN: ("blue", "Inloggen…", True),
    State.CONNECTED: ("green", "Verbonden", False),
    State.REFRESHING: ("green", "Verversen…", True),
    State.NEEDS_LOGIN: ("orange", "Opnieuw inloggen nodig", False),
    State.EXPIRED: ("red", "Verlopen", False),
}

# Setting keys in the database (no secrets here).
S_CANVAS_URL = "portflow_canvas_url"
S_ALWAYS_VISIBLE = "portflow_always_visible"
S_PORTFOLIO_ID = "portflow_portfolio_id"
S_USER_NAME = "portflow_user_name"
S_LAST_REFRESH = "portflow_last_refresh"
S_LAST_REFRESH_KIND = "portflow_last_refresh_kind"


def _spawn(target: Callable[[], None]) -> None:
    threading.Thread(target=target, daemon=True).start()


def local_time(moment: datetime, now: datetime) -> str:
    """'16:59' today, otherwise '10 nov 16:59'."""
    local, today = moment.astimezone(), now.astimezone()
    text = local.strftime("%H:%M")
    if local.date() != today.date():
        text = f"{local.day} {MONTHS[local.month - 1]} {text}"
    return text


def initials(name: str | None) -> str:
    """'Anna van der Berg' -> 'AB' (first and last name part, without tussenvoegsels)."""
    skip = {"van", "de", "der", "den", "ten", "ter", "te", "het"}
    parts = [p for p in (name or "").replace("-", " ").split() if p.lower() not in skip]
    letters = [p[0].upper() for p in parts if p[0].isalpha()]
    return "".join(letters[:1] + letters[1:][-1:])


def remaining(until: datetime, now: datetime) -> str:
    minutes = max(0, int((until - now).total_seconds() // 60))
    hours, minutes = divmod(minutes, 60)
    return f"nog {hours} u {minutes} min" if hours else f"nog {minutes} min"


class PortflowConnection:
    def __init__(
        self,
        database: str,
        store: TokenStore,
        profile_dir: Path,
        *,
        capture: Callable[..., CaptureResult] = portflow_login.capture_token,
        api=portflow_api,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        spawn: Callable[[Callable[[], None]], None] = _spawn,
    ):
        self.database = database
        self.store = store
        self.profile_dir = profile_dir
        self.capture = capture
        self.api = api
        self.now = now
        self.spawn = spawn

        self.state = State.DISCONNECTED
        self.message: str | None = None
        self.expires: datetime | None = None
        self.last_auto_attempt: datetime | None = None
        self._token: str | None = None
        self._lock = threading.Lock()
        self._busy = False
        self._cancel = threading.Event()

    # Settings ---------------------------------------------------------------

    def setting(self, key: str, default: str | None = None) -> str | None:
        return db.get_setting(self.database, key, default)

    @property
    def canvas_url(self) -> str:
        return self.setting(S_CANVAS_URL) or DEFAULT_CANVAS_URL

    @property
    def always_visible(self) -> bool:
        # Default on: headless refresh gets stuck on the SURFconext account choice,
        # because the Canvas session cookie does not survive a closed browser (2026-11-09).
        return self.setting(S_ALWAYS_VISIBLE, "1") == "1"

    def save_settings(self, canvas_url: str, always_visible: bool) -> None:
        db.set_setting(self.database, S_CANVAS_URL, canvas_url.strip() or DEFAULT_CANVAS_URL)
        db.set_setting(self.database, S_ALWAYS_VISIBLE, "1" if always_visible else "0")

    @property
    def user_name(self) -> str | None:
        return self.setting(S_USER_NAME)

    # Starting up (F6) -------------------------------------------------------

    def start_up(self) -> None:
        token = self.store.read()
        expiry = expires_at(token) if token else None
        if token and expiry and expiry > self.now():
            self._set_token(token, expiry)
            self.state = State.CONNECTED
        elif token:
            self._set_token(token, expiry)
            self.state = State.EXPIRED
            self.refresh()
        else:
            self.connect()

    # Actions ----------------------------------------------------------------

    def connect(self) -> None:
        """Visible login window (F1); does nothing if an attempt is already running (F3)."""
        if not self._begin():
            return
        previous = self.state
        self.state, self.message = State.LOGGING_IN, None
        self._cancel.clear()

        def work():
            try:
                self._apply(self._capture(headless=False), kind="handmatig")
            except LoginError as error:
                self.message = error.message
                self.state = self._fallback_state(previous)
            except Exception as error:  # never leave the app stuck in "Inloggen…"
                self.message = f"Inloggen is mislukt door een onverwachte fout ({type(error).__name__})."
                self.state = self._fallback_state(previous)
            finally:
                self._end()

        self.spawn(work)

    def refresh(self, visible_fallback: bool = True) -> None:
        """Automatic refresh: headless first, then a visible window (F7, F8).

        Retries after a failure (F9) use visible_fallback=False, so no Chrome
        window pops up every 15 minutes while the user may be away.
        """
        if not self._begin():
            return
        self.last_auto_attempt = self.now()
        self.state, self.message = State.REFRESHING, None
        self._cancel.clear()

        def work():
            try:
                result = None
                if not self.always_visible:
                    try:
                        result = self._capture(headless=True)
                    except LoginError as error:
                        if error.kind in ("playwright_missing", "browser_missing", "cancelled"):
                            raise
                if result is None:
                    if not visible_fallback:
                        raise LoginError("headless_failed", "Automatisch verversen is niet gelukt. Log opnieuw in.")
                    self.state = State.LOGGING_IN  # a visible window is open now
                    result = self._capture(headless=False)
                self._apply(result, kind="automatisch")
            except LoginError as error:
                self.message = error.message
                self.state = self._after_failed_refresh()
            except Exception as error:
                self.message = f"Verversen is mislukt door een onverwachte fout ({type(error).__name__})."
                self.state = self._after_failed_refresh()
            finally:
                self._end()

        self.spawn(work)

    def cancel(self) -> None:
        self._cancel.set()

    def paste_token(self, token: str, portfolio_id: str | None = None) -> str | None:
        """Reserve route (F5). Returns None on success, otherwise a message in Dutch."""
        token = token.strip()
        if decode_payload(token) is None:
            return "Dit lijkt geen Portflow-token te zijn. Kopieer het hele token (drie delen, gescheiden door punten)."
        expiry = expires_at(token)
        if expiry and expiry <= self.now():
            return "Dit token is al verlopen. Haal een nieuw token op."
        status = self.api.check_token(token)
        if status == 0:
            return "Portflow is niet bereikbaar. Controleer je internetverbinding."
        if status != 200:
            return "Portflow accepteert dit token niet. Haal een nieuw token op."
        portfolio_id = (portfolio_id or "").strip() or self.setting(S_PORTFOLIO_ID)
        if not portfolio_id:
            return ("Vul ook je eigen portfolio-id in. Je vindt het in de adresbalk van je eigen portfolio: "
                    "portfolio.drieam.app/portfolio/<id>/…")
        error = self.api.own_portfolio_error(token, portfolio_id)
        if error:
            return error
        self._apply(CaptureResult(token=token, portfolio_id=portfolio_id), kind="handmatig")
        return None

    def disconnect(self) -> None:
        """F11: remove the token; the browser profile stays."""
        self.store.delete()
        self._token, self.expires = None, None
        self.state, self.message = State.DISCONNECTED, None

    def mark_unauthorized(self) -> None:
        """Called when Portflow answers 401 (F10)."""
        if self.state in (State.CONNECTED, State.NEEDS_LOGIN):
            self.state = State.EXPIRED

    @property
    def token(self) -> str | None:
        """For API calls only; never pass this to templates or logs."""
        return self._token if self.state in (State.CONNECTED, State.REFRESHING, State.NEEDS_LOGIN) else None

    # Scheduler (F7, F9, F10) -----------------------------------------------

    def tick(self) -> None:
        """Called about every 30 seconds by a background thread."""
        if self._busy:
            return
        now = self.now()
        if self.expires and self.expires <= now and self.state in (State.CONNECTED, State.NEEDS_LOGIN):
            self.state = State.EXPIRED
        due = self.state == State.CONNECTED and self.expires and self.expires - now <= REFRESH_BEFORE
        retry = (self.state in (State.NEEDS_LOGIN, State.EXPIRED) and self._token is not None
                 and not self.always_visible)
        if due and self._may_retry(now):
            self.refresh()
        elif retry and self._may_retry(now):
            self.refresh(visible_fallback=False)

    def _may_retry(self, now: datetime) -> bool:
        return self.last_auto_attempt is None or now - self.last_auto_attempt >= RETRY_INTERVAL

    # Status for the pages (F12-F14) ----------------------------------------

    def status(self) -> dict:
        now = self.now()
        dot, label, pulse = DISPLAY[self.state]
        sub = ""
        if self.state == State.LOGGING_IN:
            sub = "Log in in het Chrome-venster"
        elif self.expires and self.state == State.CONNECTED:
            sub = f"tot {local_time(self.expires, now)}"
        elif self.expires and self.state == State.NEEDS_LOGIN:
            sub = f"verloopt om {local_time(self.expires, now)}"
        elif self.expires and self.state == State.EXPIRED:
            sub = f"sinds {local_time(self.expires, now)}"

        last = self.setting(S_LAST_REFRESH)
        valid = bool(self.expires and self.expires > now and self._token)
        return {
            "state": str(self.state),
            "dot": dot,
            "pulse": pulse,
            "label": label,
            "sub": sub,
            "busy": self._busy,
            "message": self.message,
            "user_name": self.user_name,
            "user_initials": initials(self.user_name),
            "portfolio_id": self.setting(S_PORTFOLIO_ID),
            "valid_until": local_time(self.expires, now) if valid else None,
            "remaining": remaining(self.expires, now) if valid else None,
            "last_refresh": local_time(datetime.fromisoformat(last), now) if last else None,
            "last_refresh_kind": self.setting(S_LAST_REFRESH_KIND),
            "poll_ms": 2000 if self._busy else 60000,
        }

    # Internals ----------------------------------------------------------------

    def _begin(self) -> bool:
        with self._lock:
            if self._busy:
                return False
            self._busy = True
            return True

    def _end(self) -> None:
        with self._lock:
            self._busy = False

    def _capture(self, headless: bool) -> CaptureResult:
        def validate(token: str) -> bool:
            return self.api.check_token(token) == 200

        return self.capture(
            self.canvas_url,
            self.profile_dir,
            headless=headless,
            timeout_s=HEADLESS_TIMEOUT_S if headless else VISIBLE_TIMEOUT_S,
            validate=validate,
            cancel=self._cancel,
        )

    def _set_token(self, token: str, expiry: datetime | None) -> None:
        self._token, self.expires = token, expiry

    def _apply(self, result: CaptureResult, kind: str) -> None:
        self.store.save(result.token)
        self._set_token(result.token, expires_at(result.token))
        portfolio_id = result.portfolio_id or self.setting(S_PORTFOLIO_ID)
        if portfolio_id:
            db.set_setting(self.database, S_PORTFOLIO_ID, portfolio_id)
            name = self.api.own_name(result.token, portfolio_id)
            if name:
                db.set_setting(self.database, S_USER_NAME, name)
                db.add_user_as_coach(self.database, name)
        db.set_setting(self.database, S_LAST_REFRESH, self.now().isoformat())
        db.set_setting(self.database, S_LAST_REFRESH_KIND, kind)
        self.state, self.message = State.CONNECTED, None

    def _token_still_valid(self) -> bool:
        return bool(self._token and self.expires and self.expires > self.now())

    def _fallback_state(self, previous: State) -> State:
        if self._token_still_valid():
            return State.NEEDS_LOGIN if previous == State.NEEDS_LOGIN else State.CONNECTED
        return State.EXPIRED if self._token else State.DISCONNECTED

    def _after_failed_refresh(self) -> State:
        if self._token_still_valid():
            return State.NEEDS_LOGIN
        return State.EXPIRED if self._token else State.DISCONNECTED

