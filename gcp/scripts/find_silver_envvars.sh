#!/bin/bash
#
# find_silver_envvars.sh
#
# Scans all Cloud Run services and jobs in production GCP projects
# for environment variables containing "silver.devops.gov.bc.ca".
#
# Usage:
#   ./find_silver_envvars.sh
#   SCAN_PROJECTS="a083gt,c4hnrd" ./find_silver_envvars.sh   # scan specific projects only
#

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────
SEARCH_STRING="silver.devops.gov.bc.ca"
ENV="prod"

# Patterns to ignore in matched values (pipe-separated for grep -E / awk)
IGNORE_PATTERNS=("pay-connector" "namex-solr" "traction-tenant" "minio" "ocp-relay")
IGNORE_REGEX=$(IFS='|'; echo "${IGNORE_PATTERNS[*]}")

# Patterns to ignore for environment variable keys
IGNORE_KEY_PATTERNS=("VALID_REDIRECT_URLS")
IGNORE_KEY_REGEX=$(IFS='|'; echo "${IGNORE_KEY_PATTERNS[*]}")

DEFAULT_PROJECTS=("a083gt" "bcrbk9" "c4hnrd" "eogruh" "gtksf3" "yfjq17" "yfthig" "k973yf" "p0q6jr" "keee67" "mvnjri" "sbgmug" "okagqp")

if [[ -n "${SCAN_PROJECTS:-}" ]]; then
    IFS=',' read -ra projects <<< "${SCAN_PROJECTS}"
    echo "Using projects from SCAN_PROJECTS environment variable"
else
    projects=("${DEFAULT_PROJECTS[@]}")
fi

REGION="northamerica-northeast1"
MD_FILE="${ENV}_silver_envvars.md"

# ── Counters ─────────────────────────────────────────────────────────
total_matches=0
scanned_services=0
scanned_jobs=0

echo "# Cloud Run Environment Variables — \`${SEARCH_STRING}\` (${ENV})" > "$MD_FILE"
echo "" >> "$MD_FILE"
echo "**Scan Date:** $(date +%Y-%m-%d)" >> "$MD_FILE"
echo "**Environment:** ${ENV}" >> "$MD_FILE"
echo "**Projects Scanned:** ${#projects[@]} | **Services Scanned:** MAGIC_SERVICES | **Jobs Scanned:** MAGIC_JOBS | **Total Matches:** MAGIC_MATCHES" >> "$MD_FILE"
echo "" >> "$MD_FILE"
echo "---" >> "$MD_FILE"
echo "" >> "$MD_FILE"

echo "==============================================="
echo "Cloud Run Environment Variable Scanner"
echo "==============================================="
echo "  Search String : ${SEARCH_STRING}"
echo "  Environment   : ${ENV}"
echo "  Projects      : ${#projects[@]}"
echo "==============================================="
echo ""

# ── Helper: inspect env vars ─────────────────────────────────────────
# Prints matching env-var names/values for a given resource's YAML.
check_env_vars() {
    local project="$1"
    local resource_type="$2"   # "service" or "job"
    local resource_name="$3"
    local yaml="$4"

    # Extract env var lines that contain the search string (case-insensitive)
    local matches
    matches=$(echo "$yaml" | grep -i "${SEARCH_STRING}" || true)

    if [[ -n "$matches" ]]; then
        echo "  ⚠️  ${resource_type}: ${resource_name}"
        # Parse name/value pairs from the YAML
        local current_name=""
        while IFS= read -r line; do
            # Trim leading whitespace
            line_trimmed=$(echo "$line" | sed 's/^[[:space:]]*//')

            if [[ "$line_trimmed" == name:* ]]; then
                current_name=$(echo "$line_trimmed" | sed 's/^name:[[:space:]]*//')
            elif [[ "$line_trimmed" == value:* ]]; then
                local val
                val=$(echo "$line_trimmed" | sed 's/^value:[[:space:]]*//')
                if echo "$val" | grep -qi "${SEARCH_STRING}"; then
                    echo "      ENV VAR : ${current_name}"
                    echo "      VALUE   : ${val}"
                    echo ""
                    total_matches=$((total_matches + 1))
                fi
            fi
        done <<< "$(echo "$yaml" | grep -B1 -i "${SEARCH_STRING}" | grep -E '^\s*(name:|value:)' || true)"

        # Fallback: if the above structured parsing didn't catch it, just show raw matches
        if [[ $total_matches -eq 0 || -z "$(echo "$yaml" | grep -B1 -i "${SEARCH_STRING}" | grep -E '^\s*(name:|value:)' || true)" ]]; then
            echo "$matches" | while IFS= read -r m; do
                echo "      ${m}"
            done
            echo ""
        fi
        return 0
    fi
    return 1
}

