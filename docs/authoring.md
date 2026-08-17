# Task authoring guide

## Required task assets

Each public task directory contains:

```text
TASK.md
task.toml
starter/
public-tests/
```

Its private evaluator lives under `private/hidden-tests/<task-slug>/` and is referenced by `private_scorer` in `task.toml`.

## Authoring sequence

1. Write a capability map before writing tests. Every scored requirement needs one owner and an explicit weight.
2. Build a correct reference solution privately.
3. Write deterministic public smoke tests that establish the interface without revealing all edge cases.
4. Write hidden tests for boundaries, failures, invariants, restart behavior, and regression safety.
5. Run the scorer against the untouched starter, the reference solution, and at least two deliberately incomplete mutations.
6. Freeze hashes and version the task. Any scoring-semantic change increments the task version.

## Quality rules

- A task must be solvable without network access.
- Public instructions must describe every required behavior. Hidden tests may hide examples, not requirements.
- Do not reward modifying tests, deleting fixtures, printing fabricated evidence, or special-casing hidden inputs.
- Prefer behavioral assertions and invariants over exact implementation shapes.
- Use an LLM judge only for a capability that cannot be made deterministic, and keep that capability outside ShipReady gates when possible.
- Keep task-specific objective quality separate from operational efficiency.

## Optimization tasks

Every optimization instance must include a deterministic baseline and a frozen oracle or lower bound. A recommended normalized score is:

```text
clamp((baseline - candidate) / (baseline - oracle), 0, 1)
```

Feasibility is always a gate. An infeasible solution receives no objective-quality credit. Include several instance families so one heuristic cannot dominate by matching a single distribution.
