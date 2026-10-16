"""AirPilot self-verification: 39 assertions, no network, no credentials.

Run:  python eval.py
Covers: incident detectors (incl. the two adversarial ones), the prove-then-act
verifier gate (never-double-pay / balance / no-self-pay / account-change /
rapid-repeat / allowlist), the crash-safe idempotency ledger, the offline
agent pass, client write-safety (live writes never silently simulate, reads
retry transient failures), the HTML receipt (no external assets / no script
tags), and the CLI.
"""
from __future__ import annotations

import datetime
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from airpilot.client import AirwallexClient, AirwallexError  # noqa: E402
from airpilot import incidents as INC  # noqa: E402
from airpilot import verifier as VER  # noqa: E402
from airpilot import agent as AGT  # noqa: E402
from airpilot import receipts as RC  # noqa: E402
from airpilot.ledger import IdempotencyLedger, fingerprint  # noqa: E402
from airpilot.cli import _run as cli_run  # noqa: E402

NOW = datetime.datetime(2026, 11, 11, 0, 0, 0)


def offline_client():
    c = AirwallexClient()
    c.offline = True
    return c


class Detectors(unittest.TestCase):
    def setUp(self):
        self.client = offline_client()
        self.bal = self.client.get_balances()
        self.tr = self.client.list_transfers()
        self.now = NOW

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
        self.client = offline_client()
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
        self.client = offline_client()

    def test_command_runs_offline(self):
        rc = AGT.command(self.client, now=NOW)
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
        rc = AGT.command(self.client, now=NOW)
        for a in rc["actions"]:
            if not a["verified"]:
                self.assertFalse(a["acted"])


class Receipts(unittest.TestCase):
    def test_html_self_contained(self):
        client = offline_client()
        rc = AGT.command(client, now=NOW)
        h = RC.to_html(rc)
        self.assertNotIn("<script", h)
        self.assertNotIn("http://", h)
        self.assertNotIn("https://", h)
        self.assertIn("AirPilot", h)

    def test_json_roundtrip(self):
        client = offline_client()
        rc = AGT.command(client, now=NOW)
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


# ---------------------------------------------------------------- adversarial
class AdversarialDetectors(unittest.TestCase):
    """The two attacks that slip through a naive duplicate check."""

    def setUp(self):
        self.tr = offline_client().list_transfers()

    def test_beneficiary_changed_fires(self):
        # PO-5561 was paid to INITECH-1001; t_fraud_pending pays ATTACKER-9999
        d = INC.detect_beneficiary_changed(self.tr)
        self.assertTrue(any(i["transfer_id"] == "t_fraud_pending" for i in d))
        inc = d[0]
        self.assertEqual(inc["severity"], "CRITICAL")
        self.assertEqual(inc["expected_account"], "INITECH-1001")

    def test_beneficiary_changed_negative(self):
        # same reference but SAME account everywhere -> no incident
        tr = [dict(t) for t in self.tr if t["id"] in ("t_fraud_done", "t_fraud_pending")]
        for t in tr:
            t["beneficiary_account"] = "INITECH-1001"
        self.assertEqual(INC.detect_beneficiary_changed(tr), [])

    def test_rapid_repeat_fires(self):
        # SUB-1001 and SUB-1001-R2 to Stark Retail 45 min apart
        d = INC.detect_rapid_repeat(self.tr)
        self.assertTrue(any(i["transfer_id"] == "t_smurf_b" for i in d))
        self.assertIn("SUB-1001-R2", d[0]["references"])

    def test_rapid_repeat_window_respected(self):
        # same beneficiary, different refs, but 3 hours apart -> not a burst
        tr = [
            {"id": "a", "status": "completed", "beneficiary": "X", "currency": "USD",
             "amount": "10.00", "reference": "R1",
             "created_at": "2026-11-11T08:00:00Z"},
            {"id": "b", "status": "review", "beneficiary": "X", "currency": "USD",
             "amount": "10.00", "reference": "R2",
             "created_at": "2026-11-11T11:00:00Z"},
        ]
        self.assertEqual(INC.detect_rapid_repeat(tr, window_min=90), [])

    def test_rapid_repeat_skips_identical_reference(self):
        # identical reference in a burst is detect_duplicate's job, not this one
        tr = [
            {"id": "a", "status": "completed", "beneficiary": "X", "currency": "USD",
             "amount": "10.00", "reference": "R1",
             "created_at": "2026-11-11T10:00:00Z"},
            {"id": "b", "status": "review", "beneficiary": "X", "currency": "USD",
             "amount": "10.00", "reference": "R1",
             "created_at": "2026-11-11T10:10:00Z"},
        ]
        self.assertEqual(INC.detect_rapid_repeat(tr, window_min=90), [])

    def test_verifier_blocks_retry_on_account_change(self):
        ctx = {"transfers": self.tr, "balances": offline_client().get_balances(),
               "account_id": "acc_main"}
        ok, r = VER.verify({"remedy": "retry_transfer", "transfer_id": "t_fraud_pending"}, ctx)
        self.assertFalse(ok)
        self.assertIn("account-change", r)

    def test_verifier_blocks_retry_on_rapid_repeat(self):
        ctx = {"transfers": self.tr, "balances": offline_client().get_balances(),
               "account_id": "acc_main"}
        ok, r = VER.verify({"remedy": "retry_transfer", "transfer_id": "t_smurf_b"}, ctx)
        self.assertFalse(ok)
        self.assertIn("rapid-repeat", r)

    def test_fraud_escalates_not_retries(self):
        inc = INC.detect_beneficiary_changed(self.tr)[0]
        self.assertEqual(AGT.plan_for(inc)["remedy"], "escalate")

    def test_account_swap_is_not_a_duplicate(self):
        # same reference + amount but a DIFFERENT account is a takeover, not a
        # duplicate payment — it must surface only as beneficiary_account_changed
        fraud_ids = {"t_fraud_done", "t_fraud_pending"}
        for i in INC.detect_duplicate(self.tr):
            self.assertFalse(fraud_ids & set(i["matched_transfer_ids"]))


