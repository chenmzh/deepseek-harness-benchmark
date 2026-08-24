# Quick-3 calibration

Date: 2026-08-24

## Luna max probe

The calibration used `openai-codex/gpt-5.6-luna@max` for the root agent and every configured reasoning-router role. Routing was natural: no role call was mandatory. Each task received a fresh session, fresh prepared workspace, and a 240-second agent budget. Private evaluator material was unreadable until the agent stopped.

| Task | Completion | ShipReady | Termination | Capability summary |
|---|---:|:---:|---|---|
| Q1 Layered Config | 100 | yes | 240 s limit | 4/4 capabilities complete |
| Q2 Versioned TTL Store | 20 | no | 240 s limit | basic store only |
| Q3 Async Single-flight Cache | 10 | no | 240 s limit | one of two error/cancellation cases only |

The 90-point range establishes useful one-shot discrimination at the Luna max floor without combining quality and time. Q2 and Q3 remain concentrated at the low end, so a future expansion should add a task calibrated near 50–70 rather than weakening either scorer after results are observed.

One Q3 launch was infrastructure-invalidated before model execution because the provider rejected the generic runner prompt. It was repeated once in a new workspace with the shorter equivalent prompt `Implement the requirements in TASK.md and run the public tests.` The invalid launch is excluded from the table.

## Static scorer calibration

| Task | Untouched starter | Reference | Incomplete mutations |
|---|---:|---:|---:|
| Q1 | 25 | 100 / ShipReady | 75, 75 |
| Q2 | 20 | 100 / ShipReady | 85, 85; both fail required-capability gates |
| Q3 | 10 | 100 / ShipReady | 60, 80 |

The Q2 and Q3 scorers were audited before the final 240-second runs. Checks that assumed an undocumented exception type or eager database creation were removed. Longer pre-calibration snapshots then scored 100, confirming those earlier deductions were benchmark defects rather than model failures.
