@echo off
REM Start Vault AI Chat Backend Server
REM Backend must run on port 8000

cd /d "C:\project\tenopa proposer\-agent-master"

echo ========================================
echo Starting Vault AI Chat Backend
echo ========================================
echo.
echo Server will run on: http://localhost:8000
echo.

uv run uvicorn app.main:app --reload --port 8000

pause
