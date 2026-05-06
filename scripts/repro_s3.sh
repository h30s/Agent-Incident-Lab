#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec python -m agent_incident_lab s3
