# Sync snapshot_api.py fix to WSL
Write-Host "Copying snapshot_api.py to WSL..." -ForegroundColor Yellow

wsl bash -c "cp /mnt/d/batfish_vis/backend/src/api/snapshot_api.py ~/batfish_vis/backend/src/api/snapshot_api.py"

Write-Host "Verifying copy..." -ForegroundColor Yellow
wsl bash -c "grep -n 'file_name' ~/batfish_vis/backend/src/api/snapshot_api.py"

Write-Host "`nDone! Backend will auto-reload (uvicorn --reload is running)." -ForegroundColor Green
Write-Host "Please test again in browser." -ForegroundColor Cyan
