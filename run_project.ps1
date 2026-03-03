Param(
  [switch]$Install
)

$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

if ($Install) {
  python -m pip install -r requirements.txt
}

Write-Host "Starting API (FastAPI) on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Start-Process -FilePath "powershell" -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location -Path `"$PSScriptRoot`"; python -m uvicorn api:app --reload"
)

Write-Host "Starting UI (Streamlit) on http://localhost:8501 ..." -ForegroundColor Cyan
Start-Process -FilePath "powershell" -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location -Path `"$PSScriptRoot`"; python -m streamlit run app.py"
)

Write-Host ""
Write-Host "Open:" -ForegroundColor Green
Write-Host "  UI  -> http://localhost:8501"
Write-Host "  API -> http://127.0.0.1:8000/docs"
