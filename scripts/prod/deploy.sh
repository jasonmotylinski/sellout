#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/var/projects/sellout"
VENV="$APP_DIR/.venv"

echo "==> Pulling latest code..."
cd "$APP_DIR"
git pull origin main

echo "==> Installing/updating dependencies..."
"$VENV/bin/pip" install -q -r requirements.txt

echo "==> Running tests..."
"$VENV/bin/pytest" tests/ -v --tb=short
if [ $? -ne 0 ]; then
  echo "ERROR: Tests failed. Aborting deployment."
  exit 1
fi

echo "==> Restarting service..."
sudo systemctl restart sellout

echo "==> Deployment complete."
