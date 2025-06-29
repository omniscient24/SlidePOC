#!/bin/bash

echo "▶ Starting bulk upsert with job tracking at $(date)"
PLAN_DIR="./plans"
CSV_BASE="./data/csv_output"
JOB_LOG="bulk_job_ids.txt"
> $JOB_LOG

run_upserts_from_plan() {
    PLAN_FILE="$1"
    echo "Processing plan: $PLAN_FILE"
    COUNT=$(jq length "$PLAN_FILE")
    for ((i = 0; i < COUNT; i++)); do
        SOBJECT=$(jq -r ".[$i].sobject" "$PLAN_FILE")
        EXTID=$(jq -r ".[$i].externalId" "$PLAN_FILE")
        FILE=$(jq -r ".[$i].files[0]" "$PLAN_FILE")
        CSV_PATH="${CSV_BASE}/${FILE##*/}"

        if [ -f "$CSV_PATH" ]; then
            echo "➡ Importing $SOBJECT from $CSV_PATH using external ID $EXTID"
            OUTPUT=$(sfdx force:data:bulk:upsert --sobjecttype "$SOBJECT" --externalid "$EXTID" --csv "$CSV_PATH" --json)
            JOB_ID=$(echo "$OUTPUT" | jq -r '.result.id // empty')
            if [ -n "$JOB_ID" ]; then
                echo "$SOBJECT: $JOB_ID" | tee -a "$JOB_LOG"
            else
                echo "❌ Failed to extract job ID for $SOBJECT"
            fi
        else
            echo "⚠ CSV not found: $CSV_PATH"
        fi
    done
}

run_upserts_from_plan "$PLAN_DIR/pass1_insert_minimal.json"
run_upserts_from_plan "$PLAN_DIR/pass2_insert_full.json"

echo "🎯 Job IDs written to $JOB_LOG"
echo "📌 Use: sfdx force:data:bulk:status --job-id JOB_ID to check job status"
echo "✅ Bulk upsert with job tracking complete at $(date)"
