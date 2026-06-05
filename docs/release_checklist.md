# Lightweight Release Checklist

Use this before tagging a release, merging a major platform change, or introducing
real LLM/tool execution.

## Required deterministic checks

- [ ] Run `scripts/ci_regression.sh` locally.
- [ ] Confirm `pytest` passes.
- [ ] Confirm `ruff check .` passes.
- [ ] Confirm all team specs validate.
- [ ] Confirm `golden-check` passes.
- [ ] Confirm mock evaluations pass for scientific, trading, and travel teams.
- [ ] Confirm trace comparison and run-log smoke tests pass.
- [ ] Confirm local API direct smoke test passes.

## Golden snapshot review

- [ ] If golden snapshots changed, inspect diffs manually.
- [ ] Confirm snapshot changes are intentional.
- [ ] Update goldens only with `golden-update --approve`.
- [ ] Include the reason for golden updates in the commit/PR description.

## Safety review before real LLM/tool execution

- [ ] Confirm no high-impact action can execute without explicit approval.
- [ ] Confirm real LLM usage is behind `TEAM_FACTORY_ENABLE_REAL_LLM=1` and explicit config/CLI opt-in.
- [ ] Confirm real LLM requests do not include tools unless a later tool-calling phase has been reviewed.
- [ ] Confirm `run-llm-smoke` requires no-tools and simulation-only acknowledgements.
- [ ] Confirm tool manifests have risk and side-effect levels.
- [ ] Confirm critical/high-impact tools require approval.
- [ ] Confirm run/audit logging captures proposed tool usage.
- [ ] Confirm financial/trading flows remain research/simulation-only.
- [ ] Confirm privacy/redaction policy is updated for any new memory writes.

## Documentation review

- [ ] Update `README.md` if user-facing commands changed.
- [ ] Update phase docs if architecture changed.
- [ ] Update `docs/implementation_progress.md`.
- [ ] Update the local site under `site/`.

## Release notes

Record:

- release version or commit SHA
- summary of changes
- validation command output
- golden snapshot changes, if any
- known limitations
- next recommended step
