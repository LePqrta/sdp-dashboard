$ErrorActionPreference = "Stop"

$RootDir = $PSScriptRoot
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
$PidDir = Join-Path $RootDir ".dashboard-pids"

function Test-PythonPackage {
    param([string]$PackageName)

    & $VenvPython -c "import $PackageName" *> $null
    return $LASTEXITCODE -eq 0
}

function Test-PortOpen {
    param([int]$Port)

    $Client = New-Object System.Net.Sockets.TcpClient
    try {
        $Client.Connect("127.0.0.1", $Port)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $Client.Close()
    }
}

function Stop-PortProcess {
    param([int]$Port)

    $ProcessIds = netstat -ano |
        Select-String ":$Port" |
        ForEach-Object { ($_ -split "\s+")[-1] } |
        Where-Object { $_ -match "^\d+$" } |
        Select-Object -Unique

    foreach ($ProcessId in $ProcessIds) {
        Stop-Process -Id ([int]$ProcessId) -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Preparing churn dashboard dev environment..."

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating backend virtual environment..."
    Push-Location $BackendDir
    python -m venv .venv
    Pop-Location
}

if (-not (Test-PythonPackage "fastapi")) {
    Write-Host "Installing backend dependencies..."
    Push-Location $BackendDir
    & $VenvPython -m pip install -r requirements.txt
    Pop-Location
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $FrontendDir
    npm.cmd install
    Pop-Location
}

if (Test-PortOpen 3000) {
    Write-Host "Stopping stale frontend process on port 3000..."
    Stop-PortProcess 3000
}

if (Test-Path (Join-Path $FrontendDir ".next")) {
    Write-Host "Clearing frontend dev cache..."
    Remove-Item -LiteralPath (Join-Path $FrontendDir ".next") -Recurse -Force
}

Write-Host ""
Write-Host "Starting backend at http://localhost:8000"
Write-Host "Starting frontend at http://localhost:3000"
Write-Host "Press Ctrl+C to stop both servers."
Write-Host ""

if (Test-PortOpen 8000) {
    Write-Host "Port 8000 is already in use. Backend appears to be running."
}
else {
    if (-not (Test-Path $PidDir)) {
        New-Item -ItemType Directory -Path $PidDir | Out-Null
    }

    $BackendProcess = Start-Process -FilePath $VenvPython `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--reload", "--port", "8000") `
        -WorkingDirectory $BackendDir `
        -WindowStyle Hidden `
        -PassThru
    Set-Content -Path (Join-Path $PidDir "backend.pid") -Value $BackendProcess.Id
}

Write-Host "Frontend logs below. Press Ctrl+C to stop the frontend server."
Write-Host "If backend was started by this script, it will keep running in the background."
Write-Host ""

Push-Location $FrontendDir
$env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"
npm.cmd run dev
Pop-Location
