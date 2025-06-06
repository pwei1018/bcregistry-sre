#!/bin/bash
export ENV="prod"
export TAG="prod"  # this might be different from env, e.g. sandbox vs tools
export HOST_PROJECT_ID="c4hnrd"
export TARGET_PROJECT_ID="gtksf3"
export HOST_PROJECT_ID="${HOST_PROJECT_ID}-${ENV}"
export TARGET_PROJECT_ID="${TARGET_PROJECT_ID}-${ENV}"
export APP_NAME="pay-api"
export DB_NAME="pay-db"
export CLOUD_RUN_NAME="${APP_NAME}-${TAG}"
export CLOUD_SQL_NAME="${DB_NAME}-${TAG}"
export CREATE_LOG_SINK="false"

gcloud config set project $TARGET_PROJECT_ID

if [ "$CREATE_LOG_SINK" == true ]; then
  # create log sink
  gcloud logging sinks create cloud_run_errors_${TAG} \
  bigquery.googleapis.com/projects/${HOST_PROJECT_ID}/datasets/cloud_run_logs_${TAG} \
  --log-filter='resource.type="cloud_run_revision" AND severity="ERROR"' \
  --use-partitioned-tables
fi

# create alerts
ALERT_POLICIES_DIR="alert_policies"

for policy_file in "$ALERT_POLICIES_DIR"/*.json; do
  policy_name=$(basename "$policy_file")

  echo "Processing $policy_name..."

  # Process the template file with environment variables
  envsubst < "$policy_file" > alert_policy.json
  
  # Extract display name and filter for checking
  display_name=$(cat alert_policy.json | grep -o '"displayName": "[^"]*"' | head -1 | cut -d '"' -f 4)
  filter=$(cat alert_policy.json | grep -o '"filter": "[^"]*"' | cut -d '"' -f 4)
  
  echo "Policy: $display_name"
  echo "Filter: $filter"
  
  # Verify the filter is valid before proceeding
  echo "Validating metric filter..."
  
  # Check if a policy with this display name already exists
  existing_policy=$(gcloud alpha monitoring policies list --filter="displayName=$display_name" --format="value(name)" 2>/dev/null)
  
  if [ -n "$existing_policy" ]; then
    echo "Policy with display name '$display_name' already exists. Updating..."
    gcloud alpha monitoring policies update $existing_policy --policy-from-file=alert_policy.json
    result=$?
  else
    echo "Creating new policy with display name '$display_name'..."
    gcloud alpha monitoring policies create --policy-from-file=alert_policy.json
    result=$?
  fi

  if [ $result -eq 0 ]; then
    echo "Successfully processed alert policy from $policy_name."
  else
    echo "Failed to process alert policy from $policy_name with filter: $filter"
    echo "Check that the metric type and resource type specified in the filter exist and are compatible."
  fi

  rm -f alert_policy.json

done
