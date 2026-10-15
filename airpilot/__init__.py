"""AirPilot — Airwallex-native Payment Ops Incident Commander.

Proposes remedies to payment incidents (delayed transfers, duplicate-payment
risk, insufficient balances); a deterministic verifier decides what moves money.
Never double-pays.
"""
from .client import AirwallexClient
from .agent import command
from . import incidents, verifier, receipts

__all__ = ["AirwallexClient", "command", "incidents", "verifier", "receipts"]
__version__ = "0.1.0"
