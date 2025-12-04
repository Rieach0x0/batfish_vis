/**
 * Verification Panel Component.
 *
 * Provides UI for executing Batfish verification queries:
 * - Reachability analysis
 * - ACL/filter testing
 * - Routing table inspection
 */

import verificationService from '../services/verificationService.js';

/**
 * Create verification panel component.
 *
 * @param {HTMLElement} container - Container element
 * @param {string} snapshotName - Active snapshot name
 * @param {string} networkName - Network name (default: "default")
 * @returns {Object} Component API
 */
export function createVerificationPanel(container, snapshotName, networkName = 'default') {
  let currentQueryType = 'reachability';
  let queryHistory = [];
  let isLoading = false;

  /**
   * Render the verification panel.
   */
  function render() {
    container.innerHTML = `
      <div class="verification-panel">
        <div class="verification-header">
          <h3>Configuration Verification</h3>
          <div class="query-type-selector">
            <button class="query-type-btn ${currentQueryType === 'reachability' ? 'active' : ''}" data-type="reachability">
              Reachability
            </button>
            <button class="query-type-btn ${currentQueryType === 'acl' ? 'active' : ''}" data-type="acl">
              ACL Test
            </button>
            <button class="query-type-btn ${currentQueryType === 'routing' ? 'active' : ''}" data-type="routing">
              Routing
            </button>
          </div>
        </div>

        <div class="verification-content">
          <div class="query-form-container">
            ${renderQueryForm()}
          </div>

          <div class="verification-results-container">
            ${renderResults()}
          </div>

          <div class="query-history-container">
            ${renderQueryHistory()}
          </div>
        </div>
      </div>
    `;

    attachEventListeners();
  }

  /**
   * Render query form based on selected query type.
   */
  function renderQueryForm() {
    switch (currentQueryType) {
      case 'reachability':
        return `
          <div class="query-form">
            <h4>Reachability Analysis</h4>
            <p class="form-description">Test if traffic can reach from source to destination IP</p>

            <div class="form-group">
              <label for="srcIp">Source IP Address *</label>
              <input type="text" id="srcIp" class="form-control" placeholder="192.168.1.10" required>
            </div>

            <div class="form-group">
              <label for="dstIp">Destination IP Address *</label>
              <input type="text" id="dstIp" class="form-control" placeholder="10.0.0.5" required>
            </div>

            <div class="form-group">
              <label for="srcNode">Source Node (Optional)</label>
              <input type="text" id="srcNode" class="form-control" placeholder="router1">
              <small>Leave empty to test from all nodes</small>
            </div>

            <button id="executeQuery" class="btn btn-primary" ${isLoading ? 'disabled' : ''}>
              ${isLoading ? 'Executing...' : 'Execute Query'}
            </button>
          </div>
        `;

      case 'acl':
        return `
          <div class="query-form">
            <h4>ACL Filter Test</h4>
            <p class="form-description">Test traffic against ACL/filter rules</p>

            <div class="form-group">
              <label for="filterName">Filter/ACL Name *</label>
              <input type="text" id="filterName" class="form-control" placeholder="ACL_WAN" required>
              <small>Use * for wildcard matching</small>
            </div>

            <div class="form-group">
              <label for="srcIp">Source IP Address *</label>
              <input type="text" id="srcIp" class="form-control" placeholder="192.168.1.10" required>
            </div>

            <div class="form-group">
              <label for="dstIp">Destination IP Address *</label>
              <input type="text" id="dstIp" class="form-control" placeholder="10.0.0.5" required>
            </div>

            <div class="form-group">
              <label for="protocol">Protocol (Optional)</label>
              <select id="protocol" class="form-control">
                <option value="">Any</option>
                <option value="TCP">TCP</option>
                <option value="UDP">UDP</option>
                <option value="ICMP">ICMP</option>
              </select>
            </div>

            <button id="executeQuery" class="btn btn-primary" ${isLoading ? 'disabled' : ''}>
              ${isLoading ? 'Executing...' : 'Execute Query'}
            </button>
          </div>
        `;

      case 'routing':
        return `
          <div class="query-form">
            <h4>Routing Table Query</h4>
            <p class="form-description">Inspect routing table entries</p>

            <div class="form-group">
              <label for="nodes">Node Filter (Optional)</label>
              <input type="text" id="nodes" class="form-control" placeholder="router1, router2">
              <small>Comma-separated list of node names. Leave empty for all nodes.</small>
            </div>

            <div class="form-group">
              <label for="networkFilter">Network Prefix Filter (Optional)</label>
              <input type="text" id="networkFilter" class="form-control" placeholder="10.0.0.0/8">
              <small>CIDR notation (e.g., 10.0.0.0/8)</small>
            </div>

            <button id="executeQuery" class="btn btn-primary" ${isLoading ? 'disabled' : ''}>
              ${isLoading ? 'Executing...' : 'Execute Query'}
            </button>
          </div>
        `;

      default:
        return '<p>Select a query type</p>';
    }
  }

  /**
   * Render verification results.
   */
  function renderResults() {
    if (queryHistory.length === 0) {
      return `
        <div class="empty-state">
          <p>No queries executed yet.</p>
          <p>Fill out the form above and click "Execute Query" to run a verification.</p>
        </div>
      `;
    }

    const latestResult = queryHistory[0];

    if (latestResult.status === 'FAILED') {
      return `
        <div class="verification-result error">
          <div class="result-header">
            <h4>Query Failed</h4>
            <span class="execution-time">${latestResult.execution_time_ms}ms</span>
          </div>
          <div class="error-message">
            <strong>Error:</strong> ${latestResult.error_message || 'Unknown error'}
          </div>
        </div>
      `;
    }

    return `
      <div class="verification-result success">
        <div class="result-header">
          <h4>${getQueryTypeLabel(latestResult.query_type)} Results</h4>
          <span class="execution-time">${latestResult.execution_time_ms}ms</span>
        </div>
        <div class="result-content">
          ${renderResultContent(latestResult)}
        </div>
      </div>
    `;
  }

  /**
   * Render result content based on query type.
   */
  function renderResultContent(result) {
    switch (result.query_type) {
      case 'reachability':
        return renderReachabilityResults(result);
      case 'acl':
        return renderACLResults(result);
      case 'routing':
        return renderRoutingResults(result);
      default:
        return '<p>Unknown query type</p>';
    }
  }

  /**
   * Render reachability flow traces.
   */
  function renderReachabilityResults(result) {
    if (!result.flow_traces || result.flow_traces.length === 0) {
      return '<p class="no-results">No flow traces found. Traffic may be blocked or unreachable.</p>';
    }

    let html = '';
    result.flow_traces.forEach((trace, index) => {
      html += `
        <div class="flow-trace">
          <div class="flow-disposition ${trace.disposition.toLowerCase()}">
            <strong>Flow ${index + 1}:</strong> ${trace.disposition}
          </div>
          ${renderFlowHops(trace.hops)}
        </div>
      `;
    });

    return html;
  }

  /**
   * Render flow trace hops.
   */
  function renderFlowHops(hops) {
    if (!hops || hops.length === 0) {
      return '<p class="no-hops">No hop information available</p>';
    }

    let html = '<div class="flow-hops">';
    hops.forEach((hop, index) => {
      html += `
        <div class="flow-hop">
          <span class="hop-number">${index + 1}</span>
          <span class="hop-node">${hop.node}</span>
          <span class="hop-action">${hop.action}</span>
          ${hop.interface_in ? `<span class="hop-interface">in: ${hop.interface_in}</span>` : ''}
          ${hop.interface_out ? `<span class="hop-interface">out: ${hop.interface_out}</span>` : ''}
        </div>
      `;
    });
    html += '</div>';

    return html;
  }

  /**
   * Render ACL match results.
   */
  function renderACLResults(result) {
    if (!result.acl_results || result.acl_results.length === 0) {
      return '<p class="no-results">No ACL matches found.</p>';
    }

    let html = '<div class="acl-results">';
    result.acl_results.forEach((aclResult, index) => {
      html += `
        <div class="acl-result">
          <div class="acl-header">
            <strong>Match ${index + 1}:</strong> ${aclResult.node} - ${aclResult.filter_name}
          </div>
          <div class="acl-details">
            <span class="acl-action ${aclResult.action.toLowerCase()}">${aclResult.action}</span>
            ${aclResult.line_number !== null ? `<span class="acl-line">Line ${aclResult.line_number}</span>` : ''}
          </div>
          ${aclResult.line_content ? `<div class="acl-line-content"><code>${aclResult.line_content}</code></div>` : ''}
        </div>
      `;
    });
    html += '</div>';

    return html;
  }

  /**
   * Render routing table entries.
   */
  function renderRoutingResults(result) {
    if (!result.route_entries || result.route_entries.length === 0) {
      return '<p class="no-results">No routing entries found.</p>';
    }

    let html = `
      <div class="routing-results">
        <table class="routing-table">
          <thead>
            <tr>
              <th>Node</th>
              <th>Network</th>
              <th>Next Hop</th>
              <th>Protocol</th>
              <th>AD</th>
              <th>Metric</th>
              <th>Interface</th>
            </tr>
          </thead>
          <tbody>
    `;

    result.route_entries.forEach(route => {
      html += `
        <tr>
          <td>${route.node}</td>
          <td>${route.network}</td>
          <td>${route.next_hop || '-'}</td>
          <td><span class="protocol-badge">${route.protocol}</span></td>
          <td>${route.admin_distance !== null ? route.admin_distance : '-'}</td>
          <td>${route.metric !== null ? route.metric : '-'}</td>
          <td>${route.interface || '-'}</td>
        </tr>
      `;
    });

    html += `
          </tbody>
        </table>
      </div>
    `;

    return html;
  }

  /**
   * Render query history.
   */
  function renderQueryHistory() {
    if (queryHistory.length === 0) {
      return '';
    }

    let html = `
      <div class="query-history">
        <h4>Recent Queries</h4>
        <div class="history-list">
    `;

    queryHistory.slice(0, 5).forEach((query, index) => {
      html += `
        <div class="history-item ${index === 0 ? 'active' : ''}">
          <span class="history-type">${getQueryTypeLabel(query.query_type)}</span>
          <span class="history-status ${query.status.toLowerCase()}">${query.status}</span>
          <span class="history-time">${query.execution_time_ms}ms</span>
        </div>
      `;
    });

    html += `
        </div>
      </div>
    `;

    return html;
  }

  /**
   * Get query type label.
   */
  function getQueryTypeLabel(type) {
    const labels = {
      'reachability': 'Reachability',
      'acl': 'ACL Test',
      'routing': 'Routing'
    };
    return labels[type] || type;
  }

  /**
   * Attach event listeners.
   */
  function attachEventListeners() {
    // Query type buttons
    container.querySelectorAll('.query-type-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        currentQueryType = btn.dataset.type;
        render();
      });
    });

    // Execute query button
    const executeBtn = container.querySelector('#executeQuery');
    if (executeBtn) {
      executeBtn.addEventListener('click', handleExecuteQuery);
    }
  }

  /**
   * Handle query execution.
   */
  async function handleExecuteQuery() {
    if (isLoading) return;

    try {
      isLoading = true;
      render();

      let result;

      switch (currentQueryType) {
        case 'reachability':
          result = await executeReachabilityQuery();
          break;
        case 'acl':
          result = await executeACLQuery();
          break;
        case 'routing':
          result = await executeRoutingQuery();
          break;
        default:
          throw new Error('Unknown query type');
      }

      // Add to history
      queryHistory.unshift(result);
      if (queryHistory.length > 10) {
        queryHistory = queryHistory.slice(0, 10);
      }

    } catch (error) {
      console.error('Query execution failed:', error);
      alert(`Query failed: ${error.message}`);

    } finally {
      isLoading = false;
      render();
    }
  }

  /**
   * Execute reachability query.
   */
  async function executeReachabilityQuery() {
    const srcIp = container.querySelector('#srcIp').value.trim();
    const dstIp = container.querySelector('#dstIp').value.trim();
    const srcNode = container.querySelector('#srcNode').value.trim() || null;

    if (!srcIp || !dstIp) {
      throw new Error('Source IP and Destination IP are required');
    }

    return await verificationService.verifyReachability(
      snapshotName,
      srcIp,
      dstIp,
      networkName,
      srcNode
    );
  }

  /**
   * Execute ACL query.
   */
  async function executeACLQuery() {
    const filterName = container.querySelector('#filterName').value.trim();
    const srcIp = container.querySelector('#srcIp').value.trim();
    const dstIp = container.querySelector('#dstIp').value.trim();
    const protocol = container.querySelector('#protocol').value || null;

    if (!filterName || !srcIp || !dstIp) {
      throw new Error('Filter name, Source IP, and Destination IP are required');
    }

    return await verificationService.verifyACL(
      snapshotName,
      filterName,
      srcIp,
      dstIp,
      networkName,
      protocol
    );
  }

  /**
   * Execute routing query.
   */
  async function executeRoutingQuery() {
    const nodesInput = container.querySelector('#nodes').value.trim();
    const networkFilter = container.querySelector('#networkFilter').value.trim() || null;

    const nodes = nodesInput
      ? nodesInput.split(',').map(n => n.trim()).filter(n => n.length > 0)
      : null;

    return await verificationService.verifyRouting(
      snapshotName,
      networkName,
      nodes,
      networkFilter
    );
  }

  /**
   * Refresh the panel.
   */
  function refresh() {
    render();
  }

  /**
   * Destroy the component.
   */
  function destroy() {
    container.innerHTML = '';
  }

  // Initial render
  render();

  // Return public API
  return {
    refresh,
    destroy
  };
}
