#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export RATE_LIMIT_FAIL_COUNT="${RATE_LIMIT_FAIL_COUNT:-2}"
exec python -m agent_incident_lab s2
