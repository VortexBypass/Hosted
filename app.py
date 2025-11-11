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
    - Requires 'url' query param to be present (may be empty string).
    - Calls upstream with hard-coded apikey server-side.
    - Success -> {"status":"success","result":..., "time": ... (if present)}
    - Error   -> {"Status":"error","message":"...","time": ... (if present)}
    - Non-JSON upstream -> forwarded as text/plain
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
        return Response(resp.text, mimetype="text/plain", status=resp.status_code)

    # If upstream indicates an error, extract message and include time if present
    if isinstance(data, dict) and "error" in data:
        err = data.get("error")
        message = None
        # If "error" is an object with "message", prefer that
        if isinstance(err, dict):
            message = err.get("message") or err.get("msg")
        # fallback to top-level "message"
        if not message:
            message = data.get("message")
        if not message:
            message = str(err)
        error_obj = {"Status": "error", "message": str(message)}
        # include time if upstream provided it (either top-level or inside error object)
        if isinstance(err, dict) and "time" in err:
            error_obj["time"] = err.get("time")
        elif "time" in data:
            error_obj["time"] = data.get("time")
        return Response(json.dumps(error_obj, indent=2, ensure_ascii=False), mimetype="application/json", status=resp.status_code)

    # Not an error: keep ONLY 'result' (and 'time' if present)
    filtered = {}
    if isinstance(data, dict) and "result" in data:
        filtered["status"] = "success"
        filtered["result"] = data["result"]
        if "time" in data:
            filtered["time"] = data["time"]

    # If there's no 'result' and no 'error' -> return empty JSON object per your instructions
    return Response(json.dumps(filtered, indent=2, ensure_ascii=False), mimetype="application/json", status=resp.status_code)
