# AirPilot — Pitch Deck Outline
### Create AI Agents Championship · Dubai Chamber of Digital Economy
**Category: Best Business AI Agent** · Prepared October 2026 · All-English entry

> Prize: AED 550,000 per category winner + AED 1,000,000 "AI Agent of the Year".
> Registration closes December 2026 · one registration allows multiple entries.

---

## Slide 1 — Title
**AirPilot — the Payment Ops Incident Commander**
- An autonomous agent that watches your outgoing payments, detects incidents (delayed transfers, duplicate-payment risk, insufficient balance), and resolves them — **with a deterministic guarantee that it never pays twice**.
- Tagline: *"AirPilot proposes. The verifier decides what ships."*

## Slide 2 — The business problem
- Small and mid-sized companies run payment operations on email, spreadsheets and good intentions.
- The failure modes are expensive and routine:
  - a supplier transfer sits in `review` past its SLA — someone "just resends it" and the supplier is paid twice;
  - two systems queue the same invoice — duplicate payment discovered weeks later, often unrecoverable;
  - a transfer is pushed the balance can't cover — returned, penalised, relationship damaged.
- Cross-border supplier payments — the norm for a trade hub like Dubai — multiply the delay/duplicate surface.

## Slide 3 — Why existing tools don't fix it
- Banking dashboards show you the mess; they don't resolve it.
- Generic AI chat assistants will happily *suggest* resending a payment — with no guardrail and no audit trail.
- What finance teams need is not another dashboard: it's an **agent that acts, under rules that cannot be talked out of the rules**.

## Slide 4 — Meet AirPilot
- Watches balances + transfers from the company's payment API (Airwallex v1, stdlib client).
- Detects three incident classes with pure-function detectors.
- Proposes a remedy (`retry` / `hold` / `refund` / `fund`).
- **A deterministic verifier gate checks five rules before any money moves**: idempotency (never duplicate an existing transfer), balance (never exceed available funds), scoped action, allowlisted remedy kinds, no self-payment.
- Only verified proposals reach the API. Everything lands in an auditable receipt.

## Slide 5 — Live demo (the bundled scenario)
```
incidents_found: 2   acted: 1   blocked: 1
 - delayed_transfer    Acme Supplies Ltd    retry_transfer   ok    ACTED
 - duplicate_payment   Globex Logistics     hold_transfer    ok    BLOCKED (held, no money moved)
```
- The delayed supplier transfer is safely retried inside the verifier's rules.
- The duplicate is **held, not paid** — the "never pay twice" guarantee is enforced by code, asserted in `eval.py`.

## Slide 6 — The agent loop
PERCEIVE (pull balances + transfers) → DETECT (pure-function incident detectors) → PLAN (remedy proposal) → VERIFY (five-rule gate) → ACT (only verified proposals call the API) → RECEIPT (JSON + self-contained HTML audit report naming transfer, amount, and deciding rule).

## Slide 7 — Why this is the right shape for agentic business ops
- **It literally cannot double-pay.** The worst a confused model can do is propose something the verifier refuses — and you get to read the refusal.
- **Every decision is auditable.** Detectors are pure functions over numbers; the receipt names the transfer, the amount, and the rule that decided.
- **Offline-first, zero dependencies.** Pure Python standard library; the LLM is an upgrade path, not a dependency. Runs anywhere, audits cleanly.

## Slide 8 — Business impact (category mapping)
- **Workflow automation**: payment incidents resolved 24/7 without headcount.
- **Decision quality**: every action carries evidence and the rule that authorised it — finance controls love it.
- **Loss prevention**: duplicate payments and overdrafts are prevented at the gate, not discovered in reconciliation.
- **Service quality**: suppliers get paid inside SLA; relationships stop eroding over "lost" transfers.

## Slide 9 — Engineering proof
- **15/15 automated assertions** covering every detector, the verifier gate (never-double-pay, balance, no-self-pay, allowlist), the offline agent pass, HTML receipt safety (no script tags / external assets), and the CLI.
- CI on three Python versions; MIT-licensed public repository; web UI reads `PORT` for one-click cloud deploy.

## Slide 10 — Roadmap (what the grant funds)
- Phase 1: multi-currency + multi-account policies; approval thresholds for amounts above X; Slack/email escalation channel.
- Phase 2: reconciliation-agent pairing (match payments to invoices automatically); anomaly scoring over payment history.
- Phase 3: measured pilot with a Dubai SME — duplicate-payments avoided and SLA compliance, published openly.

## Slide 11 — Path to scale (pre-commercial today)
- Deploy per-company (self-hosted or cloud), priced per monitored account; channel via accounting firms and payment providers.
- **Eligibility note**: AirPilot is an open-source, pre-commercial prototype — it does not compete as a commercialised solution.

## Slide 12 — Team & the ask
- Solo founder (21, Shanghai): automation/AI-agent engineer; shipped 10+ open-source agent projects with assertion-tested quality bars.
- The ask: **AED 550,000 Best Business AI Agent grant** to harden the agent into a production payment-ops service and run a measured Dubai pilot.

---

## Judge Q&A prep
- *"Isn't an agent moving money dangerous?"* — That's the point: the agent only *proposes*. A deterministic verifier with five hard rules decides what ships, and the refusal is part of the receipt.
- *"Why not just use RPA?"* — RPA replays fixed clicks; this agent perceives state, detects incident classes, and acts under verifiable rules — with an audit trail per action.
- *"Does it need the Airwallex key to demo?"* — No. The same parsing code runs against bundled fixtures; swap credentials to go live, no code change.
- *"Measured impact?"* — Detection and gate behaviour are assertion-tested; pilot outcome metrics (duplicates avoided, SLA compliance) are Phase-3 deliverables funded by the grant.
