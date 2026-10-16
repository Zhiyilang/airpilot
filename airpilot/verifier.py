"""The deterministic prove-then-act gate.

The agent's brain may *propose* a remedy (retry / hold / refund / fund). It may
NOT execute anything. Every proposal must pass this verifier before a single
Airwallex call is made. Rules:

  1. idempotency  — never create a transfer that duplicates an existing one
                    (the "never pay twice" guarantee).
  2. ledger       — never repeat an action this agent already executed, even
                    across process restarts (crash-safe idempotency).
  3. balance      — a transfer must not exceed available balance.
  4. scoped       — the action must reference the incident it resolves.
  5. allowlist    — only known-safe remedy kinds are permitted.
  6. no-self-pay — beneficiary must not equal the source account.
  7. account-change — a retry whose reference was previously paid to a
                    DIFFERENT account is blocked (account-takeover signal).
  8. rapid-repeat  — a retry inside a same-beneficiary/different-reference
                    burst is blocked (reference-dodged duplicate).
"""
from __future__ import annotations

from . import incidents as _inc
from .ledger import fingerprint as _fingerprint


ALLOWED_REMEDIES = {
    "retry_transfer", "hold_transfer", "refund_transfer",
    "fund_account", "escalate", "mark_resolved",
}


def execution_key(proposal, ctx):
    """Fingerprint of the money-moving intent behind a verified proposal.

    Enriched from the target transfer so the key captures *what money would
    actually move*, not just the agent's wording. The agent records this key
    in the ledger after acting; a later process rebuilds the same key and the
    ledger blocks the replay.
    """
    transfers = ctx.get("transfers", [])
    target = next((t for t in transfers
                   if t["id"] == proposal.get("transfer_id")), {})
    return _fingerprint({
        "remedy": proposal.get("remedy"),
        "transfer_id": proposal.get("transfer_id"),
        "beneficiary": target.get("beneficiary"),
        "beneficiary_account": target.get("beneficiary_account"),
        "amount": target.get("amount"),
        "currency": target.get("currency"),
        "reference": target.get("reference"),
    })


def verify(proposal, ctx, ledger=None):
    """Return (ok: bool, reason: str). ``ctx`` holds transfers + balances +
    account. ``ledger`` (optional) adds crash-safe replay protection."""
    reasons = []
    ok = True

    kind = proposal.get("remedy")
    if kind not in ALLOWED_REMEDIES:
        return False, "remedy %r not on allowlist" % kind

    tid = proposal.get("transfer_id")
    if not tid:
        return False, "proposal does not reference a transfer_id"

    transfers = ctx.get("transfers", [])
    target = next((t for t in transfers if t["id"] == tid), None)
    if target is None:
        return False, "transfer_id %s not found" % tid

    if kind == "retry_transfer":
        # idempotency: do not retry if an identical completed transfer exists
        # (same account — a different account with the same reference is an
        # account takeover, caught by the account-change rule below)
        dup = [t for t in transfers
               if t["id"] != tid
               and t.get("beneficiary") == target.get("beneficiary")
               and t.get("beneficiary_account") == target.get("beneficiary_account")
               and t.get("amount") == target.get("amount")
               and t.get("reference") == target.get("reference")
               and t.get("status") == "completed"]
        if dup:
            ok = False
            reasons.append("idempotency: identical completed transfer exists -> would double-pay")
        # balance check
        bal = ctx.get("balances", {})
        avail = _avail(bal, target.get("currency"))
        if avail is not None and float(target.get("amount", 0)) > avail:
            ok = False
            reasons.append("balance: amount exceeds available %s" % avail)
        # no self-pay
        if target.get("beneficiary_account") == ctx.get("account_id"):
            ok = False
            reasons.append("no-self-pay: beneficiary equals source account")
        # account-takeover: same reference previously paid to another account
        changed = _inc.detect_beneficiary_changed(transfers)
        if any(tid in i["matched_transfer_ids"] for i in changed):
            ok = False
            reasons.append("account-change: reference %s was paid to a different account -> possible takeover"
                           % target.get("reference"))
        # reference-dodged duplicate burst
        rapid = _inc.detect_rapid_repeat(transfers)
        if any(tid in i["matched_transfer_ids"] for i in rapid):
            ok = False
            reasons.append("rapid-repeat: same beneficiary paid again under a tweaked reference")
        # crash-safe ledger: did THIS agent already execute this intent?
        if ledger is not None and ledger.seen(execution_key(proposal, ctx)):
            ok = False
            reasons.append("ledger: this exact action was already executed (crash-safe idempotency)")

    elif kind == "refund_transfer":
        # only refund a completed transfer, never a review one
        if target.get("status") != "completed":
            ok = False
            reasons.append("refund only allowed on completed transfers")
        if ledger is not None and ledger.seen(execution_key(proposal, ctx)):
            ok = False
            reasons.append("ledger: this exact refund was already executed")

    elif kind == "hold_transfer":
        # holding a review transfer is always safe (no money moves)
        pass

    elif kind in ("fund_account", "escalate", "mark_resolved"):
        # informational / no outbound money movement
        pass

    return ok, ("; ".join(reasons) if reasons else "ok")


def _avail(balances, currency):
    for b in balances.get("balances", []):
        if b["currency"] == currency:
            return float(b["available"])
    return None
