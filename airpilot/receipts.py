"""Receipt builders: JSON + self-contained HTML (no external assets)."""
from __future__ import annotations

import html


def build(source, balances, incidents, actions, steps):
    return {
        "product": "AirPilot",
        "source": source,
        "generated_at": _now(),
        "steps": steps,
        "incidents_found": len(incidents),
        "incidents": incidents,
        "actions": actions,
        "acted_count": sum(1 for a in actions if a.get("acted")),
        "blocked_count": sum(1 for a in actions if not a.get("acted")),
        "balances": balances,
    }


_CSS = (
    "body{font-family:system-ui,sans-serif;margin:2rem;color:#111}"
    "h1{font-size:1.3rem}.meta{color:#666;font-size:.85rem}"
    "table{border-collapse:collapse;width:100%;margin-top:1rem}"
    "th,td{border:1px solid #ddd;padding:.5rem;text-align:left;font-size:.85rem}"
    ".ok{color:#0a7d28;font-weight:600}.blocked{color:#b3261e;font-weight:600}"
    ".badge{display:inline-block;padding:.15rem .5rem;border-radius:.3rem;background:#eee}"
)


def to_html(rc):
    rows = []
    for a in rc["actions"]:
        inc = a["incident"]
        verdict_cls = "ok" if a["verified"] else "blocked"
        rows.append(
            "<tr><td>" + html.escape(inc["type"]) +
            "</td><td>" + html.escape(str(inc.get("beneficiary", inc.get("transfer_id", "")))) +
            "</td><td>" + html.escape(a["proposal"]["remedy"]) +
            "</td><td class='" + verdict_cls + "'>" + html.escape(a["verdict"]) +
            "</td><td>" + ("ACTED" if a["acted"] else "BLOCKED") + "</td></tr>")
    if not rows:
        rows.append("<tr><td colspan='5'>No incidents found — books clean.</td></tr>")
    meta = ("source: <span class='badge'>" + html.escape(rc["source"]) +
            "</span> &middot; generated: " + html.escape(rc["generated_at"]) +
            " &middot; steps: " + str(rc["steps"]) +
            " &middot; incidents: " + str(rc["incidents_found"]) +
            " &middot; acted: " + str(rc["acted_count"]) +
            " &middot; blocked: " + str(rc["blocked_count"]))
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>AirPilot Receipt</title><style>" + _CSS + "</style></head><body>"
        "<h1>🛡️ AirPilot — Payment Ops Incident Commander Receipt</h1>"
        "<p class='meta'>" + meta + "</p>"
        "<table><thead><tr><th>Incident</th><th>Beneficiary</th><th>Remedy</th>"
        "<th>Verdict</th><th>Action</th></tr></thead><tbody>"
        + "".join(rows) + "</tbody></table>"
        "<p class='meta'>AirPilot proposes. The verifier decides what moves money.</p>"
        "</body></html>")


def _now():
    import datetime
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
