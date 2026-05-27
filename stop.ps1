$ErrorActionPreference = "Stop"

$RootDir = $PSScriptRoot
node (Join-Path $RootDir "scripts\stop-local-services.js")
