from flask import Flask, request, Response, abort, render_template
import requests
import json
import time

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
    "https://krnl.cat/",
    "https://lockr.so/"
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
        # SECOND API
        try:
            resp = requests.get(
                SECOND_API_BASE,
                params={"url": target},
                headers={"x-api-key": SECOND_API_KEY},
                timeout=15
            )
            data = resp.json()
        except requests.RequestException:
            elapsed = time.time() - start
            return Response(
                json.dumps({"Status": "error", "message": "Custom error: second API failed.", "time": f"{elapsed:.2f}"}),
                indent=2, mimetype="application/json", status=502
            )
        except ValueError:
            elapsed = time.time() - start
            return Response(resp.text, mimetype="text/plain", status=resp.status_code)

        elapsed = time.time() - start
        if not isinstance(data, dict):
            return Response(
                json.dumps({"Status": "error", "message": "Custom error: invalid response from second API.", "time": f"{elapsed:.2f}"}),
                indent=2, mimetype="application/json", status=502
            )

        api_status = data.get("status", "").lower()
        api_data = data.get("data", {})

        if api_status == "success":
            result_obj = {
                "status": api_status,
                "result": api_data.get("result", ""),
                "time": f"{elapsed:.2f}"
            }
            return Response(json.dumps(result_obj, indent=2), mimetype="application/json", status=resp.status_code)
        else:
            # Second API error
            if not use_second_api_for_target(target):
                message = "URL not supported by second API."
            else:
                message = api_data.get("message") or data.get("message") or "Custom error: second API failed."
            error_obj = {"Status": "error", "message": message, "time": f"{elapsed:.2f}"}
            return Response(json.dumps(error_obj, indent=2), mimetype="application/json", status=resp.status_code)

    else:
        # FIRST API
        try:
            resp = requests.get(API_BASE, params={"url": target, "apikey": API_KEY}, timeout=15)
            data = resp.json()
        except requests.RequestException:
            elapsed = time.time() - start
            return Response(
                json.dumps({"Status": "error", "message": "Custom error: upstream API failed.", "time": f"{elapsed:.2f}"}),
                indent=2, mimetype="application/json", status=502
            )
        except ValueError:
            elapsed = time.time() - start
            return Response(resp.text, mimetype="text/plain", status=resp.status_code)

        elapsed = time.time() - start
        if isinstance(data, dict) and "error" in data:
            err = data.get("error")
            # Check if error is unsupported
            unsupported_msgs = ["unsupported", "not supported"]
            msg = ""
            if isinstance(err, dict):
                msg = err.get("message") or err.get("msg") or ""
            if not msg:
                msg = data.get("message") or str(err)

            if any(u.lower() in msg.lower() for u in unsupported_msgs):
                message = msg  # keep API unsupported message
            else:
                message = "Custom error: upstream API failed."

            error_obj = {"Status": "error", "message": message, "time": f"{elapsed:.2f}"}
            return Response(json.dumps(error_obj, indent=2), mimetype="application/json", status=resp.status_code)

        if isinstance(data, dict) and "result" in data:
            filtered = {"status": "success", "result": data["result"], "time": f"{elapsed:.2f}"}
            return Response(json.dumps(filtered, indent=2), mimetype="application/json", status=resp.status_code)

@app.route("/supported", methods=["GET"])
def supported_page():
    supported_list = [
        "Codex","Trigon","rekonise","linkvertise","paster-so","cuttlinks","boost-ink-and-bst-gg","keyguardian","bstshrt","nicuse-getkey","bit.do","bit.ly","blox-script","cl.gy","cuty-cuttlinks","getpolsec","goo.gl","is.gd","ldnesfspublic","link-hub.net","link-unlock-complete","link4m.com","link4sub","linkunlocker","lockr","mboost","mediafire","overdrivehub","paste-drop","pastebin","pastes_io","quartyz","rebrand.ly","rinku-pro","rkns.link","shorteners-and-direct","shorter.me","socialwolvez","sub2get","sub2unlock","sub4unlock.com","subfinal","t.co","t.ly","tiny.cc","tinylink.onl","tinyurl.com","tpi.li key-system","v.gd","work-ink","ytsubme",
        "https://socialwolvez.com/","https://adfoc.us/","https://sub2get.com/","https://sub4unlock.com/","https://sub2unlock.net/","https://sub2unlock.com/","https://mboost.me/","https://deltaios-executor.com/ads.html?URL=","https://krnl-ios.com/ads.html?URL=","https://auth.platoboost.app/","https://auth.platoboost.net/","https://loot-link.com","https://lootlink.org","https://lootlinks.co","https://lootdest.info","https://lootdest.org","https://lootdest.com","https://links-loot.com","https://loot-links.com","https://best-links.org","https://lootlinks.com","https://loot-labs.com","https://lootlabs.com","https://pandadevelopment.net/","https://krnl.cat/","https://lockr.so/"
    ]
    return render_template("supported.html", supported_json=json.dumps(supported_list, indent=2))
