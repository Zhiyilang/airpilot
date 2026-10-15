"""AirPilot self-verification: 30+ assertions, no network, no credentials.

Run:  python eval.py
Covers: incident detectors, the prove-then-act verifier gate (incl. the
never-double-pay and balance rules), the offline agent pass, the HTML receipt
(no external assets / no script tags), and the CLI.
"""
from __future__ import annotations

import datetime
import io
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from airpilot.client import AirwallexClient  # noqa: E402
from airpilot import incidents as INC  # noqa: E402
from airpilot import verifier as VER  # noqa: E402
from airpilot import agent as AGT  # noqa: E402
from airpilot import receipts as RC  # noqa: E402
from airpilot.cli import _run as cli_run  # noqa: E402


class Detectors(unittest.TestCase):
    def setUp(self):
        self.client = AirwallexClient()
        self.client.offline = True
        self.bal = self.client.get_balances()
        self.tr = self.client.list_transfers()
        # freeze "now" so the delayed transfer is past SLA
        self.now = datetime.datetime(2026, 11, 11, 0, 0, 0)

    def test_delayed_detected(self):
        d = INC.detect_delayed(self.tr, now=self.now)
        self.assertTrue(any(i["transfer_id"] == "t_supplier_delayed" for i in d))

    def test_duplicate_detected(self):
        d = INC.detect_duplicate(self.tr)
        self.assertTrue(any(i["type"] == "duplicate_payment_risk" for i in d))

    def test_insufficient_not_false_positive(self):
        # available USD 4200 > all pending, so no insufficient incident
        d = INC.detect_insufficient(self.tr, self.bal)
        self.assertEqual(d, [])

    def test_detect_all_counts(self):
        alli = INC.detect_all(self.tr, self.bal, now=self.now)
        self.assertGreaterEqual(len(alli), 2)


class Verifier(unittest.TestCase):
    def setUp(self):
        self.client = AirwallexClient()
        self.client.offline = True
        self.tr = self.client.list_transfers()
        self.bal = self.client.get_balances()
        self.ctx = {"transfers": self.tr, "balances": self.bal, "account_id": "acc_main"}

    def test_retry_passing(self):
        ok, r = VER.verify({"remedy": "retry_transfer", "transfer_id": "t_supplier_delayed"}, self.ctx)
        self.assertTrue(ok, r)

    def test_retry_blocked_on_duplicate(self):
        # t_dup_b has an identical completed sibling -> must be blocked (never double-pay)
        ok, r = VER.verify({"remedy": "retry_transfer", "transfer_id": "t_dup_b"}, self.ctx)
        self.assertFalse(ok)
        self.assertIn("double-pay", r)

    def test_hold_always_safe(self):
        ok, r = VER.verify({"remedy": "hold_transfer", "transfer_id": "t_dup_b"}, self.ctx)
        self.assertTrue(ok)

    def test_unknown_remedy_rejected(self):
        ok, r = VER.verify({"remedy": "launch_nukes", "transfer_id": "x"}, self.ctx)
        self.assertFalse(ok)

    def test_no_self_pay(self):
        ctx = dict(self.ctx)
        ctx["account_id"] = "ACME-8821"
        t = next(t for t in self.tr if t["id"] == "t_supplier_delayed")
        t = dict(t); t["beneficiary_account"] = "ACME-8821"
        ctx["transfers"] = [t if x["id"] == t["id"] else x for x in self.tr]
        ok, r = VER.verify({"remedy": "retry_transfer", "transfer_id": t["id"]}, ctx)
        self.assertFalse(ok)
        self.assertIn("no-self-pay", r)


class AgentOffline(unittest.TestCase):
    def setUp(self):
        self.client = AirwallexClient()
        self.client.offline = True

    def test_command_runs_offline(self):
        rc = AGT.command(self.client, now=datetime.datetime(2026, 11, 11, 0, 0, 0))
        self.assertEqual(rc["source"], "offline-fixture")
        self.assertGreaterEqual(rc["incidents_found"], 2)
        # the duplicate is resolved by a SAFE HOLD (no money moves, never double-pays)
        dup = [a for a in rc["actions"]
               if a["incident"]["type"] == "duplicate_payment_risk"][0]
        self.assertTrue(dup["verified"])
        self.assertFalse(dup["acted"])
        # the delayed one may be acted (retry passes the gate)
        delayed = [a for a in rc["actions"]
                   if a["incident"]["type"] == "delayed_transfer"][0]
        self.assertTrue(delayed["verified"])

    def test_no_money_moves_on_blocked(self):
        rc = AGT.command(self.client, now=datetime.datetime(2026, 11, 11, 0, 0, 0))
        for a in rc["actions"]:
            if not a["verified"]:
                self.assertFalse(a["acted"])


class Receipts(unittest.TestCase):
    def test_html_self_contained(self):
        client = AirwallexClient(); client.offline = True
        rc = AGT.command(client, now=datetime.datetime(2026, 11, 11, 0, 0, 0))
        h = RC.to_html(rc)
        self.assertNotIn("<script", h)
        self.assertNotIn("http://", h)
        self.assertNotIn("https://", h)
        self.assertIn("AirPilot", h)

    def test_json_roundtrip(self):
        client = AirwallexClient(); client.offline = True
        rc = AGT.command(client, now=datetime.datetime(2026, 11, 11, 0, 0, 0))
        s = json.dumps(rc, ensure_ascii=False)
        self.assertEqual(json.loads(s)["product"], "AirPilot")


class CLI(unittest.TestCase):
    def test_cli_command_exits_0(self):
        out = io.StringIO()
        old = sys.stdout; sys.stdout = out
        try:
            rc = cli_run()
        finally:
            sys.stdout = old
        self.assertIn("AirPilot", json.dumps(rc, ensure_ascii=False))
        # the bundled demo scenario must show BOTH incidents (delayed + duplicate)
        self.assertGreaterEqual(rc["incidents_found"], 2)

    def test_cli_html_written(self):
        path = os.path.join(HERE, "_eval_test_receipt.html")
        cli_run(html_out=path)
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8") as f:
            self.assertIn("AirPilot", f.read())
        os.remove(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
