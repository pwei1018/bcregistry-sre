{{/* vim: set filetype=mustache: */}}
{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "bcregistry-api.fullname" -}}
{{- .Release.Name -}}-{{- .Values.environment -}}
{{- end -}}

{{/*
Expand the name of the chart.
*/}}
{{- define "bcregistry-api.name" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "bcregistry-api.labels" -}}
{{ include "bcregistry-api.selectorLabels" . }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "bcregistry-api.selectorLabels" -}}
name: {{ include "bcregistry-api.name" . }}
environment: {{ .Values.environment }}
role: {{ .Values.role }}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "bcregistry-api.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default (include "bcregistry-api.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}


{{/*
image full path
*/}}
{{- define "bcregistry-api.image" -}}
{{- printf "%s/%s:%s-%s" .Values.image.repository .Values.image.namespace (include "bcregistry-api.fullname" .) .Values.environment }}
{{- end -}}

{{/*
host full url
*/}}
{{- define "bcregistry-api.host" -}}
{{- printf "%s.%s" (include "bcregistry-api.fullname" .) .Values.route.routerCanonicalHostname }}
{{- end -}}
