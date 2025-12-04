"""
FastAPI application entry point.

Main application with CORS middleware, exception handlers, and API routes.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pybatfish.exception import BatfishException as PyBatfishException

from .config import settings
from .utils.logger import setup_logging
from .middleware.error_handler import batfish_exception_handler, generic_exception_handler
from .api import api_router
from .exceptions import BatfishException

# Setup structured logging
setup_logging(log_level=settings.log_level)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="""
REST API for Batfish snapshot creation, topology visualization, and configuration verification.

This API integrates with Batfish v2025.07.07 container via pybatfish v2025.07.07.

**Features**:
- Snapshot creation from network configuration files
- Layer 3 topology query and visualization
- Configuration verification queries (reachability, ACL, routing)
""",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(
    "CORS middleware configured",
    extra={"allowed_origins": settings.cors_origins}
)

# Custom validation error handler for 422 debugging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle 422 Unprocessable Entity errors with detailed logging.

    This handler logs validation errors for debugging purposes.
    """
    logger.error(
        "Request validation error (422)",
        extra={
            "url": str(request.url),
            "method": request.method,
            "errors": exc.errors(),
            "body": exc.body if hasattr(exc, 'body') else None
        }
    )

    # Log detailed error information
    for error in exc.errors():
        logger.error(
            f"Validation error detail",
            extra={
                "field_loc": error.get("loc"),
                "error_msg": error.get("msg"),
                "error_type": error.get("type"),
                "error_input": error.get("input")
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Request validation failed",
            "code": "VALIDATION_ERROR",
            "details": exc.errors()
        }
    )

# Register exception handlers
# Handle both custom BatfishException and pybatfish's BatfishException
app.add_exception_handler(BatfishException, batfish_exception_handler)
app.add_exception_handler(PyBatfishException, batfish_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

logger.info("Exception handlers registered")

# Include API routers
app.include_router(api_router)

logger.info(
    "FastAPI application initialized",
    extra={
        "title": settings.api_title,
        "version": settings.api_version,
        "batfish_host": settings.batfish_host,
        "batfish_port": settings.batfish_port
    }
)


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Application starting up")
    logger.info(
        "Batfish configuration",
        extra={
            "host": settings.batfish_host,
            "port": settings.batfish_port
        }
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Application shutting down")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/api/health"
    }
