#!/bin/bash

# Update Product records with BasedOnId
PRODUCT_CLASSIFICATION_ID="11Bdp000000nAELEA2"

# Array of product IDs to update
PRODUCT_IDS=(
    "01tdp000006HfphAAC"
    "01tdp000006HfpiAAC"
    "01tdp000006HfpjAAC"
    "01tdp000006HfpkAAC"
    "01tdp000006HfplAAC"
    "01tdp000006HfpmAAC"
    "01tdp000006HfpnAAC"
    "01tdp000006HfpoAAC"
    "01tdp000006HfppAAC"
    "01tdp000006HfpqAAC"
    "01tdp000006HfprAAC"
    "01tdp000006HfpsAAC"
    "01tdp000006HfptAAC"
    "01tdp000006HfpuAAC"
    "01tdp000006HfpvAAC"
    "01tdp000006HfpwAAC"
    "01tdp000006HfpxAAC"
    "01tdp000006HfpyAAC"
    "01tdp000006HfpzAAC"
    "01tdp000006Hfq0AAC"
    "01tdp000006Hfq1AAC"
)

echo "Updating ${#PRODUCT_IDS[@]} products with BasedOnId..."

for PRODUCT_ID in "${PRODUCT_IDS[@]}"; do
    echo "Updating product: $PRODUCT_ID"
    sf data update record --sobject Product2 --record-id "$PRODUCT_ID" --values "BasedOnId='$PRODUCT_CLASSIFICATION_ID'" --target-org fortradp2
done

echo "Update complete!"