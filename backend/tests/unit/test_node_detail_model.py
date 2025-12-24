"""
Unit tests for NodeDetail Pydantic model validation

TDD Phase: RED - These tests should FAIL if model validation is incorrect
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from src.models.node_detail import NodeDetail, Interface, DeviceMetadata


def test_nodedetail_valid_data():
    """Test NodeDetail model with valid data."""
    # Arrange
    valid_data = {
        "hostname": "router-01",
        "device_type": "router",
        "vendor": "Cisco",
        "model": "ISR4451",
        "os_version": "IOS XE 17.3.4a",
        "config_format": "CISCO_IOS",
        "status": "active",
        "interface_count": 1,
        "interfaces": [
            {
                "name": "GigabitEthernet0/0/0",
                "active": True,
                "ip_addresses": ["192.168.1.1/24"],
                "description": "Uplink",
                "vlan": None,
                "bandwidth_mbps": 1000,
                "mtu": 1500
            }
        ],
        "metadata": {
            "snapshot_name": "test_snapshot",
            "last_updated": "2025-12-23T10:15:32Z",
            "config_file_path": "/snapshots/test_snapshot/configs/router-01.cfg"
        }
    }

    # Act
    node_detail = NodeDetail(**valid_data)

    # Assert
    assert node_detail.hostname == "router-01"
    assert node_detail.device_type == "router"
    assert node_detail.vendor == "Cisco"
    assert node_detail.status == "active"
    assert node_detail.interface_count == 1
    assert len(node_detail.interfaces) == 1
    assert node_detail.metadata.snapshot_name == "test_snapshot"


def test_nodedetail_with_null_metadata():
    """Test NodeDetail model handles null optional fields."""
    # Arrange
    data_with_nulls = {
        "hostname": "unknown-device",
        "device_type": None,
        "vendor": None,
        "model": None,
        "os_version": None,
        "config_format": None,
        "status": "unknown",
        "interface_count": 0,
        "interfaces": [],
        "metadata": {
            "snapshot_name": "test_snapshot",
            "last_updated": "2025-12-23T10:15:32Z",
            "config_file_path": None
        }
    }

    # Act
    node_detail = NodeDetail(**data_with_nulls)

    # Assert
    assert node_detail.hostname == "unknown-device"
    assert node_detail.vendor is None
    assert node_detail.model is None
    assert node_detail.os_version is None
    assert node_detail.interface_count == 0
    assert len(node_detail.interfaces) == 0


def test_nodedetail_invalid_status():
    """Test NodeDetail model rejects invalid status values."""
    # Arrange
    invalid_data = {
        "hostname": "router-01",
        "status": "invalid_status",  # Invalid - not in (active, inactive, unknown)
        "interface_count": 0,
        "interfaces": [],
        "metadata": {
            "snapshot_name": "test_snapshot",
            "last_updated": "2025-12-23T10:15:32Z"
        }
    }

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        NodeDetail(**invalid_data)

    assert "status" in str(exc_info.value)


def test_nodedetail_missing_required_fields():
    """Test NodeDetail model rejects missing required fields."""
    # Arrange
    incomplete_data = {
        "hostname": "router-01",
        # Missing: status, interface_count, interfaces, metadata
    }

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        NodeDetail(**incomplete_data)

    error_str = str(exc_info.value)
    assert "status" in error_str or "interface_count" in error_str


def test_interface_valid_data():
    """Test Interface model with valid data."""
    # Arrange
    valid_interface = {
        "name": "GigabitEthernet0/0/0",
        "active": True,
        "ip_addresses": ["192.168.1.1/24", "10.0.0.1/30"],
        "description": "Uplink to core switch",
        "vlan": 100,
        "bandwidth_mbps": 1000,
        "mtu": 1500
    }

    # Act
    interface = Interface(**valid_interface)

    # Assert
    assert interface.name == "GigabitEthernet0/0/0"
    assert interface.active is True
    assert len(interface.ip_addresses) == 2
    assert interface.vlan == 100
    assert interface.bandwidth_mbps == 1000
    assert interface.mtu == 1500


def test_interface_empty_ip_addresses():
    """Test Interface model allows empty IP address list."""
    # Arrange
    interface_no_ips = {
        "name": "Ethernet1",
        "active": True,
        "ip_addresses": [],  # Empty - valid for access ports
    }

    # Act
    interface = Interface(**interface_no_ips)

    # Assert
    assert interface.name == "Ethernet1"
    assert interface.active is True
    assert interface.ip_addresses == []


def test_interface_invalid_vlan():
    """Test Interface model rejects invalid VLAN IDs."""
    # Arrange
    invalid_vlan_data = {
        "name": "Ethernet1",
        "active": True,
        "ip_addresses": [],
        "vlan": 5000  # Invalid - must be 1-4094
    }

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        Interface(**invalid_vlan_data)

    assert "vlan" in str(exc_info.value)


def test_interface_invalid_mtu():
    """Test Interface model rejects invalid MTU values."""
    # Arrange
    invalid_mtu_data = {
        "name": "Ethernet1",
        "active": True,
        "ip_addresses": [],
        "mtu": 50  # Invalid - must be 68-9216
    }

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        Interface(**invalid_mtu_data)

    assert "mtu" in str(exc_info.value)


def test_devicemetadata_valid_data():
    """Test DeviceMetadata model with valid data."""
    # Arrange
    valid_metadata = {
        "snapshot_name": "prod_network_2025-12-23",
        "last_updated": "2025-12-23T10:15:32Z",
        "config_file_path": "/snapshots/prod_network/configs/router-01.cfg"
    }

    # Act
    metadata = DeviceMetadata(**valid_metadata)

    # Assert
    assert metadata.snapshot_name == "prod_network_2025-12-23"
    assert isinstance(metadata.last_updated, datetime)
    assert metadata.config_file_path == "/snapshots/prod_network/configs/router-01.cfg"


def test_devicemetadata_missing_snapshot_name():
    """Test DeviceMetadata model rejects missing snapshot_name."""
    # Arrange
    invalid_metadata = {
        "last_updated": "2025-12-23T10:15:32Z"
        # Missing: snapshot_name (required)
    }

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        DeviceMetadata(**invalid_metadata)

    assert "snapshot_name" in str(exc_info.value)


def test_nodedetail_interface_count_matches_array_length():
    """Test that interface_count should match interfaces array length (business rule)."""
    # Note: This is validated by the service layer, not the model
    # The model allows mismatches, but we document the expectation
    data = {
        "hostname": "router-01",
        "status": "active",
        "interface_count": 2,  # Says 2
        "interfaces": [  # But only 1 interface provided
            {
                "name": "GigabitEthernet0/0/0",
                "active": True,
                "ip_addresses": []
            }
        ],
        "metadata": {
            "snapshot_name": "test_snapshot",
            "last_updated": "2025-12-23T10:15:32Z"
        }
    }

    # Act - Model allows this (validation happens in service layer)
    node_detail = NodeDetail(**data)

    # Assert - Document the mismatch exists
    assert node_detail.interface_count == 2
    assert len(node_detail.interfaces) == 1
    # In real implementation, service layer should ensure these match
