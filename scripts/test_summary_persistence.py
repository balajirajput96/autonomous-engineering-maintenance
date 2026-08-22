#!/usr/bin/env python3
"""Verify the cycle-summary reconstruction contract without calling GitHub."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("maintenance_cycle.py")
spec = importlib.util.spec_from_file_location("maintenance_cycle", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    cycles = root / "cycles"
    cycles.mkdir()
    summary = root / "summary.tsv"
    module.CYCLES_DIR = cycles
    module.SUMMARY_PATH = summary
    for cycle, errors in ((3, []), (1, [{"scope": "test"}]), (2, [])):
        (cycles / f"cycle-{cycle:04d}.json").write_text(
            json.dumps(
                {
                    "cycle": cycle,
                    "started_at": f"2026-01-01T00:0{cycle}:00+00:00",
                    "finished_at": f"2026-01-01T00:0{cycle}:30+00:00",
                    "status": "completed",
                    "repository_count": 10 + cycle,
                    "open_pr_count": 20 + cycle,
                    "counts": {"clean": cycle, "non_clean": 1, "conflicting": 0, "unknown": 0},
                    "errors": errors,
                }
            )
            + "\n"
        )
    module.rewrite_summary_from_cycles()
    rows = summary.read_text().splitlines()
    assert rows[0] == "cycle\tstarted_at\tfinished_at\tstatus\trepositories\topen_prs\tclean\tnon_clean\tconflicting\tunknown\terrors"
    assert [row.split("\t")[0] for row in rows[1:]] == ["1", "2", "3"]
    assert rows[1].split("\t")[-1] == "1"
    assert rows[3].split("\t")[5] == "23"
    assert all("\\t" not in row for row in rows)

print("summary_persistence=pass")
