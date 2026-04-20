#!/bin/bash

API_URL="${API_URL:-http://localhost:8000/health}"
TIMEOUT="${TIMEOUT:-5}"

response=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$API_URL" 2>/dev/null)

if [ "$response" = "200" ]; then
    echo "API is healthy (HTTP $response)"
    exit 0
else
    echo "API unhealthy (HTTP $response)"
    exit 1
fi
