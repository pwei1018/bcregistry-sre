gcloud functions deploy deployment-notification \
--gen2 \
--runtime=python311 \
--region=northamerica-northeast1 \
--source=. \
--entry-point=subscribe \
--trigger-topic=clouddeploy-operations \
--no-allow-unauthenticated