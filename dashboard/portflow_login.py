"""Get a Portflow token by opening the Portflow tool in Canvas in a Chrome window.

Same approach as the console app (_capture_token_via_browser):
1. Start Chrome with a persistent profile, so the HU login is remembered.
2. Open the Portflow tool in Canvas; the user logs in if needed.
3. Catch the 'Authorization: Bearer ...' header of Portflow's own requests.
4. Check the token, and read the user's own portfolio id from the page.

Runs in a background thread. Playwright is imported lazily, so the rest of the
app works without it.
"""

import importlib.util
import platform
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

DEFAULT_CANVAS_URL = "https://canvas.hu.nl/courses/51659/external_tools/1134"
TOKEN_HOST_SUFFIXES = ("portflow.io", "hu.nl", "drieam.app")
PORTFOLIO_ID_GRACE_S = 10

# Portflow passes its start data in data-react-props; it contains the user's own portfolio.
OWN_PORTFOLIO_ID_JS = """() => {
  for (const el of document.querySelectorAll('div[data-react-class]')) {
    try {
      const props = JSON.parse(el.dataset.reactProps || '{}');
      if (props.portfolio && props.portfolio.id) return String(props.portfolio.id);
    } catch (e) {}
  }
  return null;
}"""


class LoginError(Exception):
    """A login attempt that did not produce a token. `message` is shown to the user (Dutch)."""

    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind
        self.message = message


@dataclass
class CaptureResult:
    token: str
    portfolio_id: str | None


def playwright_available() -> bool:
    return importlib.util.find_spec("playwright") is not None


def find_chrome() -> Path | None:
    if platform.system() == "Darwin":
        candidates = [
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    elif platform.system() == "Windows":
        import os

        candidates = [
            Path(os.environ[var]) / "Google/Chrome/Application/chrome.exe"
            for var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")
            if os.environ.get(var)
        ]
    else:
        import shutil

        candidates = [Path(p) for p in (shutil.which("google-chrome"), shutil.which("google-chrome-stable")) if p]
    return next((c for c in candidates if c.exists()), None)


def _host_matches(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == s or host.endswith("." + s) for s in TOKEN_HOST_SUFFIXES)


def capture_token(
    canvas_url: str,
    profile_dir: Path,
    *,
    headless: bool,
    timeout_s: float,
    validate: Callable[[str], bool],
    cancel: threading.Event,
) -> CaptureResult:
    """Open Chrome, wait for a valid token. Raises LoginError if that does not work."""
    if not playwright_available():
        raise LoginError(
            "playwright_missing",
            "Voor inloggen via Chrome is het pakket Playwright nodig. "
            "Installeer het met: pip install -r requirements.txt. Je kunt ook een token plakken.",
        )
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    candidates: list[str] = []
    seen: set[str] = set()

    def on_request(request) -> None:
        if not _host_matches(request.url):
            return
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:].strip()
            if token and token not in seen:
                seen.add(token)
                candidates.append(token)

    profile_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        kwargs = dict(user_data_dir=str(profile_dir), headless=headless, no_viewport=True, chromium_sandbox=True)
        if find_chrome():
            kwargs["channel"] = "chrome"
        elif not Path(p.chromium.executable_path).exists():
            raise LoginError(
                "browser_missing",
                "Google Chrome is niet gevonden. Installeer Chrome, of voer uit: "
                "python -m playwright install chromium. Je kunt ook een token plakken.",
            )
        try:
            context = p.chromium.launch_persistent_context(**kwargs)
        except PlaywrightError:
            raise LoginError(
                "profile_locked",
                "Er staat nog een inlogvenster open. Sluit dat en probeer het opnieuw.",
            ) from None

        try:
            context.on("request", on_request)
            page = context.pages[0] if context.pages else context.new_page()
            try:
                page.goto(canvas_url, wait_until="domcontentloaded")
            except PlaywrightError:
                pass  # keep waiting: the login page may still lead to Portflow

            token = _wait_for_token(context, candidates, validate, cancel, timeout_s, PlaywrightError)
            portfolio_id = _wait_for_portfolio_id(context, PlaywrightError)
            return CaptureResult(token=token, portfolio_id=portfolio_id)
        finally:
            try:
                context.close()
            except PlaywrightError:
                pass


def _wait_for_token(context, candidates, validate, cancel, timeout_s, playwright_error) -> str:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if cancel.is_set():
            raise LoginError("cancelled", "Inloggen is afgebroken.")
        while candidates:
            token = candidates.pop(0)
            if validate(token):
                return token
        if not context.pages:
            raise LoginError("closed", "Inloggen is niet afgerond: het venster is gesloten. Probeer het opnieuw.")
        try:
            context.pages[0].wait_for_timeout(500)  # lets Playwright process its events
        except playwright_error:
            raise LoginError("closed", "Inloggen is niet afgerond: het venster is gesloten. Probeer het opnieuw.")
    raise LoginError("timeout", "Inloggen is niet afgerond binnen de tijd. Probeer het opnieuw.")


def _wait_for_portfolio_id(context, playwright_error) -> str | None:
    deadline = time.monotonic() + PORTFOLIO_ID_GRACE_S
    while context.pages and time.monotonic() < deadline:
        for page in context.pages:
            for frame in page.frames:
                if not (urlparse(frame.url).hostname or "").endswith("drieam.app"):
                    continue
                try:
                    portfolio_id = frame.evaluate(OWN_PORTFOLIO_ID_JS)
                except playwright_error:
                    continue
                if portfolio_id and str(portfolio_id).isdigit():
                    return str(portfolio_id)
        try:
            context.pages[0].wait_for_timeout(500)
        except playwright_error:
            break
    return None
