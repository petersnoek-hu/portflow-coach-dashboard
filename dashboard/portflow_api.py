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


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """The token never follows a redirect to another address (docs/architectuur.md, privacy)."""

    def redirect_request(self, *args, **kwargs):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def get_json(path: str, token: str, timeout: float = TIMEOUT_S) -> tuple[int, object]:
    """GET BASE_URL + path. Returns (HTTP status, parsed JSON or None); status 0 = no connection."""
    request = urllib.request.Request(
        BASE_URL + path,
        headers={"Authorization": f"Bearer {token}", "Accept": "*/*", "User-Agent": "Mozilla/5.0"},
    )
    try:
        with _opener.open(request, timeout=timeout) as response:
            body = response.read()
            return response.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as error:
        return error.code, None
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return 0, None


def check_token(token: str) -> int:
    """Live check of a token; 200 means it works."""
    status, _ = get_json("/capabilities", token)
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


def collections(token: str, portfolio_id: int, **retry) -> tuple[int, list[dict] | None]:
    """The collections of a portfolio the user may see (spec 034)."""
    return get_all_pages(f"/portfolios/{portfolio_id}/collections", token, **retry)


def collection_evidence(token: str, portfolio_id: int, collection_id: int, **retry) -> tuple[int, list[dict] | None]:
    """The evidence in one collection, with its goals (spec 034)."""
    return get_all_pages(f"/portfolios/{portfolio_id}/collections/{collection_id}/evidence", token, **retry)


def _pages_until_repeat(path: str, token: str, **retry) -> tuple[int, list[dict] | None]:
    """Like get_all_pages, but also stops when a page repeats the previous one: the comment
    endpoints of Portflow ignore `page` (seen 2026-11-18), which would otherwise never end."""
    separator = "&" if "?" in path else "?"
    page, items, previous = 1, [], None
    while page <= 20:
        status, data = _get_json_with_retry(f"{path}{separator}page={page}&per_page=50", token,
                                            retry.get("retries", RETRIES), retry.get("retry_delay_s", RETRY_DELAY_S))
        if status != 200:
            return status, None
        batch = [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []
        ids = [item.get("id") for item in batch]
        if not batch or ids == previous:
            return 200, items
        items.extend(batch)
        previous = ids
        page += 1
    return 200, items


def evidence_comments(token: str, portfolio_id: int, evidence_id: int, **retry) -> tuple[int, list[dict] | None]:
    """Comments on one piece of evidence, among them feedback requests (spec 035)."""
    return _pages_until_repeat(f"/portfolios/{portfolio_id}/evidence/{evidence_id}/comments", token, **retry)


def comment_children(token: str, portfolio_id: int, comment_id: int, **retry) -> tuple[int, list[dict] | None]:
    """The replies to one comment (spec 035); this endpoint is not paginated."""
    return _pages_until_repeat(f"/portfolios/{portfolio_id}/comments/{comment_id}/children", token, **retry)


def evidence_detail(token: str, portfolio_id: int, evidence_id: int) -> tuple[int, object]:
    """The details of one piece of evidence with its latest version: the text of a free text, or
    the name and type of a file (spec 036). JSON, not the file itself."""
    return get_json(f"/portfolios/{portfolio_id}/evidence/{evidence_id}", token)


def preview_url(token: str, portfolio_id: int, version_file_id: int) -> tuple[int, object]:
    """Signed links (30 minutes, no token needed) to a file of a piece of evidence: the original
    (download_url), and a preview: a pdf for pdf, Word, Excel and PowerPoint (preview_url) or the
    image itself (object_url). Spec 038."""
    return get_json(f"/portfolios/{portfolio_id}/evidence-version-files/{version_file_id}/preview-url", token)
