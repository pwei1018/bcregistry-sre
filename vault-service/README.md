
[![img](https://img.shields.io/badge/Lifecycle-Stable-97ca00)](https://github.com/bcgov/repomountie/blob/master/doc/lifecycle-badges.md)

---
description: BC Registries and Online Services Vault Service
ignore: true
---

## About

The vault service is an application that can retrive the vault vaules from 1password service for each BC Registries and Online Services application during the CI/CD flow.

## Usage

```shell
oc -n "$(OPS_REPOSITORY)-tools" exec dc/vault-service -- ./scripts/1pass.sh \
		-m "secret" \
		-e "$(TAG_NAME)" \
		-a "$(DOCKER_NAME)-$(TAG_NAME)" \
		-n "$(OPENSHIFT_REPOSITORY)-$(TAG_NAME)" \
		-v "$(VAULTS)" \
		-r "true" \
		-f "false"
```
### Usage OPTIONS:
```shell
    -h prints the usage for the script.
    -m The method of using the vaults.
        secret - set vault values to Openshift secrets
    -e The environment(s) of the vault, for example dev/test/prod
    -a Openshift application name, for example: auth-api-dev
    -n Openshift namespace name, for example: 1rdehl-dev
    -f Frontend application, for exmaple: true t TRUE T True 1
    -v A list of vault and application name of the 1password account, for example:
       [
          {
              "vault": "shared",
              "application": [
                  "keycloak",
                  "email"
              ]
          },
          {
              "vault": "relationship",
              "application": [
                  "auth-api",
                  "notify-api",
                  "status-api"
              ]
          }
      ]
```
