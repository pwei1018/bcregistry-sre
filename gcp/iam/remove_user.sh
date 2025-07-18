#!/bin/bash

set -e # Exit immediately if a command exits with a non-zero status.

DRY_RUN=false

usage() {
    echo "Usage: $0 [--dry-run] [--help] <user_email_1> [user_email_2] ..."
    echo "Removes specified users from all accessible GCP projects."
    echo "  --dry-run: List users that would be removed without actually removing them."
    echo "  --help: Display this help message."
    exit 1
}

# Parse command-line arguments
for arg in "$@"
do
    case "$arg" in
        --dry-run)
            DRY_RUN=true
            shift # Remove --dry-run from arguments
            ;;
        --help|-h)
            usage
            ;;
        *)
            # Assume it's a user email
            ;;
    esac
done

if [ "$#" -eq 0 ]; then
    usage
fi

echo "Fetching project list..."
# Get the list of project IDs from gcloud
PROJECT_IDS=($(gcloud projects list --format="value(projectId)" 2>/dev/null))
echo "Found ${#PROJECT_IDS[@]} projects."

# Create a temporary file to store the proposed changes
changes_file=$(mktemp)

# Main Loop: Iterate through each project and then each user
for PROJECT_ID in "${PROJECT_IDS[@]}"
do
    set -e
    # Get the IAM policy for the project
    policy=$(gcloud projects get-iam-policy "$PROJECT_ID" --format=json 2>/dev/null || true)

    if [ -z "$policy" ]; then
        continue # Skip to the next project if the policy is empty
    fi

    original_policy=$policy
    policy_changed=false

    for user_input in "$@" # Now "$@" contains only user emails
    do
        user_lowercase=$(echo "$user_input" | tr '[:upper:]' '[:lower:]') # Convert to lowercase for comparison

        updated_policy=$(echo "$policy" | jq \
            --arg user_lower "$user_lowercase" \
            '(.bindings[].members) |= map(
                select(
                    (
                        (startswith("user:") and ((ltrimstr("user:") | ascii_downcase) == $user_lower)) or
                        (startswith("serviceAccount:") and ((ltrimstr("serviceAccount:") | ascii_downcase) == $user_lower)) or
                        (startswith("group:") and ((ltrimstr("group:") | ascii_downcase) == $user_lower))
                    ) | not
                )
            )
            | del(.bindings[] | select(.members | length == 0))
        ')

        if [ "$policy" != "$updated_policy" ]; then
            echo -e "\033[0;31m  Found user $user_input in project $PROJECT_ID.\033[0m"
            policy=$updated_policy
            policy_changed=true
        fi
    done

    # Only set the policy if it has changed.
    if [ "$policy_changed" = true ]; then
        if [ "$DRY_RUN" = true ]; then
            echo -e "\033[0;31m    [DRY RUN] Would modify policy for project $PROJECT_ID.\033[0m"
        else
            echo "echo 'Updating policy for project $PROJECT_ID...'" >> "$changes_file"
            echo "gcloud projects set-iam-policy '$PROJECT_ID' /dev/stdin --quiet <<'POLICY_JSON'" >> "$changes_file"
            echo "$policy" >> "$changes_file"
            echo "POLICY_JSON" >> "$changes_file"
        fi
    fi
done

if [ -s "$changes_file" ]; then
    if [ "$DRY_RUN" = true ]; then
        echo "Dry run complete. No changes were made."
    else
        #echo "The following commands will be executed:"
        #cat "$changes_file"
        read -p "Are you sure you want to apply all the above changes? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            bash "$changes_file"
            echo -e "\033[0;32mAll changes applied successfully.\033[0m"
        else
            echo -e "\033[0;31mAll changes cancelled by user.\033[0m"
        fi
    fi
fi

rm -f "$changes_file"




echo "Finished processing all users and projects."