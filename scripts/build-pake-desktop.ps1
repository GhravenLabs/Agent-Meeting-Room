[CmdletBinding()]
param(
    [int]$Port = 5000,
    [string]$Targets = "msi",
    [switch]$SkipServer
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

function Require-Command {
    param(
        [string]$Name,
        [string]$InstallHint
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required. $InstallHint"
    }
}

function Wait-For-Url {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 30
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2 | Out-Null
            return $true
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }

    return $false
}

Require-Command "node" "Install Node.js from https://nodejs.org/"
Require-Command "npm" "Install npm with Node.js from https://nodejs.org/"
Require-Command "cargo" "Install Rust from https://rustup.rs/ because Pake builds with Tauri."

if (-not (Test-Path "node_modules\.bin\pake.cmd")) {
    Write-Host "[1/4] Installing Node dependencies..."
    npm install
}
else {
    Write-Host "[1/4] Node dependencies already installed."
}

$url = "http://127.0.0.1:$Port"
$serverProcess = $null

try {
    if ($SkipServer) {
        Write-Host "[2/4] Skipping Flask startup. Expecting Agent Meeting Room at $url"
    }
    else {
        Require-Command "python" "Install Python 3.11+ from https://python.org/"
        Write-Host "[2/4] Starting Flask backend at $url..."
        $env:PORT = "$Port"
        $serverProcess = Start-Process -FilePath "python" -ArgumentList "app.py" -PassThru -WindowStyle Hidden
    }

    Write-Host "[3/4] Waiting for Agent Meeting Room..."
    if (-not (Wait-For-Url -Url $url)) {
        throw "Agent Meeting Room did not become reachable at $url"
    }

    Write-Host "[4/4] Building Pake desktop shell..."
    npx pake $url `
        --name AgentMeetingRoom `
        --title "Agent Meeting Room" `
        --icon "assets/icon.png" `
        --width 1280 `
        --height 860 `
        --min-width 960 `
        --min-height 640 `
        --app-version "1.9.0" `
        --targets $Targets `
        --force-internal-navigation
}
finally {
    if ($serverProcess -and -not $serverProcess.HasExited) {
        Write-Host "Stopping Flask backend..."
        Stop-Process -Id $serverProcess.Id -Force
    }
}
