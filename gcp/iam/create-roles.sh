
#!/bin/bash

declare -a environments=("dev" "test" "tools" "prod" "integration" "sandbox")
declare -a projects=("a083gt" "mvnjri" "gtksf3" "yfjq17" "c4hnrd" "k973yf" "yfthig" "eogruh")
declare -a roles=("api" "job" "queue" "developer")

for ev in "${environments[@]}"
do
    for ns in "${projects[@]}"
    do
        echo "project: $ns-$ev"
        PROJECT_ID=$ns-$ev

        if [[ ! -z `gcloud projects describe ${PROJECT_ID} --verbosity=none` ]]; then
            gcloud config set project ${PROJECT_ID}

            for ro in "${roles[@]}"
            do
                ROLE_NAME="role$ro"
                if [[ -z `gcloud iam roles describe $ROLE_NAME --project=${PROJECT_ID} --verbosity=none` ]]; then
                    echo "  Create: $ROLE_NAME"
                    gcloud iam roles create $ROLE_NAME --quiet --verbosity=none --project=${PROJECT_ID} --file=role-$ro.yaml
                else
                    echo "  Update: $ROLE_NAME"
                    gcloud iam roles update $ROLE_NAME --quiet --verbosity=none --project=${PROJECT_ID} --file=role-$ro.yaml
                fi
            done
        fi
    done
done