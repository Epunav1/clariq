#!/bin/bash
# Database backup and restore script for CLARIQ

set -e

BACKUP_DIR="./data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$BACKUP_DIR/backup.log"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "=== CLARIQ Database Backup ===" | tee -a "$LOG_FILE"
echo "Timestamp: $TIMESTAMP" | tee -a "$LOG_FILE"

# Backup SQLite databases
backup_sqlite() {
    local db_name=$1
    local db_path=$2
    
    if [ -f "$db_path" ]; then
        cp "$db_path" "$BACKUP_DIR/${db_name}_${TIMESTAMP}.db"
        echo "✓ Backed up $db_name" | tee -a "$LOG_FILE"
    else
        echo "⚠ $db_path not found, skipping" | tee -a "$LOG_FILE"
    fi
}

# Backup PostgreSQL database (if configured)
backup_postgres() {
    if [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_DB" ]; then
        echo "⚠ PostgreSQL not configured, skipping" | tee -a "$LOG_FILE"
        return
    fi
    
    PGPASSWORD=$POSTGRES_PASSWORD pg_dump \
        -h "$POSTGRES_HOST" \
        -p "${POSTGRES_PORT:-5432}" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        > "$BACKUP_DIR/postgres_${TIMESTAMP}.sql"
    
    gzip "$BACKUP_DIR/postgres_${TIMESTAMP}.sql"
    echo "✓ Backed up PostgreSQL database" | tee -a "$LOG_FILE"
}

# Main backup routine
echo "Starting backup routine..." | tee -a "$LOG_FILE"

backup_sqlite "clariq_pilots" "./data/clariq_pilots.sqlite"
backup_sqlite "clariq_actions" "./data/clariq_actions.sqlite"
backup_sqlite "clariq_roi_params" "./data/clariq_roi_params.sqlite"
backup_sqlite "clariq_performance" "./data/clariq_performance_metrics.sqlite"
backup_sqlite "clariq_alerts" "./data/clariq_alerts.sqlite"
backup_sqlite "clariq_sync" "./data/sync_status.sqlite"

# Uncomment to enable PostgreSQL backup
# backup_postgres

# Clean up old backups (keep last 30 days)
echo "" | tee -a "$LOG_FILE"
echo "Cleaning up old backups (>30 days)..." | tee -a "$LOG_FILE"

find "$BACKUP_DIR" -name "*.db" -mtime +30 -exec rm {} \; -print | tee -a "$LOG_FILE"
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -exec rm {} \; -print | tee -a "$LOG_FILE"

# Calculate backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | awk '{print $1}')
echo "" | tee -a "$LOG_FILE"
echo "✓ Backup complete! Total size: $BACKUP_SIZE" | tee -a "$LOG_FILE"
echo "✓ Backups stored in: $BACKUP_DIR" | tee -a "$LOG_FILE"

# Send email notification (optional)
if [ ! -z "$BACKUP_NOTIFY_EMAIL" ]; then
    echo "Sending notification email to $BACKUP_NOTIFY_EMAIL..." | tee -a "$LOG_FILE"
    # Implementation depends on your email setup
fi

echo "=== Backup End ===" | tee -a "$LOG_FILE"
