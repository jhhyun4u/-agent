@echo off
REM ============================================================
REM 인트라넷 KB 매월 자동 동기화 — Windows 작업 스케줄러 등록
REM
REM 사내 PC에서 관리자 권한으로 실행:
REM   scripts\setup_monthly_sync.bat
REM
REM 등록 후 확인:
REM   schtasks /query /tn "TenopIntranetSync"
REM
REM 삭제:
REM   schtasks /delete /tn "TenopIntranetSync" /f
REM
REM 수동 즉시 실행:
REM   schtasks /run /tn "TenopIntranetSync"
REM ============================================================

SET SCRIPT_DIR=%~dp0
SET PYTHON=python
SET SCRIPT=%SCRIPT_DIR%migrate_intranet.py
SET ENV_FILE=%SCRIPT_DIR%migrate_intranet.env
SET LOG_DIR=%SCRIPT_DIR%..\logs
SET TASK_NAME=TenopIntranetSync

REM 로그 디렉터리 생성
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM 환경 변수 파일 확인
if not exist "%ENV_FILE%" (
    echo [오류] %ENV_FILE% 파일이 없습니다.
    echo migrate_intranet.env.example을 복사하여 설정하세요.
    pause
    exit /b 1
)

echo.
echo ━━━ 인트라넷 KB 매월 자동 동기화 등록 ━━━
echo.
echo  작업 이름: %TASK_NAME%
echo  실행 일정: 매월 1일 09:00
echo  스크립트:  %SCRIPT%
echo  로그:      %LOG_DIR%\intranet_sync.log
echo.

REM 기존 작업 제거 (업데이트용)
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel%==0 (
    echo 기존 작업을 업데이트합니다...
    schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
)

REM 작업 스케줄러 등록: 매월 1일 09:00 실행
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%PYTHON%\" \"%SCRIPT%\" --incremental --triggered-by scheduler >> \"%LOG_DIR%\intranet_sync.log\" 2>&1" ^
    /sc monthly /d 1 /st 09:00 ^
    /rl HIGHEST ^
    /f

if %errorlevel%==0 (
    echo.
    echo [성공] 매월 1일 09:00 자동 동기화가 등록되었습니다.
    echo.
    echo  확인:    schtasks /query /tn "%TASK_NAME%" /v
    echo  즉시실행: schtasks /run /tn "%TASK_NAME%"
    echo  삭제:    schtasks /delete /tn "%TASK_NAME%" /f
) else (
    echo.
    echo [실패] 작업 등록에 실패했습니다. 관리자 권한으로 다시 실행하세요.
)

echo.
pause
