"""All calls to the (unofficial) Portflow API live here (docs/architectuur.md).

Only GET requests. See docs/portflow-API-reverse-engineer.md for the details.
"""

import json
import time
import urllib.error
import urllib.request

BASE_URL = "https://portfolio.drieam.app/api/v1"
TIMEOUT_S = 15
RETRIES = 3        # architectuur.md#portflow-api: other errors get 3 attempts
RETRY_DELAY_S = 5.0
SHARES_PAGE_SIZE = 50


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


def _get_json_with_retry(path: str, token: str, retries: int, delay_s: float) -> tuple[int, object]:
    """401 and 404 are not retried (architectuur.md#portflow-api); other errors are, up to `retries`."""
    status, data = get_json(path, token)
    attempt = 1
    while status not in (200, 401, 404) and attempt < retries:
        time.sleep(delay_s)
        status, data = get_json(path, token)
        attempt += 1
    return status, data


def shared_with_me(
    token: str, *, retries: int = RETRIES, retry_delay_s: float = RETRY_DELAY_S
) -> tuple[int, list[dict] | None]:
    """All portfolios shared with the logged-in user (spec 004), `GET /shares/shared-with-me`.

    This endpoint always returns at most 20 items per page, regardless of `per_page`
    (docs/portflow-API-reverse-engineer.md#3-algemene-conventies). "Stop at a page
    shorter than requested" would therefore stop after the first 20 shares; paginate
    until an **empty** page instead.
    """
    page, items = 1, []
    while True:
        path = (
            f"/shares/shared-with-me?order_by=created_at&order_direction=desc"
            f"&page={page}&per_page={SHARES_PAGE_SIZE}"
        )
        status, data = _get_json_with_retry(path, token, retries, retry_delay_s)
        if status != 200:
            return status, None
        batch = data if isinstance(data, list) else []
        if not batch:
            break
        items.extend(batch)
        page += 1
    return 200, items


def get_all_pages(
    path: str, token: str, *, retries: int = RETRIES, retry_delay_s: float = RETRY_DELAY_S
) -> tuple[int, list[dict] | None]:
    """GET every page of a list endpoint until an empty page (architectuur.md#portflow-api).

    Returns (200, items) or (the failing status, None). `path` must not contain page params.
    """
    separator = "&" if "?" in path else "?"
    page, items = 1, []
    while True:
        status, data = _get_json_with_retry(
            f"{path}{separator}page={page}&per_page=50", token, retries, retry_delay_s
        )
        if status != 200:
            return status, None
        batch = data if isinstance(data, list) else []
        if not batch:
            return 200, items
        items.extend(item for item in batch if isinstance(item, dict))
        page += 1


def goals(token: str, portfolio_id: int, **retry) -> tuple[int, list[dict] | None]:
    """Goals of a portfolio (skills, professional tasks, ...), spec 005 F1."""
    return get_all_pages(f"/portfolios/{portfolio_id}/goals", token, **retry)


def feedback_items(token: str, portfolio_id: int, goal_id: int, **retry) -> tuple[int, list[dict] | None]:
    """Self-evaluations and assessments on one goal, spec 005 F1."""
    return get_all_pages(f"/portfolios/{portfolio_id}/goals/{goal_id}/feedback-items", token, **retry)


def received_invitations(token: str, own_portfolio_id: str, **retry) -> tuple[int, list[dict] | None]:
    """Review requests sent to the user (all statuses), spec 005 F3."""
    return get_all_pages(
        f"/portfolios/{own_portfolio_id}/progress-review/invitations/received"
        "?order_by=created_at&order_direction=desc",
        token, **retry,
    )
