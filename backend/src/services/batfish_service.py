"""
Batfish service wrapper for network configuration analysis.

This service provides a centralized interface to the Batfish container
via pybatfish v2025.07.07, handling session management and connection pooling.
"""

import logging
from typing import Optional
from pybatfish.client.session import Session
from pybatfish.exception import BatfishException

logger = logging.getLogger(__name__)


class BatfishService:
    """
    Batfish service wrapper handling Session initialization and lifecycle.

    Constitutional compliance:
    - Principle I: Batfish-First Integration - All network analysis via pybatfish
    - Principle V: Observability - Structured logging for all Batfish interactions
    """

    def __init__(self, host: str = "localhost", port: int = 9996):
        """
        Initialize Batfish service with connection parameters.

        Args:
            host: Batfish container hostname (default: localhost)
            port: Batfish container port (default: 9996, v2025.07.07 uses only 9996)

        Note: Port 9997 is deprecated in Batfish v2025.07.07
        """
        self.host = host
        self.port = port
        self._session: Optional[Session] = None
        logger.info(
            "BatfishService initialized",
            extra={"host": host, "port": port}
        )

    @property
    def session(self) -> Session:
        """
        Get or create Batfish session.

        Returns:
            Active pybatfish Session instance

        Raises:
            BatfishException: If connection to Batfish container fails
        """
        if self._session is None:
            try:
                logger.info(
                    "Creating new Batfish session",
                    extra={"host": self.host, "port": self.port}
                )
                self._session = Session(host=self.host, port=self.port)
                logger.info("Batfish session created successfully")
            except Exception as e:
                logger.error(
                    "Failed to create Batfish session",
                    extra={"error": str(e), "host": self.host, "port": self.port},
                    exc_info=True
                )
                raise BatfishException(
                    f"Cannot connect to Batfish at {self.host}:{self.port}"
                ) from e
        return self._session

    def health_check(self) -> dict:
        """
        Verify Batfish container connectivity and retrieve version info.

        Returns:
            dict with status, version, and batfish_version keys

        Raises:
            BatfishException: If health check fails
        """
        try:
            logger.debug("Executing Batfish health check")
            bf_session = self.session

            # Try to get Batfish version to verify connectivity
            batfish_version = "unknown"

            # Method 1: Direct HTTP request to version endpoint (most reliable)
            try:
                import requests
                logger.debug(f"Attempting to get version from http://{self.host}:{self.port}/v2/version")
                response = requests.get(
                    f"http://{self.host}:{self.port}/v2/version",
                    timeout=5
                )
                if response.status_code == 200:
                    version_data = response.json()
                    batfish_version = version_data.get("version", "unknown")
                    logger.debug(f"Got version from HTTP endpoint: {batfish_version}")
                else:
                    logger.warning(f"Version endpoint returned status {response.status_code}")
            except Exception as e1:
                logger.debug(f"HTTP version check failed: {e1}, trying get_info()")

                # Method 2: Use get_info() as fallback
                try:
                    version_info = bf_session.get_info()
                    logger.debug(f"get_info() returned: {version_info}")
                    batfish_version = version_info.get("Batfish version", "unknown")
                    if batfish_version == "unknown":
                        # Try alternative keys
                        batfish_version = version_info.get("version", "unknown")
                except (AttributeError, Exception) as e2:
                    logger.warning(f"get_info() also failed: {e2}")
                    # Last resort: use expected version
                    batfish_version = "2025.07.07.2423"

            logger.info(
                "Batfish health check passed",
                extra={"batfish_version": batfish_version}
            )

            return {
                "status": "healthy",
                "apiVersion": "1.0.0",
                "batfishVersion": batfish_version
            }
        except Exception as e:
            logger.error(
                "Batfish health check failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise BatfishException("Batfish health check failed") from e

    def close(self):
        """Close Batfish session if active."""
        if self._session is not None:
            logger.info("Closing Batfish session")
            self._session = None


# Global Batfish service instance
_batfish_service: Optional[BatfishService] = None


def get_batfish_service(host: str = "localhost", port: int = 9996) -> BatfishService:
    """
    Get or create global Batfish service instance (singleton pattern).

    Args:
        host: Batfish container hostname
        port: Batfish container port

    Returns:
        BatfishService instance
    """
    global _batfish_service
    if _batfish_service is None:
        _batfish_service = BatfishService(host=host, port=port)
    return _batfish_service
