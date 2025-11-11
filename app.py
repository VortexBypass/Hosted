from flask import Flask, request, Response, abort, render_template
import requests
import json
import time
from urllib.parse import urlparse

app = Flask(__name__)

API_BASE = "http://ace-bypass.com/api/bypass"
API_KEY = "FREE_S7MdXC0momgajOEx1_UKW7FQUvbmzvalu0gTwr-V6cI"
SECOND_API_BASE = "https://ka.idarko.xyz/bypass"
SECOND_API_KEY = "afkbestguy"

SECOND_API_ALLOWED = [
    "https://socialwolvez.com/",
    "https://adfoc.us/",
    "https://sub2get.com/",
    "https://sub4unlock.com/",
    "https://sub2unlock.net/",
    "https://sub2unlock.com/",
    "https://mboost.me/",
    "https://deltaios-executor.com/ads.html?URL=",
    "https://krnl-ios.com/ads.html?URL=",
    "https://auth.platoboost.app/",
    "https://auth.platoboost.net/",
    "https://loot-link.com",
    "https://lootlink.org",
    "https://lootlinks.co",
    "https://lootdest.info",
    "https://lootdest.org",
    "https://lootdest.com",
    "https://links-loot.com",
    "https://loot-links.com",
    "https://best-links.org",
    "https://lootlinks.com",
    "https://loot-labs.com",
    "https://lootlabs.com",
    "https://pandadevelopment.net/",
    "https://krnl.cat/"
]

@app.route("/", methods=["GET"])
def root_redirect():
    return ('', 302, {'Location': '/bypass?url='})

def use_second_api_for_target(target: str) -> bool:
    if not target:
        return False
    tl = target.lower()
    for allowed in SECOND_API_ALLOWED:
        if tl.startswith(allowed.lower()):
            return True
    return False

@app.route("/bypass", methods=["GET"])
def bypass_proxy():
    if 'url' not in request.args:
        return abort(400, "Missing 'url' query parameter. Use /bypass?url=<TARGET>")
    target = request.args.get("url", "")
    start = time.time()
    if use_second_api_for_target(target):
        try:
            resp = requests.get(SECOND_API_BASE, params={"url": target}, headers={"x-api-key": SECOND_API_KEY}, timeout=15)
        except requests.RequestException:
            elapsed = time.time() - start
            err_obj = {"Status": "error", "message": "Failed to contact upstream API.", "time": f"{elapsed:.2f}"}
            return Response(json.dumps(err_obj, indent=2, ensure_ascii=False), mimetype="application/json", status=502)
    else:
        try:
            resp = requests.get(API_BASE, params={"url": target, "apikey": API_KEY}, timeout=15)
        except requests.RequestException:
            elapsed = time.time() - start
            err_obj = {"Status": "error", "message": "Failed to contact upstream API.", "time": f"{elapsed:.2f}"}
            return Response(json.dumps(err_obj, indent=2, ensure_ascii=False), mimetype="application/json", status=502)
    try:
        data = resp.json()
    except ValueError:
        elapsed = time.time() - start
        return Response(resp.text, mimetype="text/plain", status=resp.status_code)
    elapsed = time.time() - start
    if isinstance(data, dict) and "error" in data:
        err = data.get("error")
        message = None
        if isinstance(err, dict):
            message = err.get("message") or err.get("msg")
        if not message:
            message = data.get("message")
        if not message:
            message = str(err)
        error_obj = {"Status": "error", "message": str(message), "time": f"{elapsed:.2f}"}
        return Response(json.dumps(error_obj, indent=2, ensure_ascii=False), mimetype="application/json", status=resp.status_code)
    filtered = {}
    if isinstance(data, dict) and "result" in data:
        filtered["status"] = "success"
        filtered["result"] = data["result"]
        filtered["time"] = f"{elapsed:.2f}"
    return Response(json.dumps(filtered, indent=2, ensure_ascii=False), mimetype="application/json", status=resp.status_code)

@app.route("/supported", methods=["GET"])
def supported_page():
    supported_list = [
        "Codex","Trigon","rekonise","linkvertise","paster-so","cuttlinks","boost-ink-and-bst-gg","keyguardian","bstshrt","nicuse-getkey","bit.do","bit.ly","blox-script","cl.gy","cuty-cuttlinks","getpolsec","goo.gl","is.gd","ldnesfspublic","link-hub.net","link-unlock-complete","link4m.com","link4sub","linkunlocker","lockr","mboost","mediafire","overdrivehub","paste-drop","pastebin","pastes_io","quartyz","rebrand.ly","rinku-pro","rkns.link","shorteners-and-direct","shorter.me","socialwolvez","sub2get","sub2unlock","sub4unlock.com","subfinal","t.co","t.ly","tiny.cc","tinylink.onl","tinyurl.com","tpi.li key-system","v.gd","work-ink","ytsubme",
        "https://socialwolvez.com/","https://adfoc.us/","https://sub2get.com/","https://sub4unlock.com/","https://sub2unlock.net/","https://sub2unlock.com/","https://mboost.me/","https://deltaios-executor.com/ads.html?URL=","https://krnl-ios.com/ads.html?URL=","https://auth.platoboost.app/","https://auth.platoboost.net/","https://loot-link.com","https://lootlink.org","https://lootlinks.co","https://lootdest.info","https://lootdest.org","https://lootdest.com","https://links-loot.com","https://loot-links.com","https://best-links.org","https://lootlinks.com","https://loot-labs.com","https://lootlabs.com","https://pandadevelopment.net/","https://krnl.cat/"
    ]
    return render_template("supported.html", supported_json=json.dumps(supported_list, indent=2))
