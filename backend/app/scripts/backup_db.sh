#!/bin/bash

DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/automation}"
BACKUP_DIR="${BACKUP_DIR:-/tmp/}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

pg_dump "$DATABASE_URL" >"$BACKUP_FILE" 2>&1

if [ $? -eq 0 ]; then
    gzip "$BACKUP_FILE"
    echo "Database backup created: ${BACKUP_FILE}.gz"
else
    echo "Failed to backup database"
    exit 1
fi
