#!/bin/bash
# Phase 5 Automated Checkpoint Collection
# Runs every 2-4 hours to collect staging deployment metrics

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_FILE="PHASE5_MONITORING_STATUS.jsonl"
STAGING_URL="https://staging.api.tenopa.co.kr"
STAGING_TOKEN="${STAGING_AUTH_TOKEN:-}"

echo "=== Phase 5 Checkpoint Collection ==="
echo "Timestamp: $TIMESTAMP"

# 1. Health check
echo "Checking scheduler health..."
health_response=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $STAGING_TOKEN" \
  "$STAGING_URL/api/scheduler/health")

http_code=$(echo "$health_response" | tail -1)
health_body=$(echo "$health_response" | head -n -1)

if [ "$http_code" = "200" ]; then
  status=$(echo "$health_body" | jq -r '.status // "unknown"')
  uptime=$(echo "$health_body" | jq -r '.uptime_seconds // 0')
  db_connected=$(echo "$health_body" | jq -r '.db_connected // false')
else
  status="unhealthy"
  uptime=0
  db_connected=false
fi

# 2. Error log count (last 30 min)
error_count=$(grep -c "ERROR\|CRITICAL" /var/log/tenopa/scheduler.log 2>/dev/null || echo "0")

# 3. Memory usage
memory_mb=$(ps aux 2>/dev/null | grep "uvicorn.*scheduler" | awk '{print $6}' | head -1 || echo "0")
if [ -z "$memory_mb" ] || [ "$memory_mb" = "0" ]; then
  memory_mb=$(ps aux 2>/dev/null | grep "python" | grep "scheduler" | awk '{print $6}' | head -1 || echo "0")
fi

# 4. API latency sample (ms)
latency=$(curl -s -w "%{time_total}" -o /dev/null \
  -H "Authorization: Bearer $STAGING_TOKEN" \
  "$STAGING_URL/api/migrations/status" 2>/dev/null || echo "0")
latency_ms=$(echo "$latency * 1000" | bc | cut -d. -f1)

# 5. Go/No-Go determination
status_icon="🟢"
go_decision="GO"

if [ "$status" != "healthy" ]; then
  status_icon="🔴"
  go_decision="NO-GO"
elif [ "$error_count" -gt "5" ]; then
  status_icon="🟡"
  go_decision="CAUTION"
elif [ "$memory_mb" -gt "500" ]; then
  status_icon="🟡"
  go_decision="CAUTION"
elif [ "$latency_ms" -gt "1000" ]; then
  status_icon="🟡"
  go_decision="CAUTION"
fi

# 6. Create checkpoint record (JSONL format)
checkpoint=$(cat <<EOF
{
  "timestamp": "$TIMESTAMP",
  "checkpoint": "$status_icon",
  "status": "$status",
  "go_decision": "$go_decision",
  "uptime_seconds": $uptime,
  "error_count_30min": $error_count,
  "memory_mb": $memory_mb,
  "api_latency_ms": $latency_ms,
  "db_connected": $db_connected,
  "http_code": $http_code
}
EOF
)

# 7. Append to log
echo "$checkpoint" >> "$LOG_FILE"

# 8. Display checkpoint
echo ""
echo "=== Checkpoint Summary ==="
echo "$checkpoint" | jq .
echo ""
echo "Status: $status_icon $go_decision"
echo "Log appended to: $LOG_FILE"
