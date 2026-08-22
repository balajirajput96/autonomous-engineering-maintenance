# Recovered Work and State Manifest

## Purpose

This manifest records only **verified, non-secret recovery metadata** for useful engineering work available during the master-mission audit. It preserves where future maintenance cycles should look first without copying credentials, raw terminal transcripts, private tokens, or unstable sandbox-only material into Git.

## Authoritative control-plane state

| Asset | Verified location | Authority rule |
| --- | --- | --- |
| Maintenance implementation | `main` branch of `balajirajput96/autonomous-engineering-maintenance` | Source code, workflow definition, policy, tests, and documentation are maintained on `main`. |
| Durable cycle state | `maintenance-state` branch of the same repository | `state/latest.json`, `state/cycles/`, and `state/summary.tsv` on this branch are the authoritative runtime checkpoint. Do not infer current cycle status from the copies on `main`. |
| Current observed checkpoint | `maintenance-state:state/latest.json` | The audit found completed cycle **28** with no cycle-level errors. The prior `main` copy intentionally remained at cycle 14. |
| Scope policy | `config/targets.json` | The engine is limited to 2,400 diagnostics-first cycles; unattended rebases, reruns, merges, credential changes, and deployments are disabled. |

## Recovered engineering evidence

| Artifact | Verified source | Fingerprint / status | Preservation treatment |
| --- | --- | --- | --- |
| GitHub repair validation report | `/home/ubuntu/github_repair_validation_report.md` | SHA-256 `81f5e91d641af8e4cdf8be187476a41488fa091907f6393f984944a464f139cd`; 31 lines | Copied into this repository as `docs/recovered-github-repair-validation-2026-08-21.md` because it contains verified, non-secret repair evidence. |
| B local checkout | `/home/ubuntu/repo-fixes/B` | Remote `balajirajput96/B`; commit `15ad4cd`; clean worktree | Reuse as a local validation checkout only; source of truth remains GitHub. |
| ai-agent-hub local checkout | `/home/ubuntu/repo-fixes/ai-agent-hub` | Remote `balajirajput96/ai-agent-hub`; commit `0cc4edc`; clean worktree | Reuse as a local validation checkout only; source of truth remains GitHub. |
| github-cockpit local checkout | `/home/ubuntu/repo-fixes/github-cockpit` | Remote `balajirajput96/github-cockpit`; commit `c6423ea`; clean worktree at audit time | Reuse as a local validation checkout only; source of truth remains GitHub. |
| Terminal archive | `/home/ubuntu/terminal_full_output/` | Present; contains historical command output from multiple sessions | Treat as sandbox-local and potentially sensitive. Preserve only metadata or deliberately redacted, reviewed extracts. Do not commit raw logs. |

## Recovery procedure for a new cycle

1. Fetch `origin/main` and `origin/maintenance-state` for this repository.
2. Load `state/latest.json` from `origin/maintenance-state`, not from the `main` checkout.
3. Read the latest cycle’s `next_action`, blockers, and scope reconciliation fields before re-inventorying work.
4. Reuse the local checkouts only after fetching their remote default branches and confirming a clean worktree.
5. Do not copy shell histories, API tokens, OAuth data, or unreviewed logs into Git.
6. For any code change, work on a repair branch, validate locally, push with a lease-protected update, and rely on GitHub CI before merge.

## Known repository-documentation correction

The older README referred to `/home/ubuntu/github_repair_workspace`, which is absent in the audited environment. The verified local repair workspace is `/home/ubuntu/repo-fixes`, supplemented by the report above. This reference should be corrected in the maintenance documentation.
