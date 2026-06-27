@echo off
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\.."

echo [INFO] Stopping all containers...
docker compose down
echo [SUCCESS] All containers stopped.
