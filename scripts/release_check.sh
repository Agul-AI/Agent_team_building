#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

scripts/ci_regression.sh

echo "== Release checklist reminder =="
echo "Review docs/release_checklist.md before tagging or merging release changes."
echo "Confirm no real LLM/tool execution has been introduced without updated safety gates."
