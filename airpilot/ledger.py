"""Crash-safe idempotency ledger for AirPilot.

The verifier's in-memory checks (duplicate sibling, balance, allowlist) protect
a *single* command pass. Real payment ops needs stronger: if the process
crashes after creating a transfer but before the receipt is written, a restart
must not pay the supplier again. This ledger is that guarantee.

Design:
  - Keys are deterministic fingerprints of the money-moving intent
    (remedy + transfer id + beneficiary + amount + currency + reference), so
    the same intent always maps to the same key across processes.
  - Storage is a JSON file (one object per line: {"key":..., "at":...}), so it
    survives restarts and is diffable by auditors. Default is memory-only
    (``path=None``) which is what the offline eval uses; production passes a
    real path (or ``AIRPILOT_LEDGER``).
  - ``record`` is idempotent: recording an existing key is a no-op, so a
    half-written line can never corrupt the guarantee.
"""
from __future__ import annotations

import json
import os


def fingerprint(proposal):
    """Deterministic key for a money-moving intent.

    Same intent -> same key, in any process, on any machine. Two proposals
    that would move the same money to the same place for the same reason
    MUST collide here, otherwise the ledger cannot block the replay.
    """
    parts = [
        str(proposal.get("remedy", "")),
        str(proposal.get("transfer_id", "")),
        str(proposal.get("beneficiary", "")),
        str(proposal.get("beneficiary_account", "")),
        str(proposal.get("amount", "")),
        str(proposal.get("currency", "")),
        str(proposal.get("reference", "")),
    ]
    return "|".join(parts)


class IdempotencyLedger:
    """Records every money-moving action by fingerprint.

    ``seen(key)`` answers "did we already move this money?" — the question the
    never-double-pay guarantee is made of. Persistence is opt-in via ``path``.
    """

    def __init__(self, path=None):
        self.path = path or os.environ.get("AIRPILOT_LEDGER")
        self._keys = set()
        self._records = {}
        if self.path:
            self.load()

    # ---- queries --------------------------------------------------------
    def seen(self, key):
        return key in self._keys

    def __contains__(self, key):
        return self.seen(key)

    def __len__(self):
        return len(self._keys)

    def keys(self):
        return sorted(self._keys)

    def records(self):
        return dict(self._records)

    # ---- mutation -------------------------------------------------------
    def record(self, key, payload=None):
        """Record an executed action. Idempotent: re-recording is a no-op."""
        if key in self._keys:
            return False
        self._keys.add(key)
        self._records[key] = {
            "at": _now(),
            "payload": payload if payload is not None else {},
        }
        if self.path:
            self._append(key, self._records[key])
        return True

    # ---- persistence ----------------------------------------------------
    def load(self):
        """Load an existing ledger file. Missing file -> empty ledger.

        A corrupt line is skipped rather than fatal: losing one historical
        record must not stop the agent from protecting *future* payments.
        """
        if not self.path or not os.path.exists(self.path):
            return
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    key = rec["key"]
                except (ValueError, KeyError):
                    continue
                self._keys.add(key)
                self._records[key] = {
                    "at": rec.get("at"),
                    "payload": rec.get("payload", {}),
                }

    def _append(self, key, record):
        d = os.path.dirname(os.path.abspath(self.path))
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"key": key, "at": record["at"],
                                "payload": record["payload"]},
                               ensure_ascii=False) + "\n")


def _now():
    import datetime
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
