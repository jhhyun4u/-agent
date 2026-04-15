@echo off
REM Run Vault AI Chat E2E Tests
REM Prerequisites: Backend must be running on port 8000

cd /d "C:\project\tenopa proposer\-agent-master\frontend"

echo ========================================
echo Vault AI Chat E2E Test Suite
echo ========================================
echo.
echo ⚠️  IMPORTANT: Backend must be running!
echo.
echo If backend is not started yet:
echo   1. Open another terminal/command prompt
echo   2. Run: C:\project\tenopa proposer\-agent-master\start-backend.bat
echo   3. Wait for "Uvicorn running on http://0.0.0.0:8000"
echo   4. Then continue with this test runner
echo.
echo ========================================
echo.

REM The frontend will auto-start on port 3000 via Playwright config
echo Starting E2E tests with headed browser (visible)...
echo.

npm run test:e2e:headed

pause
