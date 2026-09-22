# run_local.ps1
# Opens TWO new PowerShell windows:
#   Window 1: Mock Smart Home API on http://localhost:9000
#   Window 2: Agent API           on http://localhost:8000

$Uvicorn = "C:\Users\GANGARI DHRUVAVEER\AppData\Local\Programs\Python\Python310\Scripts\uvicorn.exe"
$Root = (Get-Item (Split-Path -Parent $PSScriptRoot)).FullName

Write-Host ""
Write-Host "Starting Mock Smart Home API in a new window (port 9000)..." -ForegroundColor Cyan
$mockCmd = "Set-Location '$Root'; Write-Host 'MOCK SMART HOME API - http://localhost:9000' -ForegroundColor Cyan; & '$Uvicorn' mock_api.main:app --port 9000 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $mockCmd

Start-Sleep -Seconds 1

Write-Host "Starting Agent API in a new window (port 8000)..." -ForegroundColor Yellow
$agentCmd = "Set-Location '$Root'; Write-Host 'AGENT API - http://localhost:8000' -ForegroundColor Yellow; & '$Uvicorn' api.main:app --port 8000 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $agentCmd

Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "  Both servers launched in separate windows." -ForegroundColor Green
Write-Host "  Mock API:  http://localhost:9000/docs" -ForegroundColor Green
Write-Host "  Agent API: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Write-Host ""
Write-Host "When both are running, run:" -ForegroundColor White
Write-Host "  .\scripts\run_red_team.ps1" -ForegroundColor Gray
Write-Host ""
