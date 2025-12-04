"""
Verification API endpoints.

Provides REST API endpoints for network configuration verification
including reachability, ACL, and routing queries.
"""

import logging
import re
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator

from ..models.verification import VerificationResult
from ..services.batfish_service import BatfishService
from ..services.verification_service import VerificationService
from ..exceptions import BatfishException
from ..config import settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/verification", tags=["verification"])

# Initialize services
bf_service = BatfishService(host=settings.batfish_host, port=settings.batfish_port)
verification_service = VerificationService(bf_service.session)


# Request models

class ReachabilityRequest(BaseModel):
    """Request model for reachability verification."""

    snapshot: str = Field(..., min_length=1, description="Snapshot name")
    network: str = Field(default="default", description="Network name")
    src_ip: str = Field(..., description="Source IP address")
    dst_ip: str = Field(..., description="Destination IP address")
    src_node: Optional[str] = Field(None, description="Optional source node hostname")

    @validator('src_ip', 'dst_ip')
    def validate_ip_address(cls, v):
        """Validate IP address format."""
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ip_pattern, v):
            raise ValueError(f"Invalid IP address format: {v}")

        # Validate octets are 0-255
        octets = v.split('.')
        for octet in octets:
            if not 0 <= int(octet) <= 255:
                raise ValueError(f"Invalid IP address: {v}")

        return v


class ACLRequest(BaseModel):
    """Request model for ACL verification."""

    snapshot: str = Field(..., min_length=1, description="Snapshot name")
    network: str = Field(default="default", description="Network name")
    filter_name: str = Field(..., min_length=1, description="ACL/filter name or pattern")
    src_ip: str = Field(..., description="Source IP address")
    dst_ip: str = Field(..., description="Destination IP address")
    protocol: Optional[str] = Field(None, description="Protocol (TCP, UDP, ICMP)")

    @validator('src_ip', 'dst_ip')
    def validate_ip_address(cls, v):
        """Validate IP address format."""
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ip_pattern, v):
            raise ValueError(f"Invalid IP address format: {v}")

        octets = v.split('.')
        for octet in octets:
            if not 0 <= int(octet) <= 255:
                raise ValueError(f"Invalid IP address: {v}")

        return v

    @validator('protocol')
    def validate_protocol(cls, v):
        """Validate protocol value."""
        if v is not None:
            valid_protocols = ['TCP', 'UDP', 'ICMP', 'tcp', 'udp', 'icmp']
            if v not in valid_protocols:
                raise ValueError(f"Invalid protocol: {v}. Must be TCP, UDP, or ICMP")
            return v.upper()
        return v


class RoutingRequest(BaseModel):
    """Request model for routing verification."""

    snapshot: str = Field(..., min_length=1, description="Snapshot name")
    network: str = Field(default="default", description="Network name")
    nodes: Optional[List[str]] = Field(None, description="Optional list of node hostnames")
    network_filter: Optional[str] = Field(None, description="Optional network prefix (e.g., 10.0.0.0/8)")

    @validator('network_filter')
    def validate_network_prefix(cls, v):
        """Validate network prefix format."""
        if v is not None:
            # Simple CIDR validation
            cidr_pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
            if not re.match(cidr_pattern, v):
                raise ValueError(f"Invalid network prefix format: {v}. Expected CIDR notation (e.g., 10.0.0.0/8)")
        return v


# Endpoints

@router.post("/reachability", response_model=VerificationResult)
async def verify_reachability(request: ReachabilityRequest):
    """
    Verify network reachability between source and destination IPs.

    Executes Batfish reachability analysis to determine if traffic from
    source IP can reach destination IP, and provides flow traces showing
    the packet path through the network.

    Args:
        request: Reachability verification request

    Returns:
        VerificationResult with flow traces

    Raises:
        HTTPException: If validation fails or query encounters an error
    """
    try:
        logger.info(
            f"Reachability verification request",
            extra={
                "snapshot": request.snapshot,
                "src_ip": request.src_ip,
                "dst_ip": request.dst_ip,
                "src_node": request.src_node
            }
        )

        result = verification_service.verify_reachability(
            snapshot_name=request.snapshot,
            src_ip=request.src_ip,
            dst_ip=request.dst_ip,
            network_name=request.network,
            src_node=request.src_node
        )

        return result

    except BatfishException as e:
        logger.error(f"Batfish error in reachability verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batfish verification failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in reachability verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/acl", response_model=VerificationResult)
async def verify_acl(request: ACLRequest):
    """
    Verify ACL/filter behavior for specified traffic.

    Executes Batfish searchFilters query to determine which ACL lines
    match the specified traffic and what action is taken.

    Args:
        request: ACL verification request

    Returns:
        VerificationResult with ACL match results

    Raises:
        HTTPException: If validation fails or query encounters an error
    """
    try:
        logger.info(
            f"ACL verification request",
            extra={
                "snapshot": request.snapshot,
                "filter_name": request.filter_name,
                "src_ip": request.src_ip,
                "dst_ip": request.dst_ip,
                "protocol": request.protocol
            }
        )

        result = verification_service.verify_acl(
            snapshot_name=request.snapshot,
            filter_name=request.filter_name,
            src_ip=request.src_ip,
            dst_ip=request.dst_ip,
            network_name=request.network,
            protocol=request.protocol
        )

        return result

    except BatfishException as e:
        logger.error(f"Batfish error in ACL verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batfish verification failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in ACL verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/routing", response_model=VerificationResult)
async def verify_routing(request: RoutingRequest):
    """
    Verify routing table entries.

    Executes Batfish routes query to retrieve routing table information
    for specified nodes and/or networks.

    Args:
        request: Routing verification request

    Returns:
        VerificationResult with route entries

    Raises:
        HTTPException: If validation fails or query encounters an error
    """
    try:
        logger.info(
            f"Routing verification request",
            extra={
                "snapshot": request.snapshot,
                "nodes": request.nodes,
                "network_filter": request.network_filter
            }
        )

        result = verification_service.verify_routing(
            snapshot_name=request.snapshot,
            network_name=request.network,
            nodes=request.nodes,
            network_filter=request.network_filter
        )

        return result

    except BatfishException as e:
        logger.error(f"Batfish error in routing verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batfish verification failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in routing verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
