[CmdletBinding()]
param(
    [switch]$SkipBackend,
    [switch]$SkipNodeInstall
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$DesktopDir = Join-Path $RepoRoot "desktop"
$VsDevCmd = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"

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

Require-Command "python" "Install Python 3.11+ from https://python.org/"
Require-Command "npm" "Install Node.js from https://nodejs.org/"

if (-not (Test-Path "$env:USERPROFILE\.cargo\bin\cargo.exe")) {
    throw "cargo is required. Install Rust from https://rustup.rs/"
}

if (-not (Test-Path $VsDevCmd)) {
    throw "Visual Studio Build Tools with C++ workload are required."
}

if (-not $SkipBackend) {
    Write-Host "[1/4] Installing Python dependencies..."
    python -m pip install -r requirements.txt --quiet

    Write-Host "[2/4] Building backend sidecar..."
    pyinstaller AgentMeetingRoomBackend.spec --noconfirm
}
else {
    Write-Host "[1/4] Skipping backend sidecar build."
    Write-Host "[2/4] Using existing dist\AgentMeetingRoomBackend.exe."
}

if (-not (Test-Path "dist\AgentMeetingRoomBackend.exe")) {
    throw "dist\AgentMeetingRoomBackend.exe was not found."
}

if (-not $SkipNodeInstall) {
    Write-Host "[3/4] Installing desktop Node dependencies..."
    npm install --prefix $DesktopDir
}
else {
    Write-Host "[3/4] Skipping desktop Node dependency install."
}

Write-Host "[4/4] Building Tauri desktop app..."
$cargoPath = "$env:USERPROFILE\.cargo\bin"
$cmd = "call `"$VsDevCmd`" -arch=x64 -host_arch=x64 >nul && set PATH=$cargoPath;%PATH% && npm run build --prefix `"$DesktopDir`""
cmd /c $cmd
