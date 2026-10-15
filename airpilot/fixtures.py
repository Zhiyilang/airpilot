"""Bundled offline fixtures for AirPilot (Airwallex Agentic Banking Hackathon).

These let the agent run end-to-end without live credentials. Shapes mirror the
Airwallex v1 API responses closely enough that the same parsing code works
against the real API.
"""
from __future__ import annotations

import datetime
import json
import time

_BALANCES = {
    "acc_main": {
        "account_id": "acc_main",
        "balances": [
            {"currency": "USD", "available": "4200.00", "on_hold": "300.00"},
            {"currency": "EUR", "available": "1500.00", "on_hold": "0.00"},
        ],
    }
}

# A realistic incident mix:
#  - t_supplier_delayed : stuck in "review" past SLA (delayed supplier transfer)
#  - t_dup_a / t_dup_b  : two transfers to SAME beneficiary, SAME amount (dup risk)
#  - t_ok               : healthy completed transfer
_TRANSFERS = [
    {
        "id": "t_supplier_delayed",
        "status": "review",
        "beneficiary": "Acme Supplies Ltd",
        "beneficiary_account": "ACME-8821",
        "currency": "USD",
        "amount": "1800.00",
        "reference": "INV-2026-0901",
        "created_at": "2026-11-08T09:00:00Z",
        "updated_at": "2026-11-08T09:00:00Z",
        "sla_minutes": 240,
    },
    {
        "id": "t_dup_a",
        "status": "completed",
        "beneficiary": "Globex Logistics",
        "beneficiary_account": "GLX-4410",
        "currency": "USD",
        "amount": "650.00",
        "reference": "FREIGHT-771",
        "created_at": "2026-11-09T10:00:00Z",
        "updated_at": "2026-11-09T10:05:00Z",
        "sla_minutes": 240,
    },
    {
        "id": "t_dup_b",
        "status": "review",
        "beneficiary": "Globex Logistics",
        "beneficiary_account": "GLX-4410",
        "currency": "USD",
        "amount": "650.00",
        "reference": "FREIGHT-771",
        "created_at": "2026-11-11T10:00:00Z",
        "updated_at": "2026-11-11T10:00:00Z",
        "sla_minutes": 240,
    },
    {
        "id": "t_ok",
        "status": "completed",
        "beneficiary": "Umbrella Utilities",
        "beneficiary_account": "UMB-2200",
        "currency": "USD",
        "amount": "320.00",
        "reference": "UTIL-OCT",
        "created_at": "2026-11-07T08:00:00Z",
        "updated_at": "2026-11-07T08:03:00Z",
        "sla_minutes": 240,
    },
]


def balances(account_id="acc_main"):
    return _BALANCES.get(account_id, _BALANCES["acc_main"])


def transfers(status=None):
    items = list(_TRANSFERS)
    if status:
        items = [t for t in items if t["status"] == status]
    return items


def transfer_by_id(tid):
    for t in _TRANSFERS:
        if t["id"] == tid:
            return t
    return None


def scenario_now():
    """A 'now' shortly after the latest fixture transfer, so delayed SLA fires
    on the genuinely-stuck transfer but not on the fresh duplicate."""
    latest = max(datetime.datetime.strptime(t["updated_at"].rstrip("Z"),
                                            "%Y-%m-%dT%H:%M:%S") for t in _TRANSFERS)
    return latest + datetime.timedelta(hours=1)


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sim_create_transfer(payload, reason=""):
    return {
        "id": "sim_" + str(abs(hash(json.dumps(payload, sort_keys=True))) % 10**8),
        "status": "pending",
        "simulated": True,
        "offline_reason": reason,
        "request": payload,
        "created_at": _now(),
    }


def sim_create_refund(payload, reason=""):
    return {
        "id": "sim_rf_" + str(abs(hash(json.dumps(payload, sort_keys=True))) % 10**8),
        "status": "pending",
        "simulated": True,
        "offline_reason": reason,
        "request": payload,
        "created_at": _now(),
    }
