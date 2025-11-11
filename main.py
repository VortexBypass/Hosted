# app.py
from flask import Flask, request, Response, abort
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging

app = Flask(__name__)

# === HARD-CODED KEY (kept only on the server) ===
API_BASE = "http://ace-bypass.com/api/bypass"
API_KEY = "FREE_S7MdXC0momgajOEx1_UKW7FQUvbmzvalu0gTwr-V6cI"
# =================================================

# Optional: silence the default werkzeug request logger so requests (including querystrings)
# won't be printed to stdout. Keep disabled in production if you prefer logs.
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

@app.route("/bypass", methods=["GET"])
def bypass_proxy():
    """
    Endpoint: /bypass?url=<TARGET>
    Example: https://example.com/bypass?url=https://target.example/path
    This will call the upstream API with the hard-coded apikey and return the raw upstream body.
    The API key is never included in any response headers or body returned to clients.
    """
    target = request.args.get("url")
    if target is None:
        return abort(400, "Missing 'url' query parameter. Use /bypass?url=<TARGET>")

    # Build request to upstream API (apikey is sent server-side only)
    params = {"url": target, "apikey": API_KEY}
    try:
        resp = requests.get(API_BASE, params=params, timeout=15)
    except requests.RequestException:
        return Response("Error contacting upstream API.", status=502, mimetype="text/plain")

    # Filter headers so we don't forward anything that could reveal the API key
    safe_headers = filtered_response_headers(resp.headers)

    # Build and return response with raw content and upstream status code
    response = Response(resp.content, status=resp.status_code)
    # Apply content-type if provided
    if 'Content-Type' in safe_headers:
        response.headers['Content-Type'] = safe_headers.pop('Content-Type')
    for hk, hv in safe_headers.items():
        # avoid accidental overwrites
        if hk.lower() == 'content-type':
            continue
        response.headers[hk] = hv

    return response

if __name__ == "__main__":
    # Run WITHOUT debug mode so Flask won't leak internal info.
    app.run(host="0.0.0.0", port=5000, debug=False)
