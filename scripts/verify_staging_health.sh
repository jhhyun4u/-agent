#!/bin/bash
# Verify Staging Scheduler Health Endpoint
# Run this script after staging deployment to validate fix

set -e

STAGING_URL="https://staging-api.tenopa.co"
HEALTH_ENDPOINT="/api/scheduler/health"
MAX_RETRIES=5
RETRY_INTERVAL=10

echo "=========================================="
echo "Staging Scheduler Health Verification"
echo "=========================================="
echo ""

# Function to check health
check_health() {
    echo "[Check $(date '+%H:%M:%S')] Testing $STAGING_URL$HEALTH_ENDPOINT..."

    # Try to reach the endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$STAGING_URL$HEALTH_ENDPOINT" 2>&1 || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        echo "✓ SUCCESS: Health endpoint responding"

        # Get actual response
        RESPONSE=$(curl -s "$STAGING_URL$HEALTH_ENDPOINT" 2>&1)
        echo "Response: $RESPONSE"
        echo ""

        # Quick functional test
        echo "[Check $(date '+%H:%M:%S')] Running functional tests..."

        # Test 1: List schedules (requires auth - may get 401)
        echo "1. Testing list schedules endpoint..."
        curl -s "$STAGING_URL/api/scheduler/schedules" -H "Authorization: Bearer test" 2>&1 | head -c 100
        echo ""
        echo ""

        return 0
    else
        echo "✗ FAILED: HTTP $HTTP_CODE"
        return 1
    fi
}

# Try health check with retries
ATTEMPT=1
while [ $ATTEMPT -le $MAX_RETRIES ]; do
    echo "Attempt $ATTEMPT / $MAX_RETRIES"

    if check_health; then
        echo "=========================================="
        echo "✓ STAGING DEPLOYMENT SUCCESSFUL"
        echo "=========================================="
        exit 0
    fi

    if [ $ATTEMPT -lt $MAX_RETRIES ]; then
        echo "Waiting $RETRY_INTERVAL seconds before retry..."
        sleep $RETRY_INTERVAL
    fi

    ATTEMPT=$((ATTEMPT + 1))
    echo ""
done

echo "=========================================="
echo "✗ STAGING HEALTH CHECK FAILED"
echo "=========================================="
echo ""
echo "Debugging information:"
echo "1. Check Railway/Render dashboard deployment logs"
echo "2. SSH to staging server and check app logs"
echo "3. Verify latest code is deployed (git log)"
echo ""
exit 1
