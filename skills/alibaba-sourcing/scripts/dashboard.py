#!/usr/bin/env python3
"""Build one HTML dashboard for all sourcing projects.

Reads $SOURCING_HOME/_shared/projects.json (written by coord.py) and each project's
<folder>/status.json, and writes $SOURCING_HOME/dashboard.html (auto-refreshes every 60 s).
Optional labels in the user's language: $SOURCING_HOME/_shared/dashboard_labels.json
({"title": "...", "needs_you": "...", ...}; missing keys fall back to English).

status.json (written by each project after every check):
{
  "product": "1500W heater", "stage": "negotiation", "updated": "2026-10-27T09:00:00Z",
  "platforms": ["alibaba", "mic"], "workbook": "sourcing/output/heater.xlsx",
  "suppliers": {"contacted": 15, "replied": 9, "waiting": 4, "final": 3, "declined": 2, "no_reply": 1},
  "best_prices": [{"tier": "500", "price": 12.4, "currency": "USD", "incoterm": "EXW",
                   "supplier": "Ningbo X", "platform": "alibaba", "final": true, "valid_until": "2026-11-05"}],
  "waiting_on": [{"supplier": "Foshan Y", "platform": "mic", "since": "2026-10-25", "next_follow_up": "2026-10-28"}],
  "needs_user": [{"what": "CAPTCHA on Alibaba", "since": "2026-10-27T08:55:00Z"}],
  "verification": [{"supplier": "Ningbo X", "result": "verified"}],
  "next_action": "Counter Foshan Y with 11.9 USD"
}
"""
import html, json, os, sys
from datetime import date, datetime

HOME = os.path.expanduser(os.environ.get("SOURCING_HOME", "~/Sourcing"))
SHARED = os.path.join(HOME, "_shared")
OUT = os.path.join(HOME, "dashboard.html")

STAGES = ["brief", "search", "quotes", "negotiation", "finalists", "verification", "wechat", "done"]
L = {
    "title": "Sourcing projects", "updated": "Updated", "needs_you": "Needs you", "nothing": "Nothing right now",
    "expiring": "Quotes expiring within 3 days", "projects": "Projects", "no_projects": "No projects yet",
    "stage": "Stage", "next": "Next action", "best": "Best prices", "tier": "Qty", "price": "Price",
    "supplier": "Supplier", "platform": "Platform", "final": "Final", "valid": "Valid until", "yes": "yes",
    "no": "no", "waiting": "Waiting for reply", "since": "since", "follow_up": "follow-up",
    "contacted": "contacted", "replied": "replied", "final_n": "final", "declined": "declined",
    "no_reply": "no reply", "verification": "Verification", "workbook": "Workbook", "missing": "status.json not found",
    "stages": {s: s.capitalize() for s in STAGES},
}


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def e(x):
    return html.escape("" if x is None else str(x))


def ts(x):
    return str(x or "")[:16].replace("T", " ")


def days_left(d):
    try:
        return (date.fromisoformat(str(d)[:10]) - date.today()).days
    except ValueError:
        return None


