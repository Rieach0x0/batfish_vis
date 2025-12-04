"""
Edge model for network topology links.

Represents Layer 3 connections between devices in the network topology.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Edge(BaseModel):
    """
    Represents a network link (edge) between two devices.

    Attributes:
        source_hostname: Source device hostname
        source_interface: Source interface name
        target_hostname: Target device hostname
        target_interface: Target interface name
        link_type: Type of link (layer3, layer2, etc.)
        source_ip: Source IP address
        target_ip: Target IP address
        bandwidth: Link bandwidth in Mbps
        protocol: Routing protocol on this link (ospf, bgp, static, etc.)
    """

    source_hostname: str = Field(..., min_length=1, description="Source device hostname")
    source_interface: str = Field(..., min_length=1, description="Source interface name")
    target_hostname: str = Field(..., min_length=1, description="Target device hostname")
    target_interface: str = Field(..., min_length=1, description="Target interface name")
    link_type: str = Field(default="layer3", description="Link type")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    target_ip: Optional[str] = Field(None, description="Target IP address")
    bandwidth: Optional[int] = Field(None, ge=0, description="Link bandwidth in Mbps")
    protocol: Optional[str] = Field(None, description="Routing protocol")

    class Config:
        json_schema_extra = {
            "example": {
                "source_hostname": "router1",
                "source_interface": "GigabitEthernet0/0",
                "target_hostname": "router2",
                "target_interface": "GigabitEthernet0/1",
                "link_type": "layer3",
                "source_ip": "192.168.1.1",
                "target_ip": "192.168.1.2",
                "bandwidth": 1000,
                "protocol": "ospf"
            }
        }
