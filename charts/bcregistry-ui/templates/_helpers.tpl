{{/* vim: set filetype=mustache: */}}
{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "bcregistry-ui.fullname" -}}
{{- .Release.Name -}}-{{- .Values.environment -}}
{{- end -}}

{{/*
Expand the name of the chart.
*/}}
{{- define "bcregistry-ui.name" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Expand the db miagration name of the chart.
*/}}
{{- define "bcregistry-ui.dbMiagrationName" -}}
{{- .Release.Name -}}-db-miagration-{{- .Values.environment -}}
{{- end -}}

{{/*
Expand the db miagration name of the chart.
*/}}
{{- define "bcregistry-ui.secretName" -}}
{{- .Release.Name -}}-{{- .Values.environment -}}-secret
{{- end -}}

{{/*
{{- end -}}

{{/*
Common labels
*/}}
{{- define "bcregistry-ui.labels" -}}
{{ include "bcregistry-ui.selectorLabels" . }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "bcregistry-ui.selectorLabels" -}}
name: {{ include "bcregistry-ui.name" . }}
environment: {{ .Values.environment }}
role: {{ .Values.role }}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "bcregistry-ui.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default (include "bcregistry-ui.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}


{{/*
image full path
*/}}
{{- define "bcregistry-ui.image" -}}
{{- printf "%s/%s/%s@%s" .Values.image.repository .Values.image.namespace (include "bcregistry-ui.name" .) .Values.image.digest }}
{{- end -}}

{{/*
host full url
*/}}
{{- define "bcregistry-ui.host" -}}
{{- printf "%s.%s" (include "bcregistry-ui.fullname" .) .Values.route.routerCanonicalHostname }}
{{- end -}}