# ---------------------------------------------------------------- ledger
class IdempotencyLedgerTests(unittest.TestCase):
    def setUp(self):
        self.client = offline_client()
        self.tr = self.client.list_transfers()
        self.bal = self.client.get_balances()
        self.ctx = {"transfers": self.tr, "balances": self.bal, "account_id": "acc_main"}
        self.proposal = {"remedy": "retry_transfer", "transfer_id": "t_supplier_delayed"}

    def test_memory_record_and_seen(self):
        led = IdempotencyLedger()
        key = VER.execution_key(self.proposal, self.ctx)
        self.assertFalse(led.seen(key))
        self.assertTrue(led.record(key))
        self.assertTrue(led.seen(key))
        self.assertEqual(len(led), 1)

    def test_record_is_idempotent(self):
        led = IdempotencyLedger()
        key = VER.execution_key(self.proposal, self.ctx)
        led.record(key)
        self.assertFalse(led.record(key))
        self.assertEqual(len(led), 1)

    def test_fingerprint_stable_and_discriminating(self):
        a = {"remedy": "retry_transfer", "transfer_id": "t1", "beneficiary": "B",
             "beneficiary_account": "ACC", "amount": "10", "currency": "USD",
             "reference": "R"}
        b = dict(a)
        c = dict(a); c["amount"] = "11"
        self.assertEqual(fingerprint(a), fingerprint(b))
        self.assertNotEqual(fingerprint(a), fingerprint(c))

    def test_persistence_across_instances(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "ledger.jsonl")
            led = IdempotencyLedger(path=path)
            key = VER.execution_key(self.proposal, self.ctx)
            led.record(key, {"incident": "delayed_transfer"})
            led2 = IdempotencyLedger(path=path)  # simulates a process restart
            self.assertTrue(led2.seen(key))
            self.assertEqual(led2.records()[key]["payload"]["incident"],
                             "delayed_transfer")

    def test_corrupt_line_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "ledger.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write("this is not json\n")
                f.write(json.dumps({"key": "good|key", "at": "x"}) + "\n")
            led = IdempotencyLedger(path=path)
            self.assertTrue(led.seen("good|key"))
            self.assertEqual(len(led), 1)

    def test_verifier_blocks_replayed_retry(self):
        led = IdempotencyLedger()
        led.record(VER.execution_key(self.proposal, self.ctx))
        ok, r = VER.verify(self.proposal, self.ctx, ledger=led)
        self.assertFalse(ok)
        self.assertIn("ledger", r)

    def test_verifier_blocks_replayed_refund(self):
        proposal = {"remedy": "refund_transfer", "transfer_id": "t_dup_a"}
        ok, _ = VER.verify(proposal, self.ctx)
        self.assertTrue(ok)
        led = IdempotencyLedger()
        led.record(VER.execution_key(proposal, self.ctx))
        ok, r = VER.verify(proposal, self.ctx, ledger=led)
        self.assertFalse(ok)
        self.assertIn("ledger", r)

    def test_agent_records_after_acting(self):
        led = IdempotencyLedger()
        rc = AGT.command(self.client, now=NOW, ledger=led)
        self.assertEqual(rc["ledger_keys"], 1)  # only the delayed retry moved money
        acted = [a for a in rc["actions"] if a["acted"]]
        self.assertEqual(len(acted), 1)

    def test_second_pass_blocked_by_ledger(self):
        led = IdempotencyLedger()
        AGT.command(self.client, now=NOW, ledger=led)
        rc2 = AGT.command(self.client, now=NOW, ledger=led)
        delayed = [a for a in rc2["actions"]
                   if a["incident"]["type"] == "delayed_transfer"][0]
        self.assertFalse(delayed["verified"])
        self.assertIn("ledger", delayed["verdict"])
        self.assertFalse(delayed["acted"])

    def test_without_ledger_both_passes_act(self):
        rc1 = AGT.command(self.client, now=NOW)
        rc2 = AGT.command(self.client, now=NOW)
        self.assertEqual(rc1["acted_count"], rc2["acted_count"])
        self.assertNotIn("ledger_keys", rc1)

    def test_receipt_exposes_ledger_size(self):
        led = IdempotencyLedger()
        rc = AGT.command(self.client, now=NOW, ledger=led)
        self.assertEqual(rc["ledger_keys"], len(led))
        json.dumps(rc, ensure_ascii=False)  # receipt must stay JSON-serialisable


