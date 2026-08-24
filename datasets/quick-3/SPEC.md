# Quick-3 short-horizon development probe specification

Quick-3 targets fast model–harness iteration with Luna max as the calibration floor. It is a public development probe, not a sealed selection set.

## Calibration target

On one-shot Luna max runs, the three tasks should not all be ShipReady and should not cluster within a ten-point completion band. The intended profile is one ShipReady result, one partial result, and one materially incomplete result. Each task must leave a runnable, externally scorable snapshot within its fixed wall-time budget.

| ID | Difficulty | Task family | Primary capabilities | Agent budget |
|---|---|---|---|---:|
| Q1 | Easy | Layered Config | recursive merge, deletion, validation, isolation | 240 s |
| Q2 | Medium | Versioned TTL Store | CAS, expiry, idempotency, restart, atomic persistence | 240 s |
| Q3 | Hard | Async Single-flight Cache | coalescing, stale refresh, error/cancellation, invalidation | 240 s |

Quality and operational efficiency remain separate. The time budgets bound the probe; they do not contribute points to `completion_score`.

See [CALIBRATION.md](CALIBRATION.md) for the Luna max baseline and static scorer calibration.
