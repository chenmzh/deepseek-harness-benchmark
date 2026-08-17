# Contributing

New tasks start as development tasks and must not enter a sealed dataset until their public contract, reference solution, hidden evaluator, and mutation checks agree.

Before submitting a change:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m harnessbench validate datasets/minimal-3
```

Do not include real model traces, API keys, subscription ledgers, or user-specific harness configuration. Treat changes to hidden scoring semantics as benchmark version changes.
