# run_red_team.ps1 - Phase 1(d): Run the red-team baseline measurement
#
# Prerequisites:
#   1. Both services are running (run .\scripts\run_local.ps1 first)
#   2. Your .env file has a valid GOOGLE_API_KEY
#
# Usage (from the smart-home-agent/ project root):
#   .\scripts\run_red_team.ps1
#
# This runs ONLY the red-team tests (not the normal CI suite).
# The -s flag shows the results summary table printed at the end.

$Pytest = "C:\Users\GANGARI DHRUVAVEER\AppData\Local\Programs\Python\Python310\Scripts\pytest.exe"
$Root = (Get-Item (Split-Path -Parent $PSScriptRoot)).FullName

Write-Host ""
Write-Host "===================================================" -ForegroundColor Magenta
Write-Host "  Phase 1(d) - Red-Team Baseline Measurement" -ForegroundColor Magenta
Write-Host "===================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "Checking services are up..." -ForegroundColor Gray

# Quick health check before spending API tokens
try {
    $mockHealth  = Invoke-RestMethod -Uri "http://localhost:9000/health" -TimeoutSec 3
    $agentHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 3
    Write-Host "  Mock API:  OK ($($mockHealth.status))" -ForegroundColor Green
    Write-Host "  Agent API: OK ($($agentHealth.status))" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "ERROR: One or both services are not reachable." -ForegroundColor Red
    Write-Host "Run .\scripts\run_local.ps1 first, wait for both to say 'Application startup complete'," -ForegroundColor Red
    Write-Host "then re-run this script." -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "Starting red-team attack suite (9 tests, real LLM calls - this takes 1-3 minutes)..." -ForegroundColor Yellow
Write-Host ""

Set-Location $Root
& $Pytest -m red_team -v -s

Write-Host ""
Write-Host "===================================================" -ForegroundColor Magenta
Write-Host "  Done. Copy the results table above into" -ForegroundColor Magenta
Write-Host "  SECURITY_NOTES.md under 'Phase 1(d)'." -ForegroundColor Magenta
Write-Host "===================================================" -ForegroundColor Magenta
Write-Host ""
