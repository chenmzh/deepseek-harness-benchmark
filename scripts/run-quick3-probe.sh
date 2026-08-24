#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
dataset_root="$repo_root/datasets/quick-3"
private_root="$repo_root/private"

if [[ $# -lt 1 || $# -gt 2 ]]; then
    printf 'usage: %s OUTPUT_DIR [DSH_PATCH]\n' "$0" >&2
    exit 64
fi

output_dir=$(realpath -m -- "$1")
config_path=$(realpath -m -- "${2:-$repo_root/configs/quick3-all-luna-max.yml}")
profile=${QUICK3_DSH_PROFILE:-hb-codex-bench}
probe_dsh_home=${QUICK3_DSH_HOME:-/tmp/dhb-codex-router-home}
prompt='Implement the requirements in TASK.md and run the public tests.'

case "$output_dir" in
    /|"$repo_root"|"$repo_root"/*)
        printf 'refusing unsafe output directory: %s\n' "$output_dir" >&2
        exit 64
        ;;
esac
if [[ -e "$output_dir" ]]; then
    printf 'output directory already exists: %s\n' "$output_dir" >&2
    exit 73
fi
if [[ ! -f "$config_path" ]]; then
    printf 'missing DSH patch: %s\n' "$config_path" >&2
    exit 66
fi
for command_name in awk chmod date dirname dsh find git mkdir python3 realpath sha256sum stat timeout; do
    if ! command -v "$command_name" >/dev/null; then
        printf 'missing command: %s\n' "$command_name" >&2
        exit 69
    fi
done

mkdir -p "$output_dir/workspaces" "$output_dir/logs" \
    "$output_dir/evaluations" "$output_dir/metrics"

original_private_mode=$(stat -c %a "$private_root")
private_locked=0
restore_private() {
    if [[ "$private_locked" -eq 1 ]]; then
        chmod "$original_private_mode" "$private_root"
        private_locked=0
    fi
}
trap restore_private EXIT INT TERM

PYTHONPATH="$repo_root/src" python3 -m harnessbench validate "$dataset_root"

config_sha256=$(sha256sum "$config_path" | awk '{print $1}')
benchmark_commit=$(git -C "$repo_root" rev-parse HEAD)
{
    printf 'dataset=quick-3@0.1.0\n'
    printf 'benchmark_commit=%s\n' "$benchmark_commit"
    printf 'config=%s\n' "$config_path"
    printf 'config_sha256=%s\n' "$config_sha256"
    printf 'profile=%s\n' "$profile"
    printf 'prompt=%s\n' "$prompt"
} > "$output_dir/run-policy.env"
printf 'task_id\tdsh_status\tvalidity\twall_ms\tcompletion_score\tship_ready\n' \
    > "$output_dir/summary.tsv"

tasks=(q1-layered-config q2-versioned-ttl-store q3-async-singleflight-cache)
task_ids=(Q1 Q2 Q3)

for index in "${!tasks[@]}"; do
    task=${tasks[$index]}
    task_id=${task_ids[$index]}
    task_dir="$dataset_root/$task"
    workspace="$output_dir/workspaces/$task"
    log="$output_dir/logs/$task.log"
    evaluation="$output_dir/evaluations/$task.json"
    metrics="$output_dir/metrics/$task.env"
    timeout_seconds=$(python3 -c \
        'import pathlib, sys, tomllib; print(tomllib.loads(pathlib.Path(sys.argv[1]).read_text())["limits"]["timeout_seconds"])' \
        "$task_dir/task.toml")

    PYTHONPATH="$repo_root/src" python3 -m harnessbench prepare "$task_dir" "$workspace"
    leaked_path=$(find "$workspace" -type d \
        \( -name private -o -name hidden-tests -o -name reference-solutions \) \
        -print -quit)
    if [[ -n "$leaked_path" ]]; then
        printf 'private material found in prepared workspace: %s\n' "$leaked_path" >&2
        exit 97
    fi

    chmod 000 "$private_root"
    private_locked=1
    if [[ -r "$private_root/hidden-tests" ]]; then
        printf 'private evaluator remains readable during agent run\n' >&2
        exit 97
    fi

    start_ns=$(date +%s%N)
    set +e
    (
        cd "$workspace"
        DSH_HOME="$probe_dsh_home" \
        DSH_PERMISSION_MODE=workspace-write \
        DSH_TELEMETRY_DISABLED=1 \
        timeout --signal=TERM --kill-after=20s "${timeout_seconds}s" \
            dsh --profile "$profile" --patch "$config_path" "$prompt"
    ) > "$log" 2>&1
    dsh_status=$?
    set -e
    end_ns=$(date +%s%N)
    wall_ms=$(((end_ns - start_ns) / 1000000))

    restore_private
    validity=valid
    if [[ "$dsh_status" -ne 0 && "$dsh_status" -ne 124 ]]; then
        validity=review_required
    fi
    {
        printf 'task_id=%s\n' "$task_id"
        printf 'dsh_status=%s\n' "$dsh_status"
        printf 'validity=%s\n' "$validity"
        printf 'wall_ms=%s\n' "$wall_ms"
        printf 'timeout_seconds=%s\n' "$timeout_seconds"
    } > "$metrics"

    PYTHONPATH="$repo_root/src" python3 -m harnessbench evaluate \
        "$task_dir" "$workspace" --private-root "$private_root/hidden-tests" \
        --output "$evaluation"
    score=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["completion_score"])' "$evaluation")
    ship_ready=$(python3 -c 'import json, sys; print(str(json.load(open(sys.argv[1]))["ship_ready"]).lower())' "$evaluation")
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$task_id" "$dsh_status" "$validity" "$wall_ms" "$score" "$ship_ready" \
        >> "$output_dir/summary.tsv"
done

restore_private
printf 'Quick-3 probe complete: %s\n' "$output_dir"
printf 'Summary: %s\n' "$output_dir/summary.tsv"
