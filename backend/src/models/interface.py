"""
Interface model for device network interfaces.

Represents physical and logical interfaces on network devices.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class Interface(BaseModel):
    """
    Represents a network interface on a device.

    Attributes:
        hostname: Device hostname that owns this interface
        interface_name: Interface name (e.g., GigabitEthernet0/0, eth0)
        active: Whether the interface is administratively up
        ip_addresses: List of IP addresses assigned to the interface
        subnet_mask: Subnet mask for the primary IP
        description: Interface description from configuration
        vlan: VLAN ID if applicable
        bandwidth: Interface bandwidth in Mbps
        mtu: Maximum transmission unit
    """

    hostname: str = Field(..., min_length=1, description="Device hostname")
    interface_name: str = Field(..., min_length=1, description="Interface name")
    active: bool = Field(default=True, description="Interface is active")
    ip_addresses: List[str] = Field(default_factory=list, description="IP addresses")
    subnet_mask: Optional[str] = Field(None, description="Subnet mask")
    description: Optional[str] = Field(None, description="Interface description")
    vlan: Optional[int] = Field(None, ge=1, le=4094, description="VLAN ID")
    bandwidth: Optional[int] = Field(None, ge=0, description="Bandwidth in Mbps")
    mtu: Optional[int] = Field(None, ge=64, le=9216, description="MTU in bytes")

    class Config:
        json_schema_extra = {
            "example": {
                "hostname": "router1",
                "interface_name": "GigabitEthernet0/0",
                "active": True,
                "ip_addresses": ["192.168.1.1"],
                "subnet_mask": "255.255.255.0",
                "description": "Link to switch1",
                "bandwidth": 1000,
                "mtu": 1500
            }
        }
