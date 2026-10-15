"""Incident detectors for the Payment Ops Incident Commander track.

Each detector returns a list of incident dicts. Detectors are pure functions
over the data Airwallex returns (transfers + balances) — no network, no model.
This is what makes the "command" auditable: every incident is derived from
numbers you can point at.
"""
from __future__ import annotations

import datetime


def _parse(ts):
    # tolerate trailing Z
    return datetime.datetime.strptime(ts.rstrip("Z"), "%Y-%m-%dT%H:%M:%S")


def detect_delayed(transfers, now=None, sla_buffer_min=0):
    """Delayed supplier transfer: still in a non-terminal state past its SLA."""
    now = now or datetime.datetime.utcnow()
    out = []
    for t in transfers:
        if t.get("status") in ("review", "processing"):
            created = _parse(t["created_at"])
            sla = int(t.get("sla_minutes", 240))
            age_min = (now - created).total_seconds() / 60.0
            if age_min > (sla + sla_buffer_min):
                out.append({
                    "type": "delayed_transfer",
                    "transfer_id": t["id"],
                    "beneficiary": t["beneficiary"],
                    "amount": t["amount"],
                    "currency": t["currency"],
                    "age_minutes": round(age_min, 1),
                    "severity": "HIGH",
                    "summary": "Transfer to %s stuck in %s for %.0f min (SLA %d)."
                               % (t["beneficiary"], t["status"], age_min, sla),
                })
    return out


def detect_duplicate(transfers):
    """Duplicate-payment risk: same beneficiary + amount + reference, one pending."""
    out = []
    by_key = {}
    for t in transfers:
        key = (t["beneficiary"], t["amount"], t.get("reference"))
        by_key.setdefault(key, []).append(t)
    for (ben, amt, ref), group in by_key.items():
        if len(group) < 2:
            continue
        pending = [g for g in group if g.get("status") in ("review", "processing")]
        done = [g for g in group if g.get("status") == "completed"]
        if pending and done:
            out.append({
                "type": "duplicate_payment_risk",
                "beneficiary": ben,
                "amount": amt,
                "currency": group[0]["currency"],
                "reference": ref,
                "matched_transfer_ids": [g["id"] for g in group],
                "severity": "HIGH",
                "summary": "Likely double payment to %s (%s %s, ref %s): %d paid, %d pending."
                           % (ben, amt, group[0]["currency"], ref, len(done), len(pending)),
            })
    return out


def detect_insufficient(transfers, balances, proposed=None):
    """Insufficient balance: a pending transfer exceeds available balance."""
    out = []
    avail = {}
    for b in balances.get("balances", []):
        avail[b["currency"]] = float(b["available"])
    for t in transfers:
        if t.get("status") in ("review", "processing"):
            cur = t["currency"]
            amt = float(t["amount"])
            if cur in avail and amt > avail[cur]:
                out.append({
                    "type": "insufficient_balance",
                    "transfer_id": t["id"],
                    "beneficiary": t["beneficiary"],
                    "amount": t["amount"],
                    "currency": cur,
                    "available": str(avail[cur]),
                    "severity": "CAUTION",
                    "summary": "Transfer to %s (%s %s) exceeds available %s %s."
                               % (t["beneficiary"], t["amount"], cur, avail[cur], cur),
                })
    return out


def detect_all(transfers, balances, now=None):
    return (detect_delayed(transfers, now=now)
            + detect_duplicate(transfers)
            + detect_insufficient(transfers, balances))
