"""AirPilot — the Payment Ops Incident Commander.

Loop: PERCEIVE -> DETECT -> (PLAN -> VERIFY -> ACT) per incident -> RECEIPT.

The brain (``plan``) only *proposes* a remedy. The verifier gate decides whether
any Airwallex call is allowed. Nothing moves money unless the gate passes — and
an optional idempotency ledger makes "nothing moves twice" survive restarts.
"""
from __future__ import annotations

import datetime

from . import incidents as _inc
from . import verifier as _ver
from . import receipts as _rc


def plan_for(incident):
    """Propose a remedy for an incident. Pure, deterministic, no model."""
    t = incident["type"]
    if t == "delayed_transfer":
        return {"remedy": "retry_transfer", "transfer_id": incident["transfer_id"],
                "note": "escalate stuck transfer after idempotency + balance check"}
    if t == "duplicate_payment_risk":
        return {"remedy": "hold_transfer", "transfer_id": incident["matched_transfer_ids"][-1],
                "note": "hold the pending duplicate; keep the completed one"}
    if t == "insufficient_balance":
        return {"remedy": "fund_account", "transfer_id": incident["transfer_id"],
                "note": "flag funding gap; do not push overdraft"}
    return {"remedy": "escalate", "transfer_id": incident.get("transfer_id"), "note": "human review"}


def command(client, now=None, max_steps=50, ledger=None):
    """Run one command pass. Returns a receipt dict.

    ``ledger`` (optional IdempotencyLedger) makes the never-double-pay
    guarantee survive crashes: actions already executed in a previous
    process are blocked before any Airwallex call is made.
    """
    trace = []
    balances = client.get_balances()
    transfers = client.list_transfers()
    ctx = {"transfers": transfers, "balances": balances,
           "account_id": client.base_url and "acc_main"}

    found = _inc.detect_all(transfers, balances, now=now)
    actions = []
    for inc in found:
        proposal = plan_for(inc)
        ok, reason = _ver.verify(proposal, ctx, ledger=ledger)
        record = {
            "incident": inc,
            "proposal": proposal,
            "verified": ok,
            "verdict": reason,
        }
        if ok:
            key = _ver.execution_key(proposal, ctx)
            res = _apply(client, proposal)
            record["result"] = res
            record["acted"] = bool(res.get("acted", True))
            if record["acted"] and ledger is not None:
                # only money that actually moved enters the ledger
                ledger.record(key, {"incident": inc["type"],
                                    "result_id": res.get("id")})
        else:
            record["acted"] = False
        actions.append(record)
        trace.append(record)

    receipt = _rc.build(
        source=client.source,
        balances=balances,
        incidents=found,
        actions=actions,
        steps=len(trace),
    )
    if ledger is not None:
        receipt["ledger_keys"] = len(ledger)
    return receipt


def _apply(client, proposal):
    kind = proposal["remedy"]
    tid = proposal["transfer_id"]
    if kind == "retry_transfer":
        t = client.get_transfer(tid)
        return client.create_transfer({
            "currency": t["currency"],
            "transfer_amount": t["amount"],
            "beneficiary": t["beneficiary"],
            "beneficiary_account": t.get("beneficiary_account"),
            "reference": t.get("reference", "") + " (retry)",
            "idempotency_key": "airpilot-retry-" + tid,
        })
    if kind == "hold_transfer":
        # Airwallex has no "hold" verb; we model it as a no-op + recorded decision
        return {"id": "hold-" + tid, "status": "held_by_agent", "acted": False}
    if kind == "refund_transfer":
        t = client.get_transfer(tid)
        res = client.create_refund({"transfer_id": tid,
                                    "reason": "incident-commander-refund"})
        res["acted"] = True
        return res
    # fund_account / escalate / mark_resolved -> informational, no money moves
    return {"id": "info-" + (tid or "na"), "status": "queued_for_review", "acted": False}
