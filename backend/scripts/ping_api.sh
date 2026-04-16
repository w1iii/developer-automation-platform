#!/bin/bash
echo "[$(date)] Starting API health check..."

API_URL="${API_URL:-https://httpbin.org/status/200}"
EXPECTED_STATUS="${EXPECTED_STATUS:-200}"

echo "Checking: $API_URL"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$API_URL")

if [ "$HTTP_CODE" = "$EXPECTED_STATUS" ]; then
    echo "[$(date)] API is healthy (HTTP $HTTP_CODE)"
    echo "[$(date)] API health check completed successfully"
else
    echo "[$(date)] API check failed (HTTP $HTTP_CODE, expected $EXPECTED_STATUS)"
    exit 1
fi

echo "[$(date)] API ping job finished"
