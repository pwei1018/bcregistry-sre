#!/bin/bash

cd ../mocha-e2e
export $(grep -v '^#' .env | sed 's/\r//' | xargs  )  # Load environment variables

gcloud config set disable_prompts true
gcloud config set compute/region $REGION  # Set the region

echo "Setting project to $PROJECT_ID"
gcloud config set project $PROJECT_ID  # Set the project

gcloud functions deploy $FUNCTION_NAME \
--gen2 \
--runtime=$RUNTIME \
--region=$REGION \
--source=. \
--entry-point=$ENTRY_POINT \
--memory=$MEMORY \
--timeout=$TIMEOUT \
--trigger-http \
--service-account=$SERVICE_ACCOUNT \
--project=$PROJECT_ID \
--no-allow-unauthenticated \
--set-env-vars REGISTRY_HOME_URL=$REGISTRY_HOME_URL,APP_AUTH_WEB_URL=$APP_AUTH_WEB_URL,NAMES_HOME_URL=$NAMES_HOME_URL \
--set-secrets 'USERNAMESCBC=USERNAMESCBC:latest,PWDSCBC=PWDSCBC:latest,USERNAMEIDIR=USERNAMEIDIR:latest,PWDIDIR=PWDIDIR:latest'

gcloud monitoring uptime create $UPTIME_CHECK_NAME \
--synthetic-target=projects/$PROJECT_ID/locations/$REGION/functions/$FUNCTION_NAME \
--period=5 \
--timeout=60
