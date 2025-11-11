from flask import Flask, request, Response, abort, redirect
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging
import os

# === HARD-CODED KEY (kept only on the server) ===
API_BASE = "http://ace-bypass.com/api/bypass"
API_KEY = "FREE_S7MdXC0momgajOEx1_UKW7FQUvbmzvalu0gTwr-V6cI"
# =================================================

# Export the Flask app as a top-level variable (Vercel/WGSI expects this).
app = Flask(__name__)

# Silence werkzeug request logging so querystrings won't be printed to stdout in logs.
# (Vercel still collects logs; this reduces accidental prints of full URLs.)
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

def filtered_response_headers(original_headers):
    """
    Return a dict of headers to forward to client but remove headers that might reveal credentials.
    Also sanitize Location header.
    """
    out = {}
    forbidden_substrings = ('key', 'auth', 'token', 'cookie')
    for k, v in original_headers.items():
        kl = k.lower()
        if kl.startswith('set-cookie') or any(s in kl for s in forbidden_substrings):
            continue
        if kl == 'location':
            v = remove_apikey_from_url(v)
        out[k] = v
    return out

@app.route("/", methods=["GET"])
def root_redirect():
    """
    Redirect root to /bypass?url= so visiting the site auto-adds that path/query.
    Example: https://example.com/  ->  https://example.com/bypass?url=
    """
    return redirect("/bypass?url=", code=302)

@app.route("/bypass", methods=["GET"])
def bypass_proxy():
    """
    Endpoint: /bypass?url=<TARGET>
    Calls upstream API with hard-coded apikey and returns upstream raw body.
    The API key is never included in any response headers or body returned to clients.
    """
    # Accept empty value (user may want /bypass?url=) — only treat missing as error
    if 'url' not in request.args:
        return abort(400, "Missing 'url' query parameter. Use /bypass?url=<TARGET>")

    target = request.args.get("url", "")

    # Build request to upstream API (apikey is sent server-side only)
    params = {"url": target, "apikey": API_KEY}
    try:
        resp = requests.get(API_BASE, params=params, timeout=15)
    except requests.RequestException:
        # Generic error message — do not leak API_KEY or full upstream URL
        return Response("Error contacting upstream API.", status=502, mimetype="text/plain")

    # Filter headers so we don't forward anything that could reveal the API key
    safe_headers = filtered_response_headers(resp.headers)

    # Return raw upstream content with upstream status code
    response = Response(resp.content, status=resp.status_code)
    if 'Content-Type' in safe_headers:
        response.headers['Content-Type'] = safe_headers.pop('Content-Type')
    for hk, hv in safe_headers.items():
        if hk.lower() == 'content-type':
            continue
        response.headers[hk] = hv

    return response

# Do NOT call app.run() — Vercel will handle the WSGI entrypoint.
