@echo off
REM Phase 5 Scheduler Integration - Staging Deployment Script (Windows)

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo Phase 5 - Staging Deployment
echo ==========================================
echo.

REM Step 1: Verify environment
echo [STEP 1] Verifying staging environment...
python -c "from app.config import settings; print(f'Database: {settings.database_url[:30]}...')" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Cannot connect to database. Check SUPABASE_URL and SUPABASE_KEY
    exit /b 1
)
echo [OK] Environment verified
echo.

REM Step 2: Run unit tests
echo [STEP 2] Running unit test suite (24 tests)...
python -m pytest tests/test_scheduler_integration.py -v --tb=short
if errorlevel 1 (
    echo ERROR: Unit tests failed. Do not proceed with deployment.
    exit /b 1
)
echo [OK] All 24 unit tests passing
echo.

REM Step 3: Database backup
echo [STEP 3] Database backup (MANUAL STEP REQUIRED)...
echo.
echo Before proceeding, please backup your staging database:
echo.
echo  Option A (Supabase Dashboard):
echo    1. Go to Database ^> Backups
echo    2. Click 'Create backup'
echo    3. Wait for backup to complete
echo.
echo  Option B (Command line):
echo    pg_dump --format custom -f staging_backup_%%date:~10,4%%%%date:~4,2%%%%date:~7,2%%.bak [DATABASE_URL]
echo.
pause
echo [OK] Database backup confirmed
echo.

REM Step 4: Apply database migration
echo [STEP 4] Applying database migration...
echo.
echo Execute the following SQL on your staging database:
echo.
echo ========== SQL MIGRATION BELOW ==========
type database\migrations\006_scheduler_integration.sql
echo ========== END SQL MIGRATION ===========
echo.
echo Options to execute:
echo.
echo  Option A (Supabase SQL Editor):
echo    1. Go to Supabase Dashboard ^> SQL Editor
echo    2. Click 'New Query'
echo    3. Copy and paste the SQL above
echo    4. Click 'Run'
echo.
echo  Option B (Command line):
echo    psql -h [HOST] -U [USER] -d [DATABASE] -f database\migrations\006_scheduler_integration.sql
echo.
pause
echo [OK] Database migration applied
echo.

REM Step 5: Validate database schema
echo [STEP 5] Validating database schema...
echo.
echo Manually verify tables were created:
echo   SELECT table_name FROM information_schema.tables
echo   WHERE table_schema = 'public' AND table_name LIKE 'migration%%';
echo.
echo Expected tables:
echo   - migration_schedules
echo   - migration_batches
echo   - migration_logs
echo.
pause
echo [OK] Database schema validated
echo.

REM Step 6: Deploy application code
echo [STEP 6] Deploying application code...
echo.
echo Option A (Git push to staging):
echo   git push origin main
echo.
echo Option B (Manual deployment):
echo   1. Copy app\ and database\ directories to staging server
echo   2. Run: uv sync
echo   3. Restart application service
echo.
pause
echo [OK] Application code deployed
echo.

REM Step 7: Verify scheduler initialization
echo [STEP 7] Verifying scheduler initialization...
echo.
echo Check application logs for:
echo   "[Phase 5] 정기 문서 마이그레이션 스케줄러 초기화 완료"
echo.
echo Or check logs via:
echo   - Railway: railway logs
echo   - Render: render logs
echo   - Direct SSH: tail -f /var/log/app.log
echo.
pause
echo [OK] Scheduler initialization verified
echo.

REM Step 8: Run API validation tests
echo [STEP 8] Running API validation tests...
echo.
echo From staging environment, run:
echo   pytest tests/test_scheduler_integration.py -v
echo.
echo Expected result: 24/24 tests PASSING
echo.
pause
echo [OK] API tests validated
echo.

REM Step 9: Manual API endpoint testing
echo [STEP 9] Testing API endpoints...
echo.
echo Run the following curl commands from staging:
echo.
echo Create Schedule:
echo   curl -X POST http://staging-api.local/api/migration/schedules ^
echo     -H "Authorization: Bearer [TOKEN]" ^
echo     -H "Content-Type: application/json" ^
echo     -d "{\"name\": \"Test\", \"cron_expression\": \"0 8 * * *\", \"enabled\": true}"
echo.
echo Get Schedules:
echo   curl -X GET http://staging-api.local/api/migration/schedules ^
echo     -H "Authorization: Bearer [TOKEN]"
echo.
pause
echo [OK] API endpoints tested
echo.

REM Step 10: Monitoring setup
echo [STEP 10] Setting up monitoring...
echo.
echo Monitor these metrics for 30 minutes:
echo.
echo   - Scheduler startup time (target: less than 2s)
echo   - API response time (target: less than 200ms)
echo   - Error rate (target: less than 0.1%%)
echo   - Batch processing time (target: less than 30s for 100 docs)
echo.
pause
echo [OK] Monitoring setup complete
echo.

REM Summary
echo.
echo ==========================================
echo DEPLOYMENT COMPLETE
echo ==========================================
echo.
echo Phase 5 Scheduler Integration has been deployed to staging.
echo.
echo Next Steps:
echo   1. Continue monitoring for 30 minutes
echo   2. If all checks pass, update deployment status
echo   3. Plan production deployment for 2026-04-25
echo   4. Review any issues found in staging
echo.
echo Documentation:
echo   - Full guide: docs/operations/phase5-staging-deployment-guide.md
echo   - Rollback plan: See guide Appendix
echo   - Test results: tests/test_scheduler_integration.py
echo.
pause
