"""The local AI model (spec 040): talking to Ollama on the laptop itself, and the checks of the wizard (F12).

Only an address on the laptop itself is accepted (F11, privacy): nothing about students leaves the
laptop. Plain urllib, no extra package. Labels are Dutch: they are shown to the user.
"""

import ctypes
import json
import os
import platform
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

DEFAULT_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "gemma4:12b-it-qat"     # spec 040, Onderzoek (2026-11-22)
DEFAULT_MODEL_SIZE = "7,2 GB"
MIN_MEMORY_GB = 16
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
S_URL = "ai_ollama_url"
S_MODEL = "ai_model"
S_THREADS = "ai_threads"        # F29: processor cores for the model
S_CONTEXT = "ai_context"        # F30: how much material per advice
S_UNLOAD = "ai_unload"          # F31: "1": unload the model right after the advice
# F30: per choice the tokens the model may use (memory) and the characters of material (F8).
CONTEXTS = {"weinig": (8192, 20000), "normaal": (16384, 40000), "veel": (32768, 80000)}
DEFAULT_CONTEXT = "veel"


def cores() -> int:
    """F29: the number of processor cores (threads) of the laptop."""
    return max(1, os.cpu_count() or 1)


def default_threads() -> int:
    """F29: all cores but one, so the laptop keeps responding."""
    return max(1, cores() - 1)
DOWNLOAD_URL = "https://ollama.com/download"

# F28: the models tested for the advice (spec 040, Onderzoek), offered for download in Instellingen.
TESTED_MODELS = [
    {"name": DEFAULT_MODEL, "size": DEFAULT_MODEL_SIZE, "memory": "16 GB of meer",
     "note": "Aangeraden: de beste balans tussen kwaliteit en snelheid."},
    {"name": "gemma4:e4b", "size": "9,6 GB", "memory": "16 GB",
     "note": "Lichter: ongeveer twee keer zo snel, het advies is iets minder goed. Voor een laptop waarop het aangeraden model zwaar is."},
    {"name": "gemma4:26b", "size": "18 GB", "memory": "32 GB of meer",
     "note": "Zwaarder: het zorgvuldigst, maar traag en alleen voor een laptop met veel geheugen."},
]
MODEL_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._\-/]*(:[A-Za-z0-9._\-]+)?")


def valid_name(name: str) -> bool:
    """F28: a model name as `ollama pull` takes it (e.g. gemma4:e4b)."""
    return len(name) <= 100 and bool(MODEL_NAME.fullmatch(name))


class OllamaError(Exception):
    """`message` is shown to the user (Dutch); `detail` is the technical message of the system, for the
    log of spec 042 (F2)."""

    def __init__(self, message: str, detail: str = ""):
        super().__init__(message)
        self.message = message
        self.detail = detail


def _reason(error: BaseException, timeout: float) -> str:
    """Spec 042, F2: what the system said, e.g. "Connection refused" or "timed out na 5 s"."""
    reason = getattr(error, "reason", error)
    if isinstance(reason, (TimeoutError,)) or "timed out" in str(reason).lower():
        return f"timed out na {timeout:g} s"
    name = type(reason).__name__
    text = getattr(reason, "strerror", None) or str(reason)
    return f"{name}: {text}" if text else name


def is_local(url: str) -> bool:
    parsed = urlparse(url or "")
    return parsed.scheme == "http" and (parsed.hostname or "") in LOCAL_HOSTS and not parsed.path.strip("/")


