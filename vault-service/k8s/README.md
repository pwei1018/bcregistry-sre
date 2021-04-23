
# RBAC
oc process -f k8s/templates/rbac.yaml -o yaml | oc apply -f - -n 73c567-dev

oc process -f k8s/templates/rbac.yaml -p TAG=test -o yaml | oc apply -f - -n 73c567-test

oc process -f k8s/templates/rbac.yaml -p TAG=prod -o yaml | oc apply -f - -n 73c567-prod

# buildconfig
oc process -f k8s/templates/bc.yaml -o yaml | oc apply -f - -n 73c567-tools

# deploymentconfig, service and route
oc process -f k8s/templates/dc.yaml -o yaml | oc apply -f - -n 73c567-dev

oc process -f k8s/templates/dc.yaml -p TAG=test -o yaml | oc apply -f - -n 73c567-test

oc process -f k8s/templates/dc.yaml -p TAG=prod -o yaml | oc apply -f - -n 73c567-prod

