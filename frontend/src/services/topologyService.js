/**
 * Topology service for network topology API calls.
 *
 * Provides methods for fetching topology data including nodes,
 * edges, and complete topology graphs.
 */

import apiClient from './apiClient.js';

const topologyService = {
  /**
   * Get all network devices (nodes) in a snapshot.
   *
   * @param {string} snapshotName - Snapshot name
   * @param {string} networkName - Network name (default: "default")
   * @returns {Promise<Array>} Array of device objects
   */
  async getNodes(snapshotName, networkName = 'default') {
    const params = new URLSearchParams({
      snapshot: snapshotName,
      network: networkName
    });

    return await apiClient.get(`/topology/nodes?${params.toString()}`);
  },

  /**
   * Get all Layer 3 edges (links) in a snapshot.
   *
   * @param {string} snapshotName - Snapshot name
   * @param {string} networkName - Network name (default: "default")
   * @returns {Promise<Array>} Array of edge objects
   */
  async getEdges(snapshotName, networkName = 'default') {
    const params = new URLSearchParams({
      snapshot: snapshotName,
      network: networkName
    });

    return await apiClient.get(`/topology/edges?${params.toString()}`);
  },

  /**
   * Get network interfaces from a snapshot.
   *
   * @param {string} snapshotName - Snapshot name
   * @param {string} networkName - Network name (default: "default")
   * @param {string|null} hostname - Optional device hostname filter
   * @returns {Promise<Array>} Array of interface objects
   */
  async getInterfaces(snapshotName, networkName = 'default', hostname = null) {
    const params = new URLSearchParams({
      snapshot: snapshotName,
      network: networkName
    });

    if (hostname) {
      params.append('hostname', hostname);
    }

    return await apiClient.get(`/topology/interfaces?${params.toString()}`);
  },

  /**
   * Get complete network topology including nodes and edges.
   *
   * @param {string} snapshotName - Snapshot name
   * @param {string} networkName - Network name (default: "default")
   * @returns {Promise<Object>} Topology object with nodes and edges arrays
   */
  async getTopology(snapshotName, networkName = 'default') {
    const params = new URLSearchParams({
      snapshot: snapshotName,
      network: networkName
    });

    return await apiClient.get(`/topology?${params.toString()}`);
  }
};

export default topologyService;
