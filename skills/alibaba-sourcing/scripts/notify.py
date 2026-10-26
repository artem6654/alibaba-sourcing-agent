#!/usr/bin/env python3
"""Send a short sourcing alert to the user's phone (and as a local macOS notification).

Usage: notify.py "<message>" [--key <dedupe-key>] [--project <slug>] [--priority high]

Channels come from $SOURCING_HOME/_shared/notify.json, which the user fills in themselves:
  {"ntfy": {"topic": "my-secret-topic", "server": "https://ntfy.sh"},
   "telegram": {"bot_token": "...", "chat_id": "..."},
   "macos": true}
Any subset works. With no file, only the macOS notification is shown.
--key makes the alert one-off: the same key is never sent twice (log in _shared/notified.json).
Messages are trimmed to 200 characters. Prints JSON with the result per channel.
"""
import argparse, fcntl, json, os, subprocess, sys, time, urllib.parse, urllib.request

HOME = os.path.expanduser(os.environ.get("SOURCING_HOME", "~/Sourcing"))
SHARED = os.path.join(HOME, "_shared")


def post(url, data, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("message")
    ap.add_argument("--key")
    ap.add_argument("--project")
    ap.add_argument("--priority", choices=["default", "high"], default="default")
    a = ap.parse_args()

    msg = " ".join(a.message.split())
    if a.project:
        msg = f"[{a.project}] {msg}"
    msg = msg[:200]

    os.makedirs(SHARED, exist_ok=True)
    log_path = os.path.join(SHARED, "notified.json")
    with open(os.path.join(SHARED, ".notify.lock"), "w") as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)
        try:
            sent = json.load(open(log_path))
        except (OSError, ValueError):
            sent = {}
        if a.key and a.key in sent:
            print(json.dumps({"skipped": "already sent", "key": a.key}))
            return 0
        try:
            cfg = json.load(open(os.path.join(SHARED, "notify.json")))
        except (OSError, ValueError):
            cfg = {}

        result = {}
        ntfy = cfg.get("ntfy") or {}
        if ntfy.get("topic"):
            url = ntfy.get("server", "https://ntfy.sh").rstrip("/") + "/" + urllib.parse.quote(ntfy["topic"])
            headers = {"Title": "Sourcing", "Priority": "high" if a.priority == "high" else "default"}
            try:
                result["ntfy"] = post(url, msg.encode(), headers)
            except Exception as ex:  # report and keep trying other channels
                result["ntfy"] = f"error: {ex}"
        tg = cfg.get("telegram") or {}
        if tg.get("bot_token") and tg.get("chat_id"):
            url = f"https://api.telegram.org/bot{tg['bot_token']}/sendMessage"
            data = urllib.parse.urlencode({"chat_id": tg["chat_id"], "text": msg}).encode()
            try:
                result["telegram"] = post(url, data)
            except Exception as ex:
                result["telegram"] = f"error: {type(ex).__name__}"  # never echo the token
        if cfg.get("macos", True) and sys.platform == "darwin":
            quoted = '"' + msg.replace("\\", "\\\\").replace('"', '\\"') + '"'
            script = f'display notification {quoted} with title "Sourcing"'
            result["macos"] = subprocess.run(["osascript", "-e", script], capture_output=True).returncode

        delivered = any(v in (200, 0) for v in result.values())
        if a.key and delivered:
            sent[a.key] = time.time()
            with open(log_path + ".tmp", "w") as f:
                json.dump(sent, f)
            os.replace(log_path + ".tmp", log_path)
    print(json.dumps({"delivered": delivered, "channels": result, "message": msg}, ensure_ascii=False))
    return 0 if delivered else 1


if __name__ == "__main__":
    sys.exit(main())
