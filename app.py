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
    # Redirect to /bypass?url= so visiting root auto-adds it
    return ('', 302, {'Location': '/bypass?url='})

@app.route("/bypass", methods=["GET"])
def bypass_proxy():
    """
    Renders an HTML page (black background) showing the raw upstream response.
    The API key is only used server-side and is never exposed to clients.
    """
    # Require the presence of the 'url' parameter (it may be empty "")
    if 'url' not in request.args:
        return abort(400, "Missing 'url' query parameter. Use /bypass?url=<TARGET>")

    target = request.args.get("url", "")

    # Call upstream with hard-coded API key (server-side only)
    params = {"url": target, "apikey": API_KEY}
    try:
        resp = requests.get(API_BASE, params=params, timeout=15)
    except requests.RequestException:
        # Render error page without exposing key or upstream URL
        return render_template("bypass.html", raw="Error contacting upstream API.", status="502", ctype="text/plain")

    # decode content safely to text for display (replace invalid bytes)
    try:
        raw_text = resp.content.decode("utf-8")
    except Exception:
        raw_text = resp.content.decode("utf-8", errors="replace")

    # If upstream returned a Location header, make sure any apikey is removed from it
    location = resp.headers.get("Location")
    if location:
        location = remove_apikey_from_url(location)

    # Render HTML template with raw response (escaped in template)
    return render_template(
        "bypass.html",
        raw=raw_text,
        status=resp.status_code,
        ctype=resp.headers.get("Content-Type", "text/plain"),
        upstream_location=location
    )

# No app.run() — Vercel will use the `app` WSGI application.
