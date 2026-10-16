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
2. **DETECT** — pure-function detectors find five incident types:
   `delayed_transfer`, `duplicate_payment_risk`, `insufficient_balance`, plus the
   two adversarial patterns that beat a naive duplicate check:
   `beneficiary_account_changed` (reference reuse + account swap = takeover) and
   `rapid_repeat_payment` (reference-dodged duplicate).
3. **PLAN** — the brain proposes a remedy (`retry` / `hold` / `refund` / `fund` / `escalate`).
4. **VERIFY** — the gate checks eight rules before *any* API call:
   - **idempotency** — never create a transfer that duplicates an existing one
   - **ledger** — never repeat an action this agent already executed, even after a crash
   - **balance** — a transfer must not exceed available funds
   - **scoped** — the action must reference the incident it resolves
   - **allowlist** — only known-safe remedy kinds
   - **no-self-pay** — beneficiary ≠ source account
   - **account-change** — a retry whose reference was previously paid to a different account is blocked
   - **rapid-repeat** — a retry inside a same-beneficiary/different-reference burst is blocked
5. **ACT** — only verified proposals call Airwallex (`create_transfer` / `create_refund`).
6. **RECEIPT** — every incident, proposal, verdict, and action, with a self-contained HTML report.

```bash
python -m airpilot command                    # one pass (JSON receipt)
python -m airpilot command --ledger led.jsonl # crash-safe never-double-pay
python -m airpilot command --html r.html
python -m airpilot demo                       # bundled scenario
```

Example bundled scenario (offline fixtures) — five incident types, one pass:

```
incidents_found: 4  acted: 1  blocked: 3
 - delayed_transfer              Acme Supplies Ltd   retry_transfer   ok   ACTED
 - duplicate_payment_risk        Globex Logistics    hold_transfer    ok   BLOCKED (held)
 - beneficiary_account_changed   Initech Corp        escalate         ok   BLOCKED (takeover)
 - rapid_repeat_payment          Stark Retail        escalate         ok   BLOCKED (dodged dup)
```

Only one transfer moved money. The duplicate is **held, not paid**; the two
attacks are **escalated, not paid**. The "never pay twice" guarantee is enforced
by the verifier, and — with `--ledger` — survives process restarts. Both are
proven in `eval.py` (40 assertions).

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

With no credentials it runs in explicit offline mode: **reads** come from bundled
fixtures and the receipt shows `source: offline-fixture`. The same parsing code
runs against the real API — swap credentials, no code change.

**Writes never silently simulate.** If a live `create_transfer` fails, the call
raises instead of pretending the money moved — an agent that *thinks* it paid
when it did not is strictly worse than one that stopped and shouted. (Friction
found and fixed while building this; see `FRICTION_LOG.md`.)

## Why this is the right shape for agentic banking

- **It literally cannot double-pay.** The worst a confused model can do is propose
  something the verifier refuses — and you get to read the refusal.
- **The guarantee survives crashes.** The idempotency ledger (`airpilot/ledger.py`)
  fingerprints every money-moving intent and persists it, so a restart after a
  half-finished action is blocked, not repeated.
- **It is adversarial by default.** The bundled fixtures include the two attacks
  that slip through the obvious duplicate check (account swap, reference dodge) —
  see `examples/adversarial_scenario.md`.
- **Every decision is auditable.** Detectors are pure functions over numbers; the
  receipt names the transfer, the amount, and the rule that decided.
- **Offline-first.** The whole decision layer is stdlib; the LLM (if you add one)
  is an upgrade path, not a dependency.

## Self-verification

```bash
python eval.py          # 40 assertions, no network, no credentials
```

Covers: all five incident detectors (incl. the adversarial pair), the verifier
gate (never-double-pay + balance + no-self-pay + allowlist + account-change +
rapid-repeat), the idempotency ledger (memory + file persistence + corrupt-line
tolerance + replay blocking), client write-safety (live writes never simulate;
reads retry transient 429/5xx), the offline agent pass, the HTML receipt (no
script tags / no external assets), and the CLI.

## Web app

```bash
pip install -r requirements.txt
python app.py           # reads PORT; binds 0.0.0.0 for Render
```

Runs the Incident Commander on the bundled scenario and shows the receipt.

## Layout

```
airpilot/
  client.py     Airwallex v1 REST client (reads retry; writes never simulate)
  fixtures.py   bundled scenario (mirrors API shapes)
  incidents.py  pure-function detectors (5 types incl. 2 adversarial)
  verifier.py   the prove-then-act gate (8 rules)
  ledger.py     crash-safe idempotency ledger
  agent.py      PERCEIVE→DETECT→PLAN→VERIFY→ACT→RECEIPT
  receipts.py   JSON + self-contained HTML
  cli.py        command / demo (--ledger)
app.py          Gradio UI (reads PORT)
eval.py         40 assertions
examples/       bundled scenario + adversarial_scenario.md (the two attacks)
```

## License

MIT — see `LICENSE`.
