"""
API router registration module.

Centralizes all API endpoint routers for the FastAPI application.
"""

from fastapi import APIRouter
from .health_api import router as health_router
from .snapshot_api import router as snapshot_router
from .topology_api import router as topology_router
from .verification_api import router as verification_router

# Create main API router
api_router = APIRouter(prefix="/api")

# Register all endpoint routers
api_router.include_router(health_router)
api_router.include_router(snapshot_router)
api_router.include_router(topology_router)
api_router.include_router(verification_router)
