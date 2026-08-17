# Fixed run policy

Deliver the task exactly as written in `TASK.md`. The runner must not add encouragement, solution hints, benchmark names, hidden-test descriptions, or different completion criteria.

Allowed automatic messages are limited to:

- the initial task;
- a predetermined phase message for an explicitly multi-stage task;
- an infrastructure error that contains no task-solving information;
- a timeout warning when the manifest declares one.

All other messages count as human intervention. Store their complete text in the run record.
