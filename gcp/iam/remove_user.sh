#!/bin/bash
#
# 🌤️ GCP IAM User Access Manager - Removal Script
#
# This script gracefully removes a user's IAM access from Google Cloud projects.
# It supports dry-run mode, logging, and can target a single project or all accessible projects.
#

# 🎨 Color definitions
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# 📝 Initialize log file with timestamp
LOG_FILE="iam_removal_$(date +%Y-%m-%d_%H-%M-%S).log"
TEMP_DIR=$(mktemp -d)

# 🔧 Function to display usage
usage() {
    cat <<EOF
$0 - Remove GCP IAM User Access with Style

Usage:
    $0 --user=EMAIL [--project=PROJECT_ID] [--all] [--dry-run] [--environments=ENV1,ENV2]

Required:
    --user=EMAIL             Email address of the user to remove

Options:
    --project=PROJECT_ID     Target a specific project
    --all                    Target all accessible projects
    --dry-run                Simulate removal without making changes
    --environments=ENV1,ENV2 Comma-separated list of environments (dev,test,prod,etc)
    --help                   Display this help message

Examples:
    $0 --user=john.doe@example.com --all --dry-run
    $0 --user=john.doe@example.com --project=my-project-id
    $0 --user=john.doe@example.com --environments=dev,test,prod
EOF
    exit 1
}

# 📊 Function to log messages
log() {
    local level=$1
    local message=$2
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")

    case $level in
        INFO)  echo -e "${BLUE}[INFO]${NC} $message" | tee -a "$LOG_FILE" ;;
        WARN)  echo -e "${YELLOW}[WARN]${NC} $message" | tee -a "$LOG_FILE" ;;
        ERROR) echo -e "${RED}[ERROR]${NC} $message" | tee -a "$LOG_FILE" ;;
        SUCCESS) echo -e "${GREEN}[SUCCESS]${NC} $message" | tee -a "$LOG_FILE" ;;
        DRY-RUN) echo -e "${CYAN}[DRY-RUN]${NC} $message" | tee -a "$LOG_FILE" ;;
        *) echo -e "[${level}] $message" | tee -a "$LOG_FILE" ;;
    esac
}

# 🔍 Function to get user's roles in a project
get_user_roles() {
    local project=$1
    local user=$2

    log "INFO" "Checking roles for user ${MAGENTA}$user${NC} in project ${YELLOW}$project${NC}"
    gcloud projects get-iam-policy "$project" \
        --format="value(bindings.role)" \
        --filter="bindings.members:$user" 2>/dev/null || {
            log "ERROR" "Failed to get IAM policy for project $project"
            return 1
        }
}

# 🧹 Function to remove user from a role in a project
remove_role() {
    local project=$1
    local user=$2
    local role=$3
    local dry_run=$4

    if [[ "$dry_run" == "true" ]]; then
        log "DRY-RUN" "Would remove role ${YELLOW}$role${NC} from user ${MAGENTA}$user${NC} in project ${CYAN}$project${NC}"
    else
        log "INFO" "Removing role ${YELLOW}$role${NC} from user ${MAGENTA}$user${NC} in project ${CYAN}$project${NC}"
        gcloud projects remove-iam-policy-binding "$project" \
            --member="$user" \
            --role="$role" \
            --quiet &> /dev/null

        if [[ $? -eq 0 ]]; then
            log "SUCCESS" "Successfully removed role ${YELLOW}$role${NC} from user ${MAGENTA}$user${NC} in project ${CYAN}$project${NC}"
        else
            log "ERROR" "Failed to remove role ${YELLOW}$role${NC} from user ${MAGENTA}$user${NC} in project ${CYAN}$project${NC}"
        fi
    fi
}