def _request(url: str, path: str, body: dict | None = None, timeout: float = 5.0):
    if not is_local(url):
        raise OllamaError("Het adres van Ollama moet op deze laptop zijn (bijvoorbeeld http://127.0.0.1:11434).")
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url.rstrip("/") + path, data=data,
                                     headers={"Content-Type": "application/json"} if data else {})
    try:
        return urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as error:
        try:
            detail = json.loads(error.read() or b"{}").get("error") or ""
        except ValueError:
            detail = ""
        raise OllamaError(f"Ollama gaf een fout ({error.code}){': ' + detail if detail else ''}.",
                          f"HTTP {error.code} op {path}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise OllamaError("Ollama is niet bereikbaar. Is Ollama gestart?", _reason(error, timeout)) from None


def _json(url: str, path: str, body: dict | None = None, timeout: float = 5.0) -> dict:
    with _request(url, path, body, timeout) as response:
        try:
            return json.loads(response.read() or b"{}")
        except ValueError:
            raise OllamaError("Ollama gaf een onverwacht antwoord.") from None


# The checks of the wizard (F12) ----------------------------------------------------------------

def memory_gb() -> float | None:
    """Step 1: the working memory of the laptop, in GB (None if unknown)."""
    try:
        if sys.platform == "win32":
            class Status(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                            ("avail", ctypes.c_ulonglong), ("page_total", ctypes.c_ulonglong),
                            ("page_avail", ctypes.c_ulonglong), ("virtual_total", ctypes.c_ulonglong),
                            ("virtual_avail", ctypes.c_ulonglong), ("extended", ctypes.c_ulonglong)]
            status = Status()
            status.length = ctypes.sizeof(Status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return status.total / 1024 ** 3
            return None
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024 ** 3
    except (AttributeError, ValueError, OSError):
        return None


def system_name() -> str:
    return {"darwin": "macOS", "win32": "Windows"}.get(sys.platform, platform.system() or "onbekend")


def version(url: str) -> str:
    """Step 2: the version of Ollama; raises OllamaError when it does not answer."""
    return str(_json(url, "/api/version").get("version") or "onbekend")


def models(url: str) -> list[dict]:
    """Step 3, F11: the installed models: name and size in GB."""
    return [{"name": m.get("name", ""), "size_gb": round((m.get("size") or 0) / 1e9, 1)}
            for m in _json(url, "/api/tags").get("models") or [] if m.get("name")]


def has_model(url: str, model: str) -> bool:
    names = {m["name"] for m in models(url)}
    return model in names or (":" not in model and f"{model}:latest" in names)


def capabilities(url: str, model: str) -> set[str]:
    """F7: whether the model reads images ('vision')."""
    try:
        return set(_json(url, "/api/show", {"model": model}).get("capabilities") or [])
    except OllamaError:
        return set()


class Pull:
    """Step 3: let Ollama download a model, with progress; one at a time."""

    def __init__(self):
        self.lock = threading.Lock()
        self.state = {"running": False, "model": "", "done": 0, "total": 0, "status": "", "error": ""}

    def start(self, url: str, model: str, log=None) -> bool:
        """`log(ok, text, detail)` (spec 042): called when the download ends."""
        with self.lock:
            if self.state["running"]:
                return False
            self.state = {"running": True, "model": model, "done": 0, "total": 0, "status": "Starten…", "error": ""}
        threading.Thread(target=self._run, args=(url, model, log), daemon=True).start()
        return True

    def _run(self, url: str, model: str, log=None) -> None:
        started = time.monotonic()
        error_seen: OllamaError | None = None
        try:
            with _request(url, "/api/pull", {"model": model, "stream": True}, timeout=600) as response:
                for line in response:
                    try:
                        part = json.loads(line)
                    except ValueError:
                        continue
                    if part.get("error"):
                        raise OllamaError(f"Downloaden is niet gelukt: {part['error']}")
                    with self.lock:
                        self.state["status"] = str(part.get("status") or "")
                        if part.get("total"):
                            self.state["total"], self.state["done"] = part["total"], part.get("completed") or 0
        except OllamaError as error:
            error_seen = error
            with self.lock:
                self.state["error"] = error.message
        finally:
            with self.lock:
                self.state["running"] = False
            if log:
                seconds = round(time.monotonic() - started)
                if error_seen:
                    log(False, f"Downloaden van {model} mislukt na {seconds} s: {error_seen.message}", error_seen.detail)
                else:
                    log(True, f"{model} gedownload in {seconds} s")

    def status(self) -> dict:
        with self.lock:
            return dict(self.state)


# Asking the model ----------------------------------------------------------------------------

def chat(url: str, model: str, system: str, user: str, schema: dict | None, *, images: list[str] = (),
         history: list[dict] = (), num_ctx: int = 16384, cancel: threading.Event | None = None, progress=None,
         timeout: float = 900, num_thread: int | None = None, keep_alive: int | str | None = None):
    """F5: a question with a fixed JSON answer (Ollama's `format`); without a schema a free text answer
    (F21, with `history`: earlier user/assistant messages after the first). Streams, so it can be
    stopped (F4) and shows progress. Returns the parsed JSON or the text; raises OllamaError."""
    first = {"role": "user", "content": user}
    if images:
        first["images"] = list(images)
    options = {"temperature": 0.2, "num_ctx": num_ctx}
    if num_thread:
        options["num_thread"] = num_thread          # F29
    body = {"model": model, "stream": True, "think": False, "options": options,
            "messages": [{"role": "system", "content": system}, first, *history]}
    if keep_alive is not None:
        body["keep_alive"] = keep_alive              # F31
    if schema is not None:
        body["format"] = schema
    parts: list[str] = []
    part_done = False
    started = time.monotonic()
    with _request(url, "/api/chat", body, timeout=timeout) as response:
        for line in response:
            if cancel is not None and cancel.is_set():
                raise OllamaError("Gestopt.")
            try:
                part = json.loads(line)
            except ValueError:
                continue
            if part.get("error"):
                raise OllamaError(f"Het model gaf een fout: {part['error']}")
            parts.append((part.get("message") or {}).get("content") or "")
            if progress:
                progress(len("".join(parts)), time.monotonic() - started)
            if part.get("done"):
                part_done = True
                break
    if schema is None:
        return "".join(parts).strip()
    text = "".join(parts)
    try:
        return json.loads(text)
    except ValueError:   # spec 042, F6: the size, not the content
        raise OllamaError("Het model gaf geen geldig antwoord. Probeer het opnieuw.",
                          f"antwoord van {len(text)} tekens was geen geldige JSON; "
                          f"{'Ollama meldde klaar' if part_done else 'de stroom stopte zonder klaar-melding'}") from None
