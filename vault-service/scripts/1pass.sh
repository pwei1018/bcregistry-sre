#!/bin/bash


# =================================================================================================================
# Usage:
# -----------------------------------------------------------------------------------------------------------------
usage() {
  cat <<-EOF
  A helper script to get the secrcts from 1password' vault.
  Usage: ./1pass.sh [-h <help>
                     -m <method>
                     -e <environment(s)>
                     -v <vaultDetails>
                     -a <appName>
                     -n <namespace>
                     -f <frontend>

  OPTIONS:
  ========
    -h prints the usage for the script.
    -m The methodof using the vaults.
        secret - set vault values to Openshift secrets
    -e The environment(s) of the vault, for example pytest/dev/test/prod or "dev test".
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

EOF
exit
}

# -----------------------------------------------------------------------------------------------------------------
# Initialization:
# -----------------------------------------------------------------------------------------------------------------
while getopts h:a:v:m:e:n:r:f: FLAG; do
  case $FLAG in
    h ) usage ;;
    a ) APP_NAME=$OPTARG ;;
    v ) VAULT=$OPTARG ;;
    m ) METHOD=$OPTARG ;;
    e ) ENVIRONMENT=$OPTARG ;;
    n ) NAMESPACE=$OPTARG ;;
    r ) DEPLOYMENT=$OPTARG ;;
    f ) FRONTEND=$OPTARG ;;
    \? ) #unrecognized option - show help
      echo -e \\n"Invalid script option: -${OPTARG}"\\n
      usage
      ;;
  esac
done

# Shift the parameters in case there any more to be used

shift $((OPTIND-1))
# echo Remaining arguments: $@

deployment_true=(true t TRUE T True 1)
if [[ " ${deployment_true[@]} " =~ " ${DEPLOYMENT} " ]]; then
  DEPLOYMENT=true
else
  DEPLOYMENT=false
fi

if [ -z "${ENVIRONMENT}" ]; then
  echo -e \\n"Missing parameters - environment"\\n
  usage
fi

if [ -z "${VAULT}" ]; then
  echo -e \\n"Missing parameters - vault"\\n
  usage
fi

methods=(secret env)
if [[ ! " ${methods[@]} " =~ " ${METHOD} " ]]; then
  echo -e \\n"Method must be contain one of the following method: secret or env."\\n
  usage
fi

envs=(${ENVIRONMENT})
case  ${ENVIRONMENT}  in
  dev)
    envs=('dev')
    ;;
  test)
    envs=('dev' 'test')
    ;;
  prod)
    envs=('test' 'prod')
    ;;
esac

if [[ " secret " =~ " ${METHOD} " ]]; then
  if [[ -z "${APP_NAME}" ]]; then
    echo -e \\n"Missing parameters - application name"\\n
    usage
  else
    if [[ -z "${NAMESPACE}" ]]; then
      echo -e \\n"Missing parameters - namespace"\\n
      usage
    fi
  fi
fi

frontend_true=(true t TRUE T True 1)
if [[ " ${frontend_true[@]} " =~ " ${FRONTEND} " ]]; then
  FRONTEND=true
else
  FRONTEND=false
fi

