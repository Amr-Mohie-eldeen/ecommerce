#!/usr/bin/env bash
set -euo pipefail

echo "Running local tests"

# Create an isolated venv for tests to avoid polluting app deps
TEST_VENV=".venv-testtools"
if [ ! -d "$TEST_VENV" ]; then
  python3 -m venv "$TEST_VENV" || python -m venv "$TEST_VENV"
fi
"$TEST_VENV"/bin/pip install --upgrade pip >/dev/null
"$TEST_VENV"/bin/pip install pytest httpx >/dev/null

echo "Executing pytest under apps/*/tests"
"$TEST_VENV"/bin/pytest -q apps

echo "Tests complete."
