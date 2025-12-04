#!/bin/bash
# Backend startup script

cd ~/batfish_vis/backend

# Clear Python cache
echo "Clearing Python cache..."
find src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find src -type f -name '*.pyc' -delete 2>/dev/null

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Verify Python can import the module
echo "Testing imports..."
python -c "from src.main import app; print('✓ Import successful')" || {
    echo "✗ Import failed!"
    echo "Checking Python path..."
    python -c "import sys; print('\n'.join(sys.path))"
    echo "Checking src/__init__.py..."
    ls -la src/__init__.py
    echo "Checking src/exceptions.py..."
    ls -la src/exceptions.py
    exit 1
}

# Start uvicorn with PYTHONPATH set
echo "Starting uvicorn with PYTHONPATH..."
echo "PYTHONPATH=$PWD"
PYTHONPATH=$PWD uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
