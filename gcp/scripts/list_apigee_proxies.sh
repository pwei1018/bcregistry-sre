#!/bin/bash

# Exit automatically on errors
set -e

# Requires jq
if ! command -v jq &> /dev/null; then
    echo "jq is required but not installed. Please install jq first."
    exit 1
fi

if [ -z "$1" ]; then
    echo "Usage: $0 <gcp-project-name> [output-file.md]"
    echo "Example: $0 okagqp-test proxies.md"
    exit 1
fi

PROJECT=$1
OUT_FILE=${2:-"apigee_endpoints.md"}

echo "Fetching gcloud access token..."
TOKEN=$(gcloud auth print-access-token)

# Initialize Output Markdown File
echo "# Apigee Proxies and Endpoints - $PROJECT" > "$OUT_FILE"
echo "" >> "$OUT_FILE"
echo "## Backend KVM Endpoints" >> "$OUT_FILE"
echo "| Environment | KVM Name | Key | Endpoint URL |" >> "$OUT_FILE"
echo "|-------------|----------|-----|--------------|" >> "$OUT_FILE"

echo ""
echo "---------------------------------------------------------"
echo "1. Listing all Apigee API Proxies"
echo "---------------------------------------------------------"
API_JSON=$(curl -s -H "Authorization: Bearer $TOKEN" "https://apigee.googleapis.com/v1/organizations/$PROJECT/apis")
API_ERROR=$(echo "$API_JSON" | jq -r '.error.message // empty')
if [ -n "$API_ERROR" ]; then
    echo "  [!] Error fetching proxies: $API_ERROR"
    exit 1
fi
echo "$API_JSON" | jq -r 'if type=="array" then .[] else (.proxies // .) | .[]? end | if type=="object" then .name else . end | select(. != null)' | while read -r proxy; do
    echo " - $proxy"
done

echo ""
echo "Fetching environments..."
ENV_JSON=$(curl -s -H "Authorization: Bearer $TOKEN" "https://apigee.googleapis.com/v1/organizations/$PROJECT/environments")
ENV_ERROR=$(echo "$ENV_JSON" | jq -r 'if type == "object" and has("error") then .error.message else empty end')
if [ -n "$ENV_ERROR" ]; then
    echo "  [!] Error fetching environments: $ENV_ERROR"
    exit 1
fi
ENVS=$(echo "$ENV_JSON" | jq -r 'if type=="array" then .[] else empty end | select(type=="string")')

if [ -z "$ENVS" ]; then
    echo "  No environments found or unable to parse..."
    exit 0
fi

for ENV in $ENVS; do
    echo ""
    echo "---------------------------------------------------------"
    echo "Environment: $ENV"
    echo "---------------------------------------------------------"
    
    # Target Servers
    echo ">>> Target Servers (Another common place for backend URLs):"
    TS_LIST_JSON=$(curl -s -H "Authorization: Bearer $TOKEN" "https://apigee.googleapis.com/v1/organizations/$PROJECT/environments/$ENV/targetservers")
    TS_ERROR=$(echo "$TS_LIST_JSON" | jq -r 'if type == "object" and has("error") then .error.message else empty end')
    if [ -n "$TS_ERROR" ]; then
        echo "    [!] Error fetching target servers: $TS_ERROR"
        TS_LIST=""
    else
        TS_LIST=$(echo "$TS_LIST_JSON" | jq -r 'if type=="array" then .[] else empty end | select(type=="string")')
    fi
    
    if [ -z "$TS_LIST" ]; then
        echo "  None found."
    else
        for TS in $TS_LIST; do
            TS_DATA=$(curl -s -H "Authorization: Bearer $TOKEN" "https://apigee.googleapis.com/v1/organizations/$PROJECT/environments/$ENV/targetservers/$TS")
            HOST=$(echo "$TS_DATA" | jq -r '.host')
            PORT=$(echo "$TS_DATA" | jq -r '.port')
            echo "  - $TS -> $HOST:$PORT"
        done
    fi

    # KVMs
    echo ""
    echo ">>> KVMs (Key Value Maps):"
    KVM_LIST_JSON=$(curl -s -H "Authorization: Bearer $TOKEN" "https://apigee.googleapis.com/v1/organizations/$PROJECT/environments/$ENV/keyvaluemaps")
    KVM_ERROR=$(echo "$KVM_LIST_JSON" | jq -r 'if type == "object" and has("error") then .error.message else empty end')
    if [ -n "$KVM_ERROR" ]; then
        echo "    [!] Error fetching KVMs: $KVM_ERROR"
        KVM_LIST=""
    else
        KVM_LIST=$(echo "$KVM_LIST_JSON" | jq -r 'if type=="array" then .[] else empty end | select(type=="string")')
    fi
    
    if [ -z "$KVM_LIST" ]; then
        echo "  None found."
    else
        for KVM in $KVM_LIST; do
            echo "  * KVM Name: $KVM"
            
            # Fetch entries
            ENTRIES=$(curl -s -H "Authorization: Bearer $TOKEN" "https://apigee.googleapis.com/v1/organizations/$PROJECT/environments/$ENV/keyvaluemaps/$KVM")
            # In Apigee API v1, sometimes .keyValueEntries isn't populated directly from list, need to call the entries endpoint or it's within the KVM data
            
            # Try fetching entries sub-resource
            ENTRIES=$(curl -s -H "Authorization: Bearer $TOKEN" "https://apigee.googleapis.com/v1/organizations/$PROJECT/environments/$ENV/keyvaluemaps/$KVM/entries")
            
            ERROR=$(echo "$ENTRIES" | jq -r 'if type == "object" and has("error") then .error.message else empty end')
            if [ -n "$ERROR" ]; then
                 echo "    [!] Error fetching entries: $ERROR"
            else
                 # Check if the array exists and iterate
                 HAS_ENTRIES=$(echo "$ENTRIES" | jq -e 'has("keyValueEntries")')
                 if [ "$HAS_ENTRIES" == "true" ]; then
                     echo "$ENTRIES" | jq -c '.keyValueEntries[]?' | while read -r entry; do
                         KEY=$(echo "$entry" | jq -r '.name')
                         VAL=$(echo "$entry" | jq -r '.value')
                         echo "    > $KEY = $VAL"
                         
                         # Check if it looks like an endpoint or backend URL
                         if [[ "$KEY" == *"endpoint"* ]] || [[ "$KEY" == *"url"* ]] || [[ "$VAL" == http* ]]; then
                             echo "| $ENV | $KVM | $KEY | $VAL |" >> "$OUT_FILE"
                         fi
                     done
                 else
                     echo "    (No entries found or KVM is encrypted and hidden)"
                 fi
            fi
        done
    fi
done

echo ""
echo "Done. Results saved to $OUT_FILE"
