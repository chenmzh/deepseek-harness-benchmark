# Security and benchmark integrity

Report leaked hidden cases, evaluator escapes, credential exposure, or result-tampering paths privately to the repository owner.

An agent workspace must never contain:

- `private/hidden-tests`;
- reference solutions;
- results from the same task family;
- credentials or a writable evaluator;
- a Git history that contains any of the above.

Evaluation should run after the agent process has stopped, against a workspace snapshot. A production runner should add OS-level CPU, memory, filesystem, process, and network isolation; the Python CLI provides workflow separation, not a security sandbox.
