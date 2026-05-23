$ErrorActionPreference = "Stop"

$RootDir = $PSScriptRoot
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
$NextBuild = Join-Path $FrontendDir ".next\BUILD_ID"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Backend virtual environment is missing. Run npm.cmd run dev once to install local setup."
    exit 1
}

if (-not (Test-Path $NextBuild)) {
    Write-Host "Production frontend build is missing. Run npm.cmd run prepare-demo first."
    exit 1
}

Write-Host "Starting optimized demo servers..."
Write-Host "Backend:  http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"
Write-Host "Press Ctrl+C to stop."
Write-Host ""

$Jobs = @()

$Jobs += Start-Job -Name "churn-backend-demo" -ScriptBlock {
    param($BackendDir, $VenvPython)
    Set-Location $BackendDir
    & $VenvPython -m uvicorn app.main:app --port 8000
} -ArgumentList $BackendDir, $VenvPython

$Jobs += Start-Job -Name "churn-frontend-demo" -ScriptBlock {
    param($FrontendDir)
    Set-Location $FrontendDir
    $env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"
    npm.cmd run start
} -ArgumentList $FrontendDir

try {
    while ($true) {
        foreach ($Job in $Jobs) {
            Receive-Job $Job
            if ($Job.State -in @("Failed", "Stopped", "Completed")) {
                throw "$($Job.Name) exited with state $($Job.State)."
            }
        }
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host ""
    Write-Host "Stopping demo servers..."
    Stop-Job $Jobs -ErrorAction SilentlyContinue
    Remove-Job $Jobs -Force -ErrorAction SilentlyContinue
}
