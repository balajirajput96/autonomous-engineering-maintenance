# Cycle 17 Evidence and Decision Record

This directory records the diagnostics-first continuation from cycle 16. The inventory ran from the existing maintenance script against the authenticated owner account, with no engineering-repository mutations, automatic rebases, check reruns, merges, closes, review bypasses, authentication changes, or branch-protection changes.

## Current inventory

The cycle-17 engine observed **254 owner repositories**, **309 open pull requests**, **287 clean records**, **18 non-clean records**, and **4 records whose mergeability remained unknown at the observation point**. The current default-branch snapshot covers 217 repositories returned by the owner-repository REST pages; pull-request records retain each observed base branch and SHA. The difference between repository-page count and engine scope is retained as evidence rather than inferred away because the established engine also includes configured focus repositories.

The 14 pull requests in `vscode-live-server-plus-plus` are mergeable but blocked by the active `Balaji Rajput` ruleset. The current ruleset requires 10 approving reviews, code-owner review, approval from the last pusher, resolved review threads, linear history, signed commits, and merge-only integration. No bypass is authorized. The current REST recheck found no completed failing check for the newly observed `ai-assistant-app#1` or `github-mcp-server-#61`; the latter still has seven in-progress checks. The four `codex` records remain unsettled at the observation point because their checks are still running or the CLI reports unknown mergeability. No rerun or repair is justified by the evidence.

## Recoverable state-contract issue

The cycle-16 continuation branch contained an older maintenance script that replaced `summary.tsv` with only the newest row. Running the cycle-17 inventory therefore created a real state-contract failure. The merged main-line implementation already contained the smallest safe fix: reconstruct the summary from all immutable cycle files. That implementation and its existing validators were restored on the new continuation branch, the summary was rebuilt with the repository’s own function, and the state validator plus state-contract and summary-persistence regression tests passed. The composed-authoritative-cycle test reached its engine assertions but then failed because its temporary source worktree did not contain `scripts/validate_state_contract.py`; this is retained as a test-harness/path limitation, not represented as a passing validation claim.

## Evidence files

| File | Purpose |
| --- | --- |
| `targeted-recheck.ndjson` | REST pull-request and check-run observations for prior non-clean and conflicting candidates. |
| `default-branch-refs.json` | Owner-repository default-branch snapshot. |
| `protection.ndjson` | Read-only branch-protection and ruleset endpoint observations for affected bases. |
| `non-clean.ndjson` | Concise cycle-17 non-clean records. |
| `unknown.ndjson` | Concise cycle-17 unknown records. |
| `postscan-focus.ndjson` | Current REST recheck for newly non-clean records and the open continuation PR. |
| `engine-stdout.txt` and `engine-stderr.txt` | Existing engine output and error stream. |
| `validation-before-repair.txt` and `validation-diagnosis.txt` | Initial validation failure and root-cause evidence. |
| `validation-after-summary-repair.txt` | Validation results after the bounded summary repair. |
| `summary-root-cause.txt` | Direct comparison showing the older script’s single-row summary behavior. |

## Continuation directive

Continue from the published cycle-17 checkpoint. Re-load this state, recheck only newly changed non-clean or unknown records and progress on current checks, preserve the diagnostics-first boundary, and do not rebase, rerun, merge, close, modify protected branches, or bypass required reviews without a concrete and separately verified safe repair. Stop additional work once the configured cycle reaches 2400 by recording the terminal state.
