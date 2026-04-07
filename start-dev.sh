#!/bin/bash
# 프론트엔드 + 백엔드 동시 실행 스크립트

echo "=== 용역제안 Coworker 개발 서버 시작 ==="

# 백엔드 (포트 8000)
echo "[1/2] 백엔드 서버 시작 (port 8000)..."
cd "C:/project/tenopa proposer/-agent-master"
uv run uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# 프론트엔드 (포트 3000)
echo "[2/2] 프론트엔드 서버 시작 (port 3000)..."
cd "C:/project/tenopa proposer/-agent-master/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=== 서버 실행 완료 ==="
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "종료: Ctrl+C"

# Ctrl+C로 둘 다 종료
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
