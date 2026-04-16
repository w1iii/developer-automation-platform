#!/bin/bash
echo "[$(date)] Starting temp file cleanup..."

TEMP_DIRS=("/tmp" "./temp" "./uploads")
FILES_REMOVED=0

for dir in "${TEMP_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        COUNT=$(find "$dir" -type f -name "*.tmp" -mtime +1 2>/dev/null | wc -l)
        if [ "$COUNT" -gt 0 ]; then
            find "$dir" -type f -name "*.tmp" -mtime +1 -delete 2>/dev/null
            FILES_REMOVED=$((FILES_REMOVED + COUNT))
            echo "[$(date)] Removed $COUNT temp files from $dir"
        fi
    fi
done

echo "[$(date)] Temp cleanup completed. Total files removed: $FILES_REMOVED"
echo "[$(date)] Temp file cleanup job finished"
