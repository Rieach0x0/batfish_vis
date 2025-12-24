"""
Unit tests for topology service - get_node_details() method

TDD Phase: GREEN - These tests validate the implementation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import pandas as pd
from src.models.node_detail import NodeDetail, Interface, DeviceMetadata
from src.services.topology_service import TopologyService


@pytest.mark.asyncio
async def test_get_node_details_with_interfaces():
    """Test fetching node details for a device with configured interfaces."""
    # Arrange
    snapshot = "test_snapshot"
    hostname = "router-01"
    network = "default"

    # Create mock Batfish session
    mock_session = MagicMock()
    mock_session.q = MagicMock()

    # Mock nodeProperties query response
    node_data = pd.DataFrame([{
        'Node': 'router-01',
        'Device_Type': 'router',
        'Vendor': 'Cisco',
        'Model': 'ISR4451',
        'Configuration_Format': 'CISCO_IOS'
    }])

    mock_node_answer = MagicMock()
    mock_node_answer.frame.return_value = node_data
    mock_node_query = MagicMock()
    mock_node_query.answer.return_value = mock_node_answer
    mock_session.q.nodeProperties.return_value = mock_node_query

    # Mock interfaceProperties query response
    iface_data = pd.DataFrame([
        {
            'Interface': MagicMock(hostname='router-01', interface='GigabitEthernet0/0/0'),
            'Active': True,
            'Primary_Address': '192.168.1.1/24',
            'All_Addresses': [],
            'Description': 'Uplink',
            'Access_VLAN': None,
            'Bandwidth': 1000,
            'MTU': 1500
        },
        {
            'Interface': MagicMock(hostname='router-01', interface='GigabitEthernet0/0/1'),
            'Active': False,
            'Primary_Address': None,
            'All_Addresses': [],
            'Description': None,
            'Access_VLAN': None,
            'Bandwidth': None,
            'MTU': 1500
        }
    ])

    mock_iface_answer = MagicMock()
    mock_iface_answer.frame.return_value = iface_data
    mock_iface_query = MagicMock()
    mock_iface_query.answer.return_value = mock_iface_answer
    mock_session.q.interfaceProperties.return_value = mock_iface_query

    # Create service and execute
    service = TopologyService(mock_session)
    result = await service.get_node_details(snapshot, hostname, network)

    # Assert
    assert isinstance(result, NodeDetail)
    assert result.hostname == "router-01"
    assert result.device_type == "router"
    assert result.vendor == "Cisco"
    assert result.model == "ISR4451"
    assert result.config_format == "CISCO_IOS"
    assert result.status == "active"  # At least one interface is active
    assert result.interface_count == 2
    assert len(result.interfaces) == 2
    assert result.interfaces[0].name == "GigabitEthernet0/0/0"
    assert result.interfaces[0].active is True
    assert "192.168.1.1/24" in result.interfaces[0].ip_addresses
    assert result.metadata.snapshot_name == snapshot


@pytest.mark.asyncio
async def test_get_node_details_no_interfaces():
    """Test node with no configured interfaces."""
    # Arrange
    snapshot = "test_snapshot"
    hostname = "placeholder-device"
    network = "default"

    # Create mock Batfish session
    mock_session = MagicMock()
    mock_session.q = MagicMock()

    # Mock nodeProperties query
    node_data = pd.DataFrame([{
        'Node': 'placeholder-device',
        'Device_Type': None,
        'Vendor': None,
        'Model': None,
        'Configuration_Format': None
    }])

    mock_node_answer = MagicMock()
    mock_node_answer.frame.return_value = node_data
    mock_node_query = MagicMock()
    mock_node_query.answer.return_value = mock_node_answer
    mock_session.q.nodeProperties.return_value = mock_node_query

    # Mock interfaceProperties query (empty)
    iface_data = pd.DataFrame([])

    mock_iface_answer = MagicMock()
    mock_iface_answer.frame.return_value = iface_data
    mock_iface_query = MagicMock()
    mock_iface_query.answer.return_value = mock_iface_answer
    mock_session.q.interfaceProperties.return_value = mock_iface_query

    # Create service and execute
    service = TopologyService(mock_session)
    result = await service.get_node_details(snapshot, hostname, network)

    # Assert
    assert isinstance(result, NodeDetail)
    assert result.hostname == "placeholder-device"
    assert result.status == "unknown"  # No interfaces
    assert result.interface_count == 0
    assert len(result.interfaces) == 0


@pytest.mark.asyncio
async def test_get_node_details_null_metadata():
    """Test handling of null/missing metadata fields."""
    # Arrange
    snapshot = "test_snapshot"
    hostname = "minimal-device"
    network = "default"

    # Create mock Batfish session
    mock_session = MagicMock()
    mock_session.q = MagicMock()

    # Mock nodeProperties with null fields
    node_data = pd.DataFrame([{
        'Node': 'minimal-device',
        'Device_Type': None,
        'Vendor': None,
        'Model': None,
        'Configuration_Format': None
    }])

    mock_node_answer = MagicMock()
    mock_node_answer.frame.return_value = node_data
    mock_node_query = MagicMock()
    mock_node_query.answer.return_value = mock_node_answer
    mock_session.q.nodeProperties.return_value = mock_node_query

    # Mock interfaceProperties (empty)
    iface_data = pd.DataFrame([])

    mock_iface_answer = MagicMock()
    mock_iface_answer.frame.return_value = iface_data
    mock_iface_query = MagicMock()
    mock_iface_query.answer.return_value = mock_iface_answer
    mock_session.q.interfaceProperties.return_value = mock_iface_query

    # Create service and execute
    service = TopologyService(mock_session)
    result = await service.get_node_details(snapshot, hostname, network)

    # Assert
    assert result.device_type is None
    assert result.vendor is None
    assert result.model is None
    assert result.os_version is None
    assert result.config_format is None
    assert result.metadata.config_file_path is None


@pytest.mark.asyncio
async def test_get_node_details_derives_status_from_interfaces():
    """Test that status is correctly derived from interface states."""
    # Arrange
    snapshot = "test_snapshot"
    hostname = "switch-01"
    network = "default"

    # Create mock Batfish session
    mock_session = MagicMock()
    mock_session.q = MagicMock()

    # Mock nodeProperties
    node_data = pd.DataFrame([{
        'Node': 'switch-01',
        'Device_Type': 'switch',
        'Vendor': 'Cisco',
        'Model': None,
        'Configuration_Format': 'CISCO_IOS'
    }])

    mock_node_answer = MagicMock()
    mock_node_answer.frame.return_value = node_data
    mock_node_query = MagicMock()
    mock_node_query.answer.return_value = mock_node_answer
    mock_session.q.nodeProperties.return_value = mock_node_query

    # Mock interfaceProperties (all inactive)
    iface_data = pd.DataFrame([
        {
            'Interface': MagicMock(hostname='switch-01', interface='Ethernet1'),
            'Active': False,
            'Primary_Address': None,
            'All_Addresses': [],
            'Description': None,
            'Access_VLAN': 100,
            'Bandwidth': 10000,
            'MTU': 9214
        },
        {
            'Interface': MagicMock(hostname='switch-01', interface='Ethernet2'),
            'Active': False,
            'Primary_Address': None,
            'All_Addresses': [],
            'Description': None,
            'Access_VLAN': 100,
            'Bandwidth': 10000,
            'MTU': 9214
        }
    ])

    mock_iface_answer = MagicMock()
    mock_iface_answer.frame.return_value = iface_data
    mock_iface_query = MagicMock()
    mock_iface_query.answer.return_value = mock_iface_answer
    mock_session.q.interfaceProperties.return_value = mock_iface_query

    # Create service and execute
    service = TopologyService(mock_session)
    result = await service.get_node_details(snapshot, hostname, network)

    # Assert
    assert result.status == "inactive"  # All interfaces inactive
    assert result.interface_count == 2
