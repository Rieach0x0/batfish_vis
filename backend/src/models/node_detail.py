"""
Node Detail Data Models

This module defines Pydantic models for the Node Detail Panel feature.
All data originates from Batfish snapshot analysis.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DeviceMetadata(BaseModel):
    """Metadata about the snapshot and device configuration."""

    snapshot_name: str = Field(..., min_length=1, description="Batfish snapshot identifier")
    last_updated: datetime = Field(..., description="ISO 8601 timestamp of snapshot initialization")
    config_file_path: Optional[str] = Field(None, description="Path to device config file in snapshot")


class Interface(BaseModel):
    """Network interface with IP addresses and properties."""

    name: str = Field(..., min_length=1, max_length=100, description="Interface name/identifier")
    active: bool = Field(..., description="Whether interface is administratively up")
    ip_addresses: List[str] = Field(default_factory=list, description="IP addresses in CIDR notation")
    description: Optional[str] = Field(None, max_length=255, description="Interface description or comment")
    vlan: Optional[int] = Field(None, ge=1, le=4094, description="VLAN ID if applicable")
    bandwidth_mbps: Optional[int] = Field(None, ge=0, description="Interface bandwidth in Mbps")
    mtu: Optional[int] = Field(None, ge=68, le=9216, description="Maximum transmission unit")


class NodeDetail(BaseModel):
    """Complete node details including interfaces and metadata."""

    hostname: str = Field(..., min_length=1, max_length=255, description="Network device hostname")
    device_type: Optional[str] = Field(None, description="Device type (router, switch, firewall, host, unknown)")
    vendor: Optional[str] = Field(None, max_length=100, description="Device vendor/manufacturer")
    model: Optional[str] = Field(None, max_length=100, description="Device hardware model")
    os_version: Optional[str] = Field(None, max_length=100, description="Operating system version")
    config_format: Optional[str] = Field(None, description="Configuration file format")
    status: str = Field(..., pattern="^(active|inactive|unknown)$", description="Operational status")
    interface_count: int = Field(..., ge=0, description="Total number of interfaces")
    interfaces: List[Interface] = Field(..., description="Array of network interfaces")
    metadata: DeviceMetadata = Field(..., description="Additional device metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "hostname": "router-01",
                "device_type": "router",
                "vendor": "Cisco",
                "model": "ISR4451",
                "os_version": "IOS XE 17.3.4a",
                "config_format": "CISCO_IOS",
                "status": "active",
                "interface_count": 2,
                "interfaces": [
                    {
                        "name": "GigabitEthernet0/0/0",
                        "active": True,
                        "ip_addresses": ["192.168.1.1/24"],
                        "description": "Uplink to core",
                        "vlan": None,
                        "bandwidth_mbps": 1000,
                        "mtu": 1500
                    }
                ],
                "metadata": {
                    "snapshot_name": "prod_network_2025-12-23",
                    "last_updated": "2025-12-23T10:15:32Z",
                    "config_file_path": "/snapshots/prod_network/configs/router-01.cfg"
                }
            }
        }
