#!/bin/bash

# Vault AI Chat Phase 1 Week 2 - E2E Test Runner
# This script starts both backend and frontend, then runs E2E tests

set -e

echo "=========================================="
echo "Vault AI Chat E2E Test Suite"
echo "=========================================="
echo ""

# Check if running in git bash or similar
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please ensure Node.js is installed."
    exit 1
fi

if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please ensure uv is installed."
    exit 1
fi

echo "✅ Dependencies verified"
echo ""

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install --legacy-peer-deps
cd ..
echo "✅ Frontend dependencies installed"
echo ""

echo "=========================================="
echo "IMPORTANT: You need 3 terminal windows:"
echo "=========================================="
echo ""
echo "Terminal 1 - Backend Server:"
echo "  cd \"C:\\project\\tenopa proposer\\-agent-master\""
echo "  uv run uvicorn app.main:app --reload --port 8000"
echo ""
echo "Terminal 2 - Frontend Dev Server:"
echo "  cd \"C:\\project\\tenopa proposer\\-agent-master\\frontend\""
echo "  npm run dev"
echo ""
echo "Terminal 3 - Run Tests (after servers are running):"
echo "  cd \"C:\\project\\tenopa proposer\\-agent-master\\frontend\""
echo "  npm run test:e2e:headed"
echo ""
echo "=========================================="
echo ""
echo "Waiting for your input. Start the servers in the other terminals,"
echo "then run the tests command above when both are ready."
echo ""
