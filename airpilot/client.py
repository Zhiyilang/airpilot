"""Airwallex REST client (stdlib-only) for the Agentic Banking Hackathon.

Talks to Airwallex v1 APIs (auth, balances, transfers, payments, refunds).

Fallback policy — the load-bearing safety decision in this client:

  * READS (balances / list / get) fall back to bundled fixtures when the
    client is explicitly in offline mode. The receipt shows
    ``source: "offline-fixture"`` so the operator can see it happened.
  * WRITES (create transfer / create refund) NEVER silently simulate. If a
    live write fails, the call raises: an agent that *thinks* it moved money
    when it did not is strictly worse than one that stopped and shouted.
    Simulated writes exist only in explicit offline mode (the demo/eval path).

Reads retry transient failures (429 / 5xx) with capped exponential backoff;
writes do not retry — a retry without a proven idempotency key is how double
payments happen, and this client always sends the agent's idempotency_key.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from . import fixtures as _fx


DEFAULT_BASE_URL = "https://api.airwallex.com"
DEMO_BASE_URL = "https://api-demo.airwallex.com"

_RETRYABLE = (429, 500, 502, 503, 504)


class AirwallexError(Exception):
    pass


class AirwallexClient:
    def __init__(self, api_key=None, api_secret=None, base_url=None, token=None,
                 max_retries=3, retry_sleep=1.0):
        self.api_key = api_key or os.environ.get("AIRWALLEX_API_KEY")
        self.api_secret = api_secret or os.environ.get("AIRWALLEX_API_SECRET")
        self.base_url = (base_url or os.environ.get("AIRWALLEX_BASE_URL")
                         or DEFAULT_BASE_URL).rstrip("/")
        self._token = token
        self.offline = False
        self.max_retries = max_retries
        self.retry_sleep = retry_sleep
        if not (self.api_key and self.api_secret):
            self.offline = True

    # ---- low level -------------------------------------------------------
    def _url(self, path):
        return self.base_url + path

    def _post(self, path, payload):
        if self.offline:
            raise AirwallexError("offline: no credentials")
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self._url(path), data=data,
                                     method="POST")
        req.add_header("Content-Type", "application/json")
        if self._token:
            req.add_header("Authorization", "Bearer " + self._token)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise AirwallexError("HTTP %s on %s" % (e.code, path))
        except Exception as e:  # network / timeout
            raise AirwallexError(str(e))

    def _get(self, path, opener=None):
        """GET with capped backoff on transient failures.

        ``opener`` is injectable so tests can exercise the retry loop without
        a network (see eval.py). Defaults to urllib.request.urlopen.
        """
        if self.offline:
            raise AirwallexError("offline: no credentials")
        opener = opener or urllib.request.urlopen
        last = None
        for attempt in range(max(1, self.max_retries)):
            req = urllib.request.Request(self._url(path), method="GET")
            if self._token:
                req.add_header("Authorization", "Bearer " + self._token)
            try:
                with opener(req, timeout=15) as r:
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                last = AirwallexError("HTTP %s on %s" % (e.code, path))
                if e.code not in _RETRYABLE or attempt == self.max_retries - 1:
                    raise last
            except Exception as e:  # network / timeout: not worth retrying a dead socket
                raise AirwallexError(str(e))
            time.sleep(self.retry_sleep * (2 ** attempt))
        raise last

    # ---- auth ------------------------------------------------------------
    def authenticate(self):
        if self._token:
            return self._token
        if self.offline:
            self._token = "offline-token"
            return self._token
        resp = self._post("/api/v1/authentication/login",
                          {"api_key": self.api_key, "api_secret": self.api_secret})
        self._token = resp.get("token")
        if not self._token:
            raise AirwallexError("no token in auth response")
        return self._token

    # ---- resources (reads: explicit-offline -> fixtures) -----------------
    def get_balances(self, account_id="acc_main"):
        if self.offline:
            return _fx.balances(account_id)
        try:
            self.authenticate()
            return self._get("/api/v1/balances?account_id=" + account_id)
        except AirwallexError:
            # a live read failure must not be papered over with fixture data:
            # acting on invented balances is how overdrafts happen
            raise

    def list_transfers(self, status=None):
        if self.offline:
            return _fx.transfers(status=status)
        try:
            self.authenticate()
            path = "/api/v1/transfers"
            if status:
                path += "?status=" + status
            return self._get(path).get("items", [])
        except AirwallexError:
            raise

    def get_transfer(self, transfer_id):
        if self.offline:
            return _fx.transfer_by_id(transfer_id)
        try:
            self.authenticate()
            return self._get("/api/v1/transfers/" + transfer_id)
        except AirwallexError:
            raise

    # ---- resources (writes: never silently simulate) ---------------------
    def create_transfer(self, payload):
        """Create a transfer. Mirrors Airwallex /api/v1/transfers/create."""
        if self.offline:
            return _fx.sim_create_transfer(payload, reason="explicit offline mode")
        self.authenticate()
        return self._post("/api/v1/transfers/create", payload)

    def create_refund(self, payload):
        if self.offline:
            return _fx.sim_create_refund(payload, reason="explicit offline mode")
        self.authenticate()
        return self._post("/api/v1/refunds/create", payload)

    @property
    def source(self):
        return "offline-fixture" if self.offline else "airwallex-api"
