#!/bin/bash

TMP_DIRS="${TMP_DIRS:-/tmp}"
DAYS_OLD="${DAYS_OLD:-7}"

find "$TMP_DIRS" -type f -name "*.tmp" -mtime +"$DAYS_OLD" -delete 2>/dev/null
find "$TMP_DIRS" -type f -name "*.log" -mtime +"$DAYS_OLD" -delete 2>/dev/null
find "$TMP_DIRS" -type d -empty -mtime +"$DAYS_OLD" -delete 2>/dev/null

echo "Cleaned tmp files older than $DAYS_OLD days"