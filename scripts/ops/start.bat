@echo off
setlocal enabledelayedexpansion

:: Get script directory and change context to project root
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\.."

if not exist .env (
    echo [INFO] .env file not found. Copying from .env.example...
    copy .env.example .env
)

echo [INFO] Building and starting all containers via Docker Compose...
docker compose up --build -d

echo [INFO] Waiting for backend API to become healthy (this may take a few minutes if pulling models)...
set /a count=0
set /a max_retries=100

:loop
curl -s -f http://localhost:8000/api/health >nul 2>&1
if !errorlevel! equ 0 (
    echo.
    echo [SUCCESS] Backend API is healthy!
    echo ====================================================================
    echo AI Resource Management Platform is running!
    echo.
    echo - Next.js Frontend : http://localhost:3000
    echo - FastAPI Backend  : http://localhost:8000
    echo - Qdrant Dashboard : http://localhost:6333/dashboard
    echo - Ollama API       : http://localhost:11434
    echo ====================================================================
    exit /b 0
)

set /a count+=1
if !count! geq !max_retries! (
    echo.
    echo [WARNING] Reached maximum wait time. Services might still be starting up in the background.
    echo Check status using: docker compose ps
    echo View logs using: docker compose logs -f
    exit /b 1
)

<nul set /p =.
ping -n 4 127.0.0.1 >nul
goto loop
