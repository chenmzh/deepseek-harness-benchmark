# DeepSeek Harness Benchmark

English | [中文](README.zh-CN.md) | [Agent/AI instructions](AGENTS.md)

Deterministic, repository-level benchmarks for measuring how harness design changes an agent's delivery quality, latency, token use, and cost.

> Status: early development. `minimal-3` is the first implemented probe set; larger sealed datasets remain specifications until the probe framework is validated.

## Design principles

- Evaluate a complete model–harness configuration, not a model name in isolation.
- Treat delivery quality as a gate and time/tokens/cost as separate efficiency dimensions.
- Keep hidden evaluators outside the agent workspace.
- Freeze task inputs, evaluator versions, limits, and result schemas before a run.
- Do not rerun valid probe failures. Only infrastructure-invalid runs may be repeated.
- Prefer deterministic local tests over LLM judging.

## Repository layout

```text
datasets/                  Public task definitions and starter repositories
private/hidden-tests/      Evaluators never copied into the agent workspace
src/harnessbench/          Dataset validation, workspace preparation and evaluation CLI
schemas/                   Machine-readable contracts
docs/                      Authoring, operation and instruction guidance
tests/                     Self-tests for the benchmark tooling
```

## Quick start

Use Python 3.11 or newer. The tooling itself has no runtime dependencies outside the standard library.

```bash
python -m harnessbench validate datasets/minimal-3
python -m harnessbench prepare datasets/minimal-3/m1-reservation-repair /tmp/m1-workspace
python -m harnessbench evaluate datasets/minimal-3/m1-reservation-repair /tmp/m1-workspace \
  --private-root private/hidden-tests --output result.json
python -m harnessbench assemble result.json examples/run-metadata.json --output complete-result.json
```

When running from a checkout without installing the package, prefix commands with `PYTHONPATH=src`.

## Minimal-3

| ID | Task | Primary signal |
|---|---|---|
| M1 | Reservation Repair | Diagnosis, invariants, idempotency, rollback |
| M2 | MicroScheduler-12 | Constraint modelling and bounded optimization |
| M3 | Durable Lease Queue | Greenfield completeness and crash-safe state transitions |

See [`docs/operations.md`](docs/operations.md) for the one-shot protocol, [`docs/authoring.md`](docs/authoring.md) for adding tasks, and [`docs/metrics.md`](docs/metrics.md) for result semantics.

AI systems should begin with [`AGENTS.md`](AGENTS.md) for repository rules or [`llms.txt`](llms.txt) for a compact document index.

## Security boundary

The prepared workspace contains only `TASK.md`, `starter/`, and public material. Never mount `private/hidden-tests` into the agent environment. Run evaluation only after the agent session has stopped and the workspace has been snapshotted.
