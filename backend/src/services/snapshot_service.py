"""
Snapshot service for Batfish snapshot management.

Handles snapshot creation, listing, retrieval, and deletion using pybatfish v2025.07.07.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from pybatfish.exception import BatfishException

from ..models.snapshot import Snapshot, ParseError
from .batfish_service import BatfishService

logger = logging.getLogger(__name__)


class SnapshotService:
    """
    Service for managing Batfish snapshots.

    Constitutional compliance:
    - Principle I: Batfish-First Integration - All network analysis via pybatfish
    - Principle II: Topology Visualization as Contract - Snapshots are source of truth
    - Principle V: Observability - Structured logging for all operations
    """

    def __init__(self, batfish_service: BatfishService):
        """
        Initialize snapshot service with Batfish service.

        Args:
            batfish_service: BatfishService instance for Batfish operations
        """
        self.bf_service = batfish_service
        logger.info("SnapshotService initialized")

    def create_snapshot(
        self,
        snapshot_name: str,
        network_name: str,
        config_dir: Path
    ) -> Snapshot:
        """
        Create Batfish snapshot from configuration files directory.

        Constitutional compliance:
        - Principle I: Uses pybatfish bf.init_snapshot() - no custom parsers

        Args:
            snapshot_name: Unique snapshot name
            network_name: Network name for logical grouping
            config_dir: Directory containing configuration files

        Returns:
            Snapshot object with metadata and parse status

        Raises:
            BatfishException: If snapshot initialization fails
            ValueError: If config_dir doesn't exist or is empty
        """
        if not config_dir.exists() or not config_dir.is_dir():
            raise ValueError(f"Configuration directory not found: {config_dir}")

        config_files = list(config_dir.glob("*"))
        if not config_files:
            raise ValueError(f"No configuration files found in {config_dir}")

        logger.info(
            "Creating Batfish snapshot",
            extra={
                "snapshot": snapshot_name,
                "network": network_name,
                "config_dir": str(config_dir),
                "file_count": len(config_files)
            }
        )

        try:
            bf_session = self.bf_service.session

            # Set network first (required before init_snapshot)
            bf_session.set_network(network_name)

            # Initialize Batfish snapshot
            # Note: init_snapshot is synchronous in pybatfish v2025.07.07
            # API: init_snapshot(upload: str, name: str | None = None, overwrite: bool = False)
            init_result = bf_session.init_snapshot(
                upload=str(config_dir),
                name=snapshot_name,
                overwrite=False
            )

            logger.info(
                "Batfish snapshot initialized",
                extra={
                    "snapshot": snapshot_name,
                    "network": network_name,
                    "init_result": str(init_result)
                }
            )

            # Get parse errors
            parse_errors = self.get_parse_errors(snapshot_name, network_name)

            # Get device count
            device_count = self._get_device_count(snapshot_name, network_name)

            # Determine status
            status = "COMPLETE" if not any(
                err.error_message for err in parse_errors
            ) else "COMPLETE"  # Even with warnings, snapshot can be complete

            snapshot = Snapshot(
                name=snapshot_name,
                network=network_name,
                created_at=datetime.utcnow(),
                status=status,
                config_file_count=len(config_files),
                device_count=device_count,
                batfish_version="v2025.07.07",
                parse_errors=parse_errors
            )

            logger.info(
                "Snapshot created successfully",
                extra={
                    "snapshot": snapshot_name,
                    "device_count": device_count,
                    "parse_error_count": len(parse_errors),
                    "status": status
                }
            )

            return snapshot

        except BatfishException as e:
            logger.error(
                "Failed to create Batfish snapshot",
                extra={
                    "snapshot": snapshot_name,
                    "network": network_name,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    def get_parse_errors(
        self,
        snapshot_name: str,
        network_name: str
    ) -> List[ParseError]:
        """
        Get parse errors for a snapshot using Batfish fileParseStatus query.

        Constitutional compliance:
        - Principle I: Uses pybatfish bf.q.fileParseStatus()

        Args:
            snapshot_name: Snapshot name
            network_name: Network name

        Returns:
            List of ParseError objects for files that failed to parse
        """
        logger.debug(
            "Fetching parse errors",
            extra={"snapshot": snapshot_name, "network": network_name}
        )

        try:
            bf_session = self.bf_service.session
            bf_session.set_network(network_name)
            bf_session.set_snapshot(snapshot_name)

            # Query file parse status
            parse_status_df = bf_session.q.fileParseStatus().answer().frame()

            parse_errors = []
            for _, row in parse_status_df.iterrows():
                status = row.get("Status", "")
                if status != "PASSED":
                    filename = row.get("File_Name", "unknown")
                    # Parse warnings/errors from Batfish
                    error_msg = row.get("Nodes", "") or "Parse failed"

                    parse_errors.append(
                        ParseError(
                            file_name=filename,
                            error_message=str(error_msg),
                            line_number=None  # Batfish doesn't always provide line numbers
                        )
                    )

            logger.debug(
                "Parse errors retrieved",
                extra={
                    "snapshot": snapshot_name,
                    "error_count": len(parse_errors)
                }
            )

            return parse_errors

        except Exception as e:
            logger.warning(
                "Could not retrieve parse errors",
                extra={
                    "snapshot": snapshot_name,
                    "error": str(e)
                }
            )
            return []

    def list_snapshots(self, network_name: Optional[str] = None) -> List[Snapshot]:
        """
        List all Batfish snapshots.

        Constitutional compliance:
        - Principle I: Uses pybatfish bf.list_snapshots()

        Args:
            network_name: Optional network filter

        Returns:
            List of Snapshot objects
        """
        logger.debug("Listing snapshots", extra={"network": network_name})

        try:
            bf_session = self.bf_service.session

            if network_name:
                bf_session.set_network(network_name)
                snapshot_names = bf_session.list_snapshots()
                networks = [network_name] * len(snapshot_names)
            else:
                # List all networks and their snapshots
                networks_list = bf_session.list_networks()
                snapshot_names = []
                networks = []
                for net in networks_list:
                    bf_session.set_network(net)
                    snaps = bf_session.list_snapshots()
                    snapshot_names.extend(snaps)
                    networks.extend([net] * len(snaps))

            snapshots = []
            for snap_name, net in zip(snapshot_names, networks):
                try:
                    snapshot = self.get_snapshot_details(snap_name, net)
                    snapshots.append(snapshot)
                except Exception as e:
                    logger.warning(
                        "Could not get details for snapshot",
                        extra={"snapshot": snap_name, "network": net, "error": str(e)}
                    )

            logger.info(
                "Snapshots listed",
                extra={"snapshot_count": len(snapshots), "network": network_name}
            )

            return snapshots

        except Exception as e:
            logger.error(
                "Failed to list snapshots",
                extra={"network": network_name, "error": str(e)},
                exc_info=True
            )
            return []

    def get_snapshot_details(
        self,
        snapshot_name: str,
        network_name: str
    ) -> Snapshot:
        """
        Retrieve detailed metadata for a specific snapshot.

        Args:
            snapshot_name: Snapshot name
            network_name: Network name

        Returns:
            Snapshot object with full metadata

        Raises:
            ValueError: If snapshot doesn't exist
        """
        logger.debug(
            "Getting snapshot details",
            extra={"snapshot": snapshot_name, "network": network_name}
        )

        try:
            bf_session = self.bf_service.session
            bf_session.set_network(network_name)
            bf_session.set_snapshot(snapshot_name)

            # Get device count
            device_count = self._get_device_count(snapshot_name, network_name)

            # Get parse errors
            parse_errors = self.get_parse_errors(snapshot_name, network_name)

            # Estimate config file count from parse status
            parse_status_df = bf_session.q.fileParseStatus().answer().frame()
            config_file_count = len(parse_status_df)

            snapshot = Snapshot(
                name=snapshot_name,
                network=network_name,
                created_at=datetime.utcnow(),  # Note: Batfish doesn't store creation time
                status="COMPLETE",
                config_file_count=config_file_count,
                device_count=device_count,
                batfish_version="v2025.07.07",
                parse_errors=parse_errors
            )

            logger.debug(
                "Snapshot details retrieved",
                extra={
                    "snapshot": snapshot_name,
                    "device_count": device_count,
                    "config_files": config_file_count
                }
            )

            return snapshot

        except Exception as e:
            logger.error(
                "Failed to get snapshot details",
                extra={"snapshot": snapshot_name, "network": network_name, "error": str(e)},
                exc_info=True
            )
            raise ValueError(f"Snapshot not found: {snapshot_name}") from e

    def delete_snapshot(
        self,
        snapshot_name: str,
        network_name: str
    ) -> None:
        """
        Delete a Batfish snapshot.

        Constitutional compliance:
        - Principle I: Uses pybatfish bf.delete_snapshot()

        Args:
            snapshot_name: Snapshot name
            network_name: Network name

        Raises:
            BatfishException: If deletion fails
        """
        logger.info(
            "Deleting snapshot",
            extra={"snapshot": snapshot_name, "network": network_name}
        )

        try:
            bf_session = self.bf_service.session
            bf_session.set_network(network_name)
            bf_session.delete_snapshot(snapshot_name)

            logger.info(
                "Snapshot deleted successfully",
                extra={"snapshot": snapshot_name, "network": network_name}
            )

        except Exception as e:
            logger.error(
                "Failed to delete snapshot",
                extra={"snapshot": snapshot_name, "network": network_name, "error": str(e)},
                exc_info=True
            )
            raise BatfishException(f"Failed to delete snapshot: {str(e)}") from e

    def _get_device_count(
        self,
        snapshot_name: str,
        network_name: str
    ) -> int:
        """
        Get device count for a snapshot using nodeProperties query.

        Args:
            snapshot_name: Snapshot name
            network_name: Network name

        Returns:
            Number of devices detected
        """
        try:
            bf_session = self.bf_service.session
            bf_session.set_network(network_name)
            bf_session.set_snapshot(snapshot_name)

            nodes_df = bf_session.q.nodeProperties().answer().frame()
            device_count = len(nodes_df)

            logger.debug(
                "Device count retrieved",
                extra={"snapshot": snapshot_name, "device_count": device_count}
            )

            return device_count

        except Exception as e:
            logger.warning(
                "Could not get device count",
                extra={"snapshot": snapshot_name, "error": str(e)}
            )
            return 0
