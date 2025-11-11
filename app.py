from flask import Flask, request, Response, abort
import requests
import json

app = Flask(__name__)

API_BASE = "http://ace-bypass.com/api/bypass"
API_KEY = "FREE_S7MdXC0momgajOEx1_UKW7FQUvbmzvalu0gTwr-V6cI"

@app.route("/", methods=["GET"])
def root_redirect():
    return ('', 302, {'Location': '/bypass?url='})

@app.route("/bypass", methods=["GET"])
def bypass_proxy():
    if 'url' not in request.args:
        return abort(400, "Missing 'url' query parameter. Use /bypass?url=<TARGET>")
    target = request.args.get("url", "")
    params = {"url": target, "apikey": API_KEY}
    try:
        resp = requests.get(API_BASE, params=params, timeout=15)
    except requests.RequestException:
        err_obj = {"Status": "error", "message": "Failed to contact upstream API."}
        return Response(json.dumps(err_obj, indent=2, ensure_ascii=False), mimetype="application/json", status=502)
    try:
        data = resp.json()
    except ValueError:
        return Response(resp.text, mimetype="text/plain", status=resp.status_code)
    if isinstance(data, dict) and "error" in data:
        err = data.get("error")
        message = None
        if isinstance(err, dict):
            message = err.get("message") or err.get("msg")
        if not message:
            message = data.get("message")
        if not message:
            message = str(err)
        error_obj = {"Status": "error", "message": str(message)}
        if isinstance(err, dict) and "time" in err:
            error_obj["time"] = err.get("time")
        elif "time" in data:
            error_obj["time"] = data.get("time")
        return Response(json.dumps(error_obj, indent=2, ensure_ascii=False), mimetype="application/json", status=resp.status_code)
    filtered = {}
    if isinstance(data, dict) and "result" in data:
        filtered["status"] = "success"
        filtered["result"] = data["result"]
        if "time" in data:
            filtered["time"] = data["time"]
    return Response(json.dumps(filtered, indent=2, ensure_ascii=False), mimetype="application/json", status=resp.status_code)
