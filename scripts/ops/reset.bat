@echo off
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\.."

echo [WARNING] This will stop containers and delete database and Qdrant named volumes.
echo [INFO] Resetting all containers and data...
docker compose down -v
echo [SUCCESS] Volumes cleared. Running start script...
call "%SCRIPT_DIR%start.bat"
