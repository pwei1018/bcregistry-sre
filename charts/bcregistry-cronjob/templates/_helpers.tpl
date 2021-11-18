{{/* vim: set filetype=mustache: */}}
{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "bcregistry-cronjob.fullname" -}}
{{- .Release.Name -}}-{{- .Values.environment -}}
{{- end -}}

{{/*
Expand the name of the chart.
*/}}
{{- define "bcregistry-cronjob.name" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Expand the db miagration name of the chart.
*/}}
{{- define "bcregistry-cronjob.dbMiagrationName" -}}
{{- .Release.Name -}}-db-miagration-{{- .Values.environment -}}
{{- end -}}

{{/*
Expand the db miagration name of the chart.
*/}}
{{- define "bcregistry-cronjob.secretName" -}}
{{- .Release.Name -}}-{{- .Values.environment -}}-secret
{{- end -}}

{{/*
{{- end -}}

{{/*
Common labels
*/}}
{{- define "bcregistry-cronjob.labels" -}}
{{ include "bcregistry-cronjob.selectorLabels" . }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "bcregistry-cronjob.selectorLabels" -}}
name: {{ include "bcregistry-cronjob.name" . }}
environment: {{ .Values.environment }}
role: {{ .Values.role }}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "bcregistry-cronjob.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default (include "bcregistry-cronjob.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}


{{/*
image full path
*/}}
{{- define "bcregistry-cronjob.image" -}}
{{- printf "%s/%s/%s@%s" .Values.image.repository .Values.image.namespace (include "bcregistry-cronjob.name" .) .Values.image.digest }}
{{- end -}}

{{/*
host full url
*/}}
{{- define "bcregistry-cronjob.host" -}}
{{- printf "%s.%s" (include "bcregistry-cronjob.fullname" .) .Values.route.routerCanonicalHostname }}
{{- end -}}
