[![img](https://img.shields.io/badge/Lifecycle-Experimental-339999)](https://github.com/bcgov/repomountie/blob/master/doc/lifecycle-badges.md)

# BC Registries Services Helm Charts Repository

## TL;DR

```bash
$ helm repo add bcregistry https://bcgov.github.io/bcregistry-charts
$ helm search repo bcregistry
$ helm install my-app-name bcregistry/<chart> --namespace <namespace> -f <override value file>
```

### Prerequisites
- OpenShift 4.5+
- Kubernetes 1.12+
- Helm 3.1.0+


### Install Helm

Helm is a tool for managing Kubernetes charts. Charts are packages of pre-configured Kubernetes resources.

To install Helm, refer to the [Helm install guide](https://github.com/helm/helm#install) and ensure that the `helm` binary is in the `PATH` of your shell.

### Add Repo

The following command allows you to download and install all the charts from this repository:

```bash
$ helm repo add bcregistry https://bcgov.github.io/bcregistry-charts
```
### Using Helm

Please refer to the [Quick Start guide](https://helm.sh/docs/intro/quickstart/) if you wish to get running in just a few commands, otherwise the [Using Helm Guide](https://helm.sh/docs/intro/using_helm/) provides detailed instructions on how to use the Helm client to manage packages on your Kubernetes cluster.

Useful Helm Client Commands:
* View available charts: `helm search repo`
* Install a chart from repo: `helm install my-app-name bcregistry/<chart> --namespace <namespace> -f <override value file>`
* Install a chart from local: `helm dep up & helm install my-app-name ./charts/<chart> --namespace <namespace> -f <override value file>`
* Upgrade your application: `helm upgrade my-app-name --namespace <namespace> -f <override value file>`
* Uninstall/delete your application: `helm uninstall/delete --namespace <namespace> my-app-name`

### Charts

| Name | Description | Supprt Applications |
| --------- | ----------- | ------- |
| `bcregistry-api` | Chart for API applications | `[auth-api,pay-api,legal-api,namex-api,notify-api,colin-api,status-api,search-api,ppr-api]` |
| `bcregistry-ui` | Chart for UI applications | `[auth-web,namerequest-ui,business-filings-ui,business-edit-ui,business-create-ui,search-web,namex-ui]` |
| `bcregistry-queue` | Chart for Queue Service applications | `[notify-queue,entity-filer,entity-emailer,entity-pay,account-mailer,activity-log-listener,events-listener,payment-reconciliations,namex-pay]` |
| `bcregistry-job` | Chart for Job Service applications | `[future-effective-filings,update-colin-filings,update-legal-filings,ftp-poller,payment-jobs,inprogress_update,nro-extractor,nro-update]` |
