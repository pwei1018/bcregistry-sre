
export PROJECT_ID=
gcloud config set project ${PROJECT_ID}

SERVICE_NAME="api"
ROLE_NAME="role$SERVICE_NAME"
SA_NAME="sa-$SERVICE_NAME"
SA_FULL_NAME="$SA_NAME@${PROJECT_ID}.iam.gserviceaccount.com"
SA_DESCRIPTION="Service Account for running $SERVICE_NAME services"
SA_ROLE="projects/${PROJECT_ID}/roles/$ROLE_NAME"

if [[ -z `gcloud iam roles describe $ROLE_NAME --project=${PROJECT_ID} --verbosity=none`]]
then
    gcloud iam roles create $ROLE_NAME --quiet --project=${PROJECT_ID} --file=role-$SERVICE_NAME.yaml
else
    gcloud iam roles update $ROLE_NAME --quiet --project=${PROJECT_ID} --file=role-$SERVICE_NAME.yaml
fi

## API service account
gcloud iam service-accounts create $SA_NAME \
    --description="$SA_DESCRIPTION" \
    --display-name="$SA_NAME"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:$SA_FULL_NAME" \
    --role="$SA_ROLE"

gcloud iam service-accounts list --filter $SA_NAME
gcloud iam roles describe $ROLE_NAME --project=${PROJECT_ID}