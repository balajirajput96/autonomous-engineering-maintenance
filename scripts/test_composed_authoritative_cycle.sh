#!/usr/bin/env bash
# Run one non-publishing maintenance cycle against the current branch and the
# authoritative maintenance-state branch, then discard the temporary state.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$(mktemp -d)"
state_dir="$(mktemp -d)"

cleanup() {
  git -C "$repo_root" worktree remove --force "$source_dir" 2>/dev/null || true
  git -C "$repo_root" worktree remove --force "$state_dir" 2>/dev/null || true
  rmdir "$source_dir" "$state_dir" 2>/dev/null || true
}
trap cleanup EXIT

: "${GH_TOKEN:?GH_TOKEN is required for the authenticated GitHub inventory}"
git -C "$repo_root" fetch origin maintenance-state
git -C "$repo_root" worktree add --detach "$source_dir" HEAD
git -C "$repo_root" worktree add --detach "$state_dir" origin/maintenance-state

previous_cycle="$(jq -r '.cycle' "$state_dir/state/latest.json")"
rm -rf "$source_dir/state"
cp -R "$state_dir/state" "$source_dir/state"

(
  cd "$source_dir"
  python3 scripts/maintenance_cycle.py
  python3 scripts/validate_state_contract.py
)

observed_cycle="$(jq -r '.cycle' "$source_dir/state/latest.json")"
expected_cycle="$((previous_cycle + 1))"
test "$observed_cycle" = "$expected_cycle"
printf 'composed_authoritative_cycle=pass previous=%s observed=%s\n' "$previous_cycle" "$observed_cycle"
