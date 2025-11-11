# app.py
from flask import Flask, request, render_template, abort
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging

# === HARD-CODED KEY (kept only on the server) ===
API_BASE = "http://ace-bypass.com/api/bypass"
API_KEY = "FREE_S7MdXC0momgajOEx1_UKW7FQUvbmzvalu0gTwr-V6cI"
# =================================================

app = Flask(__name__)

# Silence werkzeug prints in logs when not debugging
if not app.debug:
    logging.getLogger("werkzeug").disabled = True

def remove_apikey_from_url(url: str) -> str:
    """Remove any 'apikey' query parameter from a URL (if present)."""
    try:
        parsed = urlparse(url)
    except Exception:
        return url
    qs = parse_qs(parsed.query, keep_blank_values=True)
    qs.pop('apikey', None)
    new_query = urlencode(qs, doseq=True)
    sanitized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
    return sanitized

@app.route("/", methods=["GET"])
def root_redirect():
    # Redirect root to /bypass?url= so visiting root auto-adds it
    return ('', 302, {'Location': '/bypass?url='})

@app.route("/bypass", methods=["GET"])
def bypass_proxy():
    """
    Endpoint only accepts GET requests.
    Usage: GET /bypass?url=<TARGET>
    - If the 'url' parameter is missing entirely -> returns 400.
    - If the 'url' parameter exists (including an empty value) -> it's forwarded to upstream.
    """
    # Ensure we only accept GET: Flask enforces this because methods=["GET"] above.
    # Check presence of 'url' param (may be empty string "")
    if 'url' not in request.args:
        return abort(400, "Missing 'url' query parameter. Use /bypass?url=<TARGET>")

    target = request.args.get("url", "")

    # Build request to upstream API (apikey is sent server-side only)
    params = {"url": target, "apikey": API_KEY}
    try:
        resp = requests.get(API_BASE, params=params, timeout=15)
    except requests.RequestException:
        # Generic error message — do not leak API_KEY or full upstream URL
        return render_template("bypass.html", raw="Error contacting upstream API.", status="502", ctype="text/plain")

    # decode content safely to text for display (replace invalid bytes)
    try:
        raw_text = resp.content.decode("utf-8")
    except Exception:
        raw_text = resp.content.decode("utf-8", errors="replace")

    # Remove any apikey from Location header if present (but we don't display it)
    location = resp.headers.get("Location")
    if location:
        location = remove_apikey_from_url(location)

    # Render template (templates/bypass.html) — the template shows only {{ raw | e }}
    return render_template(
        "bypass.html",
        raw=raw_text,
        status=resp.status_code,
        ctype=resp.headers.get("Content-Type", "text/plain"),
        upstream_location=location
    )

# No app.run() — Vercel will use the `app` WSGI application.
