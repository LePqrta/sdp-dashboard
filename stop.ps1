$ErrorActionPreference = "SilentlyContinue"

$Ports = @(3000, 8000)

foreach ($Port in $Ports) {
    $ProcessIds = netstat -ano |
        Select-String ":$Port" |
        ForEach-Object { ($_ -split "\s+")[-1] } |
        Where-Object { $_ -match "^\d+$" } |
        Select-Object -Unique

    foreach ($ProcessId in $ProcessIds) {
        Stop-Process -Id ([int]$ProcessId) -Force
    }
}

Write-Host "Stopped dashboard processes on ports 3000 and 8000."
