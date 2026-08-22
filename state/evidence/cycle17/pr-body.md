## Summary

This continuation resumes from the cycle-16 checkpoint and records the current diagnostics-first cycle 17 inventory. It reuses the existing maintenance repository, script, state contract, and validation tests.

The cycle observed 254 owner repositories and 309 open pull requests. It recorded 287 clean records, 18 non-clean records, and 4 unknown mergeability records. The evidence directory preserves the current default-branch snapshot, targeted REST rechecks, check-run observations, affected ruleset diagnostics, validation output, and the root cause of the summary persistence defect.

## Bounded repair

The cycle-16 branch contained an older script that replaced `state/summary.tsv` with only the newest row. The already-merged main-line implementation reconstructs the summary from all immutable cycle files. This branch restores that implementation, rebuilds the summary, and records cycle 17. No engineering repository was changed. No pull request was rebased, rerun, merged, closed, or modified. Authentication, required reviews, branch protections, runner limits, and semantic-conflict safety were preserved.

## Validation

The state contract validator passed for 17 immutable cycles. The state-contract regression test passed. The summary-persistence regression test passed. The composed-authoritative-cycle test passed after the validator scripts were tracked in the commit; its temporary run completed as a separate composed check and did not mutate remote state.

## Explicit blockers

The 14 affected `vscode-live-server-plus-plus` pull requests remain blocked by the active ruleset requiring 10 approvals, code-owner review, last-push approval, resolved threads, linear history, signed commits, and merge-only integration. The current codex candidates remain unsettled while checks are pending or mergeability is unknown. Newly observed unstable records remain diagnostics-only because no safe semantic repair is proven. External-owner protection and required-review boundaries remain read-only.

## Continuation

The next cycle must load `state/latest.json`, recheck only newly changed non-clean or unknown records and check progress, preserve the review-only boundary, and stop additional work at cycle 2400 by recording a terminal state.
