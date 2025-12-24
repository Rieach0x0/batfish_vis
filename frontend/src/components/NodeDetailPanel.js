/**
 * NodeDetailPanel component
 *
 * Displays detailed information about a network node when clicked on the topology.
 * Shows hostname, device metadata, interfaces, and IP addresses.
 */

export class NodeDetailPanel {
  constructor(container, options = {}) {
    this.container = container;
    this.state = {
      isOpen: false,
      currentNode: null,
      nodeDetail: null,
      isLoading: false,
      error: null
    };

    // For canceling pending requests (US2 - T043)
    this.abortController = null;
    // For debouncing rapid clicks (US2 - T045)
    this.debounceTimer = null;
    this.pendingCallId = 0; // Track which call is active

    // US3 - T063: ESC key handler
    this.handleEscKey = this.handleEscKey.bind(this);

    // US3 - T064: Callback to notify when panel closes
    this.onClose = options.onClose || null;

    this.render();
  }

  /**
   * Render the panel HTML structure
   */
  render() {
    const panelHTML = `
      <div class="node-detail-panel" data-state="closed">
        <div class="panel-backdrop"></div>
        <div class="panel-container">
          <div class="panel-header">
            <h2 class="panel-title">Node Details</h2>
            <button class="panel-close-btn" aria-label="Close panel">&times;</button>
          </div>
          <div class="panel-loading" style="display: none;">
            <div class="loading-spinner"></div>
            <p>Loading node details...</p>
          </div>
          <div class="panel-error" style="display: none;">
            <p class="error-message"></p>
          </div>
          <div class="panel-content"></div>
        </div>
      </div>
    `;

    this.container.innerHTML = panelHTML;
    this.attachEventListeners();
  }

  /**
   * Attach event listeners for close button and backdrop
   */
  attachEventListeners() {
    const panel = this.container.querySelector('.node-detail-panel');
    const closeBtn = this.container.querySelector('.panel-close-btn');
    const backdrop = this.container.querySelector('.panel-backdrop');

    // Close button
    closeBtn.addEventListener('click', () => this.close());

    // Click outside to close
    backdrop.addEventListener('click', () => this.close());
  }

  /**
   * Open the panel and fetch node details
   * @param {string} hostname - Node hostname
   * @param {string} snapshot - Snapshot name
   * @param {string} network - Network name (optional, defaults to "default")
   */
  async open(hostname, snapshot, network = 'default') {
    // US2 - T045: Track this call to detect if it gets canceled
    const callId = ++this.pendingCallId;

    // US2 - T043: Cancel pending request if switching nodes
    if (this.abortController) {
      this.abortController.abort();
    }

    // US2 - T045: Debounce rapid clicks (100ms)
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }

    await new Promise(resolve => {
      this.debounceTimer = setTimeout(resolve, 100);
    });

    // Check if this call was superseded by a newer call
    if (callId !== this.pendingCallId) {
      return; // Silently exit - a newer call has taken over
    }

    // US2 - T042: Handle already-open state (switching nodes)
    const isAlreadyOpen = this.state.isOpen;

    this.state.isOpen = true;
    this.state.currentNode = hostname;
    this.state.isLoading = true;
    this.state.error = null;

    const panel = this.container.querySelector('.node-detail-panel');
    panel.dataset.state = 'open';

    this.showLoading();
    this.hideError();

    // US2 - T043: Create new AbortController for this request
    this.abortController = new AbortController();

