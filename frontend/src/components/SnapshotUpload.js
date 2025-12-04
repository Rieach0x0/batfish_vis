/**
 * SnapshotUpload component.
 *
 * UI component for uploading network configuration files and creating Batfish snapshots.
 */

import snapshotService from '../services/snapshotService.js';

/**
 * Create and render SnapshotUpload component.
 *
 * @param {HTMLElement} container - Container element to render into
 * @param {Function} onSnapshotCreated - Callback when snapshot is created successfully
 * @returns {Object} Component instance with destroy() method
 */
export function createSnapshotUpload(container, onSnapshotCreated = null) {
  let selectedFiles = [];
  let isUploading = false;

  // Render component HTML
  function render() {
    container.innerHTML = `
      <div class="snapshot-upload">
        <h2>Create Batfish Snapshot</h2>

        <form id="snapshot-form" class="upload-form">
          <div class="form-group">
            <label for="snapshot-name">Snapshot Name *</label>
            <input
              type="text"
              id="snapshot-name"
              name="snapshotName"
              required
              pattern="[a-zA-Z0-9_\-]+"
              placeholder="snapshot-2025-11-21"
              title="Alphanumeric characters, hyphens, and underscores only"
            />
            <small>1-100 characters, alphanumeric + hyphen/underscore</small>
          </div>

          <div class="form-group">
            <label for="network-name">Network Name</label>
            <input
              type="text"
              id="network-name"
              name="networkName"
              value="default"
              placeholder="default"
            />
          </div>

          <div class="form-group">
            <label>Configuration Files/Folder *</label>

            <div class="file-input-options">
              <div class="radio-group">
                <label class="radio-label">
                  <input type="radio" name="upload-mode" value="files" checked />
                  <span>Select Files</span>
                </label>
                <label class="radio-label">
                  <input type="radio" name="upload-mode" value="folder" />
                  <span>Select Folder</span>
                </label>
              </div>
            </div>

            <input
              type="file"
              id="config-files"
              name="configFiles"
              multiple
              accept=".cfg,.conf,.txt,.ios,.junos,.eos"
              required
            />
            <input
              type="file"
              id="config-folder"
              name="configFolder"
              webkitdirectory
              directory
              multiple
              style="display: none;"
            />

            <small id="file-count">No files selected</small>
            <small class="help-text">
              Files: Select multiple config files |
              Folder: Select a directory containing config files
            </small>
          </div>

          <div id="parse-errors" class="parse-errors" style="display: none;">
            <h3>Parse Errors</h3>
            <ul id="error-list"></ul>
          </div>

          <div id="progress-container" class="progress-container" style="display: none;">
            <div class="progress-bar">
              <div id="progress-fill" class="progress-fill" style="width: 0%"></div>
            </div>
            <p id="progress-text">Uploading...</p>
          </div>

          <div class="form-actions">
            <button type="submit" id="create-btn" class="btn btn-primary">
              Create Snapshot
            </button>
            <button type="button" id="cancel-btn" class="btn btn-secondary" style="display: none;">
              Cancel
            </button>
          </div>
        </form>

        <div id="status-message" class="status-message"></div>
      </div>
    `;

    attachEventListeners();
  }

  // Attach event listeners
  function attachEventListeners() {
    const form = container.querySelector('#snapshot-form');
    const fileInput = container.querySelector('#config-files');
    const folderInput = container.querySelector('#config-folder');
    const uploadModeRadios = container.querySelectorAll('input[name="upload-mode"]');

    // Upload mode switching
    uploadModeRadios.forEach(radio => {
      radio.addEventListener('change', handleUploadModeChange);
    });

    // File selection
    fileInput.addEventListener('change', handleFileSelection);
    folderInput.addEventListener('change', handleFileSelection);

    // Form submission
    form.addEventListener('submit', handleSubmit);
  }

  // Handle upload mode change (files vs folder)
  function handleUploadModeChange(event) {
    const mode = event.target.value;
    const fileInput = container.querySelector('#config-files');
    const folderInput = container.querySelector('#config-folder');

    if (mode === 'folder') {
      fileInput.style.display = 'none';
      folderInput.style.display = 'block';
      fileInput.removeAttribute('required');
      folderInput.setAttribute('required', 'required');
    } else {
      fileInput.style.display = 'block';
      folderInput.style.display = 'none';
      fileInput.setAttribute('required', 'required');
      folderInput.removeAttribute('required');
    }

    // Reset selection
    selectedFiles = [];
    container.querySelector('#file-count').textContent = 'No files selected';
  }

  // Handle file selection
  function handleFileSelection(event) {
    console.log('[DEBUG] handleFileSelection called');
    console.log('[DEBUG] event.target.id:', event.target.id);
    console.log('[DEBUG] event.target.files:', event.target.files);
    console.log('[DEBUG] event.target.files.length:', event.target.files ? event.target.files.length : 'null');

    selectedFiles = Array.from(event.target.files);
    console.log('[DEBUG] selectedFiles after Array.from:', selectedFiles);
    console.log('[DEBUG] selectedFiles.length:', selectedFiles.length);

    const fileCount = container.querySelector('#file-count');

    if (selectedFiles.length === 0) {
      fileCount.textContent = 'No files selected';
      fileCount.style.color = '#666';
    } else {
      // Count by file type
      const configFiles = selectedFiles.filter(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        return ['cfg', 'conf', 'txt', 'ios', 'junos', 'eos'].includes(ext);
      });

      // Display selection info
      if (event.target.id === 'config-folder') {
        // Folder mode: show folder name and file count
        const folderName = selectedFiles[0]?.webkitRelativePath?.split('/')[0] || 'selected folder';
        fileCount.innerHTML = `
          <strong>${folderName}</strong>: ${selectedFiles.length} file(s) total,
          ${configFiles.length} config file(s)
        `;
      } else {
        // File mode: show file count
        fileCount.textContent = `${selectedFiles.length} file(s) selected`;
      }

      fileCount.style.color = '#2563eb';

      // Warn if no valid config files
      if (configFiles.length === 0) {
        fileCount.textContent += ' (Warning: No recognized config files)';
        fileCount.style.color = '#f59e0b';
      }
    }
  }

  // Handle form submission
  async function handleSubmit(event) {
    event.preventDefault();

    if (isUploading) return;

    const snapshotName = container.querySelector('#snapshot-name').value.trim();
    const networkName = container.querySelector('#network-name').value.trim() || 'default';

    // Validate inputs
    if (!snapshotName) {
      showError('Snapshot name is required');
      return;
    }

    if (selectedFiles.length === 0) {
      showError('Please select at least one configuration file');
      return;
    }

    // Debug: Log submission details
    console.log('[DEBUG] Form submission starting');
    console.log('[DEBUG] snapshotName:', snapshotName);
    console.log('[DEBUG] networkName:', networkName);
    console.log('[DEBUG] selectedFiles count:', selectedFiles.length);
    console.log('[DEBUG] selectedFiles:', selectedFiles);

    // Start upload
    isUploading = true;
    showProgress(true);
    hideErrors();
    showStatus('Creating snapshot...', 'info');

    try {
      console.log('[DEBUG] Calling snapshotService.createSnapshot...');
      const snapshot = await snapshotService.createSnapshot(
        snapshotName,
        networkName,
        selectedFiles
      );
      console.log('[DEBUG] snapshotService.createSnapshot returned:', snapshot);

      // Success
      showProgress(false);
      showStatus(
        `Snapshot "${snapshot.name}" created successfully! Detected ${snapshot.device_count} devices.`,
        'success'
      );

      // Display parse errors if any
      if (snapshot.parse_errors && snapshot.parse_errors.length > 0) {
        displayParseErrors(snapshot.parse_errors);
      }

      // Reset form
      container.querySelector('#snapshot-form').reset();
      selectedFiles = [];
      container.querySelector('#file-count').textContent = 'No files selected';

      // Callback
      if (onSnapshotCreated) {
        onSnapshotCreated(snapshot);
      }

    } catch (error) {
      showProgress(false);

      console.error('[ERROR] Snapshot creation failed:', error);

      let errorMessage = 'Failed to create snapshot';
      if (error.message) {
        errorMessage = error.message;
      }
      if (error.status === 409) {
        errorMessage = 'Snapshot with this name already exists';
      } else if (error.status === 503) {
        errorMessage = 'Batfish container is not available. Please check connection.';
      } else if (error.status === 422) {
        errorMessage = 'Invalid request. Please check the error details in browser console.';
        // Log detailed validation errors
        console.error('[VALIDATION ERROR] Full error object:', JSON.stringify(error, null, 2));
        if (error.details) {
          console.error('[VALIDATION ERROR] Details:', JSON.stringify(error.details, null, 2));
          console.error('[VALIDATION ERROR] Please check:');
          console.error('  1. All files are valid network configuration files');
          console.error('  2. Snapshot name contains only alphanumeric, hyphen, underscore');
          console.error('  3. Files are not corrupted or empty');
        }
      }

      showStatus(errorMessage, 'error');

    } finally {
      isUploading = false;
    }
  }

  // Show/hide progress indicator
  function showProgress(show) {
    const progressContainer = container.querySelector('#progress-container');
    const createBtn = container.querySelector('#create-btn');
    const cancelBtn = container.querySelector('#cancel-btn');

    if (show) {
      progressContainer.style.display = 'block';
      createBtn.disabled = true;
      cancelBtn.style.display = 'inline-block';
    } else {
      progressContainer.style.display = 'none';
      createBtn.disabled = false;
      cancelBtn.style.display = 'none';
    }
  }

  // Display parse errors
  function displayParseErrors(parseErrors) {
    const errorContainer = container.querySelector('#parse-errors');
    const errorList = container.querySelector('#error-list');

    errorList.innerHTML = '';
    parseErrors.forEach(error => {
      const li = document.createElement('li');
      li.textContent = `${error.file_name}: ${error.error_message}`;
      errorList.appendChild(li);
    });

    errorContainer.style.display = 'block';
  }

  // Hide parse errors
  function hideErrors() {
    const errorContainer = container.querySelector('#parse-errors');
    errorContainer.style.display = 'none';
  }

  // Show status message
  function showStatus(message, type = 'info') {
    const statusMessage = container.querySelector('#status-message');
    statusMessage.textContent = message;
    statusMessage.className = `status-message status-${type}`;
    statusMessage.style.display = 'block';

    // Auto-hide after 5 seconds
    setTimeout(() => {
      statusMessage.style.display = 'none';
    }, 5000);
  }

  // Show error message
  function showError(message) {
    showStatus(message, 'error');
  }

  // Initial render
  render();

  // Return component instance
  return {
    destroy() {
      container.innerHTML = '';
    }
  };
}

export default createSnapshotUpload;
