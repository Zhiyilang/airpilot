# AirPilot — Dubai "Create AI Agents Championship" Entry Checklist
**Category: Best Business AI Agent** · Entry language: English · Prepared 2026-10-15
*(Second entry — the first is ClauseGuard AI in Best Societal AI Agent. The championship allows multiple applications under one registration.)*

---

## 1. Championship facts (verified Oct 2026)

| Item | Detail |
|---|---|
| Competition | Create AI Agents Championship, Dubai Chamber of Digital Economy |
| Prize pool | > AED 2.5M: **AED 550,000 per category winner**; +AED 1,000,000 for AI Agent of the Year |
| Categories | Best Societal / Best Personal / Best Business / Best Youth (**under 21 at registration — not eligible, applicant is 21**) |
| Eligibility | Worldwide; teams up to 6; **multiple entries allowed**; **fully commercialised solutions NOT eligible** |
| Registration | Open; **closes January 2027 (official timeline + FAQ; press reported December — official page wins)** — dubaichamberdigital.com/en/create-ai-agents |
| Deliverables | **Prototype + English pitch deck + English demo video** |
| Grand final | First week of **May 2027** — live demonstration of a **fully working agent** (not an MVP) |

## 2. Category choice: Best Business AI Agent
Official framing: agents that help **public- and private-sector organizations improve workflows, services, decision-making and customer experience**.
AirPilot maps directly: payment-operations workflow automation (resolves incidents 24/7), decision quality (every action carries evidence + the rule that authorised it), loss prevention (duplicates and overdrafts blocked at the gate), service quality (suppliers paid inside SLA).

## 3. Deliverables mapping

| Required deliverable | Status | Source |
|---|---|---|
| AI-agent prototype (public URL) | ✅ built, zero-dependency, offline-capable | https://github.com/Zhiyilang/airpilot — `python -m airpilot demo`; web app reads `PORT` for cloud deploy |
| Pitch deck (English) | ✅ outline ready (12 slides) | `DUBAI_PITCH.md` — convert to slides |
| Demo video (~3 min, English) | ✅ script ready | `DUBAI_DEMO_SCRIPT.md` — record per production notes |
| Repo + licence + tests | ✅ MIT, 15/15 assertions, 3-version CI (green) | README.md |

## 4. Applicant action list
- [ ] **B1.** Register at dubaichamberdigital.com/en/create-ai-agents (one registration covers both entries; before January 2027 (earlier registration = workshop/Academy access)).
- [ ] **B2.** Deploy the AirPilot web app (Render) so the prototype has a live URL; confirm the demo scenario renders in the browser.
- [ ] **B3.** Record the demo video per `DUBAI_DEMO_SCRIPT.md` (3 min, English, unlisted YouTube).
- [ ] **B4.** Convert `DUBAI_PITCH.md` into a slide deck (12 slides, English).
- [ ] **B5.** Submit as **Best Business AI Agent** when the submission window opens (the platform notifies registered participants).
- [ ] **B6.** (Primary entry remains ClauseGuard AI in Best Societal AI Agent — see `clauseguard-ai/DUBAI_SUBMISSION.md`.)

## 5. Judging criteria → coverage
1. **Priority problem** → Slides 2–3: payment-ops errors are routine, expensive, and unowned. ✅
2. **Agent design** → Slides 4–6: perceive→detect→plan→verify→act→receipt with a deterministic gate. ✅
3. **Tested impact** → Slide 9: 15/15 assertions incl. never-double-pay; pilot metrics in roadmap. ✅
4. **Scalable path** → Slides 10–11: grant-funded roadmap + per-account SaaS via accounting firms; explicitly pre-commercial. ✅

## 6. Risks & mitigations
| Risk | Mitigation |
|---|---|
| Live final must be a fully working agent | Zero-dependency offline fixtures mean the demo cannot fail on network/API; roadmap funded by the grant delivers production hardening |
| "Fully commercialised not eligible" | Entry framed as open-source pre-commercial prototype; grant funds the Dubai pilot |
| Two entries split attention | Both entries share one demo-recording session and one slide-deck template; total incremental effort ≈ half of a single entry |
| Money-moving agent reads as risky | The verifier gate *is* the answer — lead with it in deck and video |
