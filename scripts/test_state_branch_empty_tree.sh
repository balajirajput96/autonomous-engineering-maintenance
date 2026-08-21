#!/usr/bin/env bash
set -Eeuo pipefail

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT
source_repo="$workdir/source"
state_dir="$workdir/state-worktree"
mkdir -p "$source_repo"
git -C "$source_repo" init -q -b main
printf 'source\n' > "$source_repo/source.txt"
git -C "$source_repo" add source.txt
git -C "$source_repo" -c user.name=test -c user.email=test@example.invalid commit -q -m initial
git -C "$source_repo" worktree add --detach "$state_dir" HEAD >/dev/null
git -C "$state_dir" switch --orphan maintenance-state >/dev/null
git -C "$state_dir" rm -rf . 2>/dev/null || true
mkdir -p "$state_dir/state"
printf '{"execution_number":1}\n' > "$state_dir/state/execution-state.json"
git -C "$state_dir" add state/
git -C "$state_dir" -c user.name=test -c user.email=test@example.invalid commit -q -m state
[ "$(git -C "$state_dir" ls-tree --name-only HEAD state)" = "state" ]
git -C "$source_repo" worktree remove --force "$state_dir"
printf '%s\n' 'PASS: empty orphan state worktree can be initialized and committed safely.'
