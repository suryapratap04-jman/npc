#!/bin/bash

# Determine the directory of the script and change context to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

echo "[WARNING] This will stop containers and delete database and Qdrant named volumes."
echo "[INFO] Resetting all containers and data..."
docker compose down -v
echo "[SUCCESS] Volumes cleared. Running start script..."
chmod +x "$SCRIPT_DIR/start.sh"
"$SCRIPT_DIR/start.sh"
