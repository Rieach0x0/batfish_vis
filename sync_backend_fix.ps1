# Sync backend fix to WSL
Write-Host "Copying main.py to WSL..." -ForegroundColor Yellow

wsl bash -c "cp /mnt/d/batfish_vis/backend/src/main.py ~/batfish_vis/backend/src/main.py"

Write-Host "Verifying copy..." -ForegroundColor Yellow
wsl bash -c "grep -n 'error_msg' ~/batfish_vis/backend/src/main.py"

Write-Host "`nDone! Please restart backend in WSL Ubuntu." -ForegroundColor Green
Write-Host "Command: cd ~/batfish_vis/backend && source .venv/bin/activate && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug" -ForegroundColor Cyan
