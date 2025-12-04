# Start backend in WSL with correct PYTHONPATH
Write-Host "Starting backend in WSL..." -ForegroundColor Yellow
Write-Host ""
Write-Host "This will:" -ForegroundColor Cyan
Write-Host "1. Stop any existing uvicorn processes" -ForegroundColor White
Write-Host "2. Clear Python cache" -ForegroundColor White
Write-Host "3. Start backend with PYTHONPATH set (enables auto-reload)" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in the WSL window to stop the backend" -ForegroundColor Yellow
Write-Host ""

# Execute the startup command
wsl bash -c "cd ~/batfish_vis/backend && source .venv/bin/activate && pkill -9 -f uvicorn 2>/dev/null; find src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null && PYTHONPATH=`$PWD uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug"
