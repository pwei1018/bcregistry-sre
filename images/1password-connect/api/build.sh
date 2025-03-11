#!/bin/bash

#login to openshift first

export OPENSHIFT_DOCKER_REGISTRY=image-registry.apps.gold.devops.gov.bc.ca
export OPENSHIFT_LOGIN_REGISTRY=https://api.gold.devops.gov.bc.ca:6443
export OPENSHIFT4_IMAGE_REGISTRY=image-registry.openshift-image-registry.svc:5000

export OPENSHIFT_SA_NAME=$(oc whoami)
export OPENSHIFT_SA_TOKEN=$(oc whoami -t)

export OPENSHIFT_REPOSITORY=d2b3d8

export DOCKER_NAME=1password-connect-api

REGISTRY_IMAGE=$OPENSHIFT_DOCKER_REGISTRY/$OPENSHIFT_REPOSITORY-tools/$DOCKER_NAME


echo "$OPENSHIFT_SA_TOKEN" | docker login $OPENSHIFT_DOCKER_REGISTRY -u $OPENSHIFT_SA_NAME --password-stdin
docker build --no-cache -t $DOCKER_NAME .
docker tag gcp-sre $REGISTRY_IMAGE:latest
docker push $REGISTRY_IMAGE:latest
