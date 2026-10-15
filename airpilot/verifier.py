"""The deterministic prove-then-act gate.

The agent's brain may *propose* a remedy (retry / hold / refund / fund). It may
NOT execute anything. Every proposal must pass this verifier before a single
Airwallex call is made. Rules:

  1. idempotency  — never create a transfer that duplicates an existing one
                    (the "never pay twice" guarantee).
  2. balance      — a transfer must not exceed available balance.
  3. scoped       — the action must reference the incident it resolves.
  4. allowlist    — only known-safe remedy kinds are permitted.
  5. no-self-pay — beneficiary must not equal the source account.
"""
from __future__ import annotations


ALLOWED_REMEDIES = {
    "retry_transfer", "hold_transfer", "refund_transfer",
    "fund_account", "escalate", "mark_resolved",
}


def verify(proposal, ctx):
    """Return (ok: bool, reason: str). ``ctx`` holds transfers + balances + account."""
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
        dup = [t for t in transfers
               if t["id"] != tid
               and t.get("beneficiary") == target.get("beneficiary")
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

    elif kind == "refund_transfer":
        # only refund a completed transfer, never a review one
        if target.get("status") != "completed":
            ok = False
            reasons.append("refund only allowed on completed transfers")

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
