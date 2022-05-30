
# deploymentconfig, service, secrets and PVC
oc process -f notify-db.yaml -o yaml | oc apply -f - -n d893f6-dev
oc process -f notify-db.yaml -p TAG=test -o yaml | oc apply -f - -n d893f6-test
oc process -f notify-db.yaml -p TAG=prod -o yaml | oc apply -f - -n d893f6-prod
