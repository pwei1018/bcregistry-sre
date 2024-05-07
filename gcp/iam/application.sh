
#!/bin/bash

declare -a environments=("dev" "test" "tools" "prod" "integration" "sandbox")
declare -a projects=("")
declare -a services=("api" "job" "queue")

for ev in "${environments[@]}"
do
    for ns in "${projects[@]}"
    do
        echo "project: $ns-$ev"
        PROJECT_ID=$ns-$ev

        if [[ ! -z `gcloud projects describe ${PROJECT_ID} --verbosity=none` ]]; then
            gcloud config set project ${PROJECT_ID}

            for se in "${services[@]}"
            do
                ROLE_NAME="role$se"
                SA_NAME="sa-$se"
                SA_FULL_NAME="$SA_NAME@${PROJECT_ID}.iam.gserviceaccount.com"
                SA_DESCRIPTION="Service Account for running $se services"
                SA_ROLE="projects/${PROJECT_ID}/roles/$ROLE_NAME"

                # create/update role
                if [[ -z `gcloud iam roles describe $ROLE_NAME --project=${PROJECT_ID} --verbosity=none` ]]; then
                    gcloud iam roles create $ROLE_NAME --quiet --project=${PROJECT_ID} --file=role-$se.yaml
                else
                    gcloud iam roles update $ROLE_NAME --quiet --project=${PROJECT_ID} --file=role-$se.yaml
                fi

                # create service account
                if [[ -z `gcloud iam service-accounts describe $SA_FULL_NAME --project=${PROJECT_ID} --verbosity=none` ]]; then
                    gcloud iam service-accounts create $SA_NAME \
                        --description="$SA_DESCRIPTION" \
                        --display-name="$SA_NAME"
                fi

                # role binding
                gcloud projects add-iam-policy-binding ${PROJECT_ID} \
                    --member="serviceAccount:$SA_FULL_NAME" \
                    --role="$SA_ROLE"
            done
        fi
    done
done