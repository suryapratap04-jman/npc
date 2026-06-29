#!/bin/bash
set -e

# Get script directory and change context to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../.."

echo "[INFO] Running AI Knowledge Base Rebuild Pipeline..."
if [ -d ".venv" ]; then
    .venv/bin/python -u scripts/pipeline/full_rebuild.py
else
    python -u scripts/pipeline/full_rebuild.py
fi

echo "[SUCCESS] Rebuild pipeline completed successfully!"
