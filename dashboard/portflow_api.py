"""All calls to the (unofficial) Portflow API live here (docs/architectuur.md).

Only GET requests. See docs/portflow-API-reverse-engineer.md for the details.
"""

import json
import urllib.error
import urllib.request

BASE_URL = "https://portfolio.drieam.app/api/v1"
TIMEOUT_S = 15


def get_json(path: str, token: str, timeout: float = TIMEOUT_S) -> tuple[int, object]:
    """GET BASE_URL + path. Returns (HTTP status, parsed JSON or None); status 0 = no connection."""
    request = urllib.request.Request(
        BASE_URL + path,
        headers={"Authorization": f"Bearer {token}", "Accept": "*/*", "User-Agent": "Mozilla/5.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            return response.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as error:
        return error.code, None
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return 0, None


def check_token(token: str) -> int:
    """Live check of a token; 200 means it works."""
    status, _ = get_json("/dashboard", token)
    return status


def own_portfolio(token: str, portfolio_id: str) -> tuple[int, dict | None]:
    status, data = get_json(f"/portfolios/{portfolio_id}", token)
    return status, data if isinstance(data, dict) else None


def own_name(token: str, portfolio_id: str) -> str | None:
    """Name of the logged-in user, read from their own portfolio."""
    status, data = own_portfolio(token, portfolio_id)
    if status != 200 or not data:
        return None
    user = data.get("user") or {}
    for key in ("name", "full_name", "email"):
        value = user.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def own_portfolio_error(token: str, portfolio_id: str) -> str | None:
    """None if portfolio_id is the user's own portfolio, otherwise a message in Dutch."""
    if not portfolio_id.isdigit():
        return "Een portfolio-id bestaat alleen uit cijfers."
    status, data = own_portfolio(token, portfolio_id)
    if status == 0:
        return "Portflow is niet bereikbaar. Controleer je internetverbinding."
    if status != 200 or not data:
        return f"Portfolio {portfolio_id} is niet gevonden of je hebt er geen toegang toe."
    if data.get("access_type") != "owner":
        return f"Portfolio {portfolio_id} is niet je eigen portfolio."
    return None
