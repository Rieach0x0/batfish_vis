/**
 * Snapshot service for Batfish snapshot management.
 *
 * Provides client-side API for creating, listing, retrieving, and deleting snapshots.
 */

import apiClient from './apiClient.js';

/**
 * Snapshot service object with CRUD operations.
 */
const snapshotService = {
  /**
   * Create a new Batfish snapshot from configuration files.
   *
   * @param {string} snapshotName - Unique snapshot name
   * @param {string} networkName - Network name (default: "default")
   * @param {FileList|File[]} configFiles - Configuration files to upload
   * @param {Function} onProgress - Optional progress callback (receives percentage)
   * @returns {Promise<Object>} Created snapshot object
   * @throws {ApiError} On upload failure or validation error
   */
  async createSnapshot(snapshotName, networkName = 'default', configFiles, onProgress = null) {
    if (!snapshotName || snapshotName.trim() === '') {
      throw new Error('Snapshot name is required');
    }

    console.log('[DEBUG] createSnapshot called with:', {
      snapshotName,
      networkName,
      configFiles: configFiles,
      fileCount: configFiles ? configFiles.length : 0,
      fileType: configFiles ? typeof configFiles : 'undefined'
    });

    if (!configFiles || configFiles.length === 0) {
      console.error('[ERROR] No config files provided');
      throw new Error('At least one configuration file is required');
    }

    // Create FormData for multipart upload
    const formData = new FormData();
    formData.append('snapshotName', snapshotName);
    formData.append('networkName', networkName);

    // Add all configuration files
    for (let i = 0; i < configFiles.length; i++) {
      const file = configFiles[i];
      console.log(`[DEBUG] Adding file ${i + 1}:`, {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified
      });
      formData.append('configFiles', file);
    }

    // Log FormData contents
    console.log('[DEBUG] FormData entries:');
    for (let pair of formData.entries()) {
      if (pair[1] instanceof File) {
        console.log(`  ${pair[0]}: File(${pair[1].name}, ${pair[1].size} bytes)`);
      } else {
        console.log(`  ${pair[0]}: ${pair[1]}`);
      }
    }

    console.log(`Creating snapshot: ${snapshotName} with ${configFiles.length} files`);

    try {
      // Use postForm for multipart/form-data
      const snapshot = await apiClient.postForm('/snapshots', formData);

      console.log('Snapshot created successfully', snapshot);
      return snapshot;

    } catch (error) {
      console.error('Snapshot creation failed', error);
      throw error;
    }
  },

  /**
   * List all Batfish snapshots.
   *
   * @param {string|null} network - Optional network name filter
   * @returns {Promise<Array>} Array of snapshot objects
   * @throws {ApiError} On API failure
   */
  async listSnapshots(network = null) {
    try {
      const params = network ? { network } : null;
      const response = await apiClient.get('/snapshots', params);

      console.log(`Listed ${response.snapshots.length} snapshots`);
      return response.snapshots;

    } catch (error) {
      console.error('Failed to list snapshots', error);
      throw error;
    }
  },

  /**
   * Get detailed information about a specific snapshot.
   *
   * @param {string} snapshotName - Snapshot name
   * @param {string} network - Network name (default: "default")
   * @returns {Promise<Object>} Snapshot object with full metadata
   * @throws {ApiError} On API failure (404 if not found)
   */
  async getSnapshot(snapshotName, network = 'default') {
    if (!snapshotName) {
      throw new Error('Snapshot name is required');
    }

    try {
      const snapshot = await apiClient.get(`/snapshots/${snapshotName}`, { network });

      console.log(`Retrieved snapshot: ${snapshotName}`, snapshot);
      return snapshot;

    } catch (error) {
      console.error(`Failed to get snapshot: ${snapshotName}`, error);
      throw error;
    }
  },

  /**
   * Delete a Batfish snapshot.
   *
   * @param {string} snapshotName - Snapshot name
   * @param {string} network - Network name (default: "default")
   * @returns {Promise<void>}
   * @throws {ApiError} On API failure (404 if not found)
   */
  async deleteSnapshot(snapshotName, network = 'default') {
    if (!snapshotName) {
      throw new Error('Snapshot name is required');
    }

    try {
      await apiClient.delete(`/snapshots/${snapshotName}?network=${network}`);

      console.log(`Deleted snapshot: ${snapshotName}`);

    } catch (error) {
      console.error(`Failed to delete snapshot: ${snapshotName}`, error);
      throw error;
    }
  },
};

export default snapshotService;
