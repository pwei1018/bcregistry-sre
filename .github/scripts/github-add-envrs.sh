#!/usr/bin/env bash

GITHUB_USER="bcgov"
GITHUB_REPOS=("$@")

#if [[ ${#GITHUB_REPOS[@]} -eq 0 ]]; then
GITHUB_REPOS=($(gh repo list bcgov --topic "bcregistry" --json name | jq '.[].name' | tr -d '"'))
#fi

for GITHUB_REPO in "${GITHUB_REPOS[@]}"; do
    echo "[$GITHUB_REPO]"

    gh secret set GCP_SERVICE_ACCOUNT --body "" --repo "$GITHUB_USER/$GITHUB_REPO"
    gh secret set WORKLOAD_IDENTIFY_POOLS_PROVIDER --body "" --repo "$GITHUB_USER/$GITHUB_REPO"

    case $GITHUB_REPO in
        "namerequest")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "sbc-apigw")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "business-filings-ui")
            CODECOV_UPLOAD_TOKEN=f
            ;;
        "business-edit-ui")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "lear")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "sbc-pay")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "ppr")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "name-examination")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "business-transparency-registry")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "sbc-auth")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "business-create-ui")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "registries-search")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "fas-ui")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "bcregistry")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "sbc-producthub")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "sbc-common-components")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "STRR")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "business-ar")
            CODECOV_UPLOAD_TOKEN=
            ;;
        "namex")
            CODECOV_UPLOAD_TOKEN=
            ;;
        *)
            CODECOV_UPLOAD_TOKEN=""
            ;;
    esac

    gh secret set CODECOV_TOKEN --body "$CODECOV_UPLOAD_TOKEN" --repo "$GITHUB_USER/$GITHUB_REPO"

done
