# Autonomous Engineering Maintenance

This private repository is the durable control plane for the existing `balajirajput96` engineering-repair workflow. It stores the maintenance configuration, the deterministic cycle engine, GitHub Actions scheduling, and machine-readable state. Existing repository repairs, reports, diagnostics, and validation artifacts remain in `/home/ubuntu/github_repair_workspace`; this repository reuses their operating assumptions rather than copying their large logs into every cycle.

## Execution model

A GitHub Actions workflow runs at minute 17 of every hour and can also be started manually. Each run loads the previous state from `state/latest.json`, increments the cycle number, inventories all open pull requests across the account, classifies each PR as `clean`, `non_clean`, `conflicting`, or `unknown`, collects check-rollup summaries for actionable or uncertain PRs, writes `state/cycles/cycle-NNNN.json`, updates `state/latest.json`, and appends the current summary to `state/summary.tsv`.

The configured cap is **2,400 cycles**, which represents 100 days at hourly frequency. Once the cap is reached, the engine records `cycle_limit_reached` and stops doing inventory work. The workflow retains the latest state and the per-cycle JSON records so later cycles can resume from the last durable number rather than restarting from zero.

## Safety defaults

The current configuration is deliberately **diagnostics-first**. Automatic rebases, automatic workflow reruns, force pushes, secret changes, connector changes, and production deployments are disabled. The engine records recommended actions and evidence; source changes are made only through a bounded, reviewable repair operation. This prevents an unattended hourly job from rewriting a branch, rerunning an expensive workflow, or changing credentials merely because a transient GitHub API response changed.

A future mutation-enabled mode must add explicit policy, per-repository allowlists, retry budgets, clean-worktree checks, lease-protected pushes, and a human-reviewed GitHub App or token with only the required scopes. It must also preserve the current branch head and base SHA in state before changing anything.

## Authentication

The workflow prefers a repository secret named `AUTOMATION_GH_TOKEN` and falls back to the workflow-provided `github.token` when that secret is unavailable. The optional token must be supplied through GitHub’s secret store and must have authorized read access to every private repository being inventoried. The fallback allows public-repository diagnostics to continue, while access failures are recorded in the durable cycle state. The workflow never writes token values to state, logs, or configuration and does not attempt mutations.

## Verification snapshot

The first local cycle completed with 249 repositories, 303 open pull requests, 287 clean classifications, 16 non-clean classifications, zero conflicts, and zero errors. The first remote `workflow_dispatch` run also completed successfully and committed cycle 2, which recorded 217 repositories, 301 open pull requests, 285 clean classifications, 16 non-clean classifications, zero conflicts, zero unknowns, and zero errors. These numbers are evidence from the saved state files, not fixed expectations; subsequent cycles must be evaluated from their own records.

## State contract

`config/targets.json` is the auditable policy file. `state/latest.json` is the most recent complete or failed cycle. `state/cycles/cycle-NNNN.json` is an immutable per-cycle record. `state/summary.tsv` is the compact append-style index suitable for quick inspection. The JSON record contains timestamps, cycle number, maximum cycle count, repository count, open-PR count, category counts, check summaries, errors, and the mutation policy used for the cycle.

## Local validation

Run the cycle locally with an authenticated GitHub CLI session:

```bash
GH_TOKEN="$(gh auth token)" python3 scripts/maintenance_cycle.py
python3 -m json.tool state/latest.json >/dev/null
```

The local run should be performed from a clean branch when its state is intended to be committed. The workflow itself validates JSON and TSV state before committing.

## Existing environment preservation

The previous repair workspace contains the authoritative repair report, PR inventories, CI diagnostics, CLI smoke results, integration audit, and historical repair scripts. The maintenance repository does not delete or rewrite those files. Its role is to provide a small, durable hourly state machine that points future work toward the latest observed state.
