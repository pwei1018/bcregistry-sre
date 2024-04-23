
#!/bin/bash

declare -a environments=("dev" "test" "tools" "prod" "integration" "sandbox")
#declare -a projects=("a083gt" "mvnjri" "gtksf3" "yfjq17" "c4hnrd" "k973yf" "yfthig" "eogruh" "bcrbk9")
declare -a projects=("bcrbk9")
declare -a service="cdcloudrun"

for ev in "${environments[@]}"
do
    for ns in "${projects[@]}"
    do
        echo "project: $ns-$ev"
        PROJECT_ID=$ns-$ev

        if [[ ! -z `gcloud projects describe ${PROJECT_ID} --verbosity=none` ]]; then
            gcloud config set project ${PROJECT_ID}

            PROJECT_NUMBER=`gcloud projects list --filter="$(gcloud config get-value project)" --format="value(PROJECT_NUMBER)"`

            ROLE_NAME="$service"
            SA_FULL_NAME="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
            SA_ROLE="projects/${PROJECT_ID}/roles/$ROLE_NAME"

            if [[ -z `gcloud iam roles describe $ROLE_NAME --project=${PROJECT_ID} --verbosity=none` ]]; then
                gcloud iam roles create $ROLE_NAME --quiet --project=${PROJECT_ID} --file=role-$service.yaml
            else
                gcloud iam roles update $ROLE_NAME --quiet --project=${PROJECT_ID} --file=role-$service.yaml
            fi

            gcloud projects add-iam-policy-binding ${PROJECT_ID} \
                --member="serviceAccount:$SA_FULL_NAME" \
                --role="$SA_ROLE"

            gcloud projects add-iam-policy-binding ${PROJECT_ID} \
            --member="serviceAccount:331250273634-compute@developer.gserviceaccount.com" \
            --role="$SA_ROLE"

            gcloud projects add-iam-policy-binding ${PROJECT_ID} \
                --member="serviceAccount:331250273634@cloudbuild.gserviceaccount.com" \
                --role="$SA_ROLE"

            SA_ROBOT_FULL_NAME="service-${PROJECT_NUMBER}@serverless-robot-prod.iam.gserviceaccount.com"
            gcloud projects add-iam-policy-binding ${PROJECT_ID} \
            --member="serviceAccount:$SA_ROBOT_FULL_NAME" \
            --role="$SA_ROLE"

            SA_DEPLOY_ROLE="projects/c4hnrd-tools/roles/$ROLE_NAME"
            gcloud projects add-iam-policy-binding c4hnrd-tools \
            --member="serviceAccount:$SA_ROBOT_FULL_NAME" \
            --role="$SA_DEPLOY_ROLE"
        fi
    done
done