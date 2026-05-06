#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export TOOL_ERROR_MODE="${TOOL_ERROR_MODE:-malformed}"
exec python -m agent_incident_lab s1
