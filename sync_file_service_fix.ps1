# Sync file_service.py fix to WSL
Write-Host "Copying file_service.py to WSL..." -ForegroundColor Yellow

wsl bash -c "cp /mnt/d/batfish_vis/backend/src/services/file_service.py ~/batfish_vis/backend/src/services/file_service.py"

Write-Host "Verifying copy..." -ForegroundColor Yellow
wsl bash -c "grep -n 'file_name' ~/batfish_vis/backend/src/services/file_service.py | head -5"

Write-Host "`nDone! Backend will auto-reload." -ForegroundColor Green
Write-Host "Please test again in browser." -ForegroundColor Cyan
