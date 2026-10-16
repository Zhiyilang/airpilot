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
    """Duplicate-payment risk: same beneficiary + account + amount + reference,
    one pending.

    The account must match too: reusing a reference to pay a *different*
    account is not a duplicate payment (the first money went elsewhere), it is
    an account takeover — that pair belongs to detect_beneficiary_changed,
    which escalates instead of holding.
    """
    out = []
    by_key = {}
    for t in transfers:
        key = (t["beneficiary"], t.get("beneficiary_account"), t["amount"],
               t.get("reference"))
        by_key.setdefault(key, []).append(t)
    for (ben, _acct, amt, ref), group in by_key.items():
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


def detect_beneficiary_changed(transfers):
    """Account-takeover signal: same reference, DIFFERENT beneficiary account.

    A supplier invoice reference (``PO-5561``) should always map to the same
    bank account. If a pending transfer reuses a completed reference but pays a
    different account, that is either a compromised vendor record or an
    attacker who found the reference in an email thread. Either way the retry
    must be blocked and a human must look. This attack slips straight through
    a naive beneficiary+amount duplicate check because the *amount* is right.
    """
    out = []
    by_ref = {}
    for t in transfers:
        by_ref.setdefault(t.get("reference"), []).append(t)
    for ref, group in by_ref.items():
        if not ref or len(group) < 2:
            continue
        accounts = {g.get("beneficiary_account") for g in group
                    if g.get("beneficiary_account")}
        if len(accounts) < 2:
            continue
        pending = [g for g in group if g.get("status") in ("review", "processing")]
        done = [g for g in group if g.get("status") == "completed"]
        if not (pending and done):
            continue
        pay = next(g for g in group if g.get("beneficiary_account") !=
                   done[0].get("beneficiary_account"))
        out.append({
            "type": "beneficiary_account_changed",
            "transfer_id": pay["id"],
            "reference": ref,
            "beneficiary": pay["beneficiary"],
            "expected_account": done[0].get("beneficiary_account"),
            "actual_account": pay.get("beneficiary_account"),
            "amount": pay["amount"],
            "currency": pay["currency"],
            "matched_transfer_ids": [g["id"] for g in group],
            "severity": "CRITICAL",
            "summary": "Reference %s was paid to %s before, but transfer %s pays %s "
                       "— possible account takeover; human review required."
                       % (ref, done[0].get("beneficiary_account"), pay["id"],
                          pay.get("beneficiary_account")),
        })
    return out


def detect_rapid_repeat(transfers, window_min=90):
    """Reference-dodged duplicate: same beneficiary + currency, DIFFERENT
    references, created within a short window, at least one still pending.

    The duplicate detector groups on (beneficiary, amount, reference). An
    attacker who knows that tweaks the reference (``INV-2026-0901`` ->
    ``INV-2026-0901-R2``) and pays the same supplier the same amount twice.
    Time window is the tell: genuine supplier invoices do not arrive twice
    within 90 minutes for the same amount.
    """
    out = []
    by_bc = {}
    for t in transfers:
        by_bc.setdefault((t["beneficiary"], t["currency"]), []).append(t)
    for (ben, cur), group in by_bc.items():
        pending = [g for g in group if g.get("status") in ("review", "processing")]
        if not pending or len(group) < 2:
            continue
        refs = {g.get("reference") for g in group}
        if len(refs) < 2:
            continue  # identical reference -> handled by detect_duplicate
        times = [_parse(g["created_at"]) for g in group]
        span_min = (max(times) - min(times)).total_seconds() / 60.0
        if span_min > window_min:
            continue
        out.append({
            "type": "rapid_repeat_payment",
            "transfer_id": pending[0]["id"],
            "beneficiary": ben,
            "amount": pending[0]["amount"],
            "currency": cur,
            "window_minutes": round(span_min, 1),
            "references": sorted(r for r in refs if r),
            "matched_transfer_ids": [g["id"] for g in group],
            "severity": "HIGH",
            "summary": "%s received %s %s twice within %.0f min under different "
                       "references %s — reference-dodged duplicate suspected."
                       % (ben, pending[0]["amount"], cur, span_min,
                          sorted(r for r in refs if r)),
        })
    return out


def detect_all(transfers, balances, now=None):
    return (detect_delayed(transfers, now=now)
            + detect_duplicate(transfers)
            + detect_insufficient(transfers, balances)
            + detect_beneficiary_changed(transfers)
            + detect_rapid_repeat(transfers))
