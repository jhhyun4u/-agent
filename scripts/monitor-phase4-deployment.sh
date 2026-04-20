#!/bin/bash

# Phase 4 Production Deployment Monitoring Script
# Usage: ./scripts/monitor-phase4-deployment.sh
# Runs continuous health checks for 3 hours post-deployment

set -e

DEPLOYMENT_START="2026-04-25 09:00"
MONITORING_DURATION=180  # 3 hours in minutes
CHECK_INTERVAL=5        # Check every 5 minutes
API_URL="https://api.tenopa.co.kr"
SLACK_WEBHOOK="${SLACK_DEPLOYMENT_WEBHOOK}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
TOTAL_CHECKS=0

echo "🚀 Phase 4 Production Deployment Monitoring Started"
echo "Start Time: $(date)"
echo "Duration: ${MONITORING_DURATION} minutes"
echo "Check Interval: ${CHECK_INTERVAL} minutes"
echo "-------------------------------------------"

# Function to check API health
check_api_health() {
    local endpoint="$1"
    local description="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if curl -s -f -m 5 "${API_URL}${endpoint}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}: ${description}"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: ${description}"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))

        # Send Slack alert on failure
        if [ ! -z "$SLACK_WEBHOOK" ]; then
            curl -X POST "$SLACK_WEBHOOK" \
                -H 'Content-type: application/json' \
                -d "{
                    \"text\": \"🚨 Phase 4 Deployment Check Failed\",
                    \"blocks\": [{
                        \"type\": \"section\",
                        \"text\": {
                            \"type\": \"mrkdwn\",
                            \"text\": \"*${description}* failed\n\`${API_URL}${endpoint}\`\"
                        }
                    }]
                }"
        fi

        return 1
    fi
}

# Function to check error rate
check_error_rate() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    # Query logs for error rate (example using journalctl or application logs)
    # This is a placeholder - adjust based on your logging system
    ERROR_RATE=$(grep -c "ERROR\|error\|500\|exception" /var/log/tenopa/api.log 2>/dev/null | tail -100 | wc -l)
    ERROR_RATE=$((ERROR_RATE / 100)) # Convert to percentage

    if [ $ERROR_RATE -lt 1 ]; then
        echo -e "${GREEN}✅ PASS${NC}: Error rate ${ERROR_RATE}% < 1% threshold"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: Error rate ${ERROR_RATE}% exceeds 1% threshold - CONSIDER ROLLBACK"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
        return 1
    fi
}

# Function to check database connectivity
check_database() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if curl -s -f "${API_URL}/api/health/db" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}: Database connectivity healthy"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: Database connectivity issue - ALERT DBA"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
        return 1
    fi
}

# Function to check RLS violations
check_rls_policies() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    # Query for RLS violations in audit logs
    RLS_VIOLATIONS=$(curl -s "${API_URL}/api/admin/audit?type=rls_violation&limit=1" | grep -c "violation" || echo "0")

    if [ "$RLS_VIOLATIONS" -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: No RLS violations detected"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: RLS violations detected ($RLS_VIOLATIONS) - CRITICAL - ROLLBACK IMMEDIATELY"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
        return 1
    fi
}

# Main monitoring loop
elapsed_time=0
while [ $elapsed_time -lt $MONITORING_DURATION ]; do
    echo ""
    echo "⏱️ Elapsed: ${elapsed_time}/${MONITORING_DURATION} minutes - $(date)"
    echo "-------------------------------------------"

    # Run all checks
    check_api_health "/api/health" "API Health"
    check_api_health "/api/documents" "Document API"
    check_database "Database Health"
    check_rls_policies "RLS Policies"
    check_error_rate "Error Rate"

    # Print summary
    echo "-------------------------------------------"
    echo "Checks: ${CHECKS_PASSED} passed, ${CHECKS_FAILED} failed out of ${TOTAL_CHECKS} total"

    # Check for critical failures
    if [ $CHECKS_FAILED -gt 2 ]; then
        echo -e "${RED}🚨 CRITICAL: Multiple failures detected - INITIATING ROLLBACK${NC}"
        echo "Contact on-call engineer immediately"
        exit 1
    fi

    # Wait before next check
    if [ $elapsed_time -lt $MONITORING_DURATION ]; then
        echo "Sleeping ${CHECK_INTERVAL} minutes until next check..."
        sleep $((CHECK_INTERVAL * 60))
    fi

    elapsed_time=$((elapsed_time + CHECK_INTERVAL))
done

echo ""
echo "✅ Monitoring Complete!"
echo "Final Results:"
echo "  Passed: ${CHECKS_PASSED}"
echo "  Failed: ${CHECKS_FAILED}"
echo "  Success Rate: $((CHECKS_PASSED * 100 / TOTAL_CHECKS))%"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Phase 4 Production Deployment Successful!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️ Phase 4 Production Deployment requires investigation${NC}"
    exit 1
fi
