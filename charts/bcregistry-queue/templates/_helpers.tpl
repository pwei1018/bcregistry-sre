{{/* vim: set filetype=mustache: */}}
{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "bcregistry-queue.fullname" -}}
{{- .Release.Name -}}-{{- .Values.environment -}}
{{- end -}}

{{/*
Expand the name of the chart.
*/}}
{{- define "bcregistry-queue.name" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Expand the db miagration name of the chart.
*/}}
{{- define "bcregistry-queue.dbMiagrationName" -}}
{{- .Release.Name -}}-db-miagration-{{- .Values.environment -}}
{{- end -}}

{{/*
Expand the db miagration name of the chart.
*/}}
{{- define "bcregistry-queue.secretName" -}}
{{- .Release.Name -}}-{{- .Values.environment -}}-secret
{{- end -}}

{{/*
{{- end -}}

{{/*
Common labels
*/}}
{{- define "bcregistry-queue.labels" -}}
{{ include "bcregistry-queue.selectorLabels" . }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "bcregistry-queue.selectorLabels" -}}
name: {{ include "bcregistry-queue.name" . }}
environment: {{ .Values.environment }}
role: {{ .Values.role }}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "bcregistry-queue.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default (include "bcregistry-queue.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}


{{/*
image full path
*/}}
{{- define "bcregistry-queue.image" -}}
{{- printf "%s/%s/%s@%s" .Values.image.repository .Values.image.namespace (include "bcregistry-queue.name" .) .Values.image.digest }}
{{- end -}}

{{/*
host full url
*/}}
{{- define "bcregistry-queue.host" -}}
{{- printf "%s.%s" (include "bcregistry-queue.fullname" .) .Values.route.routerCanonicalHostname }}
{{- end -}}
