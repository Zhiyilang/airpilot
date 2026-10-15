# AirPilot — Demo Video Script (Dubai entry)
**Target length: 3:00** · Language: English · Format: screen recording + voiceover

---

## 0:00–0:25 — Hook (the expensive mistake)
**[Screen: a payment-ops spreadsheet; highlight two identical rows]**

> "These two rows are the same supplier invoice, paid twice — a month apart.
> It happens in every company that runs payments on spreadsheets. By the time
> finance spots it in reconciliation, the money is usually gone. Last year this
> class of mistake cost businesses billions. We built an agent that makes it
> structurally impossible."

## 0:25–0:55 — The agent at work
**[Screen: terminal — `python -m airpilot demo`]**

> "AirPilot is a payment-operations incident commander. It watches your
> outgoing transfers around the clock, detects incidents — a transfer stuck
> past its SLA, a duplicate-payment risk, a balance that can't cover the
> payment — and resolves them."

## 0:55–1:35 — The verifier gate (the heart of the demo)
**[Screen: JSON receipt scrolling; highlight the two incidents and their verdicts]**

> "Here's the scenario. Two incidents. A delayed supplier transfer to Acme
> Supplies — the agent proposes a safe retry, the verifier checks it against
> five rules — no duplicate, balance covers it, action is scoped, remedy is
> allowlisted, and it isn't paying itself — and it goes through. Acted.
> And a duplicate-payment risk on Globex Logistics. The agent could propose a
> retry here too. Instead the verifier blocks it: **held, no money moved.**
> The agent proposes. The verifier decides what ships."

## 1:35–2:05 — Audit trail + engineering proof
**[Screen: open the generated HTML receipt; then terminal — `python eval.py` → "15 passed / 0 failed"]**

> "Every decision lands in a receipt — the transfer, the amount, the rule that
> decided. This is what a finance auditor actually asks for. Fifteen automated
> assertions prove the detectors and the never-double-pay guarantee. Zero
> third-party dependencies — it runs anywhere and audits cleanly."

## 2:05–2:40 — Business impact close
**[Screen: split — incident list on the left, receipt on the right]**

> "For a business, this is loss prevention that never sleeps: duplicates
> blocked at the gate instead of discovered in reconciliation, suppliers paid
> inside SLA, and an audit trail for every action. That's why we entered the
> Best Business AI Agent category."

## 2:40–3:00 — End card
**[Screen: repo URL + "AirPilot proposes. The verifier decides what ships."]**

> "AirPilot. The agent proposes. The verifier decides what ships."

---

## Production notes
- Record at 1080p; keep the JSON receipt and HTML receipt on screen long enough to read (judges screenshot).
- The money shot is the duplicate being **BLOCKED (held, no money moved)** — pause on it.
- Voiceover: calm, measured. No music over speech.
- Upload unlisted to YouTube; title: "AirPilot — Payment Ops Incident Commander (Create AI Agents Championship, Best Business AI Agent)".
