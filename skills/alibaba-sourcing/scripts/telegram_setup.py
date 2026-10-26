#!/usr/bin/env python3
"""Finish Telegram alert setup: find your chat id and send a test message.

1. Create a bot with @BotFather in Telegram and copy its token.
2. Put the token into $SOURCING_HOME/_shared/notify.json yourself:
     {"telegram": {"bot_token": "123456:ABC..."}}
3. Open your new bot in Telegram and send it any message (e.g. /start).
4. Run this script. It reads the token, finds the private chat that wrote to the bot,
   saves "chat_id" into notify.json and sends a test message.

The token is never printed.
"""
import json, os, sys, urllib.parse, urllib.request

HOME = os.path.expanduser(os.environ.get("SOURCING_HOME", "~/Sourcing"))
CFG = os.path.join(HOME, "_shared", "notify.json")


def call(token, method, params=None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params).encode() if params else None
    try:
        with urllib.request.urlopen(url, data=data, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as ex:
        try:
            return json.load(ex)
        except ValueError:
            return {"ok": False, "description": f"HTTP {ex.code}"}
    except OSError as ex:
        return {"ok": False, "description": type(ex).__name__}


def done(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)


def main():
    try:
        cfg = json.load(open(CFG))
    except FileNotFoundError:
        done({"ok": False, "error": f"{CFG} not found. Create it with your bot token (see --help)."}, 1)
    except ValueError:
        done({"ok": False, "error": f"{CFG} is not valid JSON."}, 1)
    tg = cfg.get("telegram") or {}
    token = (tg.get("bot_token") or "").strip()
    if not token or ":" not in token:
        done({"ok": False, "error": 'No valid "telegram": {"bot_token": ...} in notify.json.'}, 1)

    me = call(token, "getMe")
    if not me.get("ok"):
        done({"ok": False, "error": "Telegram rejected the token: " + str(me.get("description"))}, 1)
    bot = me["result"].get("username")

    if not tg.get("chat_id"):
        upd = call(token, "getUpdates")
        if not upd.get("ok"):
            done({"ok": False, "bot": bot, "error": str(upd.get("description"))}, 1)
        chats = []
        for u in upd.get("result", []):
            m = u.get("message") or u.get("edited_message") or {}
            c = m.get("chat") or {}
            if c.get("type") == "private":
                chats.append((c["id"], c.get("first_name") or c.get("username") or ""))
        if not chats:
            done({"ok": False, "bot": bot,
                  "error": f"No messages yet. Open t.me/{bot} in Telegram, press Start or send any message, then run this again."}, 1)
        ids = {cid for cid, _ in chats}
        if len(ids) > 1:
            done({"ok": False, "bot": bot,
                  "error": "Several people wrote to the bot. Put the right chat_id into notify.json yourself.",
                  "chats": [{"chat_id": cid, "name": n} for cid, n in dict(chats).items()]}, 1)
        tg["chat_id"] = str(chats[-1][0])
        cfg["telegram"] = tg
        tmp = CFG + ".tmp"
        with open(tmp, "w") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        os.chmod(tmp, 0o600)
        os.replace(tmp, CFG)

    sent = call(token, "sendMessage", {"chat_id": tg["chat_id"],
                                       "text": "Sourcing alerts are connected. You will get final prices, expiring quotes, sign-in/CAPTCHA requests and finished projects here."})
    if not sent.get("ok"):
        done({"ok": False, "bot": bot, "error": "Test message failed: " + str(sent.get("description"))}, 1)
    os.chmod(CFG, 0o600)
    done({"ok": True, "bot": bot, "chat_id": tg["chat_id"], "config": CFG})


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    main()
