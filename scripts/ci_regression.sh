#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-$HOME/.venvs/myenv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

ARTIFACT_DIR="${ARTIFACT_DIR:-examples/artifacts/ci_regression}"
rm -rf "$ARTIFACT_DIR"
mkdir -p "$ARTIFACT_DIR"
export PYTHONPATH="$ROOT_DIR/src:${PYTHONPATH:-}"

echo "== Python =="
"$PYTHON_BIN" --version

echo "== Unit/integration tests =="
"$PYTHON_BIN" -m pytest

echo "== Ruff =="
"$PYTHON_BIN" -m ruff check .

echo "== Spec validation =="
"$PYTHON_BIN" scripts/team_factory_cli.py validate team_specs/*.yaml

echo "== Golden snapshots =="
"$PYTHON_BIN" scripts/team_factory_cli.py golden-check team_specs/*.yaml

echo "== Deterministic mock evals =="
"$PYTHON_BIN" scripts/team_factory_cli.py eval team_specs/*.yaml \
  --out-dir "$ARTIFACT_DIR/evaluation_reports"

echo "== Trace comparison smoke =="
"$PYTHON_BIN" scripts/team_factory_cli.py trace-snapshot \
  team_specs/travel_planning_team.yaml \
  "Plan a short trip." \
  --workflow-id plan_trip \
  --out "$ARTIFACT_DIR/travel_snapshot_a.json"
"$PYTHON_BIN" scripts/team_factory_cli.py trace-snapshot \
  team_specs/travel_planning_team.yaml \
  "Plan a short trip." \
  --workflow-id plan_trip \
  --out "$ARTIFACT_DIR/travel_snapshot_b.json"
"$PYTHON_BIN" scripts/team_factory_cli.py trace-compare \
  "$ARTIFACT_DIR/travel_snapshot_a.json" \
  "$ARTIFACT_DIR/travel_snapshot_b.json"

echo "== Run-log smoke =="
"$PYTHON_BIN" scripts/team_factory_cli.py run-mock \
  team_specs/travel_planning_team.yaml \
  "Plan a short trip." \
  --workflow-id plan_trip \
  --run-log "$ARTIFACT_DIR/runs.jsonl" \
  --snapshot-out "$ARTIFACT_DIR/travel_snapshot_from_run.json" \
  >/dev/null
"$PYTHON_BIN" scripts/team_factory_cli.py run-log-list --run-log "$ARTIFACT_DIR/runs.jsonl"

echo "== API direct smoke =="
"$PYTHON_BIN" - <<'PY'
from team_factory.api import TeamFactoryAPI
api = TeamFactoryAPI()
health = api.handle("GET", "/health")
assert health.status_code == 200, health
order = api.handle("POST", "/workflows/order", {"spec_path": "team_specs/travel_planning_team.yaml"})
assert order.status_code == 200, order
assert order.body["agent_order"][0] == "preference_gatherer", order.body
print("API direct smoke passed")
PY

echo "CI regression suite passed. Artifacts written to $ARTIFACT_DIR"
