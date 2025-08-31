# Use Docker Compose in local/ by default
DC ?= docker compose -f local/docker-compose.yml

.PHONY: help local-up local-down local-logs local-health seed-data test-local create-topics dev-venv check-apps

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
