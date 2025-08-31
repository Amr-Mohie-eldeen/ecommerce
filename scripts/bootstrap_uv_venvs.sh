#!/usr/bin/env bash
set -euo pipefail

# Install uv locally if missing
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

APPS=(apps/catalog-api apps/orders-api apps/recommender-svc apps/indexer-worker)

for app in "${APPS[@]}"; do
  if [[ -f "$app/requirements.txt" ]]; then
    echo "Setting up venv for $app"
    uv venv "$app/.venv"
    . "$app/.venv/bin/activate"
    uv pip install -r "$app/requirements.txt"
    deactivate || true
  fi
done

echo "uv venvs ready."

