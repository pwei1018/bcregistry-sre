
# buildconfig
oc process -f k8s/templates/bc.yaml -o yaml | oc apply -f - -n 3b2420-tools

# deploymentconfig, service and route
oc process -f k8s/templates/dc.yaml -o yaml | oc apply -f - -n 3b2420-dev

oc process -f k8s/templates/dc.yaml -p TAG=test -p APPLICATION_DOMAIN=downpage-test.apps.silver.devops.gov.bc.ca -o yaml | oc apply -f - -n 3b2420-test

oc process -f k8s/templates/dc.yaml -p TAG=prod -p APPLICATION_DOMAIN=bcregistry-downpage.apps.silver.devops.gov.bc.ca -o yaml | oc apply -f - -n 3b2420-prod

