/**
 * Verification service for configuration validation API calls.
 *
 * Provides methods for executing Batfish verification queries including
 * reachability analysis, ACL testing, and routing validation.
 */

import apiClient from './apiClient.js';

const verificationService = {
  /**
   * Verify network reachability between source and destination IPs.
   *
   * @param {string} snapshot - Snapshot name
   * @param {string} srcIp - Source IP address
   * @param {string} dstIp - Destination IP address
   * @param {string} network - Network name (default: "default")
   * @param {string|null} srcNode - Optional source node hostname
   * @returns {Promise<Object>} Verification result with flow traces
   */
  async verifyReachability(snapshot, srcIp, dstIp, network = 'default', srcNode = null) {
    const body = {
      snapshot,
      network,
      src_ip: srcIp,
      dst_ip: dstIp
    };

    if (srcNode) {
      body.src_node = srcNode;
    }

    return await apiClient.post('/verification/reachability', body);
  },

  /**
   * Verify ACL/filter behavior for specified traffic.
   *
   * @param {string} snapshot - Snapshot name
   * @param {string} filterName - ACL/filter name or pattern
   * @param {string} srcIp - Source IP address
   * @param {string} dstIp - Destination IP address
   * @param {string} network - Network name (default: "default")
   * @param {string|null} protocol - Optional protocol (TCP, UDP, ICMP)
   * @returns {Promise<Object>} Verification result with ACL match results
   */
  async verifyACL(snapshot, filterName, srcIp, dstIp, network = 'default', protocol = null) {
    const body = {
      snapshot,
      network,
      filter_name: filterName,
      src_ip: srcIp,
      dst_ip: dstIp
    };

    if (protocol) {
      body.protocol = protocol.toUpperCase();
    }

    return await apiClient.post('/verification/acl', body);
  },

  /**
   * Verify routing table entries.
   *
   * @param {string} snapshot - Snapshot name
   * @param {string} network - Network name (default: "default")
   * @param {Array<string>|null} nodes - Optional list of node hostnames
   * @param {string|null} networkFilter - Optional network prefix filter (e.g., "10.0.0.0/8")
   * @returns {Promise<Object>} Verification result with route entries
   */
  async verifyRouting(snapshot, network = 'default', nodes = null, networkFilter = null) {
    const body = {
      snapshot,
      network
    };

    if (nodes && nodes.length > 0) {
      body.nodes = nodes;
    }

    if (networkFilter) {
      body.network_filter = networkFilter;
    }

    return await apiClient.post('/verification/routing', body);
  }
};

export default verificationService;