    try {
      // Fetch node details from API with abort signal
      const response = await fetch(
        `/api/topology/nodes/${encodeURIComponent(hostname)}/details?snapshot=${encodeURIComponent(snapshot)}&network=${encodeURIComponent(network)}`,
        { signal: this.abortController.signal }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch node details: ${response.statusText}`);
      }

      const nodeDetail = await response.json();
      this.state.nodeDetail = nodeDetail;
      this.state.isLoading = false;

      this.hideLoading();
      this.renderContent(nodeDetail);

      // US3 - T063: Add ESC key listener when panel opens
      document.addEventListener('keydown', this.handleEscKey);
    } catch (error) {
      // Ignore abort errors (expected when switching nodes)
      if (error.name === 'AbortError') {
        return;
      }

      this.state.isLoading = false;
      this.state.error = error.message;

      this.hideLoading();
      this.showError(error.message);
    }
  }

  /**
   * Close the panel
   * US3 - T063: Remove ESC key listener when closing
   * US3 - T064: Call onClose callback to remove selected indicator
   */
  close() {
    this.state.isOpen = false;
    this.state.currentNode = null;
    this.state.nodeDetail = null;
    this.state.error = null;

    const panel = this.container.querySelector('.node-detail-panel');
    panel.dataset.state = 'closed';

    // US3 - T063: Remove ESC key listener
    document.removeEventListener('keydown', this.handleEscKey);

    // US3 - T064: Notify listeners that panel closed (to remove selected indicator)
    if (this.onClose) {
      this.onClose();
    }

    this.clearContent();
  }

  /**
   * Handle ESC key press (US3 - T063)
   * @param {KeyboardEvent} event - Keyboard event
   */
  handleEscKey(event) {
    if (event.key === 'Escape' && this.state.isOpen) {
      this.close();
    }
  }

  /**
   * Show loading state
   */
  showLoading() {
    const loading = this.container.querySelector('.panel-loading');
    loading.style.display = 'block';
  }

  /**
   * Hide loading state
   */
  hideLoading() {
    const loading = this.container.querySelector('.panel-loading');
    loading.style.display = 'none';
  }

  /**
   * Show error message
   * @param {string} message - Error message
   */
  showError(message) {
    const errorEl = this.container.querySelector('.panel-error');
    const errorMsg = this.container.querySelector('.error-message');
    errorMsg.textContent = message;
    errorEl.style.display = 'block';
  }

  /**
   * Hide error message
   */
  hideError() {
    const errorEl = this.container.querySelector('.panel-error');
    errorEl.style.display = 'none';
  }

  /**
   * Clear panel content
   */
  clearContent() {
    const content = this.container.querySelector('.panel-content');
    content.innerHTML = '';
  }

  /**
   * Render node detail content
   * @param {object} nodeDetail - Node detail data
   */
  renderContent(nodeDetail) {
    const content = this.container.querySelector('.panel-content');

    const contentHTML = `
      <div class="node-detail-section">
        <h3>Device Information</h3>
        <dl class="device-info">
          <dt>Hostname:</dt>
          <dd>${this.escapeHtml(nodeDetail.hostname)}</dd>

          <dt>Device Type:</dt>
          <dd>${nodeDetail.device_type || 'N/A'}</dd>

          <dt>Vendor:</dt>
          <dd>${nodeDetail.vendor || 'N/A'}</dd>

          <dt>Model:</dt>
          <dd>${nodeDetail.model || 'N/A'}</dd>

          <dt>OS Version:</dt>
          <dd>${nodeDetail.os_version || 'N/A'}</dd>

          <dt>Status:</dt>
          <dd class="status-${nodeDetail.status}">${nodeDetail.status}</dd>

          <dt>Interface Count:</dt>
          <dd>${nodeDetail.interface_count}</dd>
        </dl>
      </div>

      <div class="node-detail-section">
        <h3>Interfaces</h3>
        ${this.renderInterfaces(nodeDetail.interfaces)}
      </div>

      <div class="node-detail-section metadata">
        <h4>Snapshot Information</h4>
        <p><strong>Snapshot:</strong> ${this.escapeHtml(nodeDetail.metadata.snapshot_name)}</p>
        <p><strong>Last Updated:</strong> ${this.formatDateTime(nodeDetail.metadata.last_updated)}</p>
      </div>
    `;

    content.innerHTML = contentHTML;
  }

  /**
   * Render interfaces list
   * @param {array} interfaces - Array of interface objects
   * @returns {string} HTML string
   */
  renderInterfaces(interfaces) {
    if (!interfaces || interfaces.length === 0) {
      return '<p class="no-interfaces">No interfaces configured</p>';
    }

    const interfaceItems = interfaces.map(iface => {
      const ipAddresses = iface.ip_addresses && iface.ip_addresses.length > 0
        ? iface.ip_addresses.join(', ')
        : 'No IP assigned';

      const statusClass = iface.active ? 'active' : 'inactive';

      return `
        <div class="interface-item ${statusClass}">
          <div class="interface-header">
            <span class="interface-name">${this.escapeHtml(iface.name)}</span>
            <span class="interface-status ${statusClass}">${iface.active ? 'Active' : 'Inactive'}</span>
          </div>
          <div class="interface-details">
            <div class="interface-ips">
              <strong>IP:</strong> ${ipAddresses}
            </div>
            ${iface.description ? `<div class="interface-description"><strong>Description:</strong> ${this.escapeHtml(iface.description)}</div>` : ''}
            ${iface.vlan !== null && iface.vlan !== undefined ? `<div class="interface-vlan"><strong>VLAN:</strong> ${iface.vlan}</div>` : ''}
            ${iface.bandwidth_mbps !== null && iface.bandwidth_mbps !== undefined ? `<div class="interface-bandwidth"><strong>Bandwidth:</strong> ${iface.bandwidth_mbps} Mbps</div>` : ''}
            ${iface.mtu !== null && iface.mtu !== undefined ? `<div class="interface-mtu"><strong>MTU:</strong> ${iface.mtu}</div>` : ''}
          </div>
        </div>
      `;
    }).join('');

    return `<div class="interfaces-list">${interfaceItems}</div>`;
  }

  /**
   * Escape HTML to prevent XSS
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   */
  escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Format datetime string
   * @param {string} datetime - ISO datetime string
   * @returns {string} Formatted datetime
   */
  formatDateTime(datetime) {
    if (!datetime) return 'N/A';
    const date = new Date(datetime);
    return date.toLocaleString();
  }
}
