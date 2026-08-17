# One-shot operation protocol

This protocol measures the exact model–harness configuration captured by a run record. It does not infer a model's intrinsic ability.

## Before a run

1. Freeze the benchmark version and record the starter, evaluator, prompt, preset, plugin, and harness commit hashes.
2. Assign a unique run and session ID. Never reuse a session across tasks.
3. Validate the dataset with `harnessbench validate`.
4. Prepare a fresh workspace with `harnessbench prepare`.
5. Confirm that the workspace does not contain `private/`, hidden instances, scorers, prior results, or another task's trace.

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

## Dataset retirement

Once a task's hidden failure has influenced a harness change, that exact task is development evidence only. It may remain a regression test, but it is no longer an independent selection result. Promote to a sealed dataset or a pre-generated shadow variant.
