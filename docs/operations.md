# Benchmark operation protocol

This benchmark measures the exact model–harness configuration captured by a run record. It does not infer a model's intrinsic ability.

## Run modes

Use one of two predeclared modes. Do not choose the mode after seeing a result.

### Probe mode

Probe mode is the default for development sets such as `minimal-3`.

- Run each task once per configuration.
- Do not rerun valid failures.
- Repeat only runs invalidated by benchmark infrastructure malfunction.
- Use probe results to reject weak harness ideas and identify candidates for confirmation.
- Treat a task as development evidence once its evaluator failure has influenced a harness change.

Probe mode is intentionally cheap. It is not evidence that a small score difference is robust to model sampling variance.

### Confirm mode

Confirm mode is for comparing a small number of candidate harnesses after probe selection.

- Declare the task set, configurations, repetition count, and comparison rule before the first run.
- Every repetition uses a fresh session and fresh workspace.
- Run the full predeclared repetition count regardless of early wins or failures; do not stop when the result looks favorable.
- Do not selectively rerun individual valid outcomes.
- Where practical, interleave configurations (for example A1, B1, A2, B2) to reduce provider or client drift.
- Report all repetitions. Summarize both delivery consistency and efficiency rather than keeping only the best run.

A planned independent repetition is not a rerun of a failed attempt. The distinction is whether the repetition count was frozen before observing outcomes.

## Before a run

1. Freeze the benchmark version and record the starter, evaluator, prompt, preset, plugin, and harness commit hashes.
2. Record the declared run mode. In confirm mode, also freeze the repetition count and comparison rule.
3. Assign a unique run and session ID. Never reuse a session across tasks or repetitions.
4. Validate the dataset with `harnessbench validate`.
5. Prepare a fresh workspace with `harnessbench prepare`.
6. Confirm that the workspace does not contain `private/`, hidden instances, scorers, prior results, or another task's trace.

## During a run

- Start wall-clock and usage collection immediately before delivering `TASK.md`.
- Allow the agent to inspect and modify only its prepared workspace.
- Do not provide hints. Record every human intervention if an operational unblock is unavoidable.
- Stop on agent completion, harness failure, or task timeout.
- Treat timeout and harness crashes as valid outcomes, not infrastructure-invalid runs.

## After a run

1. Stop the agent and make the workspace read-only or snapshot it.
2. Save the complete trace, tool calls, usage ledger, workspace diff, and termination reason.
3. Run `harnessbench evaluate` outside the agent environment.
4. Merge evaluator output with operational metrics into the run-result schema.
5. Mark a run `infrastructure_invalidated` only when the runner or evaluator itself malfunctioned. Record the concrete fault before repeating it.

## Comparison order

Compare configurations in this order:

1. invalid or critical failures;
2. number of ShipReady tasks;
3. completion and capability coverage;
4. optimizer quality where applicable;
5. wall time, token classes, credits, failed tool calls, and human intervention among similarly complete runs.

Do not combine quality and cost into one universal score. Preserve the Pareto frontier.

For confirm runs, report per-task outcomes across repetitions. A harness improvement should preferably appear across tasks or repetitions rather than depend on a single unusually strong sample.

## Capability gates

A task may declare `required_capabilities` in `task.toml`. Every required capability must earn its full evaluator weight for the submission to be ShipReady, even when the aggregate completion score exceeds `ship_ready_score`.

Use required capabilities for properties whose absence makes the artifact fundamentally unshippable, such as durability, authorization boundaries, safety invariants, or feasibility. Do not use them merely to force perfection on optional quality dimensions.

## Dataset retirement and sealing

`minimal-3` is a public development probe. Its evaluators and reference solutions are visible in this repository and therefore must not be treated as a truly sealed selection set.

Once a task's evaluator failure has influenced a harness change, that exact task is development evidence only. It may remain a regression test, but it is no longer an independent selection result.

Selection and final-confidence datasets should keep evaluator cases and reference solutions outside any repository or environment accessible to the tested agent until the comparison is complete. If reproducibility requires later publication, freeze and record evaluator hashes before the runs and publish the sealed material only afterward.
