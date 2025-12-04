/**
 * SnapshotManager component.
 *
 * UI component for listing, selecting, and deleting Batfish snapshots.
 */

import snapshotService from '../services/snapshotService.js';

/**
 * Create and render SnapshotManager component.
 *
 * @param {HTMLElement} container - Container element to render into
 * @param {Function} onSnapshotSelected - Callback when snapshot is selected
 * @returns {Object} Component instance with refresh() and destroy() methods
 */
export function createSnapshotManager(container, onSnapshotSelected = null) {
  let snapshots = [];
  let activeSnapshot = null;
  let isLoading = false;

  // Render component HTML
  function render() {
    container.innerHTML = `
      <div class="snapshot-manager">
        <div class="manager-header">
          <h2>Snapshots</h2>
          <button id="refresh-btn" class="btn btn-sm btn-secondary">
            Refresh
          </button>
        </div>

        <div id="loading-indicator" class="loading" style="display: none;">
          Loading snapshots...
        </div>

        <div id="error-message" class="error-message" style="display: none;"></div>

        <div id="snapshot-list" class="snapshot-list">
          <!-- Snapshot items will be rendered here -->
        </div>

        <div id="empty-state" class="empty-state" style="display: none;">
          <p>No snapshots available</p>
          <small>Create a snapshot to get started</small>
        </div>
      </div>
    `;

    attachEventListeners();
    loadSnapshots();
  }

  // Attach event listeners
  function attachEventListeners() {
    const refreshBtn = container.querySelector('#refresh-btn');
    refreshBtn.addEventListener('click', () => loadSnapshots());
  }

  // Load snapshots from API
  async function loadSnapshots() {
    if (isLoading) return;

    isLoading = true;
    showLoading(true);
    hideError();

    try {
      snapshots = await snapshotService.listSnapshots();

      renderSnapshotList();
      showLoading(false);

      if (snapshots.length === 0) {
        showEmptyState(true);
      } else {
        showEmptyState(false);
      }

    } catch (error) {
      console.error('Failed to load snapshots', error);
      showLoading(false);
      showError('Failed to load snapshots. Please check Batfish connection.');

    } finally {
      isLoading = false;
    }
  }

  // Render snapshot list
  function renderSnapshotList() {
    const listContainer = container.querySelector('#snapshot-list');
    listContainer.innerHTML = '';

    snapshots.forEach(snapshot => {
      const item = createSnapshotItem(snapshot);
      listContainer.appendChild(item);
    });
  }

  // Create snapshot list item element
  function createSnapshotItem(snapshot) {
    const item = document.createElement('div');
    item.className = 'snapshot-item';
    if (activeSnapshot && activeSnapshot.name === snapshot.name) {
      item.classList.add('active');
    }

    // Format date
    const createdDate = new Date(snapshot.created_at).toLocaleString();

    // Status badge
    const statusClass = snapshot.status === 'COMPLETE' ? 'status-success' : 'status-warning';

    item.innerHTML = `
      <div class="snapshot-info">
        <div class="snapshot-name">${snapshot.name}</div>
        <div class="snapshot-meta">
          <span class="badge ${statusClass}">${snapshot.status}</span>
          <span class="meta-item">📊 ${snapshot.device_count} devices</span>
          <span class="meta-item">📁 ${snapshot.config_file_count} files</span>
          <span class="meta-item">🕒 ${createdDate}</span>
        </div>
        ${snapshot.parse_errors && snapshot.parse_errors.length > 0 ? `
          <div class="parse-error-badge">
            ⚠️ ${snapshot.parse_errors.length} parse error(s)
          </div>
        ` : ''}
      </div>
      <div class="snapshot-actions">
        <button class="btn btn-sm btn-primary select-btn" data-snapshot="${snapshot.name}" data-network="${snapshot.network}">
          Select
        </button>
        <button class="btn btn-sm btn-danger delete-btn" data-snapshot="${snapshot.name}" data-network="${snapshot.network}">
          Delete
        </button>
      </div>
    `;

    // Attach item event listeners
    const selectBtn = item.querySelector('.select-btn');
    const deleteBtn = item.querySelector('.delete-btn');

    selectBtn.addEventListener('click', () => handleSnapshotSelect(snapshot));
    deleteBtn.addEventListener('click', () => handleSnapshotDelete(snapshot));

    return item;
  }

  // Handle snapshot selection
  function handleSnapshotSelect(snapshot) {
    activeSnapshot = snapshot;
    renderSnapshotList();

    if (onSnapshotSelected) {
      onSnapshotSelected(snapshot);
    }

    showSuccess(`Snapshot "${snapshot.name}" selected`);
  }

  // Handle snapshot deletion
  async function handleSnapshotDelete(snapshot) {
    const confirmed = confirm(
      `Are you sure you want to delete snapshot "${snapshot.name}"?\n\n` +
      `This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
      await snapshotService.deleteSnapshot(snapshot.name, snapshot.network);

      showSuccess(`Snapshot "${snapshot.name}" deleted successfully`);

      // Clear active if deleted
      if (activeSnapshot && activeSnapshot.name === snapshot.name) {
        activeSnapshot = null;
        if (onSnapshotSelected) {
          onSnapshotSelected(null);
        }
      }

      // Reload list
      await loadSnapshots();

    } catch (error) {
      console.error('Failed to delete snapshot', error);

      let errorMessage = 'Failed to delete snapshot';
      if (error.status === 404) {
        errorMessage = 'Snapshot not found';
      }

      showError(errorMessage);
    }
  }

  // Show/hide loading indicator
  function showLoading(show) {
    const loadingIndicator = container.querySelector('#loading-indicator');
    loadingIndicator.style.display = show ? 'block' : 'none';
  }

  // Show/hide empty state
  function showEmptyState(show) {
    const emptyState = container.querySelector('#empty-state');
    const snapshotList = container.querySelector('#snapshot-list');

    emptyState.style.display = show ? 'block' : 'none';
    snapshotList.style.display = show ? 'none' : 'block';
  }

  // Show error message
  function showError(message) {
    const errorMessage = container.querySelector('#error-message');
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';

    setTimeout(() => {
      errorMessage.style.display = 'none';
    }, 5000);
  }

  // Hide error message
  function hideError() {
    const errorMessage = container.querySelector('#error-message');
    errorMessage.style.display = 'none';
  }

  // Show success message
  function showSuccess(message) {
    // Reuse error message element for success
    const errorMessage = container.querySelector('#error-message');
    errorMessage.textContent = message;
    errorMessage.className = 'success-message';
    errorMessage.style.display = 'block';

    setTimeout(() => {
      errorMessage.style.display = 'none';
      errorMessage.className = 'error-message';
    }, 3000);
  }

  // Initial render
  render();

  // Return component instance
  return {
    refresh() {
      return loadSnapshots();
    },

    getActiveSnapshot() {
      return activeSnapshot;
    },

    destroy() {
      container.innerHTML = '';
    }
  };
}

export default createSnapshotManager;