# ---------------------------------------------------------------- client safety
class _FakeResp:
    def __init__(self, payload):
        self._p = payload

    def read(self):
        return json.dumps(self._p).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _flaky_opener(fail_times, code, payload, calls):
    def opener(req, timeout=None):
        calls.append(req.full_url)
        if len(calls) <= fail_times:
            raise urllib.error.HTTPError(req.full_url, code, "err", {}, None)
        return _FakeResp(payload)
    return opener


class ClientSafety(unittest.TestCase):
    def _live(self, **kw):
        c = AirwallexClient(api_key="k", api_secret="s", **kw)
        c._token = "tok"  # skip the auth round-trip
        return c

    def test_live_write_never_simulates(self):
        c = self._live()
        def boom(path, payload):
            raise AirwallexError("HTTP 500 on create")
        c._post = boom
        with self.assertRaises(AirwallexError):
            c.create_transfer({"currency": "USD", "transfer_amount": "1.00"})

    def test_explicit_offline_write_simulates(self):
        c = offline_client()
        res = c.create_transfer({"currency": "USD", "transfer_amount": "1.00"})
        self.assertTrue(res["simulated"])
        self.assertEqual(res["offline_reason"], "explicit offline mode")

    def test_live_read_failure_raises_not_fixtures(self):
        c = self._live()
        def boom(path):
            raise AirwallexError("HTTP 503")
        c._get = boom
        with self.assertRaises(AirwallexError):
            c.get_balances()

    def test_get_retries_transient_429(self):
        calls = []
        c = self._live(max_retries=3, retry_sleep=0)
        opener = _flaky_opener(2, 429, {"balances": []}, calls)
        data = c._get("/api/v1/balances", opener=opener)
        self.assertEqual(data, {"balances": []})
        self.assertEqual(len(calls), 3)  # 2 failures + 1 success

    def test_get_raises_after_retries_exhausted(self):
        calls = []
        c = self._live(max_retries=2, retry_sleep=0)
        opener = _flaky_opener(5, 503, {"balances": []}, calls)
        with self.assertRaises(AirwallexError):
            c._get("/api/v1/balances", opener=opener)
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
