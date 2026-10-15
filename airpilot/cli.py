"""AirPilot command-line entry point (stdlib only)."""
from __future__ import annotations

import argparse
import json
import sys

from .client import AirwallexClient
from .agent import command
from . import fixtures as _fx
from . import receipts as _rc


def _run(html_out=None, offline=True):
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
    sub.add_parser("command", help="run one incident-commander pass")
    sub.add_parser("demo", help="run the bundled incident scenario")
    args = p.parse_args(argv)
    if args.cmd in (None, "command", "demo"):
        _run()
        return 0
    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
