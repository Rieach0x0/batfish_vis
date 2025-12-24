"""
Topology service for network topology extraction.

Uses Batfish queries to extract network topology information including
devices, interfaces, and Layer 3 edges.
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path

from pybatfish.client.session import Session
from pybatfish.datamodel import HeaderConstraints
from pybatfish.datamodel.flow import PathConstraints

from ..models.device import Device
from ..models.interface import Interface
from ..models.edge import Edge
from ..exceptions import BatfishException


logger = logging.getLogger(__name__)


class TopologyService:
    """
    Service for extracting and managing network topology data.

    Uses Batfish questions to query network topology information
    from snapshots.
    """

    def __init__(self, bf_session: Session):
        """
        Initialize topology service.

        Args:
            bf_session: Batfish session instance
        """
        self.bf_session = bf_session
        self.bf = bf_session  # Alias for query methods

    def get_devices(self, snapshot_name: str, network_name: str = "default") -> List[Device]:
        """
        Get all devices in the network snapshot.

        Args:
            snapshot_name: Snapshot name
            network_name: Network name (default: "default")

        Returns:
            List of Device objects

        Raises:
            BatfishException: If Batfish query fails
        """
        try:
            self.bf_session.set_network(network_name)
            self.bf_session.set_snapshot(snapshot_name)

            # Query node properties
            node_props = self.bf.q.nodeProperties().answer().frame()

            devices = []
            for _, row in node_props.iterrows():
                device = Device(
                    hostname=row.get('Node', ''),
                    vendor=self._extract_vendor(row),
                    model=row.get('Model', None),
                    device_type=self._infer_device_type(row),
                    config_format=row.get('Configuration_Format', None),
                    interfaces_count=0  # Will be updated when getting interfaces
                )
                devices.append(device)

            logger.info(f"Retrieved {len(devices)} devices from snapshot '{snapshot_name}'")
            return devices

        except Exception as e:
            logger.error(f"Failed to get devices: {str(e)}")
            raise BatfishException(f"Failed to retrieve devices: {str(e)}")

    def get_interfaces(self, snapshot_name: str, network_name: str = "default",
                      hostname: Optional[str] = None) -> List[Interface]:
        """
        Get network interfaces from the snapshot.

        Args:
            snapshot_name: Snapshot name
            network_name: Network name (default: "default")
            hostname: Optional hostname to filter interfaces by device

        Returns:
            List of Interface objects

        Raises:
            BatfishException: If Batfish query fails
        """
        try:
            self.bf_session.set_network(network_name)
            self.bf_session.set_snapshot(snapshot_name)

            # Query interface properties
            if hostname:
                interface_props = self.bf.q.interfaceProperties(nodes=hostname).answer().frame()
            else:
                interface_props = self.bf.q.interfaceProperties().answer().frame()

            interfaces = []
            for _, row in interface_props.iterrows():
                interface = Interface(
                    hostname=row.get('Interface').hostname if hasattr(row.get('Interface'), 'hostname') else '',
                    interface_name=row.get('Interface').interface if hasattr(row.get('Interface'), 'interface') else '',
                    active=row.get('Active', True),
                    ip_addresses=self._extract_ip_addresses(row),
                    subnet_mask=self._extract_subnet_mask(row),
                    description=row.get('Description', None),
                    vlan=row.get('VLAN', None),
                    bandwidth=row.get('Bandwidth', None),
                    mtu=row.get('MTU', None)
                )
                interfaces.append(interface)

            logger.info(f"Retrieved {len(interfaces)} interfaces from snapshot '{snapshot_name}'")
            return interfaces

        except Exception as e:
            logger.error(f"Failed to get interfaces: {str(e)}")
            raise BatfishException(f"Failed to retrieve interfaces: {str(e)}")

    def get_layer3_edges(self, snapshot_name: str, network_name: str = "default") -> List[Edge]:
        """
        Get Layer 3 edges (links) in the network topology.

        Uses Batfish layer3Edges() question to extract network connections.

        Args:
            snapshot_name: Snapshot name
            network_name: Network name (default: "default")

        Returns:
            List of Edge objects representing Layer 3 connections

        Raises:
            BatfishException: If Batfish query fails
        """
        try:
            self.bf_session.set_network(network_name)
            self.bf_session.set_snapshot(snapshot_name)

            # Query layer 3 edges
            edges_df = self.bf.q.layer3Edges().answer().frame()

            edges = []
            for _, row in edges_df.iterrows():
                # Extract interface information
                iface1 = row.get('Interface')
                iface2 = row.get('Remote_Interface')

                if not iface1 or not iface2:
                    continue

                edge = Edge(
                    source_hostname=iface1.hostname if hasattr(iface1, 'hostname') else '',
                    source_interface=iface1.interface if hasattr(iface1, 'interface') else '',
                    target_hostname=iface2.hostname if hasattr(iface2, 'hostname') else '',
                    target_interface=iface2.interface if hasattr(iface2, 'interface') else '',
                    link_type="layer3",
                    source_ip=row.get('IPs', {}).get(str(iface1), None) if isinstance(row.get('IPs'), dict) else None,
                    target_ip=row.get('Remote_IPs', {}).get(str(iface2), None) if isinstance(row.get('Remote_IPs'), dict) else None
                )
                edges.append(edge)

            logger.info(f"Retrieved {len(edges)} Layer 3 edges from snapshot '{snapshot_name}'")
            return edges

        except Exception as e:
            logger.error(f"Failed to get Layer 3 edges: {str(e)}")
            raise BatfishException(f"Failed to retrieve topology edges: {str(e)}")

    def get_topology(self, snapshot_name: str, network_name: str = "default") -> Dict:
        """
        Get complete network topology including devices and edges.

        Args:
            snapshot_name: Snapshot name
            network_name: Network name (default: "default")

        Returns:
            Dictionary with 'nodes' (devices) and 'edges' (links)

        Raises:
            BatfishException: If Batfish query fails
        """
        try:
            devices = self.get_devices(snapshot_name, network_name)
            edges = self.get_layer3_edges(snapshot_name, network_name)

            # Update interface counts
            interfaces = self.get_interfaces(snapshot_name, network_name)
            interface_counts = {}
            for iface in interfaces:
                interface_counts[iface.hostname] = interface_counts.get(iface.hostname, 0) + 1

            for device in devices:
                device.interfaces_count = interface_counts.get(device.hostname, 0)

            topology = {
                "nodes": [device.dict() for device in devices],
                "edges": [edge.dict() for edge in edges]
            }

            logger.info(f"Retrieved complete topology: {len(devices)} nodes, {len(edges)} edges")
            return topology

        except Exception as e:
            logger.error(f"Failed to get topology: {str(e)}")
            raise BatfishException(f"Failed to retrieve complete topology: {str(e)}")

    # Helper methods

    def _extract_vendor(self, row) -> Optional[str]:
        """Extract vendor from node properties row."""
        vendor = row.get('Vendor', None)
        if vendor:
            return vendor.lower()

        # Try to infer from configuration format
        config_format = row.get('Configuration_Format', '').lower()
        if 'cisco' in config_format or 'ios' in config_format:
            return 'cisco'
        elif 'juniper' in config_format or 'junos' in config_format:
            return 'juniper'
        elif 'arista' in config_format or 'eos' in config_format:
            return 'arista'
        elif 'paloalto' in config_format or 'panos' in config_format:
            return 'paloalto'

        return None

    def _infer_device_type(self, row) -> Optional[str]:
        """Infer device type from node properties."""
        hostname = row.get('Node', '').lower()

        if 'router' in hostname or 'rtr' in hostname:
            return 'router'
        elif 'switch' in hostname or 'sw' in hostname:
            return 'switch'
        elif 'firewall' in hostname or 'fw' in hostname:
            return 'firewall'

        return None

    def _extract_ip_addresses(self, row) -> List[str]:
        """Extract IP addresses from interface properties row."""
        primary_address = row.get('Primary_Address', None)
        all_addresses = row.get('All_Addresses', [])

        if primary_address:
            return [str(primary_address)]
        elif all_addresses:
            return [str(addr) for addr in all_addresses]

        return []

    def _extract_subnet_mask(self, row) -> Optional[str]:
        """Extract subnet mask from interface properties row."""
        primary_address = row.get('Primary_Address', None)

        if primary_address and hasattr(primary_address, 'netmask'):
            return str(primary_address.netmask)

        return None

    async def get_node_details(
        self,
        snapshot_name: str,
        hostname: str,
        network_name: str = "default"
    ):
        """
        Get comprehensive details for a specific network node.

        Aggregates node properties and interface data from Batfish queries.
        Derives operational status from interface active states.

        Args:
            snapshot_name: Batfish snapshot name
            hostname: Device hostname
            network_name: Network name (default: "default")

        Returns:
            NodeDetail object with complete node information

        Raises:
            KeyError: If node not found in snapshot
            BatfishException: If Batfish query fails
        """
        from ..models.node_detail import NodeDetail, Interface as NodeInterface, DeviceMetadata
        from datetime import datetime
        import math

        def nan_to_none(value):
            """Convert pandas NaN to None for Pydantic validation."""
            if value is None:
                return None
            if isinstance(value, float) and math.isnan(value):
                return None
            return value

        try:
            logger.info(
                f"Node detail request initiated: hostname={hostname}, "
                f"snapshot={snapshot_name}, network={network_name}"
            )

            self.bf_session.set_network(network_name)
            self.bf_session.set_snapshot(snapshot_name)

            # Query node properties
            logger.debug(f"Querying node properties for '{hostname}'")
            nodes_df = self.bf.q.nodeProperties(nodes=hostname).answer().frame()

            if nodes_df.empty:
                logger.warning(
                    f"Node not found: hostname={hostname}, snapshot={snapshot_name}, network={network_name}"
                )
                raise KeyError(f"Node '{hostname}' not found in snapshot '{snapshot_name}'")

            node_row = nodes_df.iloc[0]

            # Query interface properties for this node
            logger.debug(f"Querying interface properties for '{hostname}'")
            interfaces_df = self.bf.q.interfaceProperties(nodes=hostname).answer().frame()
            logger.debug(f"Found {len(interfaces_df)} interfaces for '{hostname}'")

            # Map interfaces to NodeInterface model
            interfaces = []
            for _, iface_row in interfaces_df.iterrows():
                iface_name = iface_row.get('Interface', {})
                if hasattr(iface_name, 'interface'):
                    iface_name_str = iface_name.interface
                else:
                    iface_name_str = str(iface_name)

                # Extract IP addresses
                ip_addresses = self._extract_ip_addresses(iface_row)

                interface = NodeInterface(
                    name=iface_name_str,
                    active=iface_row.get('Active', False),
                    ip_addresses=ip_addresses,
                    description=nan_to_none(iface_row.get('Description', None)),
                    vlan=nan_to_none(iface_row.get('Access_VLAN', None)),
                    bandwidth_mbps=nan_to_none(iface_row.get('Bandwidth', None)),
                    mtu=nan_to_none(iface_row.get('MTU', None))
                )
                interfaces.append(interface)

            # Derive status from interface states
            status = "unknown"
            if interfaces:
                status = "active" if any(iface.active for iface in interfaces) else "inactive"

            # Build metadata
            metadata = DeviceMetadata(
                snapshot_name=snapshot_name,
                last_updated=datetime.utcnow(),
                config_file_path=None  # Batfish doesn't expose this directly
            )

            # Build NodeDetail response
            node_detail = NodeDetail(
                hostname=hostname,
                device_type=node_row.get('Device_Type', None),
                vendor=node_row.get('Vendor', None),
                model=node_row.get('Model', None),
                os_version=None,  # Not directly available from nodeProperties
                config_format=node_row.get('Configuration_Format', None),
                status=status,
                interface_count=len(interfaces),
                interfaces=interfaces,
                metadata=metadata
            )

            logger.info(
                f"Node detail request completed: hostname={hostname}, "
                f"snapshot={snapshot_name}, interface_count={node_detail.interface_count}, "
                f"status={status}, vendor={node_detail.vendor}, device_type={node_detail.device_type}"
            )

            return node_detail

        except KeyError:
            raise
        except Exception as e:
            logger.error(
                f"Node detail request failed: hostname={hostname}, "
                f"snapshot={snapshot_name}, error={str(e)}"
            )
            raise BatfishException(f"Failed to retrieve node details: {str(e)}")
