# Deployment Script

The deployment script is a bash script that automates the deployment of the function to GCP. It is located in the `deploy` folder. The script is called `deploy.sh` and it uses the environment variables defined in the `.env` file in the mocha-e2e folder.

## Explanation of the Script

```bash
#!/bin/bash

cd ../mocha-e2e
export $(grep -v '^#' .env | sed 's/\r//' | xargs  )  # Load environment variables

gcloud config set disable_prompts true
gcloud config set compute/region $REGION  # Set the region

echo "Setting project to $PROJECT_ID"
gcloud config set project $PROJECT_ID  # Set the project
```

The script starts by changing the directory to the `mocha-e2e` folder and then loads the environment variables from the `.env` file.

The script sets some configurations for the gcloud command-line tool, disabling prompts and setting the region to the one specified in the `.env` file.

```bash
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
```

The script continues by deploying the function to GCP using the `gcloud functions deploy` command. It specifies the function name, runtime, region, source directory, entry point, memory, timeout, trigger type, service account, project ID, and environment variables. Also notice the e=reference to the secrets that the scripts will use.

***Note:*** The `--timeout` value needs to be higher than your expected function execution time.

The source files used are the ones in the current directory (`.`) in this case that is the mocha-e2e folder.

```bash
gcloud monitoring uptime create $UPTIME_CHECK_NAME --synthetic-target=projects/$PROJECT_ID/locations/$REGION/functions/$FUNCTION_NAME --period=5 --timeout=$TIMEOUT
```

Finally, the script creates a monitoring uptime check using the `gcloud monitoring uptime create` command. It specifies the name of the uptime check and the synthetic target.

## Running the Script

To run the deployment script, execute the following command:

```bash
cd deploy
./deploy.sh
```
