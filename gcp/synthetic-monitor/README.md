# Overview

This Synthetic Monitor uses the `@google-cloud/synthetics-sdk-mocha` to create a Google Cloud Function that can be used with Google Cloud Monitoring Synthetics. The Mocha scripts included in this project are used to test the availability of the BC Registries and Online Services applications. These scripts can be expanded to include additional tests as needed.

Google Cloud Monitoring provides a Synthetic Monitoring service that can be used to monitor the availability of your applications. This service allows you to create uptime checks that can be used to monitor the availability of your applications from different locations around the world.

The Synthetic Monitoring service supports different types of uptime checks, including HTTP, HTTPS, TCP, and PING checks. You can also create uptime checks using the Cloud Monitoring API.

The Synthetic Monitoring service also provides a set of pre-built uptime checks that you can use to monitor the availability of popular services like Google Search, Google Cloud Console, and Google Cloud Storage.

The code here is based on the samples found in the [GoogleCloudPlatform/synthetics-sdk-nodejs Repo](https://github.com/GoogleCloudPlatform/synthetics-sdk-nodejs).

## Installation

### Build all packages

```bash
cd mocha-e2e
npm install
```

### Create .env file

Create a .env file with the following content (remove the comments):

```bash
FUNCTION_NAME="<sample function name>"
PROJECT_ID="<project-id>"
RUNTIME="nodejs20"
REGION="northamerica-northeast1"
ENTRY_POINT="SyntheticMochaSuite"
MEMORY="2G"
TIMEOUT="60"
SERVICE_ACCOUNT="<Service Account for the Monitor>"
UPTIME_CHECK_NAME="<Alert Name>"

# Sensitive information - handle with care and consider alternatives if possible
USERNAMESCBC="<SCBC User Name>"
PWDSCBC="<Password>"
USERNAMEIDIR="<IDIR User Name>"
PWDIDIR="<IDIR PW>"

# Example URLS
REGISTRY_HOME_URL="https://test.bcregistry.gov.bc.ca/"
APP_AUTH_WEB_URL="https://test.account.bcregistry.gov.bc.ca/"
NAMES_HOME_URL="https://test.names.bcregistry.gov.bc.ca/"
PAYMENT_HOME_URL="https://test.payments.bcregistry.gov.bc.ca/"
```

## Running

The following command runs this Synthetic Monitor locally

```bash
npx functions-framework --target=SyntheticMochaSuite
```

or

```bash
npm run start
```

## Deploy on GCP

In the `deploy` folder, there is a script that can be used to deploy the function to GCP.
More details in the README there.

### Manually Create Secrets

The Synthetic Monitor uses the Secret Manager to store/read sensitive information. The following secrets need to be created:

- **USERNAMESCBC** (BC Services Card Username)
- **PWDSCBC** (BC Services Card Password)
- **USERNAMEIDIR** (IDIR Username)
- **PWDIDIR** (IDIR Password)

### Pre-requisites for GCP Deployment

1. Create a Service Account with the following roles:

   - Cloud Functions Developer
   - Cloud Run Admin
   - Cloud Run Service Agent
   - Logs Writer
   - Monitoring Editor
   - Secret Manager Secret Accessor
   - Secret Manager Viewer

2. The user you working as (if you are not an admin) needs to have the following roles:

   - Cloud Functions Developer
   - Error Reporting Admin
   - Cloud Run Admin
   - Monitoring Editor
   - Role Developer
   - Secret Manager Admin
   - Security Center Assets Viewer
   - Security Center Findings Viewer
   - Service Account User

## Other Synthetic Monitoring options

https://console.cloud.google.com/monitoring/synthetic-monitoring

When creating a synthetic uptime check, you'll see that here are several templates available that you can use to create your uptime check. These templates are Mocha and Broken Link Checker.
The Mocho template allows you to create a synthetic uptime check using a Mocha test script. The Broken Link Checker template allows you to create a synthetic uptime check that checks for broken links on your website.
