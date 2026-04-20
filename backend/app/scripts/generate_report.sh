#!/bin/bash

DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/automation}"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp/reports}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$OUTPUT_DIR"

REPORT_FILE="$OUTPUT_DIR/report_$TIMESTAMP.csv"

psql "$DATABASE_URL" -c "
SELECT 
    j.id,
    j.name,
    j.cron_schedule,
    je.status,
    je.started_at,
    je.ended_at,
    je.exit_code
FROM jobs j
LEFT JOIN job_executions je ON j.id = je.job_id
ORDER BY je.started_at DESC
LIMIT 100;
" > "$REPORT_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "Report generated: $REPORT_FILE"
else
    echo "Failed to generate report"
    exit 1
fi