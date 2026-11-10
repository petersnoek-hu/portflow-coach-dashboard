"""Routes for the Portflow connection (spec 003). The token never appears in a response."""

from urllib.parse import urlencode

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for

bp = Blueprint("portflow", __name__, url_prefix="/portflow")


def connection():
    return current_app.extensions["portflow"]


def back(open_panel: bool = False):
    """Redirect to the page the form came from (only local paths)."""
    target = request.form.get("next", "")
    if not target.startswith("/") or target.startswith("//"):
        target = url_for("pages.overview")
    target = target.split("?", 1)[0]
    if open_panel:
        target += "?" + urlencode({"portflow": "open"})
    return redirect(target)


@bp.get("/status")
def status():
    """Live status for app.js (F14): state plus freshly rendered pieces of the page."""
    portflow = connection().status()
    fetch = current_app.extensions["fetcher"].status()
    context = {"portflow": portflow, "fetch": fetch, "portflow_open": False,
               "next_path": request.args.get("pad", "/")}
    return jsonify(
        state=portflow["state"],
        poll_ms=1500 if fetch["running"] else portflow["poll_ms"],
        fetch_running=fetch["running"],
        fetch_last=fetch["last"],
        fingerprint="|".join(str(portflow[k]) for k in
                             ("state", "sub", "message", "user_name", "last_refresh", "busy"))
                    + "|" + fetch["text"] + str(fetch["can_start"]) + str(len(fetch["unlinked"])),
        status_html=render_template("_portflow_status.html", **context),
        refresh_html=render_template("_refresh.html", **context),
        banner_html=render_template("_portflow_banner.html", **context),
        user_html=render_template("_sidebar_user.html", **context),
        avatar_html=render_template("_topbar_avatar.html", **context),
    )


@bp.post("/verbinden")
def connect():
    connection().connect()
    return back(open_panel=True)


@bp.post("/verversen")
def refresh_data():
    """Spec 005, F6: start a fetch round (does nothing while one runs or when not connected)."""
    current_app.extensions["fetcher"].start()
    return back()


@bp.post("/annuleren")
def cancel():
    connection().cancel()
    return back(open_panel=True)


@bp.post("/token")
def paste_token():
    error = connection().paste_token(request.form.get("token", ""), request.form.get("portfolio_id"))
    connection().message = error
    return back(open_panel=True)


@bp.post("/verbreken")
def disconnect():
    connection().disconnect()
    return redirect(url_for("pages.settings"))


@bp.post("/instellingen")
def save_settings():
    connection().save_settings(request.form.get("canvas_url", ""), request.form.get("always_visible") == "1")
    return redirect(url_for("pages.settings"))
