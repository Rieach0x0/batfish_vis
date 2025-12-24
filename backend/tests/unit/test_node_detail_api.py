"""
Unit tests for Node Detail API endpoint

TDD Phase: RED - These tests should FAIL until endpoint implementation is complete
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime


# This will fail until the endpoint is implemented
@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    from src.main import app
    return TestClient(app)


def test_get_node_details_success(client):
    """Test GET /topology/nodes/{hostname}/details returns node details."""
    # Arrange
    snapshot = "test_snapshot"
    hostname = "router-01"

    mock_node_detail = {
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
                "description": "Uplink",
                "vlan": None,
                "bandwidth_mbps": 1000,
                "mtu": 1500
            },
            {
                "name": "GigabitEthernet0/0/1",
                "active": False,
                "ip_addresses": [],
                "description": None,
                "vlan": None,
                "bandwidth_mbps": None,
                "mtu": 1500
            }
        ],
        "metadata": {
            "snapshot_name": snapshot,
            "last_updated": "2025-12-23T10:15:32Z",
            "config_file_path": "/snapshots/test_snapshot/configs/router-01.cfg"
        }
    }

    # Act
    with patch('src.api.topology_api.topology_service.get_node_details', new_callable=AsyncMock) as mock_service:
        from src.models.node_detail import NodeDetail
        mock_service.return_value = NodeDetail(**mock_node_detail)

        response = client.get(f"/api/topology/nodes/{hostname}/details?snapshot={snapshot}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["hostname"] == "router-01"
    assert data["device_type"] == "router"
    assert data["vendor"] == "Cisco"
    assert data["status"] == "active"
    assert data["interface_count"] == 2
    assert len(data["interfaces"]) == 2
    assert data["interfaces"][0]["name"] == "GigabitEthernet0/0/0"
    assert data["metadata"]["snapshot_name"] == snapshot


def test_get_node_details_missing_snapshot_parameter(client):
    """Test GET /topology/nodes/{hostname}/details returns 422 without snapshot parameter."""
    # Arrange
    hostname = "router-01"

    # Act
    response = client.get(f"/api/topology/nodes/{hostname}/details")
    # Missing required query param: snapshot

    # Assert
    assert response.status_code == 422  # Unprocessable Entity (missing required param)


def test_get_node_details_node_not_found(client):
    """Test GET /topology/nodes/{hostname}/details returns 404 for non-existent node."""
    # Arrange
    snapshot = "test_snapshot"
    hostname = "nonexistent-router"

    # Act
    with patch('src.api.topology_api.topology_service.get_node_details', new_callable=AsyncMock) as mock_service:
        mock_service.side_effect = KeyError(f"Node '{hostname}' not found")

        response = client.get(f"/api/topology/nodes/{hostname}/details?snapshot={snapshot}")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert hostname in data["detail"]


def test_get_node_details_batfish_service_error(client):
    """Test GET /topology/nodes/{hostname}/details returns 500 on Batfish service failure."""
    # Arrange
    snapshot = "test_snapshot"
    hostname = "router-01"

    # Act
    with patch('src.api.topology_api.topology_service.get_node_details', new_callable=AsyncMock) as mock_service:
        mock_service.side_effect = Exception("Batfish service unavailable")

        response = client.get(f"/api/topology/nodes/{hostname}/details?snapshot={snapshot}")

    # Assert
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Batfish" in data["detail"] or "Failed" in data["detail"]


def test_get_node_details_with_network_parameter(client):
    """Test GET /topology/nodes/{hostname}/details accepts network parameter."""
    # Arrange
    snapshot = "test_snapshot"
    hostname = "router-01"
    network = "custom_network"

    mock_node_detail = {
        "hostname": "router-01",
        "status": "active",
        "interface_count": 0,
        "interfaces": [],
        "metadata": {
            "snapshot_name": snapshot,
            "last_updated": "2025-12-23T10:15:32Z",
            "config_file_path": None
        }
    }

    # Act
    with patch('src.api.topology_api.topology_service.get_node_details', new_callable=AsyncMock) as mock_service:
        from src.models.node_detail import NodeDetail
        mock_service.return_value = NodeDetail(**mock_node_detail)

        response = client.get(
            f"/api/topology/nodes/{hostname}/details?snapshot={snapshot}&network={network}"
        )

    # Assert
    assert response.status_code == 200
    # Verify service was called with network parameter
    mock_service.assert_called_once()
    call_args = mock_service.call_args
    assert call_args[0][2] == network or call_args.kwargs.get('network') == network


def test_get_node_details_default_network_parameter(client):
    """Test GET /topology/nodes/{hostname}/details uses 'default' network if not specified."""
    # Arrange
    snapshot = "test_snapshot"
    hostname = "router-01"

    mock_node_detail = {
        "hostname": "router-01",
        "status": "active",
        "interface_count": 0,
        "interfaces": [],
        "metadata": {
            "snapshot_name": snapshot,
            "last_updated": "2025-12-23T10:15:32Z",
            "config_file_path": None
        }
    }

    # Act
    with patch('src.api.topology_api.topology_service.get_node_details', new_callable=AsyncMock) as mock_service:
        from src.models.node_detail import NodeDetail
        mock_service.return_value = NodeDetail(**mock_node_detail)

        response = client.get(f"/api/topology/nodes/{hostname}/details?snapshot={snapshot}")
        # Network parameter not provided - should default to "default"

    # Assert
    assert response.status_code == 200
    # Verify service was called with default network
    mock_service.assert_called_once()
    call_args = mock_service.call_args
    # Third arg should be network (default value)
    assert call_args[0][2] == "default" or call_args.kwargs.get('network') == "default"


def test_get_node_details_response_schema(client):
    """Test GET /topology/nodes/{hostname}/details response matches NodeDetail schema."""
    # Arrange
    snapshot = "test_snapshot"
    hostname = "router-01"

    mock_node_detail = {
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
                "vlan": 100,
                "bandwidth_mbps": 1000,
                "mtu": 1500
            }
        ],
        "metadata": {
            "snapshot_name": snapshot,
            "last_updated": "2025-12-23T10:15:32Z",
            "config_file_path": "/snapshots/test_snapshot/configs/router-01.cfg"
        }
    }

    # Act
    with patch('src.api.topology_api.topology_service.get_node_details', new_callable=AsyncMock) as mock_service:
        from src.models.node_detail import NodeDetail
        mock_service.return_value = NodeDetail(**mock_node_detail)

        response = client.get(f"/api/topology/nodes/{hostname}/details?snapshot={snapshot}")

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Verify all required fields present
    assert "hostname" in data
    assert "status" in data
    assert "interface_count" in data
    assert "interfaces" in data
    assert "metadata" in data

    # Verify interfaces structure
    assert isinstance(data["interfaces"], list)
    if len(data["interfaces"]) > 0:
        interface = data["interfaces"][0]
        assert "name" in interface
        assert "active" in interface
        assert "ip_addresses" in interface

    # Verify metadata structure
    metadata = data["metadata"]
    assert "snapshot_name" in metadata
    assert "last_updated" in metadata
