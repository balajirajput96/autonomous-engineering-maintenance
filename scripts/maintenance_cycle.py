#!/usr/bin/env python3
"""Durable, diagnostics-first hourly maintenance cycle for balajirajput96 repositories."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "targets.json"
STATE_DIR = ROOT / "state"
CYCLES_DIR = STATE_DIR / "cycles"
LATEST_PATH = STATE_DIR / "latest.json"
SUMMARY_PATH = STATE_DIR / "summary.tsv"


def run_gh(*args: str) -> Any:
    env = os.environ.copy()
    env.update({"GH_FORCE_TTY": "0", "NO_COLOR": "1", "TERM": "dumb"})
    command = ["gh", *args]
    completed = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout={completed.stdout[-1000:]}\nstderr={completed.stderr[-1000:]}"
        )
    return json.loads(completed.stdout) if completed.stdout.strip() else None


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return default


def summary_row(record: dict[str, Any]) -> str:
    counts = record.get("counts", {})
    return "\t".join([
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
    ]) + "\n"


def rewrite_summary_from_cycles() -> None:
    """Rebuild summary.tsv from immutable cycle records, repairing stale summaries."""
    by_cycle: dict[int, str] = {}
    for cycle_path in sorted(CYCLES_DIR.glob("cycle-*.json")):
        record = load_json(cycle_path, {})
        try:
            cycle_number = int(record["cycle"])
        except (KeyError, TypeError, ValueError):
            continue
        by_cycle[cycle_number] = summary_row(record)
    header = "cycle\tstarted_at\tfinished_at\tstatus\trepositories\topen_prs\tclean\tnon_clean\tconflicting\tunknown\terrors\n"
    SUMMARY_PATH.write_text(header + "".join(by_cycle[number] for number in sorted(by_cycle)))


def classify(pr: dict[str, Any]) -> str:
    if pr.get("mergeable") == "CONFLICTING" or pr.get("mergeStateStatus") == "DIRTY":
        return "conflicting"
    if pr.get("mergeable") == "MERGEABLE" and pr.get("mergeStateStatus") != "CLEAN":
        return "non_clean"
    if pr.get("mergeable") == "MERGEABLE" and pr.get("mergeStateStatus") == "CLEAN":
        return "clean"
    return "unknown"


def check_summary(repo: str, number: int) -> dict[str, int]:
    try:
        rollup = run_gh("pr", "view", str(number), "--repo", repo, "--json", "statusCheckRollup").get(
            "statusCheckRollup", []
        )
    except Exception as exc:  # diagnostics must continue when GitHub omits rollups
        return {"checks": 0, "failures": 0, "pending": 0, "error": str(exc)}
    failures = 0
    pending = 0
    for item in rollup:
        conclusion = str(item.get("conclusion") or "").upper()
        status = str(item.get("status") or "").upper()
        if conclusion in {"FAILURE", "ERROR", "CANCELLED", "TIMED_OUT"}:
            failures += 1
        if status not in {"COMPLETED", "SUCCESS"} and conclusion not in {"SUCCESS", "SKIPPED", "NEUTRAL"}:
            pending += 1
    return {"checks": len(rollup), "failures": failures, "pending": pending}


def main() -> int:
    config = load_json(CONFIG_PATH, {})
    latest = load_json(LATEST_PATH, {"cycle": 0, "active": True})
    previous_cycle = int(latest.get("cycle", 0))
    max_cycles = int(config.get("max_cycles", 2400))
    cycle = previous_cycle + 1
    now = datetime.now(timezone.utc)
    base_record: dict[str, Any] = {
        "cycle": cycle,
        "max_cycles": max_cycles,
        "started_at": now.isoformat(),
        "owner": config.get("owner", "balajirajput96"),
        "mode": config.get("action_mode", "diagnostics-first"),
        "actions": [],
        "errors": [],
    }
    if previous_cycle >= max_cycles:
        base_record.update({"active": False, "status": "cycle_limit_reached", "finished_at": now.isoformat()})
        CYCLES_DIR.mkdir(parents=True, exist_ok=True)
        (CYCLES_DIR / f"cycle-{cycle:04d}.json").write_text(json.dumps(base_record, indent=2) + "\n")
        LATEST_PATH.write_text(json.dumps(base_record, indent=2) + "\n")
        rewrite_summary_from_cycles()
        return 0

    try:
        owner = str(config.get("owner", "balajirajput96"))
        repo_names = run_gh("repo", "list", owner, "--limit", str(config.get("repository_limit", 1000)), "--json", "nameWithOwner")
        names = {item["nameWithOwner"] for item in repo_names}
        names.update(config.get("focus_repositories", []))
        records: list[dict[str, Any]] = []
        for repo in sorted(names):
            try:
                prs = run_gh(
                    "pr", "list", "--repo", repo, "--state", "open",
                    "--limit", str(config.get("open_pr_limit_per_repository", 1000)),
                    "--json", "number,title,headRefName,headRefOid,baseRefName,baseRefOid,state,mergeable,mergeStateStatus,isDraft,url",
                )
            except Exception as exc:
                base_record["errors"].append({"repository": repo, "error": str(exc)})
                continue
            for pr in prs:
                category = classify(pr)
                item = {
                    "repository": repo,
                    "number": pr["number"],
                    "title": pr.get("title", ""),
                    "head": pr.get("headRefName"),
                    "head_sha": pr.get("headRefOid"),
                    "base": pr.get("baseRefName"),
                    "base_sha": pr.get("baseRefOid"),
                    "state": pr.get("state"),
                    "mergeable": pr.get("mergeable"),
                    "merge_state": pr.get("mergeStateStatus"),
                    "draft": pr.get("isDraft", False),
                    "category": category,
                    "url": pr.get("url"),
                }
                if category in {"conflicting", "non_clean", "unknown"}:
                    item["checks"] = check_summary(repo, int(pr["number"]))
                records.append(item)

        counts: dict[str, int] = {}
        for item in records:
            counts[item["category"]] = counts.get(item["category"], 0) + 1
        base_record.update({
            "active": True,
            "status": "completed",
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "repository_count": len(names),
            "open_pr_count": len(records),
            "counts": counts,
            "records": records,
            "actions": [
                {"type": "inventory", "result": "completed"},
                {"type": "mutation_policy", "automatic_rebase": False, "automatic_rerun": False},
            ],
        })
    except Exception as exc:
        base_record.update({"active": True, "status": "failed", "finished_at": datetime.now(timezone.utc).isoformat()})
        base_record["errors"].append({"scope": "cycle", "error": str(exc)})
        print(str(exc), file=sys.stderr)

    CYCLES_DIR.mkdir(parents=True, exist_ok=True)
    cycle_path = CYCLES_DIR / f"cycle-{cycle:04d}.json"
    cycle_path.write_text(json.dumps(base_record, indent=2, sort_keys=True) + "\n")
    LATEST_PATH.write_text(json.dumps(base_record, indent=2, sort_keys=True) + "\n")
    rewrite_summary_from_cycles()
    print(json.dumps({k: base_record.get(k) for k in ("cycle", "status", "repository_count", "open_pr_count", "counts", "errors")}, sort_keys=True))
    return 0 if base_record.get("status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
