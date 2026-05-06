Set-Location (Split-Path $PSScriptRoot -Parent)
$env:TOOL_ERROR_MODE = if ($env:TOOL_ERROR_MODE) { $env:TOOL_ERROR_MODE } else { "malformed" }
python -m agent_incident_lab s1