# Login to 1Password../s
# Assumes you have installed the OP CLI and performed the initial configuration
# For more details see https://support.1password.com/command-line-getting-started/
op_session=$(echo "${MASTER_PASSWORD}" | op signin ${DOMAIN_NAME} ${USERNAME} ${SECRET_KEY} | grep export | awk -F\" '{print $2}')
export OP_SESSION_registries="$op_session"

random_name=`cat /dev/urandom | tr -cd 'a-f0-9' | head -c 32`
num=0
for env_name in "${envs[@]}"; do

  num=$((num+1))
  for vault_name in $(echo "${VAULT}" | jq -r '.[] | @base64' ); do
    _vault_json() {
      # decode vault json values
      echo ${vault_name} | base64 --decode | jq -r ${1}
    }

    for application_name in $(echo "$(_vault_json '.application')" | jq -r '.[]| @base64' ); do
      # decode application json values
      _vault_json_app() {
        echo ${application_name} | base64 --decode
      }

      # My setup uses a 1Password type of 'Password' and stores all records within a
      # single section. The label is the key, and the value is the value.
      ev=`op get item --vault=$(_vault_json .vault) ${env_name}`

      touch t$num-$random_name.txt

      # Convert to base64 for multi-line secrets.
      # The schema for the 1Password type uses t as the label, and v as the value.
      for row in $(echo ${ev} | jq -r -c '.details.sections[] | select(.title=='\"$(_vault_json_app)\"') | .fields[] | @base64'); do
          _envvars() {
              echo ${row} | base64 --decode | jq -r ${1}
          }

          echo "${_vault_json_app}: $(_envvars '.t')" >> t$num-$random_name.txt

          if [[ ${env_name} == ${ENVIRONMENT} ]]; then
            # Frontend applications will create a keycloak json file
            if [ $(_vault_json '.vault') = "keycloak" ] && [ ${FRONTEND} = true ]; then
              if [[ ${env_name} == ${ENVIRONMENT} ]]; then
                echo "$(_envvars '.t')=$(_envvars '.v')"  >> tkeycloak-$random_name.txt
              fi
            else
              case  ${METHOD}  in
                secret)
                  echo "$(_envvars '.t')=$(_envvars '.v')" >> tsecret-$random_name.txt
                  ;;
                env)
                  echo "Setting environment variable $(_envvars '.t')"
                  echo ::add-mask::$(_envvars '.v')
                  echo ::echo "$(_envvars '.t')=$(_envvars '.v')" >> $GITHUB_ENV
                  ;;
              esac
            fi
          fi
      done
    done
  done
done

