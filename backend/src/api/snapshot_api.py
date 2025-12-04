"""
Snapshot API endpoints.

REST API for creating, listing, retrieving, and deleting Batfish snapshots.
"""

import logging
import re
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status

from ..models.snapshot import Snapshot, SnapshotCreate, SnapshotListResponse
from ..services.batfish_service import get_batfish_service
from ..services.file_service import get_file_service
from ..services.snapshot_service import SnapshotService
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/snapshots", tags=["Snapshots"])


def _validate_snapshot_name(name: str) -> None:
    """
    Validate snapshot name format.

    Constitutional compliance:
    - Principle IV: Test-First - Validation before processing

    Args:
        name: Snapshot name to validate

    Raises:
        HTTPException: If name is invalid (400 Bad Request)
    """
    if not name or len(name) < 1 or len(name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid Snapshot Name",
                "message": "Snapshot name must be 1-100 characters",
                "code": "INVALID_SNAPSHOT_NAME"
            }
        )

    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid Snapshot Name",
                "message": "Snapshot name must contain only alphanumeric characters, hyphens, and underscores",
                "code": "INVALID_SNAPSHOT_NAME"
            }
        )


@router.post("", response_model=Snapshot, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    snapshotName: str = Form(...),
    networkName: str = Form(default="default"),
    configFiles: List[UploadFile] = File(...)
):
    """
    Create a new Batfish snapshot from uploaded configuration files.

    Constitutional compliance:
    - Principle I: Batfish-First Integration - Uses pybatfish for all processing
    - Principle V: Observability - Structured logging for all operations

    Args:
        snapshotName: Unique snapshot name
        networkName: Network name for logical grouping
        configFiles: List of network configuration files

    Returns:
        Snapshot object with metadata and parse status

    Raises:
        HTTPException:
            - 400: Invalid snapshot name or no files provided
            - 409: Snapshot with this name already exists
            - 503: Batfish container unavailable
    """
    # Debug logging for 422 investigation
    logger.info(
        "Snapshot creation request received",
        extra={
            "snapshot": snapshotName,
            "network": networkName,
            "file_count": len(configFiles) if configFiles else 0,
            "files": [f.filename for f in configFiles] if configFiles else []
        }
    )

    # Additional debug: check each file
    if configFiles:
        for idx, file in enumerate(configFiles):
            logger.debug(
                f"File {idx + 1}",
                extra={
                    "file_name": file.filename,
                    "content_type": file.content_type,
                    "file_size": file.size if hasattr(file, 'size') else "unknown"
                }
            )
    else:
        logger.warning("No config files received in request")

    # Validate snapshot name (FR-012)
    _validate_snapshot_name(snapshotName)

    # Validate files provided
    if not configFiles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "No Configuration Files",
                "message": "At least one configuration file must be provided",
                "code": "NO_CONFIG_FILES"
            }
        )

    try:
        # Get service instances
        file_service = get_file_service(temp_dir=settings.temp_upload_dir)
        bf_service = get_batfish_service(
            host=settings.batfish_host,
            port=settings.batfish_port
        )
        snapshot_service = SnapshotService(bf_service)

        # Check for duplicate snapshot name (FR-031)
        try:
            existing = snapshot_service.get_snapshot_details(snapshotName, networkName)
            if existing:
                logger.warning(
                    "Duplicate snapshot name",
                    extra={"snapshot": snapshotName, "network": networkName}
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "Snapshot Already Exists",
                        "message": f"Snapshot '{snapshotName}' already exists in network '{networkName}'",
                        "code": "SNAPSHOT_ALREADY_EXISTS"
                    }
                )
        except ValueError:
            # Snapshot doesn't exist - this is expected
            pass

        # Save uploaded files to temporary directory (FR-001)
        config_dir = await file_service.save_uploaded_files(snapshotName, configFiles)

        logger.info(
            "Configuration files saved",
            extra={"snapshot": snapshotName, "directory": str(config_dir)}
        )

        # Create Batfish snapshot (FR-001, FR-002)
        snapshot = snapshot_service.create_snapshot(
            snapshot_name=snapshotName,
            network_name=networkName,
            config_dir=config_dir
        )

        logger.info(
            "Snapshot created successfully",
            extra={
                "snapshot": snapshotName,
                "network": networkName,
                "device_count": snapshot.device_count,
                "parse_error_count": len(snapshot.parse_errors)
            }
        )

        return snapshot

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "Snapshot creation failed",
            extra={
                "snapshot": snapshotName,
                "network": networkName,
                "error": str(e)
            },
            exc_info=True
        )

        # Check if it's a Batfish connection error (FR-030)
        if "connect" in str(e).lower() or "batfish" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Batfish Service Unavailable",
                    "message": f"Cannot connect to Batfish at {settings.batfish_host}:{settings.batfish_port}",
                    "code": "BATFISH_CONNECTION_ERROR"
                }
            ) from e

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Snapshot Creation Failed",
                "message": str(e),
                "code": "SNAPSHOT_CREATION_ERROR"
            }
        ) from e


