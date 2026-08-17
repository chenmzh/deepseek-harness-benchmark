from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys


def main() -> int:
    submission = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(submission))
    module = importlib.import_module("microscheduler")
    instance = json.load(sys.stdin)
    schedule = module.solve(instance)
    json.dump(schedule, sys.stdout, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
