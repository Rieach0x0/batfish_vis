"""
Device model for network topology nodes.

Represents network devices (routers, switches, firewalls) in the topology.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Device(BaseModel):
    """
    Represents a network device in the topology.

    Attributes:
        hostname: Unique device hostname from configuration
        vendor: Device vendor (cisco, juniper, arista, paloalto, etc.)
        model: Device model/platform
        device_type: Device type (router, switch, firewall, etc.)
        config_format: Configuration format (ios, junos, eos, etc.)
        interfaces_count: Number of interfaces on the device
        x: X-coordinate for visualization (optional)
        y: Y-coordinate for visualization (optional)
    """

    hostname: str = Field(..., min_length=1, max_length=255, description="Device hostname")
    vendor: Optional[str] = Field(None, description="Device vendor")
    model: Optional[str] = Field(None, description="Device model/platform")
    device_type: Optional[str] = Field(None, description="Device type (router/switch/firewall)")
    config_format: Optional[str] = Field(None, description="Configuration format")
    interfaces_count: int = Field(default=0, ge=0, description="Number of interfaces")
    x: Optional[float] = Field(None, description="X-coordinate for visualization")
    y: Optional[float] = Field(None, description="Y-coordinate for visualization")

    class Config:
        json_schema_extra = {
            "example": {
                "hostname": "router1",
                "vendor": "cisco",
                "model": "ISR4321",
                "device_type": "router",
                "config_format": "ios",
                "interfaces_count": 4,
                "x": 100.0,
                "y": 150.0
            }
        }
