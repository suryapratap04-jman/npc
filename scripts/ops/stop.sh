#!/bin/bash

# Determine the directory of the script and change context to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

echo "[INFO] Stopping all containers..."
docker compose down
echo "[SUCCESS] All containers stopped."
