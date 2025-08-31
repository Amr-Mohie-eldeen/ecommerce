# Use Docker Compose in local/ by default
DC ?= docker compose -f local/docker-compose.yml

# Tooling (pinned to CI versions)
TOOLS_VENV := .venv-tools
BLACK := $(TOOLS_VENV)/bin/black
RUFF := $(TOOLS_VENV)/bin/ruff
BLACK_VERSION := 24.4.2
RUFF_VERSION := 0.5.5

.PHONY: help local-up local-down local-logs local-health seed-data test-local create-topics dev-venv check-apps tools-venv format lint install-git-hooks

help:
	@echo "Targets:"
	@echo "  local-up      Start local dependencies (Docker Compose)"
	@echo "  local-down    Stop and remove local dependencies"
	@echo "  local-logs    Tail logs from all services"
	@echo "  local-health  Check readiness of local services"
	@echo "  seed-data     Load sample data into local services"
	@echo "  test-local    Run local test suite against Compose"
	@echo "  create-topics Create local Kafka topics"
	@echo "  dev-venv      Create uv-managed venvs for apps"
	@echo "  check-apps    HTTP health checks for app containers"
	@echo "  tools-venv    Create .venv-tools with Black & Ruff"
	@echo "  format        Auto-format & autofix (Black, Ruff)"
	@echo "  lint          Verify formatting/lint (CI equivalent)"
	@echo "  install-git-hooks Install pre-commit hook to run format"

local-up:
	$(DC) up -d --remove-orphans

local-down:
	$(DC) down -v

local-logs:
	$(DC) logs -f --tail=200

local-health:
	bash scripts/local_health.sh

seed-data:
	bash scripts/seed_local.sh

test-local:
	bash scripts/test_local.sh

create-topics:
	bash scripts/create_topics.sh

dev-venv:
	bash scripts/bootstrap_uv_venvs.sh

check-apps:
	bash scripts/check_apps.sh

# ----- Tooling & Quality -----
tools-venv:
	python3 -m venv $(TOOLS_VENV) || python -m venv $(TOOLS_VENV)
	$(TOOLS_VENV)/bin/pip install --upgrade pip
	$(TOOLS_VENV)/bin/pip install black==$(BLACK_VERSION) ruff==$(RUFF_VERSION)

format: tools-venv
	@echo "Running Black and Ruff --fix..."
	$(BLACK) .
	$(RUFF) check --fix . || true
	@echo "Formatting complete."

lint: tools-venv
	@echo "Linting (non-mutating): Black --check, Ruff check"
	$(BLACK) --check .
	$(RUFF) check .

install-git-hooks:
	@echo "Installing pre-commit hook to run 'make format'..."
	@mkdir -p .git/hooks
	@printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail' '' \
	  'echo "[pre-commit] Running make format..."' \
	  'make format >/dev/null' \
	  'git add -A' \
	  > .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "Pre-commit hook installed. Use SKIP format via `git commit --no-verify` if needed."
