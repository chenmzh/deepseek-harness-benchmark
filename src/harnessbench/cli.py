from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .evaluation import EvaluationError, evaluate_submission
from .manifest import ManifestError, load_dataset_manifest, load_task_manifest
from .result import ResultError, assemble_run_result
from .workspace import WorkspaceError, prepare_workspace


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harnessbench")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate a dataset and its tasks")
    validate.add_argument("dataset")

    prepare = commands.add_parser("prepare", help="create an isolated task workspace")
    prepare.add_argument("task")
    prepare.add_argument("destination")

    evaluate = commands.add_parser("evaluate", help="run the private scorer")
    evaluate.add_argument("task")
    evaluate.add_argument("submission")
    evaluate.add_argument("--private-root", required=True)
    evaluate.add_argument("--output")

    assemble = commands.add_parser("assemble", help="merge evaluator output with operational metrics")
    assemble.add_argument("evaluation")
    assemble.add_argument("metadata")
    assemble.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            dataset = load_dataset_manifest(args.dataset)
            print(
                json.dumps(
                    {
                        "dataset": dataset.dataset_id,
                        "version": dataset.version,
                        "tasks": list(dataset.task_dirs),
                        "valid": True,
                    },
                    indent=2,
                )
            )
            return 0
        if args.command == "prepare":
            manifest = load_task_manifest(args.task)
            print(prepare_workspace(manifest, args.destination))
            return 0
        if args.command == "evaluate":
            manifest = load_task_manifest(args.task)
            result = evaluate_submission(manifest, args.submission, args.private_root)
            rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
            if args.output:
                Path(args.output).write_text(rendered, encoding="utf-8")
            else:
                print(rendered, end="")
            return 0
        if args.command == "assemble":
            evaluation = json.loads(Path(args.evaluation).read_text(encoding="utf-8"))
            metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
            result = assemble_run_result(evaluation, metadata)
            rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
            if args.output:
                Path(args.output).write_text(rendered, encoding="utf-8")
            else:
                print(rendered, end="")
            return 0
    except (ManifestError, WorkspaceError, EvaluationError, ResultError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2
