"""
Pytest configuration for backend tests.

Adds the src directory to the Python path to allow imports.
"""

import sys
from pathlib import Path

# Add the backend/src directory to Python path
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(backend_dir))
