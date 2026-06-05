# CI Regression Commands

This project is intentionally deterministic before real LLM/tool execution is
introduced. The CI regression suite validates that the spec factory, mock runtime,
tool permission layer, memory layer, evaluation harness, API skeleton, traces,
run logs, and golden snapshots remain stable.

## Local command

```bash
scripts/ci_regression.sh
```

The script uses `~/.venvs/myenv/bin/python` by default when available. Override
with:

```bash
PYTHON_BIN=python scripts/ci_regression.sh
```

## What it runs

1. `pytest`
2. `ruff check .`
3. spec validation for all example teams
4. golden snapshot checks for all example teams
5. deterministic mock evaluations
6. trace snapshot/compare smoke test
7. run-log persistence smoke test
8. local API direct smoke test

## Artifacts

By default, generated artifacts are written under:

```text
examples/artifacts/ci_regression/
```

Override with:

```bash
ARTIFACT_DIR=/tmp/team_factory_ci scripts/ci_regression.sh
```

Generated artifacts are intentionally ignored by Git.

## GitHub Actions

`.github/workflows/ci.yml` runs the same script on pushes and pull requests to
`main`.

## Golden snapshot policy

If `golden-check` fails, do not blindly update snapshots. Investigate the diff.
Only run:

```bash
~/.venvs/myenv/bin/python scripts/team_factory_cli.py golden-update team_specs/*.yaml --approve
```

when the behavior change is intentional and reviewed.
