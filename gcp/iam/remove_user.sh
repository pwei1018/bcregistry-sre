#!/bin/bash

#declare -a PROJECT_IDS=("a083gt" "bcrbk9" "c4hnrd" "eogruh" "gtksf3" "k973yf" "keee67" "okagqp" "sbgmug" "yfjq17" "yfthig")
declare -a PROJECT_IDS=("a083gt" )
#declare -a ENVIRONMENTS=("dev" "test" "tools" "prod" "integration" "sandbox")
declare -a ENVIRONMENTS=("tools")
declare -a USERS=("bcregistry-sre@gov.bc.ca")

# Main Loop: Iterate through each project and remove the member
for user in "${USERS[@]}"
do
    echo "user: $user"
    for ev in "${ENVIRONMENTS[@]}"
    do
        for ns in "${PROJECT_IDS[@]}"
        do
            PROJECT_ID=$ns-$ev
            echo "project: $PROJECT_ID"

            echo "  Removing member: $user"

            # Attempt to remove IAM bindings for all roles the member might have
            ROLES=$(gcloud projects get-iam-policy "$PROJECT_ID" \
            --format="table(bindings.role)" \
            --filter="bindings.members:$user" | tail -n +2)

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
