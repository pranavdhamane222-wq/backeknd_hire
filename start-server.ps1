param(
    [int] $Port = 5000
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PORT = "$Port"
Write-Host "Starting Hirex on http://127.0.0.1:$Port/ (Ctrl+C to stop)" -ForegroundColor Cyan
python server.py
