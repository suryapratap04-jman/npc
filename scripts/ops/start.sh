#!/bin/bash

# Determine the directory of the script and change context to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

if [ ! -f .env ]; then
    echo "[INFO] .env file not found. Copying from .env.example..."
    cp .env.example .env
fi

echo "[INFO] Building and starting all containers via Docker Compose..."
docker compose up --build -d

echo "[INFO] Waiting for backend API to become healthy (this may take a few minutes if pulling models)..."
count=0
max_retries=100

until curl -s -f http://localhost:8000/api/health > /dev/null; do
    count=$((count+1))
    if [ $count -ge $max_retries ]; then
        echo -e "\n[WARNING] Reached maximum wait time. Services might still be starting in the background."
        echo "Check status using: docker compose ps"
        echo "View logs using: docker compose logs -f"
        exit 1
    fi
    echo -n "."
    sleep 3
done

echo -e "\n[SUCCESS] Backend API is healthy!"
echo "===================================================================="
echo "AI Resource Management Platform is running!"
echo ""
echo "- Next.js Frontend : http://localhost:3010"
echo "- FastAPI Backend  : http://localhost:8000"
echo "- Qdrant Dashboard : http://localhost:6333/dashboard"
echo "- Ollama API       : http://localhost:11434"
echo "===================================================================="
