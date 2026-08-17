# Core-8 sealed-set specification

Core-8 is intentionally not implemented until Minimal-3 discriminates between harnesses without infrastructure noise. Creating its hidden cases early would spend the selection set while the framework is still changing.

| ID | Task family | Primary capabilities | Target time |
|---|---|---|---:|
| C1 | Session Boundary | cookie expiry, revocation, authorization boundaries | 30 min |
| C2 | SQLite Evolution | migration, backfill, idempotent rerun, rollback | 35 min |
| C3 | Async Cache | TTL, request coalescing, stale reads, error propagation | 30 min |
| C4 | Replenishment Planner | bounded multi-period inventory optimization | 35 min |
| C5 | Reminder Clock | time zones, DST, clock rollback, deduplication | 30 min |
| C6 | Streaming Log CLI | bounded memory, malformed input, stable aggregation | 25 min |
| C7 | Offline Dashboard | state persistence, accessibility, keyboard operation | 35 min |
| C8 | Package Migration | staged API migration and cross-turn regression control | 40 min |

Before implementation, freeze the language mix, capability weights, public contracts, instance generators, and promotion rules in a new dataset version.
