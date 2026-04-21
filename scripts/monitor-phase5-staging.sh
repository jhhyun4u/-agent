#!/bin/bash

# Phase 5 Staging Deployment - 24h Monitoring Script
# Execution: 2026-04-21 11:00 - 2026-04-22 11:00 UTC
# Purpose: Continuous health checks + metrics collection

set -e

# Configuration
API_BASE="https://api.tenopa.co.kr"
STAGING_BASE="https://staging.tenopa.co.kr"
HEALTH_ENDPOINT="/api/scheduler/health"
AUTH_TOKEN="${PROD_TOKEN}"
LOG_FILE="monitoring-$(date +%Y%m%d-%H%M%S).log"
METRICS_FILE="metrics-$(date +%Y%m%d).jsonl"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== Phase 5 Staging Deployment - 24h Monitoring Start ===" | tee -a "$LOG_FILE"
echo "Start Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" | tee -a "$LOG_FILE"
echo "Log File: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Function: Health Check
health_check() {
    local endpoint="$1"
    local label="$2"

    echo "[$(date -u '+%H:%M:%S')] Checking $label..." | tee -a "$LOG_FILE"

    local response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer ${AUTH_TOKEN}" \
        "$endpoint" 2>/dev/null || echo "error\n0")

    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ $label: 200 OK${NC}" | tee -a "$LOG_FILE"
        echo "$body" >> "$METRICS_FILE"
        return 0
    else
        echo -e "${RED}✗ $label: $http_code ERROR${NC}" | tee -a "$LOG_FILE"
        return 1
    fi
}

# Function: Check Error Rate
check_error_rate() {
    echo "[$(date -u '+%H:%M:%S')] Analyzing error logs..." | tee -a "$LOG_FILE"

    # Query error logs from last hour
    local error_count=$(grep -c "ERROR\|CRITICAL" /var/log/app.log 2>/dev/null || echo "0")

    if [ "$error_count" -gt "10" ]; then
        echo -e "${YELLOW}⚠ Warning: $error_count errors in last check${NC}" | tee -a "$LOG_FILE"
    else
        echo -e "${GREEN}✓ Error rate nominal: $error_count errors${NC}" | tee -a "$LOG_FILE"
    fi
}

# Function: Check Resource Usage
check_resources() {
    echo "[$(date -u '+%H:%M:%S')] Checking resource usage..." | tee -a "$LOG_FILE"

    local cpu_usage=$(ps aux | grep uvicorn | awk '{print $3}' | head -1)
    local mem_usage=$(ps aux | grep uvicorn | awk '{print $4}' | head -1)

    echo "  CPU: ${cpu_usage}% | Memory: ${mem_usage}%" | tee -a "$LOG_FILE"

    if (( $(echo "$mem_usage > 60" | bc -l) )); then
        echo -e "${YELLOW}⚠ Memory usage high: ${mem_usage}%${NC}" | tee -a "$LOG_FILE"
    fi
}

# Main Monitoring Loop
ITERATION=0
INTERVAL=3600  # 1 hour in seconds
TOTAL_DURATION=$((24 * 3600))  # 24 hours

while [ $((ITERATION * INTERVAL)) -lt $TOTAL_DURATION ]; do
    HOUR=$((ITERATION))
    echo "" | tee -a "$LOG_FILE"
    echo "=== Checkpoint $((HOUR))/24h ===" | tee -a "$LOG_FILE"

    # Health checks
    health_check "$API_BASE$HEALTH_ENDPOINT" "Scheduler Health" || true
    health_check "$API_BASE/api/scheduler/schedules?page=1&limit=5" "List Schedules" || true
    health_check "$API_BASE/api/scheduler/batches?page=1&limit=5" "List Batches" || true

    # Error analysis
    check_error_rate

    # Resource monitoring
    check_resources

    # Alert on anomalies
    if [ $ITERATION -eq 4 ] || [ $ITERATION -eq 8 ] || [ $ITERATION -eq 12 ] || [ $ITERATION -eq 16 ] || [ $ITERATION -eq 20 ] || [ $ITERATION -eq 24 ]; then
        echo "" | tee -a "$LOG_FILE"
        echo ">>> Major Checkpoint at ${HOUR}h - Detailed Analysis Required <<<" | tee -a "$LOG_FILE"
    fi

    # Increment and wait
    ITERATION=$((ITERATION + 1))

    if [ $((ITERATION * INTERVAL)) -lt $TOTAL_DURATION ]; then
        echo "[$(date -u '+%H:%M:%S')] Next check in 1 hour..." | tee -a "$LOG_FILE"
        sleep "$INTERVAL"
    fi
done

echo "" | tee -a "$LOG_FILE"
echo "=== Phase 5 Staging Deployment - 24h Monitoring Complete ===" | tee -a "$LOG_FILE"
echo "End Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" | tee -a "$LOG_FILE"
echo "Metrics saved to: $METRICS_FILE" | tee -a "$LOG_FILE"
