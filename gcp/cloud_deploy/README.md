
# Instructions for Create/update CloudDeploy targets

```bash
PROJECTY=xxxxx
PROJECT-SANDBOX=xxxxx-xxxxx
REGION=northamerica-northeast1

gcloud deploy apply --file=clouddeploy-targets.yaml  --region=${REGION}  --project=c4hnrd-tools
```