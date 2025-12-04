# Sync all backend fixes to WSL
Write-Host "Syncing all backend fixes to WSL..." -ForegroundColor Yellow
Write-Host ""

# List of files to sync
$files = @(
    "backend/src/__init__.py",
    "backend/src/exceptions.py",
    "backend/src/main.py",
    "backend/src/api/__init__.py",
    "backend/src/api/snapshot_api.py",
    "backend/src/services/__init__.py",
    "backend/src/services/snapshot_service.py",
    "backend/src/services/file_service.py",
    "backend/src/services/batfish_service.py",
    "backend/src/services/topology_service.py",
    "backend/src/services/verification_service.py",
    "backend/src/models/__init__.py",
    "backend/src/middleware/__init__.py",
    "backend/src/utils/__init__.py"
)

$errorCount = 0

foreach ($file in $files) {
    $windowsPath = "D:\batfish_vis\$file"
    $wslPath = "/mnt/d/batfish_vis/$file"
    $targetPath = "~/batfish_vis/$file"

    Write-Host "Copying $file..." -ForegroundColor Cyan

    # Check if file exists on Windows side
    if (Test-Path $windowsPath) {
        wsl bash -c "cp $wslPath $targetPath"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Successfully copied" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Failed to copy" -ForegroundColor Red
            $errorCount++
        }
    } else {
        Write-Host "  ✗ File not found on Windows: $windowsPath" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host ""
Write-Host "Verifying critical files in WSL..." -ForegroundColor Yellow

# Verify exceptions.py
Write-Host "Checking exceptions.py..." -ForegroundColor Cyan
wsl bash -c "ls -la ~/batfish_vis/backend/src/exceptions.py"

# Verify snapshot_service.py has the fix
Write-Host "Checking snapshot_service.py for 'upload=' parameter..." -ForegroundColor Cyan
wsl bash -c "grep -n 'upload=' ~/batfish_vis/backend/src/services/snapshot_service.py | head -1"

# Verify file_service.py has the fix
Write-Host "Checking file_service.py for 'file_name' key..." -ForegroundColor Cyan
wsl bash -c "grep -n 'file_name' ~/batfish_vis/backend/src/services/file_service.py | head -1"

Write-Host ""
if ($errorCount -eq 0) {
    Write-Host "All files synced successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. In WSL Ubuntu terminal, restart the backend:" -ForegroundColor Cyan
    Write-Host "   cd ~/batfish_vis/backend" -ForegroundColor White
    Write-Host "   source .venv/bin/activate" -ForegroundColor White
    Write-Host "   uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug" -ForegroundColor White
    Write-Host ""
    Write-Host "2. Wait for 'Application startup complete'" -ForegroundColor Cyan
    Write-Host "3. Test in browser: http://localhost:5173" -ForegroundColor Cyan
} else {
    Write-Host "Sync completed with $errorCount errors!" -ForegroundColor Red
    Write-Host "Please check the errors above and try again." -ForegroundColor Yellow
}
