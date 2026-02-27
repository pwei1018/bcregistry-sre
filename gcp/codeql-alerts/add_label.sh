#!/bin/bash

# Configuration
ENV="dev"
#PROJECTS=("a083gt" "bcrbk9" "c4hnrd" "eogruh" "gtksf3" "yfjq17" "yfthig" "k973yf" "p0q6jr" "keee67" "mvnjri" "sbgmug" "okagqp")
PROJECTS=("c4hnrd")
REGION="northamerica-northeast1"

LABEL_KEY="product"
LABEL_VALUE="common"

for ns in "${PROJECTS[@]}"; do
    PROJECT_ID="${ns}-${ENV}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Project: ${PROJECT_ID}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Check if project exists
    if ! gcloud projects describe "${PROJECT_ID}" --verbosity=none >/dev/null 2>&1; then
        echo "  ⚠️  Project does not exist or is not accessible — skipping"
        continue
    fi

    echo "  Fetching services..."
    services=$(gcloud run services list \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --format="value(metadata.name)" 2>/dev/null || true)

    if [[ -n "$services" ]]; then
        for svc in $services; do
            echo "  🏷️ Adding label [${LABEL_KEY}=${LABEL_VALUE}] to: $svc"
            
            gcloud run services update "$svc" \
                --project="${PROJECT_ID}" \
                --region="${REGION}" \
                --update-labels="${LABEL_KEY}=${LABEL_VALUE}" \
                --quiet
        done
    else
        echo "    No Cloud Run services found"
    fi
    echo ""
done
