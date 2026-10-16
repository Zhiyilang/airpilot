# Adversarial scenario — the two attacks a naive duplicate check misses

AirPilot's bundled fixtures contain more than the three textbook incidents
(delayed / duplicate / insufficient). It also ships the two attack patterns
that defeat the obvious implementation, because a payment agent that only
handles the textbook version is a payment agent an attacker can use.

## Attack 1 — reference reuse, account swap (account takeover)

```
t_fraud_done     completed  PO-5561  Initech Corp -> INITECH-1001   $980
t_fraud_pending  review     PO-5561  Initech Corp -> ATTACKER-9999  $980
```

A duplicate detector that groups on (beneficiary, amount, reference) sees
**identical keys** and stays quiet — the amount and reference are right, so
nothing looks duplicated. But the bank account changed. This is what a
compromised vendor record or an attacker who found the reference in an email
thread looks like.

AirPilot: `detect_beneficiary_changed` flags it CRITICAL, `plan_for` chooses
`escalate` (never `retry_transfer`), and the verifier independently blocks any
retry of that transfer.

## Attack 2 — reference dodge (smurfed duplicate)

```
t_smurf_a  completed  SUB-1001     Stark Retail  $45  (10:30)
t_smurf_b  review     SUB-1001-R2  Stark Retail  $45  (11:15)
```

Same supplier, same amount, 45 minutes apart, reference tweaked with `-R2`.
Group on (beneficiary, amount, reference) and these are two *different*
payments. The tell is the time window: genuine supplier invoices for the same
amount do not arrive twice within 90 minutes.

AirPilot: `detect_rapid_repeat` flags it HIGH and the verifier blocks the
retry.

## Why ship these in the default fixtures?

Judges can read the detector code. What they cannot see from code alone is
whether the agent *behaves* safely on inputs the author did not have to think
about. Running the bundled demo (`python -m airpilot demo`) shows all five
incident types resolved in one pass, with the two attacks held for human
review instead of paid.
