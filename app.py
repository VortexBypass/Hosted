from flask import Flask, request, render_template, abort
import requests
import json
import logging

app = Flask(__name__)

# --- Hardcoded API key (hidden server-side) ---
API_BASE = "http://ace-bypass.com/api/bypass"
API_KEY = "FREE_S7MdXC0momgajOEx1_UKW7FQUvbmzvalu0gTwr-V6cI"
# ------------------------------------------------

# Silence werkzeug logs
logging.getLogger("werkzeug").disabled = True


@app.route("/", methods=["GET"])
def root_redirect():
    # Visiting site root automatically redirects to /bypass?url=
    return ('', 302, {'Location': '/bypass?url='})


@app.route("/bypass", methods=["GET"])
def bypass_proxy():
    """
    Example: /bypass?url=https://target.com
    Returns filtered raw output from upstream API.
    """
    if 'url' not in request.args:
        return abort(400, "Missing 'url' query parameter. Use /bypass?url=<TARGET>")

    target = request.args.get("url", "")

    params = {"url": target, "apikey": API_KEY}

    try:
        resp = requests.get(API_BASE, params=params, timeout=15)
    except requests.RequestException:
        return render_template("bypass.html", raw='{"Status":"error","message":"Failed to contact upstream API."}')

    # Try to parse JSON, otherwise show as text
    try:
        data = resp.json()
    except ValueError:
        raw_text = resp.text
        return render_template("bypass.html", raw=raw_text)

    # Handle API errors
    if isinstance(data, dict) and "error" in data:
        message = data.get("message") or data["error"]
        error_obj = {"Status": "error", "message": str(message)}
        return render_template("bypass.html", raw=json.dumps(error_obj, indent=2))

    # Clean up unwanted fields
    for key in ["made_by", "website", "action"]:
        data.pop(key, None)

    clean_json = json.dumps(data, indent=2, ensure_ascii=False)
    return render_template("bypass.html", raw=clean_json)


# No app.run() (for Vercel WSGI)
