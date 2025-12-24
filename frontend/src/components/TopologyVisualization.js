/**
 * Network Topology Visualization Component.
 *
 * Uses D3.js v7 for force-directed graph layout with interactive features:
 * - Zoom and pan
 * - Node dragging
 * - Hover information display (Feature 002)
 * - Export to SVG/PNG
 */

import * as d3 from 'd3';
import topologyService from '../services/topologyService.js';

/**
 * Create topology visualization component.
 *
 * @param {HTMLElement} container - Container element for visualization
 * @param {string} snapshotName - Snapshot name to visualize
 * @param {string} networkName - Network name (default: "default")
 * @param {Object} nodeDetailPanel - NodeDetailPanel instance (optional)
 * @returns {Object} Component API with methods
 */
export function createTopologyVisualization(container, snapshotName, networkName = 'default', nodeDetailPanel = null) {
  let svg, g, simulation;
  let nodes = [], links = [];
  let tooltip;
  let dragStart = null; // Track drag start for click detection

  const width = container.clientWidth || 800;
  const height = container.clientHeight || 600;

  // Color scheme for different device types
  const deviceColors = {
    router: '#3b82f6',    // blue
    switch: '#10b981',    // green
    firewall: '#ef4444',  // red
    default: '#6b7280'    // gray
  };

  /**
   * Initialize the visualization.
   */
  async function init() {
    // Clear container
    container.innerHTML = '';

    // Create SVG
    svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('class', 'topology-svg');

    // Create container group for zoom/pan
    g = svg.append('g');

    // Setup zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create tooltip
    tooltip = d3.select(container)
      .append('div')
      .attr('class', 'topology-tooltip')
      .style('opacity', 0)
      .style('position', 'absolute')
      .style('background', 'white')
      .style('padding', '10px')
      .style('border', '1px solid #ccc')
      .style('border-radius', '4px')
      .style('pointer-events', 'none')
      .style('box-shadow', '0 2px 4px rgba(0,0,0,0.1)')
      .style('font-size', '12px')
      .style('z-index', 1000);

    // Load topology data
    await loadTopology();
  }

  /**
   * Load topology data from API.
   */
  async function loadTopology() {
    try {
      const topology = await topologyService.getTopology(snapshotName, networkName);

      nodes = topology.nodes || [];
      links = topology.edges || [];

      // Add index to nodes for d3
      nodes.forEach((node, i) => {
        node.id = node.hostname;
        node.index = i;
      });

      // Convert edges to d3 link format
      links = links.map(edge => ({
        source: edge.source_hostname,
        target: edge.target_hostname,
        sourceInterface: edge.source_interface,
        targetInterface: edge.target_interface,
        sourceIp: edge.source_ip,
        targetIp: edge.target_ip,
        protocol: edge.protocol
      }));

      renderTopology();

    } catch (error) {
      console.error('Failed to load topology:', error);
      showError('Failed to load topology data. Please ensure Batfish is running and the snapshot exists.');
    }
  }

  /**
   * Render the topology visualization.
   */
  function renderTopology() {
    // Clear previous rendering
    g.selectAll('*').remove();

    if (nodes.length === 0) {
      showEmptyState();
      return;
    }

    // Create force simulation
    simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links)
        .id(d => d.id)
        .distance(150))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    // Create arrow marker for directed edges
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .append('svg:path')
      .attr('d', 'M 0,-5 L 10,0 L 0,5')
      .attr('fill', '#999');

    // Draw links
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', '#999')
      .attr('stroke-width', 2)
      .attr('marker-end', 'url(#arrowhead)')
      .on('mouseover', handleLinkMouseOver)
      .on('mouseout', handleMouseOut);

    // Draw nodes
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g')
      .call(d3.drag()
        .on('start', dragStarted)
        .on('drag', dragged)
        .on('end', dragEnded));

    // Node circles
    node.append('circle')
      .attr('r', 20)
      .attr('fill', d => deviceColors[d.device_type] || deviceColors.default)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('mouseover', handleNodeMouseOver)
      .on('mouseout', handleMouseOut)
      .on('click', handleNodeClick);

    // Node labels
    node.append('text')
      .text(d => d.hostname)
      .attr('x', 0)
      .attr('y', 35)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .attr('fill', '#333');

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
  }

  /**
   * Handle node hover (Feature 002: Hover information display).
   */
  function handleNodeMouseOver(event, d) {
    // Highlight node
    d3.select(this)
      .attr('stroke', '#fbbf24')
      .attr('stroke-width', 3);

    // Show tooltip with device information
    const tooltipHtml = `
      <div style="font-weight: bold; margin-bottom: 5px;">${d.hostname}</div>
      <div><strong>Type:</strong> ${d.device_type || 'Unknown'}</div>
      <div><strong>Vendor:</strong> ${d.vendor || 'Unknown'}</div>
      <div><strong>Model:</strong> ${d.model || 'Unknown'}</div>
      <div><strong>Interfaces:</strong> ${d.interfaces_count || 0}</div>
      <div><strong>Config Format:</strong> ${d.config_format || 'Unknown'}</div>
    `;

    tooltip
      .html(tooltipHtml)
      .style('left', (event.pageX + 10) + 'px')
      .style('top', (event.pageY - 10) + 'px')
      .transition()
      .duration(200)
      .style('opacity', 0.95);
  }

  /**
   * Handle link hover (Feature 002: Hover information display).
   */
  function handleLinkMouseOver(event, d) {
    // Highlight link
    d3.select(this)
      .attr('stroke', '#fbbf24')
      .attr('stroke-width', 3);

    // Show tooltip with link information
    const tooltipHtml = `
      <div style="font-weight: bold; margin-bottom: 5px;">Link Information</div>
      <div><strong>Source:</strong> ${d.source.id} (${d.sourceInterface})</div>
      <div><strong>Target:</strong> ${d.target.id} (${d.targetInterface})</div>
      ${d.sourceIp ? `<div><strong>Source IP:</strong> ${d.sourceIp}</div>` : ''}
      ${d.targetIp ? `<div><strong>Target IP:</strong> ${d.targetIp}</div>` : ''}
      ${d.protocol ? `<div><strong>Protocol:</strong> ${d.protocol}</div>` : ''}
    `;

    tooltip
      .html(tooltipHtml)
      .style('left', (event.pageX + 10) + 'px')
      .style('top', (event.pageY - 10) + 'px')
      .transition()
      .duration(200)
      .style('opacity', 0.95);
  }

  /**
   * Handle mouse out event.
   */
  function handleMouseOut() {
    // Reset highlighting
    d3.select(this)
      .attr('stroke', function() {
        return this.tagName === 'circle' ? '#fff' : '#999';
      })
      .attr('stroke-width', function() {
        return this.tagName === 'circle' ? 2 : 2;
      });

    // Hide tooltip
    tooltip.transition()
      .duration(200)
      .style('opacity', 0);
  }

  /**
   * Handle node click event (Feature 003: Node Detail Panel).
   * Opens the detail panel if the node wasn't dragged.
   * US2 - T044: Toggle close if clicking the same node again.
   * US2 - T046, T047: Add/remove selected visual indicator.
   */
  function handleNodeClick(event, d) {
    // Check if this was a drag operation
    if (event.defaultPrevented) {
      return; // This was a drag, not a click
    }

    // Open detail panel if available
    if (nodeDetailPanel) {
      // US2 - T044: Check if clicking the same node that's already open
      if (nodeDetailPanel.state.isOpen && nodeDetailPanel.state.currentNode === d.hostname) {
        // Toggle close
        nodeDetailPanel.close();
        // US2 - T046: Remove selected indicator
        removeSelectedIndicator();
      } else {
        // US2 - T047: Remove old selected indicator and add new one
        removeSelectedIndicator();
        addSelectedIndicator(d.hostname);
        // Open panel for this node (or switch to different node)
        nodeDetailPanel.open(d.hostname, snapshotName, networkName);
      }
    }
  }

  /**
   * Add selected indicator to a node (US2 - T046).
   * @param {string} hostname - Hostname of node to select
   */
  function addSelectedIndicator(hostname) {
    g.selectAll('.nodes g')
      .filter(d => d.hostname === hostname)
      .select('circle')
      .classed('selected', true);
  }

  /**
   * Remove selected indicator from all nodes (US2 - T046, T047).
   */
  function removeSelectedIndicator() {
    g.selectAll('.nodes g circle')
      .classed('selected', false);
  }

  /**
   * Drag event handlers.
   */
  function dragStarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  /**
   * Export topology to SVG.
   */
  function exportSVG() {
    const svgElement = container.querySelector('svg');
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `topology-${snapshotName}.svg`;
    link.click();

    URL.revokeObjectURL(url);
  }

  /**
   * Export topology to PNG.
   */
  function exportPNG() {
    const svgElement = container.querySelector('svg');
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');

    const data = new XMLSerializer().serializeToString(svgElement);
    const img = new Image();
    const blob = new Blob([data], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);

    img.onload = () => {
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, width, height);
      ctx.drawImage(img, 0, 0);

      canvas.toBlob((pngBlob) => {
        const pngUrl = URL.createObjectURL(pngBlob);
        const link = document.createElement('a');
        link.href = pngUrl;
        link.download = `topology-${snapshotName}.png`;
        link.click();

        URL.revokeObjectURL(url);
        URL.revokeObjectURL(pngUrl);
      });
    };

    img.src = url;
  }

  /**
   * Show empty state message.
   */
  function showEmptyState() {
    container.innerHTML = `
      <div class="empty-state">
        <p>No topology data available for this snapshot.</p>
        <p>Please ensure the snapshot contains network devices and configurations.</p>
      </div>
    `;
  }

  /**
   * Show error message.
   */
  function showError(message) {
    container.innerHTML = `
      <div class="error-state" style="padding: 2rem; text-align: center; color: #ef4444;">
        <p>${message}</p>
      </div>
    `;
  }

  /**
   * Refresh the topology visualization.
   */
  async function refresh() {
    await loadTopology();
  }

  /**
   * Destroy the visualization and clean up.
   */
  function destroy() {
    if (simulation) {
      simulation.stop();
    }
    container.innerHTML = '';
  }

  // Initialize on creation
  init();

  // US3 - T064: Wire up onClose callback to remove selected indicator when panel closes
  if (nodeDetailPanel) {
    nodeDetailPanel.onClose = removeSelectedIndicator;
  }

  // Return public API
  return {
    refresh,
    destroy,
    exportSVG,
    exportPNG
  };
}