# ── Main loop ────────────────────────────────────────────────────────
for ns in "${projects[@]}"; do
    PROJECT_ID="${ns}-${ENV}"
    
    project_has_match=false

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Project: ${PROJECT_ID}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    echo "## ${PROJECT_ID}" >> "$MD_FILE"
    echo "" >> "$MD_FILE"

    # Check if project exists / is accessible
    if ! gcloud projects describe "${PROJECT_ID}" --verbosity=none >/dev/null 2>&1; then
        echo "  ⚠️  Project does not exist or is not accessible — skipping"
        echo ""
        echo "⚠️ Project does not exist or is not accessible." >> "$MD_FILE"
        echo "" >> "$MD_FILE"
        echo "---" >> "$MD_FILE"
        echo "" >> "$MD_FILE"
        continue
    fi

    # ── Cloud Run Services ───────────────────────────────────────────
    project_has_service_match=false
    echo "  Scanning Cloud Run services..."
    services=$(gcloud run services list \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --format="value(metadata.name)" 2>/dev/null || true)

    if [[ -n "$services" ]]; then
        while IFS= read -r svc; do
            [[ -z "$svc" ]] && continue
            scanned_services=$((scanned_services + 1))

            yaml=$(gcloud run services describe "$svc" \
                --project="${PROJECT_ID}" \
                --region="${REGION}" \
                --format=yaml 2>/dev/null || true)

            if echo "$yaml" | grep -qi "${SEARCH_STRING}"; then
                # Extract env var name + value pairs, filtering out ignored patterns
                matched_md=$(echo "$yaml" | awk -v search="${SEARCH_STRING}" -v ignore="${IGNORE_REGEX}" -v ignore_keys="${IGNORE_KEY_REGEX}" -v svc="${svc}" '
                    /^[[:space:]]*- name:/ { env_name=$NF }
                    /^[[:space:]]*value:/ {
                        val = $0
                        sub(/^[[:space:]]*value:[[:space:]]*/, "", val)
                        if (env_name !~ ignore_keys && tolower(val) ~ tolower(search) && !(tolower(val) ~ tolower(ignore))) {
                            printf "| %s | `%s` | `%s` |\n", svc, env_name, val
                        }
                    }
                ')
                matched_output=$(echo "$yaml" | awk -v search="${SEARCH_STRING}" -v ignore="${IGNORE_REGEX}" -v ignore_keys="${IGNORE_KEY_REGEX}" '
                    /^[[:space:]]*- name:/ { env_name=$NF }
                    /^[[:space:]]*value:/ {
                        val = $0
                        sub(/^[[:space:]]*value:[[:space:]]*/, "", val)
                        if (env_name !~ ignore_keys && tolower(val) ~ tolower(search) && !(tolower(val) ~ tolower(ignore))) {
                            printf "        ENV VAR : %s\n", env_name
                            printf "        VALUE   : %s\n\n", val
                        }
                    }
                ')
                if [[ -n "$matched_output" ]]; then
                    if ! $project_has_service_match; then
                        echo "### Cloud Run Services" >> "$MD_FILE"
                        echo "" >> "$MD_FILE"
                        echo "| Service | Env Var | Value |" >> "$MD_FILE"
                        echo "|---------|---------|-------|" >> "$MD_FILE"
                        project_has_service_match=true
                        project_has_match=true
                    fi
                    echo "  ⚠️  SERVICE: ${svc}"
                    echo "$matched_output"
                    echo "$matched_md" >> "$MD_FILE"
                    
                    # count actual lines (matches)
                    count="$(echo "$matched_md" | wc -l)"
                    total_matches=$((total_matches + count))
                fi
            fi
        done <<< "$services"
    else
        echo "    No Cloud Run services found"
    fi

    # ── Cloud Run Jobs ───────────────────────────────────────────────
    project_has_job_match=false
    echo "  Scanning Cloud Run jobs..."
    jobs=$(gcloud run jobs list \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --format="value(metadata.name)" 2>/dev/null || true)

    if [[ -n "$jobs" ]]; then
        while IFS= read -r job; do
            [[ -z "$job" ]] && continue
            scanned_jobs=$((scanned_jobs + 1))

            yaml=$(gcloud run jobs describe "$job" \
                --project="${PROJECT_ID}" \
                --region="${REGION}" \
                --format=yaml 2>/dev/null || true)

            if echo "$yaml" | grep -qi "${SEARCH_STRING}"; then
                matched_md=$(echo "$yaml" | awk -v search="${SEARCH_STRING}" -v ignore="${IGNORE_REGEX}" -v ignore_keys="${IGNORE_KEY_REGEX}" -v job="${job}" '
                    /^[[:space:]]*- name:/ { env_name=$NF }
                    /^[[:space:]]*value:/ {
                        val = $0
                        sub(/^[[:space:]]*value:[[:space:]]*/, "", val)
                        if (env_name !~ ignore_keys && tolower(val) ~ tolower(search) && !(tolower(val) ~ tolower(ignore))) {
                            printf "| %s | `%s` | `%s` |\n", job, env_name, val
                        }
                    }
                ')
                matched_output=$(echo "$yaml" | awk -v search="${SEARCH_STRING}" -v ignore="${IGNORE_REGEX}" -v ignore_keys="${IGNORE_KEY_REGEX}" '
                    /^[[:space:]]*- name:/ { env_name=$NF }
                    /^[[:space:]]*value:/ {
                        val = $0
                        sub(/^[[:space:]]*value:[[:space:]]*/, "", val)
                        if (env_name !~ ignore_keys && tolower(val) ~ tolower(search) && !(tolower(val) ~ tolower(ignore))) {
                            printf "        ENV VAR : %s\n", env_name
                            printf "        VALUE   : %s\n\n", val
                        }
                    }
                ')
                if [[ -n "$matched_output" ]]; then
                    if ! $project_has_job_match; then
                        echo "" >> "$MD_FILE"
                        echo "### Cloud Run Jobs" >> "$MD_FILE"
                        echo "" >> "$MD_FILE"
                        echo "| Job | Env Var | Value |" >> "$MD_FILE"
                        echo "|-----|---------|-------|" >> "$MD_FILE"
                        project_has_job_match=true
                        project_has_match=true
                    fi
                    echo "  ⚠️  JOB: ${job}"
                    echo "$matched_output"
                    echo "$matched_md" >> "$MD_FILE"
                    
                    count="$(echo "$matched_md" | wc -l)"
                    total_matches=$((total_matches + count))
                fi
            fi
        done <<< "$jobs"
    else
        echo "    No Cloud Run jobs found"
    fi

    if ! $project_has_match; then
        echo "✅ No matches found." >> "$MD_FILE"
    fi
    echo "" >> "$MD_FILE"
    echo "---" >> "$MD_FILE"
    echo "" >> "$MD_FILE"
    
    echo ""
done

# ── Summary ──────────────────────────────────────────────────────────
# Replace placeholders in the markdown file
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/MAGIC_SERVICES/${scanned_services}/" "$MD_FILE"
    sed -i '' "s/MAGIC_JOBS/${scanned_jobs}/" "$MD_FILE"
    sed -i '' "s/MAGIC_MATCHES/${total_matches}/" "$MD_FILE"
else
    sed -i "s/MAGIC_SERVICES/${scanned_services}/" "$MD_FILE"
    sed -i "s/MAGIC_JOBS/${scanned_jobs}/" "$MD_FILE"
    sed -i "s/MAGIC_MATCHES/${total_matches}/" "$MD_FILE"
fi

echo "==============================================="
echo "SUMMARY"
echo "==============================================="
echo "  Services scanned : ${scanned_services}"
echo "  Jobs scanned     : ${scanned_jobs}"
echo "  Matches found    : ${total_matches}"
echo "==============================================="
echo "  Results saved to : ${MD_FILE}"
echo "==============================================="
