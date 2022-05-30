helm repo list

helm repo update

helm search repo

helm install notify-api bcregistry/bcregistry-api -f values.dev.yaml --namespace d893f6-dev

helm install notify-api bcregistry/bcregistry-api -f values.test.yaml --namespace d893f6-test

helm install notify-api bcregistry/bcregistry-api -f values.prod.yaml --namespace d893f6-prod


helm upgrade notify-api bcregistry/bcregistry-api -f values.dev.yaml --namespace d893f6-dev

helm upgrade notify-api bcregistry/bcregistry-api -f values.test.yaml --namespace d893f6-test

helm upgrade notify-api bcregistry/bcregistry-api -f values.prod.yaml --namespace d893f6-prod