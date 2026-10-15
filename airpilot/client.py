"""Airwallex REST client (stdlib-only) for the Agentic Banking Hackathon.

Talks to Airwallex v1 APIs (auth, balances, transfers, payments, refunds).
When credentials are absent or a request fails, it transparently falls back to
bundled fixtures so the agent is fully exercisable offline (eval never needs a
live key). The fallback is visible in the receipt as ``source: "offline-fixture"``.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error

from . import fixtures as _fx


DEFAULT_BASE_URL = "https://api.airwallex.com"
DEMO_BASE_URL = "https://api-demo.airwallex.com"


class AirwallexError(Exception):
    pass


class AirwallexClient:
    def __init__(self, api_key=None, api_secret=None, base_url=None, token=None):
        self.api_key = api_key or os.environ.get("AIRWALLEX_API_KEY")
        self.api_secret = api_secret or os.environ.get("AIRWALLEX_API_SECRET")
        self.base_url = (base_url or os.environ.get("AIRWALLEX_BASE_URL")
                         or DEFAULT_BASE_URL).rstrip("/")
        self._token = token
        self.offline = False
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

    def _get(self, path):
        if self.offline:
            raise AirwallexError("offline: no credentials")
        req = urllib.request.Request(self._url(path), method="GET")
        if self._token:
            req.add_header("Authorization", "Bearer " + self._token)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise AirwallexError("HTTP %s on %s" % (e.code, path))
        except Exception as e:
            raise AirwallexError(str(e))

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

    # ---- resources -------------------------------------------------------
    def get_balances(self, account_id="acc_main"):
        try:
            self.authenticate()
            return self._get("/api/v1/balances?account_id=" + account_id)
        except AirwallexError:
            self.offline = True
            return _fx.balances(account_id)

    def list_transfers(self, status=None):
        try:
            self.authenticate()
            path = "/api/v1/transfers"
            if status:
                path += "?status=" + status
            return self._get(path).get("items", [])
        except AirwallexError:
            self.offline = True
            return _fx.transfers(status=status)

    def get_transfer(self, transfer_id):
        try:
            self.authenticate()
            return self._get("/api/v1/transfers/" + transfer_id)
        except AirwallexError:
            self.offline = True
            return _fx.transfer_by_id(transfer_id)

    def create_transfer(self, payload):
        """Create a transfer. Mirrors Airwallex /api/v1/transfers/create."""
        try:
            self.authenticate()
            return self._post("/api/v1/transfers/create", payload)
        except AirwallexError as e:
            # offline simulation: stamp an id + accepted status
            self.offline = True
            return _fx.sim_create_transfer(payload, reason=str(e))

    def create_refund(self, payload):
        try:
            self.authenticate()
            return self._post("/api/v1/refunds/create", payload)
        except AirwallexError as e:
            self.offline = True
            return _fx.sim_create_refund(payload, reason=str(e))

    @property
    def source(self):
        return "offline-fixture" if self.offline else "airwallex-api"
