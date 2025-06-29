#!/bin/bash

LOGFILE="import.log"
exec > >(tee -a "$LOGFILE") 2>&1

set -e

echo "▶ Starting data load process at $(date)"

echo "▶ Running Python script to prepare external IDs and CSVs..."
python3 fortradp2_external_ids_corrected.py

echo "✅ Step 1 complete: CSVs and external IDs generated."
echo "📁 Output: ./data/csv_output/pass1, ./data/csv_output/pass2"
echo "🧾 Verification Report: ./data/csv_output/external_id_report.csv"

echo "▶ Running SFDX import: pass1_insert_minimal.json (initial inserts)..."
sfdx data import --plan plans/pass1_insert_minimal.json

echo "✅ Step 2 complete: pass1 records inserted."

echo "▶ Running SFDX import: pass2_update_with_lookups.json (lookups and relationships)..."
sfdx data import --plan plans/pass2_update_with_lookups.json

echo "✅ Step 3 complete: pass2 records updated with lookups."

echo "🎉 Data load process complete at $(date)"
echo "📄 Log written to $LOGFILE"
