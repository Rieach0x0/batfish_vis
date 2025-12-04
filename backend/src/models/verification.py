"""
Verification result models for configuration verification queries.

Represents results from Batfish verification queries including
reachability, ACL filtering, and routing table analysis.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class FlowTraceHop(BaseModel):
    """
    Represents a single hop in a flow trace.

    Attributes:
        node: Device hostname
        action: Action taken at this hop (FORWARDED, ACCEPTED, DENIED, etc.)
        interface_in: Ingress interface
        interface_out: Egress interface
    """

    node: str = Field(..., description="Device hostname")
    action: str = Field(..., description="Action taken")
    interface_in: Optional[str] = Field(None, description="Ingress interface")
    interface_out: Optional[str] = Field(None, description="Egress interface")

    class Config:
        json_schema_extra = {
            "example": {
                "node": "router1",
                "action": "FORWARDED",
                "interface_in": "GigabitEthernet0/0",
                "interface_out": "GigabitEthernet0/1"
            }
        }


class FlowTrace(BaseModel):
    """
    Represents a complete flow trace from source to destination.

    Attributes:
        disposition: Final disposition (ACCEPTED, DENIED, NO_ROUTE, etc.)
        hops: Sequence of hops in the flow trace
    """

    disposition: str = Field(..., description="Final flow disposition")
    hops: List[FlowTraceHop] = Field(default_factory=list, description="Flow trace hops")

    class Config:
        json_schema_extra = {
            "example": {
                "disposition": "ACCEPTED",
                "hops": [
                    {
                        "node": "router1",
                        "action": "FORWARDED",
                        "interface_in": "GigabitEthernet0/0",
                        "interface_out": "GigabitEthernet0/1"
                    },
                    {
                        "node": "router2",
                        "action": "ACCEPTED",
                        "interface_in": "GigabitEthernet0/0",
                        "interface_out": None
                    }
                ]
            }
        }


class ACLMatchResult(BaseModel):
    """
    Represents an ACL filter match result.

    Attributes:
        node: Device hostname
        filter_name: ACL/filter name
        action: PERMIT or DENY
        line_number: Line number in ACL
        line_content: ACL line text
    """

    node: str = Field(..., description="Device hostname")
    filter_name: str = Field(..., description="ACL/filter name")
    action: str = Field(..., description="PERMIT or DENY")
    line_number: Optional[int] = Field(None, description="ACL line number")
    line_content: Optional[str] = Field(None, description="ACL line text")

    class Config:
        json_schema_extra = {
            "example": {
                "node": "router1",
                "filter_name": "ACL_WAN",
                "action": "PERMIT",
                "line_number": 10,
                "line_content": "permit ip 192.168.1.0 0.0.0.255 any"
            }
        }


class RouteEntry(BaseModel):
    """
    Represents a routing table entry.

    Attributes:
        node: Device hostname
        network: Destination network prefix
        next_hop: Next hop IP address
        protocol: Routing protocol (STATIC, OSPF, BGP, etc.)
        admin_distance: Administrative distance
        metric: Route metric
        interface: Outgoing interface
    """

    node: str = Field(..., description="Device hostname")
    network: str = Field(..., description="Destination network")
    next_hop: Optional[str] = Field(None, description="Next hop IP")
    protocol: str = Field(..., description="Routing protocol")
    admin_distance: Optional[int] = Field(None, ge=0, le=255, description="Admin distance")
    metric: Optional[int] = Field(None, ge=0, description="Route metric")
    interface: Optional[str] = Field(None, description="Outgoing interface")

    class Config:
        json_schema_extra = {
            "example": {
                "node": "router1",
                "network": "10.0.0.0/8",
                "next_hop": "192.168.1.254",
                "protocol": "OSPF",
                "admin_distance": 110,
                "metric": 20,
                "interface": "GigabitEthernet0/1"
            }
        }


class VerificationResult(BaseModel):
    """
    Represents the result of a verification query.

    Attributes:
        query_id: Unique query identifier
        query_type: Type of query (reachability, acl, routing)
        executed_at: Query execution timestamp
        parameters: Query parameters as dict
        status: Query status (SUCCESS, FAILED, TIMEOUT)
        execution_time_ms: Execution time in milliseconds
        flow_traces: Flow traces for reachability queries
        acl_results: ACL match results for ACL queries
        route_entries: Route entries for routing queries
        error_message: Error message if query failed
    """

    query_id: str = Field(..., description="Unique query ID")
    query_type: str = Field(..., description="Query type (reachability/acl/routing)")
    executed_at: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    status: str = Field(..., description="Query status")
    execution_time_ms: int = Field(..., ge=0, description="Execution time in ms")

    # Result fields (one will be populated based on query_type)
    flow_traces: Optional[List[FlowTrace]] = Field(None, description="Reachability flow traces")
    acl_results: Optional[List[ACLMatchResult]] = Field(None, description="ACL match results")
    route_entries: Optional[List[RouteEntry]] = Field(None, description="Routing table entries")

    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "q_1234567890",
                "query_type": "reachability",
                "executed_at": "2025-11-21T10:30:00Z",
                "parameters": {
                    "snapshot": "snapshot1",
                    "src_ip": "192.168.1.10",
                    "dst_ip": "10.0.0.5"
                },
                "status": "SUCCESS",
                "execution_time_ms": 1250,
                "flow_traces": [
                    {
                        "disposition": "ACCEPTED",
                        "hops": []
                    }
                ],
                "error_message": None
            }
        }
