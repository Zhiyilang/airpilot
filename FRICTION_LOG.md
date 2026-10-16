# AirPilot Friction Log

Real problems hit while building and hardening AirPilot, what they cost, and how
they were fixed. Kept because a payment agent's failure log *is* part of the
safety argument. (Amazon-style friction log: task / steps / expected vs actual /
severity / workaround / suggestion.)

## F1 — Live writes silently simulated a money movement (CRITICAL, fixed)

- **Task**: create a transfer via the Airwallex API.
- **Steps**: call `create_transfer` with real credentials; the API returns a
  transient error (timeout / 502).
- **Expected**: the agent reports failure and stops.
- **Actual (v1)**: `create_transfer` caught *every* `AirwallexError` and fell
  back to `fixtures.sim_create_transfer`, returning `status: pending` — the
  agent's own receipt then claimed a transfer existed. An operator reading the
  receipt would believe the supplier was paid.
- **Severity**: critical. An agent that *thinks* money moved when it did not is
  strictly worse than one that stopped and shouted — every downstream decision
  (reconciliation, "already retried?" checks) is poisoned.
- **Fix**: writes never simulate. Simulated writes exist only in **explicit**
  offline mode (`client.offline = True`, set by the CLI/demo/eval path). A live
  write failure raises. Reads keep a fixture fallback but only in explicit
  offline mode too: acting on *invented balances* is how overdrafts happen.
- **Tests**: `test_live_write_never_simulates`, `test_explicit_offline_write_simulates`,
  `test_live_read_failure_raises_not_fixtures`.

## F2 — The duplicate detector double-reported an account takeover (HIGH, fixed)

- **Task**: classify the pair `t_fraud_done` (PO-5561 paid to INITECH-1001) and
  `t_fraud_pending` (PO-5561, same amount, to ATTACKER-9999).
- **Expected**: one incident — account takeover, escalate to human.
- **Actual (v1 semantics)**: `detect_duplicate` grouped on
  (beneficiary, amount, reference) and fired *in addition to*
  `detect_beneficiary_changed` — two incidents, two proposed remedies
  (`hold_transfer` + `escalate`) for the same pair.
- **Severity**: medium-high. Redundant for the demo, but the deeper issue is
  semantic: paying a *different account* under a reused reference is not a
  duplicate payment (the first money went somewhere else), and the correct
  remedy differs (hold vs escalate).
- **Fix**: `detect_duplicate` now also requires `beneficiary_account` to match;
  mismatched accounts route exclusively to the account-change detector. The
  verifier's retry idempotency check got the same account condition.
- **Tests**: `test_account_swap_is_not_a_duplicate`.

## F3 — Crash-restart could re-pay a retried transfer (HIGH, fixed)

- **Task**: guarantee "never pay twice" across a process crash.
- **Expected**: a restart after a half-finished command pass does not repeat
  the retry.
- **Actual (v1)**: the never-double-pay guarantee lived entirely in one
  in-memory `command()` pass — the verifier compared the proposal against the
  transfer list returned by the API. If the process died after
  `create_transfer` succeeded but before the receipt was written, the next
  process saw the same pending transfer and the same proposal, and the API had
  no memory of the first attempt from the agent's point of view.
- **Fix**: `airpilot/ledger.py` — a deterministic fingerprint of the
  money-moving intent (remedy + transfer + beneficiary + account + amount +
  currency + reference), persisted as JSONL, consulted by the verifier before
  any call and written after any acted action. Crash-safe by construction:
  `record` is idempotent and a corrupt line is skipped rather than fatal.
- **Tests**: `test_persistence_across_instances`,
  `test_verifier_blocks_replayed_retry`, `test_second_pass_blocked_by_ledger`.

## F4 — Two attacks defeat the naive duplicate check (addressed by design)

- **Task**: "duplicate payment" detection.
- **Actual**: grouping on (beneficiary, amount, reference) misses
  (a) reference reuse with a swapped bank account, and (b) reference dodge
  (`INV-2026-0901` → `INV-2026-0901-R2`, same supplier, same amount, 45 min
  apart). Both are in the wild; both pay out.
- **Fix**: `detect_beneficiary_changed` (CRITICAL → escalate) and
  `detect_rapid_repeat` (HIGH → escalate), wired into the verifier so *any*
  retry touching those pairs is blocked regardless of what the brain proposes.
  Both ship in the default fixtures so the demo shows them being caught.
- **Tests**: `AdversarialDetectors` (8 tests).

## F5 — eval docstring claimed "30+ assertions", actual was 15 (MEDIUM, fixed)

- Classic documentation drift: the suite grew by copy-paste, the header never
  followed. Judges read the header first.
- **Fix**: header now states the real number and it is kept honest by
  re-running the suite after every change (currently 40).

## F6 — Fixture dates are in the future relative to "now" (LOW, by design)

- `python -m airpilot command` with real wall-clock `now` does not fire the
  delayed-transfer detector: the bundled transfers are dated 2026-11-xx.
- **Workaround**: the `demo` subcommand freezes `now` via
  `fixtures.scenario_now()` (latest transfer + 1h), which is what makes the
  bundled scenario reproducible. Live runs use real `now` by design.
- Noted so nobody files it as a bug.

## F7 — Retry loop needed a network-free test seam (LOW, by design)

- `_get` retries transient 429/5xx with capped backoff, but a test that really
  slept would be slow and flaky.
- **Fix**: the HTTP opener is an injectable parameter (`_get(path, opener=...)`)
  and `retry_sleep` is a constructor arg; tests inject a fake opener and set
  sleep to 0. `test_get_retries_transient_429` / `test_get_raises_after_retries_exhausted`.

## Known unverified items (honesty register)

- **No live Airwallex key yet.** Every live-path assertion uses an injected
  fake (F1, F7). Endpoint paths and payload shapes follow the v1 docs and the
  starter kit; the first sandbox run should confirm them. If a path is wrong,
  the fix is a one-line change in `client.py` — the decision layer is
  shape-agnostic.
- Airwallex has no "hold" verb; `hold_transfer` is modeled as a recorded
  no-op decision (`acted: false`), which is also what makes it safe.
