#!/usr/bin/env bash

LOG_LEVEL="${LOG_LEVEL:-INFO}"

_log_level_value() {
  case "${1^^}" in
    DEBUG) printf '0' ;;
    INFO)  printf '1' ;;
    WARN)  printf '2' ;;
    ERROR) printf '3' ;;
    *)     printf '1' ;;
  esac
}

_log() {
  local level="$1"
  shift
  [[ "$(_log_level_value "$level")" -lt "$(_log_level_value "$LOG_LEVEL")" ]] && return 0
  printf '%s [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$level" "$*"
}

log_debug() { _log DEBUG "$@"; }
log_info() { _log INFO "$@"; }
log_warn() { _log WARN "$@"; }
log_error() { _log ERROR "$@"; }

log_section() {
  printf '\n%s\n' "$(date '+%Y-%m-%d %H:%M:%S') [INFO] === $* ==="
}

log_end() {
  local phase="$1"
  local duration="${2:-0}"
  printf '%s\n' "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Completed: ${phase} (${duration}s)"
}

die() {
  log_error "$*"
  exit 1
}
