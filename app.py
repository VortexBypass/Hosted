# app.py
from flask import Flask, request, Response, abort
import requests
import json
import logging

app = Flask(__name__)

# --- Hard-coded API key (server-side only) ---
API_BASE = "http://ace-bypass.com/api/bypass"
API_KEY  = "FREE_S7MdXC0momgajOEx1_UKW7FQUvbmzvalu0gTwr-V6cI"
# ------------------------------------------------

# Silence werkzeug logs
logging.getLogger("werkzeug").disabled = True


@app.route("/", methods=["GET"])
def root_redirect():
    # Redirect root to /bypass?url=
    return ('', 302, {'Location': '/bypass?url='})


@app.route("/bypass", methods=["GET"])
def bypass_proxy():
    """
    GET /bypass?url=<TARGET>
    Returns raw JSON/plain responses with the exact formats requested.
    """
    if 'url' not in request.args:
        return abort(400, "Missing 'url' query parameter. Use /bypass?url=<TARGET>")

    target = request.args.get("url", "")

    params = {"url": target, "apikey": API_KEY}
    try:
        resp = requests.get(API_BASE, params=params, timeout=15)
    except requests.RequestException:
        err_obj = {"Status": "error", "message": "Failed to contact upstream API."}
        return Response(json.dumps(err_obj, indent=2), mimetype="application/json", status=502)

    # Try to parse JSON; if not JSON, forward as text/plain
    try:
        data = resp.json()
    except ValueError:
        # Non-JSON: forward raw text (no HTML, no boxes)
        return Response(resp.text, mimetype="text/plain", status=resp.status_code)

    # If upstream indicates an error, extract message and return our error format
    if isinstance(data, dict) and "error" in data:
        err = data.get("error")
        # If error is a dict with message, prefer that
        message = None
        if isinstance(err, dict):
            message = err.get("message")
        # fallback to top-level 'message'
        if not message:
            message = data.get("message")
        # fallback to stringifying err
        if not message:
            message = str(err)
        error_obj = {"Status": "error", "message": str(message)}
        return Response(json.dumps(error_obj, indent=2), mimetype="application/json", status=resp.status_code)

    # Not an error: keep ONLY 'result' and 'time'
    filtered = {}
    if isinstance(data, dict):
        if "result" in data:
            filtered["status"] = "success"           # user-requested lowercase 'status'
            filtered["result"] = data["result"]
            if "time" in data:
                filtered["time"] = data["time"]
        else:
            # no 'result' present -> per instructions return empty JSON object
            filtered = {}

    # Return filtered JSON
    return Response(json.dumps(filtered, indent=2, ensure_ascii=False), mimetype="application/json", status=resp.status_code)
