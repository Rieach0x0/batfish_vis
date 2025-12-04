"""
Health check API endpoint.

Verifies Batfish container connectivity and returns service status.
"""

import logging
from fastapi import APIRouter, HTTPException, status
from pybatfish.exception import BatfishException
from ..services.batfish_service import get_batfish_service
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint to verify API and Batfish container status.

    Returns:
        dict: Health status with API version and Batfish version

    Raises:
        HTTPException: 503 if Batfish container is unreachable
    """
    try:
        logger.debug("Health check request received")

        # Get Batfish service instance
        bf_service = get_batfish_service(
            host=settings.batfish_host,
            port=settings.batfish_port
        )

        # Execute health check
        health_status = bf_service.health_check()

        logger.info("Health check passed", extra=health_status)
        return health_status

    except BatfishException as e:
        logger.error(
            "Health check failed - Batfish unavailable",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Batfish Service Unavailable",
                "message": f"Cannot connect to Batfish at {settings.batfish_host}:{settings.batfish_port}",
                "code": "BATFISH_CONNECTION_ERROR"
            }
        ) from e
    except Exception as e:
        logger.error(
            "Health check failed - unexpected error",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Health Check Failed",
                "message": str(e),
                "code": "HEALTH_CHECK_ERROR"
            }
        ) from e
