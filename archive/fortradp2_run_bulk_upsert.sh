#!/bin/bash
LOGFILE="bulk_upsert.log"
exec > >(tee -a "$LOGFILE") 2>&1
set -e
echo "▶ Starting bulk upsert at $(date)"
echo "🎉 Bulk upsert completed at $(date)"