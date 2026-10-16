"""AirPilot command-line entry point (stdlib only)."""
from __future__ import annotations

import argparse
import json
import os
import sys

from .client import AirwallexClient
from .agent import command
from .ledger import IdempotencyLedger
from . import fixtures as _fx
from . import receipts as _rc


def _run(html_out=None, offline=True, ledger_path=None):
    client = AirwallexClient()
    if offline:
        client.offline = True  # deterministic fixtures for CLI/demo
        rc = command(client, now=_fx.scenario_now())
    else:
        rc = command(client)
    if html_out:
        with open(html_out, "w", encoding="utf-8") as f:
            f.write(_rc.to_html(rc))
        print("wrote %s" % html_out)
    else:
        print(json.dumps(rc, indent=2, ensure_ascii=False))
    return rc


def main(argv=None):
    p = argparse.ArgumentParser(prog="airpilot", description="Payment Ops Incident Commander")
    sub = p.add_subparsers(dest="cmd")
    run_p = sub.add_parser("command", help="run one incident-commander pass")
    run_p.add_argument("--ledger", metavar="PATH", default=None,
                       help="idempotency ledger file (crash-safe never-double-pay); "
                            "defaults to $AIRPILOT_LEDGER if set")
    run_p.add_argument("--html", metavar="PATH", default=None,
                       help="also write the HTML receipt to PATH")
    sub.add_parser("demo", help="run the bundled incident scenario")
    args = p.parse_args(argv)
    if args.cmd in (None, "command", "demo"):
        if args.cmd == "command":
            ledger = IdempotencyLedger(path=args.ledger)
            client = AirwallexClient()
            rc = command(client, ledger=ledger)
            if args.html:
                with open(args.html, "w", encoding="utf-8") as f:
                    f.write(_rc.to_html(rc))
                print("wrote %s" % args.html)
            else:
                print(json.dumps(rc, indent=2, ensure_ascii=False))
            return 0
        _run()
        return 0
    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
