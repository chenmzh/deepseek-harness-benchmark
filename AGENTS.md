# Repository instructions for agents and AI systems

These instructions apply to the entire repository. They describe benchmark development, not the behavior of an agent being evaluated inside a prepared task workspace.

## Mission

Maintain deterministic, auditable repository-level benchmarks that measure the complete model-harness configuration. Preserve the separation between delivery quality and operational efficiency.

## Read first

Before changing files, read the smallest relevant set:

1. `README.md` or `README.zh-CN.md` for repository purpose.
2. `docs/authoring.md` when creating or changing a task.
3. `docs/operations.md` when changing execution behavior.
4. `docs/metrics.md` when changing scores or result fields.
5. The target task's `TASK.md` and `task.toml`.

Do not read unrelated hidden tests merely to solve a public task. Repository maintainers may inspect private material only when authoring, calibrating, or auditing the benchmark.

## Non-negotiable boundaries

- MUST NOT copy `private/hidden-tests` or `private/reference-solutions` into a prepared agent workspace.
- MUST NOT expose hidden cases, frozen targets, reference code, or prior solutions in `TASK.md`, starter files, public tests, prompts, traces, or reports visible to an evaluated agent.
- MUST NOT change a hidden requirement without first stating it in the public task contract.
- MUST NOT combine completion, time, token use, and cost into one universal score.
- MUST NOT mark a valid model timeout, harness crash, or poor solution as an infrastructure-invalid run.
- MUST NOT modify test results, traces, usage ledgers, or evaluator output to improve a score.
- MUST preserve deterministic behavior and standard-library-only runtime unless a task manifest explicitly says otherwise.

## Source-of-truth map

| Concern | Canonical source |
|---|---|
| Dataset membership and version | `datasets/<dataset>/dataset.toml` |
| Public task contract | `datasets/<dataset>/<task>/TASK.md` |
| Limits and scorer path | `datasets/<dataset>/<task>/task.toml` |
| Public interface examples | `datasets/<dataset>/<task>/public-tests/` |
| Hidden behavioral truth | `private/hidden-tests/<task>/` |
| Calibration ceiling | `private/reference-solutions/<task>/` |
| Run-result fields | `schemas/run-result.schema.json` |
| Operational protocol | `docs/operations.md` |
| Metric meaning | `docs/metrics.md` |

When two files disagree, repair the inconsistency at the canonical source and update dependent documentation in the same change.

## Task-authoring workflow

Follow this order:

1. Write a capability map with explicit weights totaling 100.
2. Write the complete public behavioral contract.
3. Add a deliberately incomplete but runnable starter.
4. Add public smoke tests that establish the interface without revealing hidden cases.
5. Add a private reference solution.
6. Add deterministic hidden cases for normal behavior, boundaries, failures, invariants, restart behavior, and regression.
7. Score the untouched starter, reference solution, and at least two incomplete mutations.
8. Require the reference solution to be ShipReady and the untouched starter not to be ShipReady.
9. Freeze targets and increment versions for any scoring-semantic change.

For optimization tasks, feasibility is a gate. Compare objective quality against a frozen deterministic baseline and a reviewed best-known target or valid oracle. Keep instance generation deterministic and resource-bounded.

## Safe execution sequence

```text
validate dataset
→ prepare fresh workspace
→ verify private material is absent
→ run exactly one isolated agent session
→ stop and snapshot the workspace
→ run private evaluator externally
→ assemble operational metadata
→ preserve trace and hashes
```

Never run the private evaluator while an evaluated agent can inspect its process, filesystem, command line, or output.

## Canonical commands

```bash
PYTHONPATH=src python3 -m harnessbench validate datasets/minimal-3
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src datasets private tests
git diff --check
```

Prepare and evaluate one task:

```bash
PYTHONPATH=src python3 -m harnessbench prepare \
  datasets/minimal-3/m1-reservation-repair \
  /tmp/m1-workspace

PYTHONPATH=src python3 -m harnessbench evaluate \
  datasets/minimal-3/m1-reservation-repair \
  /tmp/m1-workspace \
  --private-root private/hidden-tests \
  --output /tmp/m1-evaluation.json
```

## Change discipline

- Preserve existing public APIs unless the task version intentionally changes.
- Keep starter defects intentional and documented privately; do not accidentally repair starter code while fixing the reference solution.
- Keep reference implementations out of package imports and prepared workspaces.
- Prefer behavioral tests over implementation-shape assertions.
- Use temporary directories for evaluator writes and clean them after success or failure.
- Record exact commands and observed results in change summaries.
- Update English, Chinese, and AI-facing documents together when a shared rule changes.

## Completion checklist

A repository change is complete only when:

- manifests validate;
- relevant public contracts pass against the reference solutions;
- repository self-tests pass;
- reference solutions remain ShipReady;
- starters remain below ShipReady unless a deliberate calibration change says otherwise;
- no private material appears in a prepared workspace;
- documentation variants agree on commands, paths, versions, and safety boundaries;
- the Git diff contains only intended files.
