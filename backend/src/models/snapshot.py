"""
Snapshot data model.

Represents a Batfish snapshot with metadata and parse status.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ParseError(BaseModel):
    """Parse error for a single configuration file."""

    file_name: str = Field(..., description="Configuration file name that failed to parse")
    error_message: str = Field(..., description="Error message from Batfish parser")
    line_number: Optional[int] = Field(None, description="Line number where error occurred (if available)")


class Snapshot(BaseModel):
    """
    Batfish snapshot metadata.

    Represents an immutable snapshot of network configuration files
    analyzed by Batfish v2025.07.07.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Unique snapshot name")
    network: str = Field(..., description="Network name (logical grouping in Batfish)")
    created_at: datetime = Field(..., description="Snapshot creation timestamp")
    status: str = Field(..., description="Initialization status (COMPLETE, FAILED, IN_PROGRESS)")
    config_file_count: int = Field(..., ge=0, description="Number of configuration files uploaded")
    device_count: int = Field(..., ge=0, description="Number of devices detected by Batfish")
    batfish_version: str = Field(default="v2025.07.07", description="Batfish version used")
    parse_errors: List[ParseError] = Field(default_factory=list, description="Files that failed to parse")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "snapshot-2025-11-21-14-30",
                "network": "production-network",
                "created_at": "2025-11-21T14:30:15Z",
                "status": "COMPLETE",
                "config_file_count": 15,
                "device_count": 12,
                "batfish_version": "v2025.07.07",
                "parse_errors": []
            }
        }


class SnapshotCreate(BaseModel):
    """Request model for creating a new snapshot."""

    snapshot_name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$", description="Unique snapshot name (alphanumeric, hyphen, underscore)")
    network_name: str = Field(default="default", description="Network name for logical grouping")


class SnapshotListResponse(BaseModel):
    """Response model for listing snapshots."""

    snapshots: List[Snapshot] = Field(..., description="List of snapshots")
