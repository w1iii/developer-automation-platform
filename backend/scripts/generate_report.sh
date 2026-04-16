#!/bin/bash
echo "[$(date)] Starting report generation..."

REPORT_DIR="./reports"
mkdir -p "$REPORT_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORT_DIR/report_$TIMESTAMP.txt"

{
    echo "========================================"
    echo "         SYSTEM REPORT"
    echo "========================================"
    echo "Generated: $(date)"
    echo "----------------------------------------"
    echo ""
    echo "System Status:"
    echo "  Hostname: $(hostname 2>/dev/null || echo 'unknown')"
    echo "  Uptime: $(uptime -p 2>/dev/null || echo 'N/A')"
    echo ""
    echo "Disk Usage:"
    df -h . 2>/dev/null | tail -1 | awk '{print "  Used: " $3 " / " $2 " (" $5 ")"}'
    echo ""
    echo "Memory Usage:"
    if [ -f /proc/meminfo ]; then
        free -h 2>/dev/null | tail -2 | head -1 | awk '{print "  " $1 ": " $3 " used / " $2 " total"}'
    else
        echo "  N/A (not available on this system)"
    fi
    echo ""
    echo "========================================"
    echo "         END OF REPORT"
    echo "========================================"
} > "$REPORT_FILE"

echo "[$(date)] Report generated: $REPORT_FILE"
echo "[$(date)] Report generation job finished"
