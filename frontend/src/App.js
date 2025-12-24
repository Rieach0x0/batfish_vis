/**
 * Main application component.
 *
 * Integrates SnapshotUpload and SnapshotManager components.
 */

import { createSnapshotUpload } from './components/SnapshotUpload.js';
import { createSnapshotManager } from './components/SnapshotManager.js';
import { createTopologyVisualization } from './components/TopologyVisualization.js';
import { createVerificationPanel } from './components/VerificationPanel.js';
import { NodeDetailPanel } from './components/NodeDetailPanel.js';
import apiClient from './services/apiClient.js';

/**
 * Initialize and render the application.
 */
export function initApp() {
  const appContainer = document.getElementById('app');

  // Render app layout
  appContainer.innerHTML = `
    <div class="app">
      <header class="app-header">
        <h1>🔍 Batfish Visualization & Verification</h1>
        <div id="health-status" class="health-status">
          <span class="status-indicator"></span>
          <span class="status-text">Checking connection...</span>
        </div>
      </header>

      <main class="app-main">
        <aside class="app-sidebar">
          <div id="snapshot-manager-container"></div>
        </aside>

        <section class="app-content">
          <div id="snapshot-upload-container"></div>

          <div id="active-snapshot-info" class="active-snapshot" style="display: none;">
            <h3>Active Snapshot</h3>
            <div id="snapshot-details"></div>
          </div>

          <div id="topology-container" class="topology-container" style="display: none;">
            <div class="topology-header">
              <h2>📊 Network Topology</h2>
              <div class="topology-actions">
                <button id="export-svg-btn" class="btn btn-sm btn-secondary">Export SVG</button>
                <button id="export-png-btn" class="btn btn-sm btn-secondary">Export PNG</button>
                <button id="refresh-topology-btn" class="btn btn-sm btn-primary">Refresh</button>
              </div>
            </div>
            <div id="topology-canvas" class="topology-canvas"></div>
          </div>

          <div id="verification-container" style="display: none;"></div>
        </section>
      </main>

      <footer class="app-footer">
        <p>Batfish v2025.07.07 | API v1.0.0 | Constitutional Compliance: ✓</p>
      </footer>

      <!-- Node Detail Panel Container -->
      <div id="detail-panel-container"></div>
    </div>
  `;

  // Initialize components
  const snapshotManagerContainer = document.getElementById('snapshot-manager-container');
  const snapshotUploadContainer = document.getElementById('snapshot-upload-container');
  const topologyCanvas = document.getElementById('topology-canvas');
  const verificationContainer = document.getElementById('verification-container');
  const detailPanelContainer = document.getElementById('detail-panel-container');

  let snapshotManager = null;
  let topologyVisualization = null;
  let verificationPanel = null;
  let nodeDetailPanel = null;
  let activeSnapshot = null;

  // Create NodeDetailPanel (Feature 003)
  nodeDetailPanel = new NodeDetailPanel(detailPanelContainer);

  // Create SnapshotManager
  snapshotManager = createSnapshotManager(
    snapshotManagerContainer,
    handleSnapshotSelected
  );

  // Create SnapshotUpload
  createSnapshotUpload(
    snapshotUploadContainer,
    handleSnapshotCreated
  );

  // Handle snapshot creation
  function handleSnapshotCreated(snapshot) {
    if (snapshotManager) {
      snapshotManager.refresh();
    }
  }

  // Handle snapshot selection
  function handleSnapshotSelected(snapshot) {
    const activeSnapshotInfo = document.getElementById('active-snapshot-info');
    const snapshotDetails = document.getElementById('snapshot-details');
    const topologyContainer = document.getElementById('topology-container');

    if (snapshot) {
      activeSnapshot = snapshot;

      snapshotDetails.innerHTML = `
        <div class="snapshot-detail-item">
          <strong>Name:</strong> ${snapshot.name}
        </div>
        <div class="snapshot-detail-item">
          <strong>Network:</strong> ${snapshot.network}
        </div>
        <div class="snapshot-detail-item">
          <strong>Status:</strong> <span class="badge status-success">${snapshot.status}</span>
        </div>
        <div class="snapshot-detail-item">
          <strong>Devices:</strong> ${snapshot.device_count}
        </div>
        <div class="snapshot-detail-item">
          <strong>Config Files:</strong> ${snapshot.config_file_count}
        </div>
        <div class="snapshot-detail-item">
          <strong>Created:</strong> ${new Date(snapshot.created_at).toLocaleString()}
        </div>
        <div class="snapshot-detail-item">
          <strong>Batfish Version:</strong> ${snapshot.batfish_version}
        </div>
      `;

      activeSnapshotInfo.style.display = 'block';

      // Load topology visualization
      loadTopologyVisualization(snapshot);
      topologyContainer.style.display = 'block';

      // Load verification panel
      loadVerificationPanel(snapshot);
      verificationContainer.style.display = 'block';

    } else {
      activeSnapshotInfo.style.display = 'none';
      topologyContainer.style.display = 'none';
      verificationContainer.style.display = 'none';
      activeSnapshot = null;

      // Destroy topology visualization if exists
      if (topologyVisualization) {
        topologyVisualization.destroy();
        topologyVisualization = null;
      }

      // Destroy verification panel if exists
      if (verificationPanel) {
        verificationPanel.destroy();
        verificationPanel = null;
      }
    }
  }

  // Load topology visualization for selected snapshot
  function loadTopologyVisualization(snapshot) {
    // Destroy existing visualization
    if (topologyVisualization) {
      topologyVisualization.destroy();
    }

    // Create new visualization (with NodeDetailPanel for Feature 003)
    topologyVisualization = createTopologyVisualization(
      topologyCanvas,
      snapshot.name,
      snapshot.network,
      nodeDetailPanel
    );

    // Setup export buttons
    document.getElementById('export-svg-btn').onclick = () => {
      if (topologyVisualization) {
        topologyVisualization.exportSVG();
      }
    };

    document.getElementById('export-png-btn').onclick = () => {
      if (topologyVisualization) {
        topologyVisualization.exportPNG();
      }
    };

    document.getElementById('refresh-topology-btn').onclick = () => {
      if (topologyVisualization) {
        topologyVisualization.refresh();
      }
    };
  }

  // Load verification panel for selected snapshot
  function loadVerificationPanel(snapshot) {
    // Destroy existing panel
    if (verificationPanel) {
      verificationPanel.destroy();
    }

    // Create new verification panel
    verificationPanel = createVerificationPanel(
      verificationContainer,
      snapshot.name,
      snapshot.network
    );
  }

  // Check API health
  checkHealth();

  async function checkHealth() {
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.querySelector('.status-text');

    try {
      const health = await apiClient.healthCheck();

      statusIndicator.className = 'status-indicator status-healthy';
      statusText.textContent = `Connected | Batfish ${health.batfish_version}`;

    } catch (error) {
      console.error('Health check failed', error);

      statusIndicator.className = 'status-indicator status-unhealthy';
      statusText.textContent = 'Disconnected - Check Batfish container';
    }
  }

  // Refresh health every 30 seconds
  setInterval(checkHealth, 30000);
}

export default initApp;
