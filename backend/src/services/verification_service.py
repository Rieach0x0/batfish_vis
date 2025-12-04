"""
Verification service for network configuration validation.

Uses Batfish questions to execute verification queries including
reachability analysis, ACL testing, and routing table inspection.
"""

import logging
import time
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime

from pybatfish.client.session import Session
from pybatfish.datamodel import HeaderConstraints
from pybatfish.datamodel.flow import PathConstraints

from ..models.verification import (
    VerificationResult,
    FlowTrace,
    FlowTraceHop,
    ACLMatchResult,
    RouteEntry
)
from ..exceptions import BatfishException


logger = logging.getLogger(__name__)


class VerificationService:
    """
    Service for executing Batfish verification queries.

    Provides methods for reachability, ACL filtering, and routing validation.
    """

    def __init__(self, bf_session: Session):
        """
        Initialize verification service.

        Args:
            bf_session: Batfish session instance
        """
        self.bf_session = bf_session
        self.bf = bf_session  # Alias for query methods

    def verify_reachability(
        self,
        snapshot_name: str,
        src_ip: str,
        dst_ip: str,
        network_name: str = "default",
        src_node: Optional[str] = None
    ) -> VerificationResult:
        """
        Verify network reachability between source and destination IPs.

        Uses Batfish reachability() question to trace packet flow and
        determine if traffic can reach the destination.

        Args:
            snapshot_name: Snapshot name
            src_ip: Source IP address
            dst_ip: Destination IP address
            network_name: Network name (default: "default")
            src_node: Optional source node hostname

        Returns:
            VerificationResult with flow traces

        Raises:
            BatfishException: If query fails
        """
        query_id = f"q_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            self.bf_session.set_network(network_name)
            self.bf_session.set_snapshot(snapshot_name)

            # Build header constraints
            headers = HeaderConstraints(srcIps=src_ip, dstIps=dst_ip)

            logger.info(
                f"Executing reachability query",
                extra={
                    "query_id": query_id,
                    "snapshot": snapshot_name,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_node": src_node
                }
            )

            # Execute reachability query
            if src_node:
                answer = self.bf.q.reachability(
                    pathConstraints=PathConstraints(startLocation=src_node),
                    headers=headers
                ).answer()
            else:
                answer = self.bf.q.reachability(headers=headers).answer()

            # Parse results
            df = answer.frame()
            flow_traces = self._parse_flow_traces(df)

            execution_time_ms = int((time.time() - start_time) * 1000)

            result = VerificationResult(
                query_id=query_id,
                query_type="reachability",
                executed_at=datetime.utcnow(),
                parameters={
                    "snapshot": snapshot_name,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_node": src_node
                },
                status="SUCCESS",
                execution_time_ms=execution_time_ms,
                flow_traces=flow_traces
            )

            logger.info(
                f"Reachability query completed",
                extra={
                    "query_id": query_id,
                    "execution_time_ms": execution_time_ms,
                    "flow_count": len(flow_traces)
                }
            )

            return result

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Reachability query failed: {str(e)}", extra={"query_id": query_id})

            return VerificationResult(
                query_id=query_id,
                query_type="reachability",
                executed_at=datetime.utcnow(),
                parameters={
                    "snapshot": snapshot_name,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_node": src_node
                },
                status="FAILED",
                execution_time_ms=execution_time_ms,
                error_message=str(e)
            )

    def verify_acl(
        self,
        snapshot_name: str,
        filter_name: str,
        src_ip: str,
        dst_ip: str,
        network_name: str = "default",
        protocol: Optional[str] = None
    ) -> VerificationResult:
        """
        Verify ACL/filter behavior for given traffic.

        Uses Batfish searchFilters() question to determine which ACL lines
        match the specified traffic and what action is taken.

        Args:
            snapshot_name: Snapshot name
            filter_name: ACL/filter name pattern
            src_ip: Source IP address
            dst_ip: Destination IP address
            network_name: Network name (default: "default")
            protocol: Optional protocol (TCP, UDP, ICMP)

        Returns:
            VerificationResult with ACL match results

        Raises:
            BatfishException: If query fails
        """
        query_id = f"q_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            self.bf_session.set_network(network_name)
            self.bf_session.set_snapshot(snapshot_name)

            # Build header constraints
            headers = HeaderConstraints(srcIps=src_ip, dstIps=dst_ip)
            if protocol:
                headers = HeaderConstraints(
                    srcIps=src_ip,
                    dstIps=dst_ip,
                    ipProtocols=[protocol]
                )

            logger.info(
                f"Executing ACL verification query",
                extra={
                    "query_id": query_id,
                    "snapshot": snapshot_name,
                    "filter_name": filter_name,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "protocol": protocol
                }
            )

            # Execute searchFilters query
            answer = self.bf.q.searchFilters(
                filters=filter_name,
                headers=headers
            ).answer()

            # Parse results
            df = answer.frame()
            acl_results = self._parse_acl_results(df)

            execution_time_ms = int((time.time() - start_time) * 1000)

            result = VerificationResult(
                query_id=query_id,
                query_type="acl",
                executed_at=datetime.utcnow(),
                parameters={
                    "snapshot": snapshot_name,
                    "filter_name": filter_name,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "protocol": protocol
                },
                status="SUCCESS",
                execution_time_ms=execution_time_ms,
                acl_results=acl_results
            )

            logger.info(
                f"ACL verification query completed",
                extra={
                    "query_id": query_id,
                    "execution_time_ms": execution_time_ms,
                    "result_count": len(acl_results)
                }
            )

            return result

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"ACL verification query failed: {str(e)}", extra={"query_id": query_id})

            return VerificationResult(
                query_id=query_id,
                query_type="acl",
                executed_at=datetime.utcnow(),
                parameters={
                    "snapshot": snapshot_name,
                    "filter_name": filter_name,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "protocol": protocol
                },
                status="FAILED",
                execution_time_ms=execution_time_ms,
                error_message=str(e)
            )

    def verify_routing(
        self,
        snapshot_name: str,
        network_name: str = "default",
        nodes: Optional[List[str]] = None,
        network_filter: Optional[str] = None
    ) -> VerificationResult:
        """
        Verify routing table entries.

        Uses Batfish routes() question to retrieve routing table information.

        Args:
            snapshot_name: Snapshot name
            network_name: Network name (default: "default")
            nodes: Optional list of node hostnames to filter
            network_filter: Optional network prefix filter (e.g., "10.0.0.0/8")

        Returns:
            VerificationResult with route entries

        Raises:
            BatfishException: If query fails
        """
        query_id = f"q_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            self.bf_session.set_network(network_name)
            self.bf_session.set_snapshot(snapshot_name)

            logger.info(
                f"Executing routing verification query",
                extra={
                    "query_id": query_id,
                    "snapshot": snapshot_name,
                    "nodes": nodes,
                    "network_filter": network_filter
                }
            )

            # Execute routes query
            if nodes and network_filter:
                answer = self.bf.q.routes(nodes=",".join(nodes), network=network_filter).answer()
            elif nodes:
                answer = self.bf.q.routes(nodes=",".join(nodes)).answer()
            elif network_filter:
                answer = self.bf.q.routes(network=network_filter).answer()
            else:
                answer = self.bf.q.routes().answer()

            # Parse results
            df = answer.frame()
            route_entries = self._parse_route_entries(df)

            execution_time_ms = int((time.time() - start_time) * 1000)

            result = VerificationResult(
                query_id=query_id,
                query_type="routing",
                executed_at=datetime.utcnow(),
                parameters={
                    "snapshot": snapshot_name,
                    "nodes": nodes,
                    "network_filter": network_filter
                },
                status="SUCCESS",
                execution_time_ms=execution_time_ms,
                route_entries=route_entries
            )

            logger.info(
                f"Routing verification query completed",
                extra={
                    "query_id": query_id,
                    "execution_time_ms": execution_time_ms,
                    "route_count": len(route_entries)
                }
            )

            return result

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Routing verification query failed: {str(e)}", extra={"query_id": query_id})

            return VerificationResult(
                query_id=query_id,
                query_type="routing",
                executed_at=datetime.utcnow(),
                parameters={
                    "snapshot": snapshot_name,
                    "nodes": nodes,
                    "network_filter": network_filter
                },
                status="FAILED",
                execution_time_ms=execution_time_ms,
                error_message=str(e)
            )

    # Helper methods for parsing Batfish results

    def _parse_flow_traces(self, df) -> List[FlowTrace]:
        """Parse flow traces from reachability query results."""
        flow_traces = []

        if df.empty:
            return flow_traces

        for _, row in df.iterrows():
            # Extract trace information
            trace = row.get('Trace', None)
            disposition = row.get('Outcome', 'UNKNOWN')

            hops = []
            if trace and hasattr(trace, 'hops'):
                for hop in trace.hops:
                    flow_hop = FlowTraceHop(
                        node=getattr(hop, 'node', 'unknown'),
                        action=getattr(hop, 'action', 'UNKNOWN'),
                        interface_in=getattr(hop, 'interface_in', None),
                        interface_out=getattr(hop, 'interface_out', None)
                    )
                    hops.append(flow_hop)

            flow_trace = FlowTrace(
                disposition=str(disposition),
                hops=hops
            )
            flow_traces.append(flow_trace)

        return flow_traces

    def _parse_acl_results(self, df) -> List[ACLMatchResult]:
        """Parse ACL match results from searchFilters query."""
        acl_results = []

        if df.empty:
            return acl_results

        for _, row in df.iterrows():
            acl_result = ACLMatchResult(
                node=row.get('Node', 'unknown'),
                filter_name=row.get('Filter', 'unknown'),
                action=row.get('Action', 'UNKNOWN'),
                line_number=row.get('Line_Index', None),
                line_content=row.get('Line_Content', None)
            )
            acl_results.append(acl_result)

        return acl_results

    def _parse_route_entries(self, df) -> List[RouteEntry]:
        """Parse route entries from routes query."""
        route_entries = []

        if df.empty:
            return route_entries

        for _, row in df.iterrows():
            route_entry = RouteEntry(
                node=row.get('Node', 'unknown'),
                network=row.get('Network', 'unknown'),
                next_hop=row.get('Next_Hop_IP', None),
                protocol=row.get('Protocol', 'UNKNOWN'),
                admin_distance=row.get('Admin_Distance', None),
                metric=row.get('Metric', None),
                interface=row.get('Next_Hop_Interface', None)
            )
            route_entries.append(route_entry)

        return route_entries
