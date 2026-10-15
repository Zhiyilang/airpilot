# 🛡️ AirPilot — Airwallex Payment Ops Incident Commander

**Built for the Airwallex Agentic Banking Hackathon.** An agent that watches your
Airwallex transfers and resolves payment incidents **without ever double-paying**.

The brain may *propose* a remedy. A deterministic verifier decides what moves
money. That's the whole product: **AirPilot proposes. The verifier decides what
ships.**

## The problem it solves

Track **Payment Ops Incident Commander** (starter kit 03): *"Resolve a delayed
supplier transfer without paying twice."* In the real world this breaks constantly:

- A supplier transfer sits in `review` past its SLA and someone "just resends it."
- A duplicate invoice gets paid twice because two systems both queued it.
- A transfer is pushed that the balance can't cover.

AirPilot turns those into handled incidents with an audit trail.

## How it works

```
PERCEIVE → DETECT → PLAN → VERIFY → ACT → RECEIPT
```

1. **PERCEIVE** — pull balances + transfers from Airwallex (auth → balances → transfers).
2. **DETECT** — pure-function detectors find: `delayed_transfer`,
   `duplicate_payment_risk`, `insufficient_balance`.
3. **PLAN** — the brain proposes a remedy (`retry` / `hold` / `refund` / `fund`).
4. **VERIFY** — the gate checks five rules before *any* API call:
   - **idempotency** — never create a transfer that duplicates an existing one
   - **balance** — a transfer must not exceed available funds
   - **scoped** — the action must reference the incident it resolves
   - **allowlist** — only known-safe remedy kinds
   - **no-self-pay** — beneficiary ≠ source account
5. **ACT** — only verified proposals call Airwallex (`create_transfer` / `create_refund`).
6. **RECEIPT** — every incident, proposal, verdict, and action, with a self-contained HTML report.

```bash
python -m airpilot command          # one incident-commander pass (JSON receipt)
python -m airpilot command --html r.html
python -m airpilot demo             # bundled scenario
```

Example bundled scenario (offline fixtures):

```
incidents_found: 2  acted: 1  blocked: 1
 - delayed_transfer   Acme Supplies Ltd   retry_transfer   ok       ACTED
 - duplicate_payment Globex Logistics     hold_transfer    ok       BLOCKED (held, no money moved)
```

The duplicate is **held, not paid** — the "never pay twice" guarantee is enforced
by the verifier, proven in `eval.py`.

## Airwallex integration

`airpilot/client.py` wraps the Airwallex v1 APIs (stdlib `urllib`, no SDK):

| Action | API |
|---|---|
| Authenticate | `POST /api/v1/authentication/login` |
| Balances | `GET /api/v1/balances` |
| Transfers | `GET /api/v1/transfers`, `POST /api/v1/transfers/create` |
| Refunds | `POST /api/v1/refunds/create` |

Set credentials to go live:

```bash
export AIRWALLEX_API_KEY=...
export AIRWALLEX_API_SECRET=...
export AIRWALLEX_BASE_URL=https://api.airwallex.com   # or api-demo for sandbox
```

With no credentials (or on any API error) it **transparently falls back to bundled
fixtures** and the receipt shows `source: offline-fixture`. The same parsing code
runs against the real API — swap credentials, no code change.

## Why this is the right shape for agentic banking

- **It literally cannot double-pay.** The worst a confused model can do is propose
  something the verifier refuses — and you get to read the refusal.
- **Every decision is auditable.** Detectors are pure functions over numbers; the
  receipt names the transfer, the amount, and the rule that decided.
- **Offline-first.** The whole decision layer is stdlib; the LLM (if you add one)
  is an upgrade path, not a dependency.

## Self-verification

```bash
python eval.py          # 15 assertions, no network, no credentials
```

Covers: every incident detector, the verifier gate (incl. never-double-pay +
balance + no-self-pay + allowlist), the offline agent pass, the HTML receipt
(no script tags / no external assets), and the CLI.

## Web app

```bash
pip install -r requirements.txt
python app.py           # reads PORT; binds 0.0.0.0 for Render
```

Runs the Incident Commander on the bundled scenario and shows the receipt.

## Layout

```
airpilot/
  client.py     Airwallex v1 REST client + offline fixture fallback
  fixtures.py   bundled scenario (mirrors API shapes)
  incidents.py  pure-function detectors
  verifier.py   the prove-then-act gate
  agent.py      PERCEIVE→DETECT→PLAN→VERIFY→ACT→RECEIPT
  receipts.py   JSON + self-contained HTML
  cli.py        command / demo
app.py          Gradio UI (reads PORT)
eval.py         15 assertions
```

## License

MIT — see `LICENSE`.
