# Sync snapshot_service.py fix to WSL
Write-Host "Copying snapshot_service.py to WSL..." -ForegroundColor Yellow

wsl bash -c "cp /mnt/d/batfish_vis/backend/src/services/snapshot_service.py ~/batfish_vis/backend/src/services/snapshot_service.py"

Write-Host "Verifying copy..." -ForegroundColor Yellow
wsl bash -c "grep -n 'upload=' ~/batfish_vis/backend/src/services/snapshot_service.py | head -3"

Write-Host "`nDone! Backend will auto-reload (uvicorn --reload is running)." -ForegroundColor Green
Write-Host "Please test again in browser with a new snapshot name." -ForegroundColor Cyan
