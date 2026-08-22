#!/usr/bin/env python3
"""Validate the durable state contract for the maintenance control plane."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SUMMARY_HEADER = (
    "cycle\tstarted_at\tfinished_at\tstatus\trepositories\topen_prs\t"
    "clean\tnon_clean\tconflicting\tunknown\terrors"
)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise ValueError(f"missing required state file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"state document must be a JSON object: {path}")
    return value


def integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc


def summary_row(record: dict[str, Any]) -> str:
    counts = record.get("counts", {})
    if not isinstance(counts, dict):
        counts = {}
    return "\t".join(
        [
            str(record.get("cycle", "")),
            str(record.get("started_at", "")),
            str(record.get("finished_at", "")),
            str(record.get("status", "failed")),
            str(record.get("repository_count", 0)),
            str(record.get("open_pr_count", 0)),
            str(counts.get("clean", 0)),
            str(counts.get("non_clean", 0)),
            str(counts.get("conflicting", 0)),
            str(counts.get("unknown", 0)),
            str(len(record.get("errors") or [])),
        ]
    )


def validate(root: Path, allow_stale_source_snapshot: bool = False) -> dict[str, int]:
    config = load_json(root / "config" / "targets.json")
    state_dir = root / "state"
    cycles_dir = state_dir / "cycles"
    latest = load_json(state_dir / "latest.json")
    max_cycles = integer(config.get("max_cycles"), "config.max_cycles")
    latest_cycle = integer(latest.get("cycle"), "latest.cycle")
    if max_cycles < 1:
        raise ValueError("config.max_cycles must be positive")
    if latest_cycle < 0 or latest_cycle > max_cycles:
        raise ValueError("latest.cycle must be between 0 and config.max_cycles")

    records: dict[int, dict[str, Any]] = {}
    for path in sorted(cycles_dir.glob("cycle-*.json")):
        record = load_json(path)
        cycle = integer(record.get("cycle"), f"{path}.cycle")
        expected_name = f"cycle-{cycle:04d}.json"
        if path.name != expected_name:
            raise ValueError(f"cycle filename does not match recorded cycle: {path.name}")
        if cycle < 1 or cycle > max_cycles:
            raise ValueError(f"cycle {cycle} is outside 1..{max_cycles}")
        if cycle in records:
            raise ValueError(f"duplicate cycle record: {cycle}")
        records[cycle] = record

    numbers = sorted(records)
    if numbers and numbers != list(range(numbers[0], numbers[-1] + 1)):
        raise ValueError("cycle records contain a gap")
    if numbers and numbers[0] != 1:
        raise ValueError("cycle records must begin at cycle 1")
    if latest_cycle and latest_cycle not in records:
        raise ValueError("latest.cycle must reference an immutable cycle record")
    if not allow_stale_source_snapshot and numbers and numbers[-1] != latest_cycle:
        raise ValueError("latest.cycle must match the newest immutable cycle record")
    if latest_cycle and not numbers:
        raise ValueError("latest.cycle is nonzero but no immutable cycle records exist")
    if latest.get("status") == "cycle_limit_reached" and latest_cycle != max_cycles:
        raise ValueError("cycle_limit_reached is valid only at the configured cap")

    summary_path = state_dir / "summary.tsv"
    try:
        lines = summary_path.read_text().splitlines()
    except FileNotFoundError as exc:
        raise ValueError(f"missing required state file: {summary_path}") from exc
    if not lines or lines[0] != SUMMARY_HEADER:
        raise ValueError("summary.tsv header does not match the state contract")
    if allow_stale_source_snapshot:
        summary_numbers: list[int] = []
        for raw_row in lines[1:]:
            fields = raw_row.split("\t")
            if not fields:
                raise ValueError("summary.tsv contains an empty row")
            cycle = integer(fields[0], "summary cycle")
            if cycle not in records:
                raise ValueError("summary.tsv references an absent immutable cycle record")
            if raw_row != summary_row(records[cycle]):
                raise ValueError("summary.tsv row does not match its immutable cycle record")
            summary_numbers.append(cycle)
        if summary_numbers != sorted(set(summary_numbers)):
            raise ValueError("summary.tsv source snapshot must contain unique ascending cycle rows")
    else:
        expected_rows = [summary_row(records[number]) for number in numbers]
        if lines[1:] != expected_rows:
            raise ValueError("summary.tsv does not exactly match immutable cycle records")

    return {
        "cycles": len(records),
        "latest_cycle": latest_cycle,
        "max_cycles": max_cycles,
        "allow_stale_source_snapshot": int(allow_stale_source_snapshot),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--allow-stale-source-snapshot",
        action="store_true",
        help="Validate checked-in source fixtures that intentionally lag the authoritative maintenance-state branch.",
    )
    args = parser.parse_args()
    try:
        result = validate(args.root.resolve(), args.allow_stale_source_snapshot)
    except ValueError as exc:
        print(f"state_contract=failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"state_contract": "passed", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