@router.get("", response_model=SnapshotListResponse)
async def list_snapshots(network: str = None):
    """
    List all Batfish snapshots.

    Constitutional compliance:
    - Principle I: Batfish-First Integration - Uses pybatfish list_snapshots()

    Args:
        network: Optional network name filter

    Returns:
        List of snapshots with metadata

    Raises:
        HTTPException: 503 if Batfish unavailable
    """
    logger.debug("List snapshots request", extra={"network": network})

    try:
        bf_service = get_batfish_service(
            host=settings.batfish_host,
            port=settings.batfish_port
        )
        snapshot_service = SnapshotService(bf_service)

        snapshots = snapshot_service.list_snapshots(network_name=network)

        logger.info(
            "Snapshots listed",
            extra={"snapshot_count": len(snapshots), "network": network}
        )

        return SnapshotListResponse(snapshots=snapshots)

    except Exception as e:
        logger.error(
            "Failed to list snapshots",
            extra={"network": network, "error": str(e)},
            exc_info=True
        )

        if "connect" in str(e).lower() or "batfish" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Batfish Service Unavailable",
                    "message": str(e),
                    "code": "BATFISH_CONNECTION_ERROR"
                }
            ) from e

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to List Snapshots",
                "message": str(e),
                "code": "SNAPSHOT_LIST_ERROR"
            }
        ) from e


@router.get("/{snapshotName}", response_model=Snapshot)
async def get_snapshot(snapshotName: str, network: str = "default"):
    """
    Get detailed information about a specific snapshot.

    Args:
        snapshotName: Snapshot name
        network: Network name (default: "default")

    Returns:
        Snapshot object with full metadata

    Raises:
        HTTPException: 404 if snapshot not found, 503 if Batfish unavailable
    """
    logger.debug(
        "Get snapshot request",
        extra={"snapshot": snapshotName, "network": network}
    )

    try:
        bf_service = get_batfish_service(
            host=settings.batfish_host,
            port=settings.batfish_port
        )
        snapshot_service = SnapshotService(bf_service)

        snapshot = snapshot_service.get_snapshot_details(snapshotName, network)

        logger.info(
            "Snapshot retrieved",
            extra={"snapshot": snapshotName, "network": network}
        )

        return snapshot

    except ValueError as e:
        logger.warning(
            "Snapshot not found",
            extra={"snapshot": snapshotName, "network": network}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Snapshot Not Found",
                "message": f"Snapshot '{snapshotName}' not found in network '{network}'",
                "code": "SNAPSHOT_NOT_FOUND"
            }
        ) from e
    except Exception as e:
        logger.error(
            "Failed to get snapshot",
            extra={"snapshot": snapshotName, "network": network, "error": str(e)},
            exc_info=True
        )

        if "connect" in str(e).lower() or "batfish" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Batfish Service Unavailable",
                    "message": str(e),
                    "code": "BATFISH_CONNECTION_ERROR"
                }
            ) from e

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to Get Snapshot",
                "message": str(e),
                "code": "SNAPSHOT_GET_ERROR"
            }
        ) from e


@router.delete("/{snapshotName}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snapshot(snapshotName: str, network: str = "default"):
    """
    Delete a Batfish snapshot.

    Args:
        snapshotName: Snapshot name
        network: Network name (default: "default")

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 404 if snapshot not found, 503 if Batfish unavailable
    """
    logger.info(
        "Delete snapshot request",
        extra={"snapshot": snapshotName, "network": network}
    )

    try:
        bf_service = get_batfish_service(
            host=settings.batfish_host,
            port=settings.batfish_port
        )
        snapshot_service = SnapshotService(bf_service)

        # Verify snapshot exists first
        try:
            snapshot_service.get_snapshot_details(snapshotName, network)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Snapshot Not Found",
                    "message": f"Snapshot '{snapshotName}' not found in network '{network}'",
                    "code": "SNAPSHOT_NOT_FOUND"
                }
            ) from e

        # Delete snapshot
        snapshot_service.delete_snapshot(snapshotName, network)

        # Cleanup temporary files
        file_service = get_file_service(temp_dir=settings.temp_upload_dir)
        file_service.cleanup_snapshot_dir(snapshotName)

        logger.info(
            "Snapshot deleted successfully",
            extra={"snapshot": snapshotName, "network": network}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete snapshot",
            extra={"snapshot": snapshotName, "network": network, "error": str(e)},
            exc_info=True
        )

        if "connect" in str(e).lower() or "batfish" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Batfish Service Unavailable",
                    "message": str(e),
                    "code": "BATFISH_CONNECTION_ERROR"
                }
            ) from e

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to Delete Snapshot",
                "message": str(e),
                "code": "SNAPSHOT_DELETE_ERROR"
            }
        ) from e
