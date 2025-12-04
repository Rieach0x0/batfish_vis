"""
Error handling middleware for Batfish connection errors and API exceptions.

Provides structured error responses and logging.
"""

import logging
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from pybatfish.exception import BatfishException as PyBatfishException

from ..exceptions import BatfishException

logger = logging.getLogger(__name__)


async def batfish_exception_handler(
    request: Request,
    exc: Union[BatfishException, PyBatfishException]
) -> JSONResponse:
    """
    Handle Batfish connection and query exceptions.

    Handles both custom BatfishException and pybatfish's BatfishException.

    Args:
        request: FastAPI request object
        exc: Batfish exception (custom or pybatfish)

    Returns:
        JSON response with error details and 503 status
    """
    error_message = str(exc).lower()

    # Determine error type and provide troubleshooting hints
    troubleshooting = []

    if "connection" in error_message or "refused" in error_message:
        troubleshooting = [
            "Ensure Batfish container is running: docker ps | grep batfish",
            "Start Batfish container: docker run -d -p 9996:9996 batfish/batfish:v2025.07.07",
            "Check if port 9996 is accessible: curl http://localhost:9996",
            "Verify BATFISH_HOST and BATFISH_PORT environment variables"
        ]
        error_code = "BATFISH_UNREACHABLE"
        error_title = "Cannot Connect to Batfish Container"

    elif "timeout" in error_message:
        troubleshooting = [
            "Check Batfish container health: docker logs <container_id>",
            "Verify snapshot size is not too large (>100 devices may timeout)",
            "Increase query timeout in configuration",
            "Restart Batfish container if unresponsive"
        ]
        error_code = "BATFISH_TIMEOUT"
        error_title = "Batfish Query Timeout"

    elif "parse" in error_message or "syntax" in error_message:
        troubleshooting = [
            "Check configuration file format is supported (Cisco IOS, Juniper JunOS, Arista EOS, Palo Alto)",
            "Verify configuration files have correct file extensions",
            "Review parse errors in snapshot details",
            "Ensure configuration files are complete and not truncated"
        ]
        error_code = "BATFISH_PARSE_ERROR"
        error_title = "Configuration Parse Error"

    elif "snapshot" in error_message and "not found" in error_message:
        troubleshooting = [
            "Verify snapshot name is correct (case-sensitive)",
            "List all snapshots: GET /api/snapshots",
            "Create snapshot before querying: POST /api/snapshots",
            "Check snapshot was not deleted"
        ]
        error_code = "SNAPSHOT_NOT_FOUND"
        error_title = "Snapshot Not Found"

    else:
        troubleshooting = [
            "Check Batfish container logs: docker logs <container_id>",
            "Verify Batfish version compatibility (v2025.07.07 required)",
            "Review API request parameters for correctness",
            "Contact support with error details if issue persists"
        ]
        error_code = "BATFISH_ERROR"
        error_title = "Batfish Service Error"

    logger.error(
        "Batfish error occurred",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
            "error_code": error_code
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": error_title,
            "message": str(exc),
            "code": error_code,
            "troubleshooting": troubleshooting
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle uncaught exceptions with structured logging.

    Args:
        request: FastAPI request object
        exc: Uncaught exception

    Returns:
        JSON response with error details and 500 status
    """
    logger.error(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please check logs for details.",
            "code": "INTERNAL_ERROR"
        }
    )
