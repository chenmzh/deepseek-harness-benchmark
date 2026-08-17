# Metrics contract

Quality and efficiency remain separate dimensions. The evaluator owns completion, ShipReady status, critical failures, capability details, and optimizer quality. The runner owns time, usage, tool activity, intervention, and termination status.

Use `harnessbench assemble evaluator.json run-metadata.json --output result.json` after both sides have stopped writing.

## Quality

- `completion_score`: weighted behavioral coverage from 0 to 100.
- `ship_ready`: completion meets the task threshold and no critical failure exists.
- `critical_failures`: safety, integrity, or essential-behavior failures.
- `optimizer_quality`: task-specific normalized quality where applicable.

## Efficiency

- `wall_time_seconds`: end-to-end elapsed time visible to the user.
- `model_active_seconds`: provider/model execution time when observable.
- input, cached-input, output, and reasoning token counts.
- actual subscription credits and optional API-equivalent cost.
- tool calls, failed tool calls, test cycles, and human interventions.

API-equivalent cost is counterfactual when the run uses a subscription. Never report it as actual spend. Compare efficiency only among runs with similar completion and critical-failure status.
