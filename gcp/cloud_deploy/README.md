
# Instructions for Create/update CloudDeploy targets

```bash
PROJECTY=xxxxx-dev
REGION=northamerica-northeast1

gcloud deploy apply --file=clouddeploy-targets.yaml  --region=${REGION}  --project=c4hnrd-tools
```