def main():
    labels = load(os.path.join(SHARED, "dashboard_labels.json"), {})
    stages = {**L["stages"], **labels.pop("stages", {})}
    L.update(labels)
    projects = load(os.path.join(SHARED, "projects.json"), {})

    needs, expiring, cards = [], [], []
    for slug, rec in sorted(projects.items()):
        folder = os.path.expanduser(rec.get("folder") or os.path.join(HOME, slug))
        st = load(os.path.join(folder, "status.json"), None)
        name = (st or {}).get("product") or rec.get("product") or slug
        if st is None:
            cards.append(f'<section class="card"><h2>{e(name)}</h2><p class="muted">{e(L["missing"])}</p></section>')
            continue
        for n in st.get("needs_user", []):
            needs.append(f'<li><b>{e(name)}</b>: {e(n.get("what"))} <span class="muted">{e(ts(n.get("since")))}</span></li>')
        stage = st.get("stage") or rec.get("stage") or "brief"
        idx = STAGES.index(stage) if stage in STAGES else 0
        steps = "".join(f'<span class="step{" on" if i <= idx else ""}" title="{e(stages.get(s, s))}"></span>'
                        for i, s in enumerate(STAGES))
        sup = st.get("suppliers", {})
        counts = " · ".join(f'{sup[k]} {e(L[lbl])}' for k, lbl in
                            (("contacted", "contacted"), ("replied", "replied"), ("final", "final_n"),
                             ("declined", "declined"), ("no_reply", "no_reply")) if k in sup)
        rows = []
        for p in st.get("best_prices", []):
            dl = days_left(p.get("valid_until", ""))
            warn = dl is not None and dl <= 3
            if warn:
                expiring.append(f'<li><b>{e(name)}</b>: {e(p.get("supplier"))}, {e(p.get("tier"))} — '
                                f'{e(p.get("valid_until"))}</li>')
            rows.append(
                f'<tr><td>{e(p.get("tier"))}</td><td class="num">{e(p.get("price"))} {e(p.get("currency"))} '
                f'{e(p.get("incoterm", ""))}</td><td>{e(p.get("supplier"))}</td><td>{e(p.get("platform"))}</td>'
                f'<td>{e(L["yes"] if p.get("final") else L["no"])}</td>'
                f'<td class="{"warn" if warn else ""}">{e(p.get("valid_until", ""))}</td></tr>')
        table = (f'<h3>{e(L["best"])}</h3><table><tr><th>{e(L["tier"])}</th><th>{e(L["price"])}</th>'
                 f'<th>{e(L["supplier"])}</th><th>{e(L["platform"])}</th><th>{e(L["final"])}</th>'
                 f'<th>{e(L["valid"])}</th></tr>{"".join(rows)}</table>') if rows else ""
        waits = "".join(f'<li>{e(w.get("supplier"))} ({e(w.get("platform"))}) — {e(L["since"])} {e(w.get("since"))}'
                        f'{", " + e(L["follow_up"]) + " " + e(w.get("next_follow_up")) if w.get("next_follow_up") else ""}</li>'
                        for w in st.get("waiting_on", []))
        ver = "".join(f'<li>{e(v.get("supplier"))}: {e(v.get("result"))}</li>' for v in st.get("verification", []))
        wb = st.get("workbook")
        wb_link = ""
        if wb:
            wb_path = wb if os.path.isabs(wb) else os.path.join(folder, wb)
            wb_link = f'<p><a href="file://{e(wb_path)}">{e(L["workbook"])}</a></p>'
        waits_html = f'<h3>{e(L["waiting"])}</h3><ul>{waits}</ul>' if waits else ""
        ver_html = f'<h3>{e(L["verification"])}</h3><ul>{ver}</ul>' if ver else ""
        cards.append(
            f'<section class="card"><h2>{e(name)}</h2>'
            f'<p><span class="pill">{e(L["stage"])}: {e(stages.get(stage, stage))}</span> '
            f'<span class="muted">{e(L["updated"])} {e(ts(st.get("updated")))}</span></p>'
            f'<div class="steps">{steps}</div><p class="muted">{counts}</p>'
            f'<p><b>{e(L["next"])}:</b> {e(st.get("next_action", ""))}</p>{table}'
            f'{waits_html}{ver_html}{wb_link}</section>')

    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="60"><title>{e(L["title"])}</title><style>
:root{{--bg:#f7f7f5;--card:#fff;--text:#1c1c1a;--muted:#6b6b66;--line:#e4e4df;--accent:#2f6fde;--warn:#b4541a;--warnbg:#fdf1e7}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--card:#1f1f1d;--text:#ecece8;--muted:#9a9a94;--line:#33332f;--accent:#7aa7ff;--warn:#f0a36b;--warnbg:#3a271a}}}}
body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 -apple-system,system-ui,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:24px 16px}}h1{{font-size:22px;font-weight:500;margin:0 0 4px}}
h2{{font-size:17px;font-weight:500;margin:0 0 6px}}h3{{font-size:14px;font-weight:500;margin:14px 0 6px}}
.muted{{color:var(--muted)}}.alert{{background:var(--warnbg);border:1px solid var(--warn);border-radius:12px;padding:12px 16px;margin:16px 0}}
.alert h2{{color:var(--warn)}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:16px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;overflow-x:auto}}
.pill{{border:1px solid var(--line);border-radius:999px;padding:1px 10px;font-size:13px}}
.steps{{display:flex;gap:4px;margin:10px 0}}.step{{flex:1;height:6px;border-radius:3px;background:var(--line)}}.step.on{{background:var(--accent)}}
table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left}}
th{{font-weight:500;color:var(--muted)}}.num{{white-space:nowrap}}.warn{{color:var(--warn);font-weight:500}}ul{{margin:0;padding-left:18px}}a{{color:var(--accent)}}
</style></head><body><main><h1>{e(L["title"])}</h1><p class="muted">{e(L["updated"])} {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
<div class="alert"><h2>{e(L["needs_you"])}</h2>{"<ul>" + "".join(needs) + "</ul>" if needs else "<p class='muted'>" + e(L["nothing"]) + "</p>"}</div>
{"<div class='alert'><h2>" + e(L["expiring"]) + "</h2><ul>" + "".join(expiring) + "</ul></div>" if expiring else ""}
<h2>{e(L["projects"])}</h2><div class="grid">{"".join(cards) or "<p class='muted'>" + e(L["no_projects"]) + "</p>"}</div>
</main></body></html>"""
    os.makedirs(HOME, exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w") as f:
        f.write(page)
    os.replace(tmp, OUT)
    print(json.dumps({"dashboard": OUT, "projects": len(projects), "needs_user": len(needs), "expiring": len(expiring)}))


if __name__ == "__main__":
    sys.exit(main())
