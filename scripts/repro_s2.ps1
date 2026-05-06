Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not $env:RATE_LIMIT_FAIL_COUNT) { $env:RATE_LIMIT_FAIL_COUNT = "2" }
python -m agent_incident_lab s2
