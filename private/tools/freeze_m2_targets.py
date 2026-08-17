"""Print frozen best-known M2 objective values for review and check-in."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import runpy


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("--scorer", type=Path, default=Path("private/hidden-tests/m2-microscheduler-12/score.py"))
    args = parser.parse_args()
    scorer = runpy.run_path(str(args.scorer.resolve()))
    values = []
    for family in ("tight_deadline", "skill_bottleneck", "precedence", "setup"):
        for seed in range(11, 17):
            instance = scorer["make_instance"](family, seed)
            schedule, error = scorer["run_candidate"](args.reference.resolve(), instance)
            if error:
                raise RuntimeError(f"{family}/{seed}: {error}")
            valid, reason = scorer["validate"](instance, schedule)
            if not valid:
                raise RuntimeError(f"{family}/{seed}: {reason}")
            values.append({
                "family": family,
                "seed": seed,
                "best_known": list(scorer["objectives"](instance, schedule)),
                "baseline": list(scorer["objectives"](instance, scorer["baseline"](instance))),
                "lower_bound": list(scorer["lower_bounds"](instance)),
            })
    print(json.dumps(values, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
