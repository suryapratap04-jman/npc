@echo off
setlocal enabledelayedexpansion

:: Get script directory and change context to project root
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\.."

echo [INFO] Running AI Knowledge Base Rebuild Pipeline...
.venv\Scripts\python -u scripts/pipeline/full_rebuild.py

if !errorlevel! equ 0 (
    echo.
    echo [SUCCESS] Rebuild pipeline completed successfully!
    exit /b 0
) else (
    echo.
    echo [ERROR] Rebuild pipeline failed!
    exit /b 1
)