case  ${METHOD}  in
  secret)
    matched=true

    # Compare vaults from different environments
    env_true=(test prod)
    if [[ " ${env_true[@]} " =~ " ${ENVIRONMENT} " ]]; then
      result=$(comm -23 <(sort t1-$random_name.txt) <(sort t2-$random_name.txt))
      result2=$(comm -23 <(sort t2-$random_name.txt) <(sort t1-$random_name.txt))

      if [[ ! -z ${result} ]]; then
        matched=false
        error_message="The following vault items between ${envs[0]} and ${envs[1]} does not match. ${result}"
        echo ::error "::$error_message"
      else
        if [[ ! -z ${result2} ]]; then
          matched=false
          error_message="The following vault items between ${envs[1]} and ${envs[0]} does not match. ${result2}"
          echo ::error "::$error_message"
        fi
      fi
    fi

    # check the duplicat key(s) from vaults
    duplicate_key_check=$(sort tsecret-$random_name.txt | grep -v -P '^\s*#' | sed -E 's/(.*)=.*/\1/' | uniq -d | xargs)
    if [[ ! -z ${duplicate_key_check} ]]; then
      warning_message="Duplicate key(s) found in 1password. ${duplicate_key_check}"
      echo ::warning "::$warning_message"
      sort tsecret-$random_name.txt | uniq > tsecret1-$random_name.txt
      cp tsecret1-$random_name.txt tsecret-$random_name.txt
    fi

    if [[ $matched = true ]]; then
      if [[ ${FRONTEND} = false ]]; then
        LABELS=$(oc get secret ${APP_NAME}-secret -o jsonpath='{.metadata.labels}' -n ${NAMESPACE})
        ANNOTATIONS=$(oc get secret ${APP_NAME}-secret -o jsonpath='{.metadata.annotations}' -n ${NAMESPACE})
        SECRET_JSON=$(oc create secret generic ${APP_NAME}-secret -n ${NAMESPACE} --from-env-file=./tsecret-$random_name.txt --dry-run=client -o json)
        # Set secret key and value from 1password
        echo $SECRET_JSON | oc replace -f -
        oc patch secret ${APP_NAME}-secret --type='json' -p='[{"op":"add","path":"/metadata/labels", "value":'$LABELS'}]' -n ${NAMESPACE}
        oc patch secret ${APP_NAME}-secret --type='json' -p='[{"op":"add","path":"/metadata/annotations", "value":'$ANNOTATIONS'}]' -n ${NAMESPACE}

        if [[ ${DEPLOYMENT} = true ]]; then
          # Set environment variable of deployment config
          for secret_name in $(oc get dc/${APP_NAME} -n ${NAMESPACE} -o json | jq -r '.spec.template.spec.containers[].env[]? | select(.valueFrom.secretKeyRef.name == '"\"${APP_NAME}-secret"\"') | .name'); do
            # Remove existing environment variables of deployment config
            oc set env dc/${APP_NAME} -n ${NAMESPACE} --containers=${APP_NAME} ${secret_name}-
          done
          oc set env dc/${APP_NAME} -n ${NAMESPACE} --from=secret/${APP_NAME}-secret --containers=${APP_NAME}
        fi
      else
        # frontend application
        # create keycloak configmap
        # remove existing configmap
        KEYCLOAK_LABELS=$(oc get configmap ${APP_NAME}-keycloak-config -o jsonpath='{.metadata.labels}' -n ${NAMESPACE})
        KEYCLOAK_ANNOTATIONS=$(oc get configmap ${APP_NAME}-keycloak-config -o jsonpath='{.metadata.annotations}' -n ${NAMESPACE})

        UI_LABELS=$(oc get configmap ${APP_NAME}-ui-configuration -o jsonpath='{.metadata.labels}' -n ${NAMESPACE})
        UI_ANNOTATIONS=$(oc get configmap ${APP_NAME}-ui-configuration -o jsonpath='{.metadata.annotations}' -n ${NAMESPACE})

        # read each line of keycloak txt to variables
        while read -r line; do declare  "$line"; done <tkeycloak-$random_name.txt

        KEYCLOAK_JSON=$( jq -n \
                          --arg t1 "$KEYCLOAK_REALMNAME" \
                          --arg t2 "$KEYCLOAK_AUTH_BASE_URL" \
                          --arg t3 "$UI_KEYCLOAK_RESOURCE_NAME" \
                          "$KEYCLOAK_TEMPLATE" )
        oc create configmap ${APP_NAME}-keycloak-config -n ${NAMESPACE} --from-literal=keycloak.json="$KEYCLOAK_JSON" -o json --dry-run=client | oc replace -f -
        oc patch configmap ${APP_NAME}-keycloak-config --type='json' -p='[{"op":"add","path":"/metadata/labels", "value":'$KEYCLOAK_LABELS'}]'
        oc patch configmap ${APP_NAME}-keycloak-config--type='json' -p='[{"op":"add","path":"/metadata/annotations", "value":'$KEYCLOAK_ANNOTATIONS'}]'

        # create ui configuraiton configmap
        UI_CONFIG_JSON=$(oc create configmap ${APP_NAME}-configuration -n ${NAMESPACE} --from-env-file=./tsecret-$random_name.txt --dry-run=client -o json | jq '.data')
        oc create configmap ${APP_NAME}-ui-configuration -n ${NAMESPACE} --from-literal=configuration.json="$UI_CONFIG_JSON" -o json --dry-run=client | oc replace -f -
        oc patch configmap ${APP_NAME}-ui-configuration --type='json' -p='[{"op":"add","path":"/metadata/labels", "value":'$UI_LABELS'}]'
        oc patch configmap ${APP_NAME}-ui-configuration --type='json' -p='[{"op":"add","path":"/metadata/annotations", "value":'$UI_ANNOTATIONS'}]'
      fi
    else
      rm t*-$random_name.txt
      exit 1
    fi

    ;;

esac

rm t*-$random_name.txt
exit 0
