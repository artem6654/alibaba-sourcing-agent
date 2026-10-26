#!/usr/bin/env python3
"""Coordination for several sourcing projects that share one Alibaba / Made-in-China account.

State lives in $SOURCING_HOME/_shared (default ~/Sourcing/_shared):
  projects.json   project index: slug -> stage, status, platforms, folder, updated
  suppliers.json  "<platform>:<supplier_id>" -> name, chat url, projects {slug: product}
  sends.jsonl     one line per message sent (time, platform, supplier, project, kind)
  locks/          one directory per supplier chat that a project is writing to right now

Every command prints JSON. Exit code 0 = ok, 1 = refused (e.g. chat locked by another project).
"""
import argparse, contextlib, fcntl, json, os, sys, time
from datetime import datetime, timezone

HOME = os.path.expanduser(os.environ.get("SOURCING_HOME", "~/Sourcing"))
SHARED = os.path.join(HOME, "_shared")
LOCKS = os.path.join(SHARED, "locks")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextlib.contextmanager
def state(name):
    """Read-modify-write a shared JSON file under an exclusive file lock."""
    os.makedirs(SHARED, exist_ok=True)
    path = os.path.join(SHARED, name)
    with open(os.path.join(SHARED, ".state.lock"), "w") as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)
        data = json.load(open(path)) if os.path.exists(path) else {}
        yield data
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)


def key(platform, supplier):
    return f"{platform.lower()}:{supplier}"


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)


def cmd_project(a):
    with state("projects.json") as p:
        rec = p.setdefault(a.slug, {"created": now()})
        for f in ("stage", "status", "folder", "platforms", "product"):
            v = getattr(a, f)
            if v is not None:
                rec[f] = v
        rec["updated"] = now()
        res = {"project": a.slug, **rec}
    out(res)


def cmd_projects(a):
    with state("projects.json") as p:
        res = dict(p)
    out(res)


def cmd_register(a):
    with state("suppliers.json") as s:
        rec = s.setdefault(key(a.platform, a.supplier), {"projects": {}})
        rec["name"] = a.name or rec.get("name")
        if a.chat_url:
            rec["chat_url"] = a.chat_url
        rec["projects"][a.project] = a.product
        others = {k: v for k, v in rec["projects"].items() if k != a.project}
    out({"supplier": key(a.platform, a.supplier), "shared_with": others})


def cmd_who(a):
    with state("suppliers.json") as s:
        res = s.get(key(a.platform, a.supplier), {"projects": {}})
    out(res)


def lock_dir(platform, supplier):
    safe = key(platform, supplier).replace("/", "_").replace(":", "__")
    return os.path.join(LOCKS, safe)


def cmd_claim(a):
    os.makedirs(LOCKS, exist_ok=True)
    d = lock_dir(a.platform, a.supplier)
    for _ in range(2):
        try:
            os.mkdir(d)  # atomic: only one project can create it
            json.dump({"project": a.project, "since": time.time()}, open(os.path.join(d, "owner.json"), "w"))
            out({"claimed": True, "project": a.project})
        except FileExistsError:
            try:
                owner = json.load(open(os.path.join(d, "owner.json")))
            except (OSError, ValueError):
                owner = {"project": "?", "since": os.path.getmtime(d)}
            if owner["project"] == a.project:
                out({"claimed": True, "project": a.project, "renewed": True})
            if time.time() - owner["since"] > a.ttl:  # stale lock from a crashed session
                with contextlib.suppress(OSError):
                    os.remove(os.path.join(d, "owner.json"))
                    os.rmdir(d)
                continue
            out({"claimed": False, "held_by": owner["project"],
                 "seconds_left": int(a.ttl - (time.time() - owner["since"]))}, 1)
    out({"claimed": False, "held_by": "?"}, 1)


def cmd_release(a):
    d = lock_dir(a.platform, a.supplier)
    with contextlib.suppress(OSError):
        owner = json.load(open(os.path.join(d, "owner.json")))
        if owner["project"] != a.project:
            out({"released": False, "held_by": owner["project"]}, 1)
        os.remove(os.path.join(d, "owner.json"))
        os.rmdir(d)
    out({"released": True})


def cmd_sent(a):
    os.makedirs(SHARED, exist_ok=True)
    with open(os.path.join(SHARED, "sends.jsonl"), "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(json.dumps({"t": time.time(), "at": now(), "platform": a.platform.lower(),
                            "supplier": a.supplier, "project": a.project, "kind": a.kind}) + "\n")
    out({"logged": True})


def cmd_rate(a):
    path = os.path.join(SHARED, "sends.jsonl")
    since = time.time() - a.minutes * 60
    n = 0
    if os.path.exists(path):
        for line in open(path):
            r = json.loads(line)
            if r["t"] >= since and r["platform"] == a.platform.lower() and (not a.kind or r["kind"] == a.kind):
                n += 1
    ok = a.limit is None or n < a.limit
    out({"platform": a.platform, "kind": a.kind, "last_minutes": a.minutes, "count": n, "limit": a.limit, "ok": ok},
        0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("project", help="create/update a project in the index")
    p.add_argument("slug")
    for f in ("stage", "status", "folder", "platforms", "product"):
        p.add_argument("--" + f)
    p.set_defaults(fn=cmd_project)
    sp.add_parser("projects", help="show the project index").set_defaults(fn=cmd_projects)

    for name, fn, extra in (("register", cmd_register, True), ("who", cmd_who, False)):
        p = sp.add_parser(name)
        p.add_argument("platform"); p.add_argument("supplier")
        if extra:
            p.add_argument("project"); p.add_argument("product")
            p.add_argument("--name"); p.add_argument("--chat-url")
        p.set_defaults(fn=fn)

    for name, fn in (("claim", cmd_claim), ("release", cmd_release)):
        p = sp.add_parser(name, help="lock / unlock a supplier chat before / after writing to it")
        p.add_argument("platform"); p.add_argument("supplier"); p.add_argument("project")
        p.add_argument("--ttl", type=int, default=600, help="seconds before a lock counts as stale")
        p.set_defaults(fn=fn)

    p = sp.add_parser("sent", help="log a confirmed sent message")
    p.add_argument("platform"); p.add_argument("supplier"); p.add_argument("project")
    p.add_argument("--kind", default="reply", choices=["first_contact", "reply", "follow_up", "wechat"])
    p.set_defaults(fn=cmd_sent)

    p = sp.add_parser("rate", help="count messages sent from the shared account recently")
    p.add_argument("platform")
    p.add_argument("--minutes", type=int, default=60)
    p.add_argument("--kind")
    p.add_argument("--limit", type=int)
    p.set_defaults(fn=cmd_rate)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
