{{- define "vintage-story.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "vintage-story.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "vintage-story.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "vintage-story.labels" -}}
helm.sh/chart: {{ include "vintage-story.chart" . }}
{{ include "vintage-story.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "vintage-story.selectorLabels" -}}
app.kubernetes.io/name: {{ include "vintage-story.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "vintage-story.secretName" -}}
{{- default (include "vintage-story.fullname" .) .Values.secrets.existingSecret }}
{{- end }}

{{- define "vintage-story.claimName" -}}
{{- default (include "vintage-story.fullname" .) .Values.persistence.existingClaim }}
{{- end }}

{{- define "vintage-story.bool" -}}
{{- ternary "true" "false" . -}}
{{- end }}