# 🧮 Function to process a single project
process_project() {
    local project=$1
    local user=$2
    local dry_run=$3
    local roles

    log "INFO" "Processing project ${YELLOW}$project${NC}"

    # Check if project exists
    if ! gcloud projects describe "$project" &>/dev/null; then
        log "ERROR" "Project $project does not exist or you don't have access"
        return 1
    fi

    # Get user's roles
    roles=$(get_user_roles "$project" "$user")

    if [[ -z "$roles" ]]; then
        log "INFO" "User ${MAGENTA}$user${NC} has no roles in project ${YELLOW}$project${NC}"
        return 0
    fi

    log "INFO" "Found ${#roles[@]} role(s) for user ${MAGENTA}$user${NC} in project ${YELLOW}$project${NC}"

    # Remove each role
    echo "$roles" | while read -r role; do
        [[ -z "$role" ]] && continue
        remove_role "$project" "$user" "$role" "$dry_run"
    done
}

# 🚀 Main function
main() {
    local user=""
    local project=""
    local all_projects=false
    local dry_run=false
    local environments=""

    # Parse arguments
    for arg in "$@"; do
        case $arg in
            --user=*)
                user="${arg#*=}"
                # Check if it's a valid email or user:email format
                if [[ ! "$user" =~ ^user: ]]; then
                    user="user:$user"
                fi
                shift
                ;;
            --project=*)
                project="${arg#*=}"
                shift
                ;;
            --all)
                all_projects=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --environments=*)
                environments="${arg#*=}"
                shift
                ;;
            --help)
                usage
                ;;
            *)
                echo "Unknown option: $arg"
                usage
                ;;
        esac
    done

    # Validate inputs
    if [[ -z "$user" ]]; then
        log "ERROR" "User email is required (--user=EMAIL)"
        usage
    fi

    if [[ -z "$project" && "$all_projects" == "false" && -z "$environments" ]]; then
        log "ERROR" "Either --project, --all, or --environments must be specified"
        usage
    fi

    # Log start
    log "INFO" "🌤️ Starting IAM removal process"
    log "INFO" "Log file: $LOG_FILE"

    if [[ "$dry_run" == "true" ]]; then
        log "DRY-RUN" "Running in simulation mode - no changes will be made"
    fi

    # Get list of projects to process
    local projects=()

    if [[ "$all_projects" == "true" ]]; then
        log "INFO" "Getting list of all accessible projects..."

        # Get all projects the user has access to
        readarray -t projects < <(gcloud projects list --format="value(projectId)")
        log "INFO" "Found ${#projects[@]} accessible projects"
    elif [[ -n "$project" ]]; then
        # Use the specified project
        projects=("$project")
    elif [[ -n "$environments" ]]; then
        # Use the legacy PROJECT_IDS and ENVIRONMENTS arrays
        # Convert comma-separated list to array
        IFS=',' read -r -a ENV_ARRAY <<< "$environments"

        # Default project IDs if not set
        declare -a PROJECT_IDS=("a083gt" "bcrbk9" "c4hnrd" "eogruh" "gtksf3" "k973yf" "keee67" "okagqp" "sbgmug" "yfjq17" "yfthig")

        # Generate project IDs from the environment list
        for env in "${ENV_ARRAY[@]}"; do
            for ns in "${PROJECT_IDS[@]}"; do
                projects+=("$ns-$env")
            done
        done

        log "INFO" "Generated ${#projects[@]} project IDs from environments: $environments"
    fi

    # Process each project
    local processed=0
    local failed=0

    for project in "${projects[@]}"; do
        if process_project "$project" "$user" "$dry_run"; then
            ((processed++))
        else
            ((failed++))
        fi
    done

    # Log completion
    if [[ "$dry_run" == "true" ]]; then
        log "DRY-RUN" "Simulation complete: Would process $processed projects (with $failed failures)"
    else
        log "SUCCESS" "IAM removal complete: Processed $processed projects (with $failed failures)"
    fi

    log "INFO" "Full log available at: $LOG_FILE"

    # Clean up temp directory
    rm -rf "$TEMP_DIR"
}

# Execute main function with all arguments
main "$@"
