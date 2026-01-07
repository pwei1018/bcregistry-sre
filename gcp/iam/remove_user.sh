#!/bin/bash

#declare -a PROJECT_IDS=("a083gt" "bcrbk9" "c4hnrd" "eogruh" "gtksf3" "k973yf" "keee67" "okagqp" "sbgmug" "yfjq17" "yfthig")
declare -a PROJECT_IDS=("a083gt" )
#declare -a ENVIRONMENTS=("dev" "test" "tools" "prod" "integration" "sandbox")
declare -a ENVIRONMENTS=("tools")
declare -a USERS=("bcregistry-sre@gov.bc.ca")

# Main Loop: Iterate through each project and remove the member
for user in "${USERS[@]}"
do
    # Ensure the user has the 'user:' prefix if not present (and it's not a serviceAccount or group)
    if [[ "$user" != user:* && "$user" != serviceAccount:* && "$user" != group:* ]]; then
        user="user:$user"
    fi

    echo "user: $user"
    for ev in "${ENVIRONMENTS[@]}"
    do
        for ns in "${PROJECT_IDS[@]}"
        do
            PROJECT_ID=$ns-$ev
            echo "project: $PROJECT_ID"

            # Check if project exists
            if ! gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
                echo "    Project $PROJECT_ID does not exist or you don't have permission to access it. Skipping."
                continue
            fi

            echo "  Removing member: $user"

            # Attempt to remove IAM bindings for all roles the member might have
            if ! RAW_POLICY=$(gcloud projects get-iam-policy "$PROJECT_ID" \
            --format="value(bindings.role)" \
            --filter="bindings.members:$user"); then
                echo "    ERROR: Failed to get IAM policy for project $PROJECT_ID. See above for details."
                continue
            fi

            ROLES=$(echo "$RAW_POLICY" | tr ';' ' ')

            if [[ -z "$ROLES" ]]; then
            echo "    Member $user has no roles in project $PROJECT_ID."
            else
            for ROLE in $ROLES; do
                echo "    Removing role $ROLE for $user..."
                gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
                --member="$user" \
                --role="$ROLE" \
                --quiet
                echo "    Role $ROLE removed for $user in project $PROJECT_ID."
            done
            fi
        done
    done
done

echo "Finished processing all projects."
