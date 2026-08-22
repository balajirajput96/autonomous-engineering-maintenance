#!/usr/bin/env python3
"""Regression tests for the durable maintenance state validator."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("state_contract", ROOT / "scripts" / "validate_state_contract.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def record(cycle: int) -> dict[str, object]:
    return {
        "cycle": cycle,
        "max_cycles": 3,
        "status": "completed",
        "started_at": f"2026-01-01T0{cycle}:00:00+00:00",
        "finished_at": f"2026-01-01T0{cycle}:01:00+00:00",
        "repository_count": 2,
        "open_pr_count": cycle,
        "counts": {"clean": cycle, "non_clean": 0, "conflicting": 0, "unknown": 0},
        "errors": [],
    }


def build_valid_state(root: Path) -> None:
    write_json(root / "config" / "targets.json", {"max_cycles": 3})
    rows = [MODULE.SUMMARY_HEADER]
    for cycle in (1, 2):
        item = record(cycle)
        write_json(root / "state" / "cycles" / f"cycle-{cycle:04d}.json", item)
        rows.append(MODULE.summary_row(item))
    write_json(root / "state" / "latest.json", record(2))
    (root / "state" / "summary.tsv").write_text("\n".join(rows) + "\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_valid_state(root)
        result = MODULE.validate(root)
        assert result["cycles"] == 2
        assert result["latest_cycle"] == 2

        summary = root / "state" / "summary.tsv"
        summary.write_text(summary.read_text().replace("\t2\t0\t0\t0\t0\n", "\t999\t0\t0\t0\t0\n"))
        try:
            MODULE.validate(root)
        except ValueError as exc:
            assert "summary.tsv" in str(exc)
        else:
            raise AssertionError("corrupted summary was accepted")
    print("state_contract_tests=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
