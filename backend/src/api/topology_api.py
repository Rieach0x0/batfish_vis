"""
Topology API endpoints.

Provides REST API endpoints for network topology visualization.
"""

import logging
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, status

from ..models.device import Device
from ..models.interface import Interface
from ..models.edge import Edge
from ..services.batfish_service import BatfishService
from ..services.topology_service import TopologyService
from ..exceptions import BatfishException
from ..config import settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/topology", tags=["topology"])

# Initialize services
bf_service = BatfishService(host=settings.batfish_host, port=settings.batfish_port)
topology_service = TopologyService(bf_service.session)


@router.get("/nodes", response_model=List[Device])
async def get_topology_nodes(
    snapshot: str = Query(..., description="Snapshot name"),
    network: str = Query(default="default", description="Network name")
):
    """
    Get all network devices (nodes) in the topology.

    Args:
        snapshot: Snapshot name to query
        network: Network name (default: "default")

    Returns:
        List of Device objects representing network nodes

    Raises:
        HTTPException: If snapshot not found or query fails
    """
    try:
        logger.info(f"Getting topology nodes for snapshot '{snapshot}' in network '{network}'")
        devices = topology_service.get_devices(snapshot, network)
        return devices

    except BatfishException as e:
        logger.error(f"Batfish error getting nodes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve topology nodes: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting nodes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/edges", response_model=List[Edge])
async def get_topology_edges(
    snapshot: str = Query(..., description="Snapshot name"),
    network: str = Query(default="default", description="Network name")
):
    """
    Get all Layer 3 edges (links) in the topology.

    Args:
        snapshot: Snapshot name to query
        network: Network name (default: "default")

    Returns:
        List of Edge objects representing network links

    Raises:
        HTTPException: If snapshot not found or query fails
    """
    try:
        logger.info(f"Getting topology edges for snapshot '{snapshot}' in network '{network}'")
        edges = topology_service.get_layer3_edges(snapshot, network)
        return edges

    except BatfishException as e:
        logger.error(f"Batfish error getting edges: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve topology edges: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting edges: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/interfaces", response_model=List[Interface])
async def get_topology_interfaces(
    snapshot: str = Query(..., description="Snapshot name"),
    network: str = Query(default="default", description="Network name"),
    hostname: Optional[str] = Query(None, description="Filter by device hostname")
):
    """
    Get network interfaces from the snapshot.

    Args:
        snapshot: Snapshot name to query
        network: Network name (default: "default")
        hostname: Optional hostname to filter interfaces by device

    Returns:
        List of Interface objects

    Raises:
        HTTPException: If snapshot not found or query fails
    """
    try:
        logger.info(f"Getting interfaces for snapshot '{snapshot}' in network '{network}'")
        interfaces = topology_service.get_interfaces(snapshot, network, hostname)
        return interfaces

    except BatfishException as e:
        logger.error(f"Batfish error getting interfaces: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interfaces: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting interfaces: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("", response_model=Dict)
async def get_complete_topology(
    snapshot: str = Query(..., description="Snapshot name"),
    network: str = Query(default="default", description="Network name")
):
    """
    Get complete network topology including nodes and edges.

    This endpoint returns a complete topology graph suitable for
    visualization with D3.js or other graph libraries.

    Args:
        snapshot: Snapshot name to query
        network: Network name (default: "default")

    Returns:
        Dictionary containing:
        - nodes: List of Device objects
        - edges: List of Edge objects

    Raises:
        HTTPException: If snapshot not found or query fails
    """
    try:
        logger.info(f"Getting complete topology for snapshot '{snapshot}' in network '{network}'")
        topology = topology_service.get_topology(snapshot, network)
        return topology

    except BatfishException as e:
        logger.error(f"Batfish error getting topology: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve topology: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting topology: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
