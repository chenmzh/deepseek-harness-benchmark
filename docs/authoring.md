# Task authoring guide

## Required task assets

Each public task directory contains:

```text
TASK.md
task.toml
starter/
public-tests/
```

Its development evaluator lives under `private/hidden-tests/<task-slug>/` and is referenced by `private_scorer` in `task.toml`. For a true sealed selection or confidence set, keep evaluator material outside any repository or environment accessible to the tested agent.

## Authoring sequence

1. Write a capability map before writing tests. Every scored requirement needs one owner and an explicit weight.
2. Identify capabilities whose absence makes the artifact fundamentally unshippable and declare those names in `required_capabilities`.
3. Build a correct reference solution privately.
4. Write deterministic public smoke tests that establish the interface without revealing all edge cases.
5. Write hidden tests for boundaries, failures, invariants, restart behavior, and regression safety.
6. Run the scorer against the untouched starter, the reference solution, and at least two deliberately incomplete mutations, including mutations that fail each required capability.
7. Freeze hashes and version the task. Any scoring-semantic or ShipReady-gate change increments the task version.

## Quality rules

- A task must be solvable without network access.
- Public instructions must describe every required behavior. Hidden tests may hide examples, not requirements.
- Do not reward modifying tests, deleting fixtures, printing fabricated evidence, or special-casing hidden inputs.
- Prefer behavioral assertions and invariants over exact implementation shapes.
- Use an LLM judge only for a capability that cannot be made deterministic, and keep that capability outside ShipReady gates when possible.
- Keep task-specific objective quality separate from operational efficiency.

## Required capabilities

`required_capabilities` is an optional array in the evaluator section of `task.toml`:

```toml
[evaluator]
ship_ready_score = 85
private_scorer = "example/score.py"
required_capabilities = ["durability", "authorization_boundary"]
```

Each named capability must appear in the scorer's `capabilities` object with numeric `earned` and `weight` fields. A required capability passes only when `earned == weight`. Missing, malformed, or partially earned required capabilities make the result non-ShipReady even if the aggregate completion score is above the threshold.

Use this mechanism sparingly. Good gates cover properties such as persistence guarantees, safety invariants, authorization boundaries, or optimization feasibility where partial credit must not imply deployability.

## Optimization tasks

Every optimization instance must include a deterministic baseline and a frozen oracle or lower bound. A recommended normalized score is:

```text
clamp((baseline - candidate) / (baseline - oracle), 0, 1)
```

Feasibility is always a gate. An infeasible solution receives no objective-quality credit. Include several instance families so one heuristic cannot dominate by matching a single distribution.
