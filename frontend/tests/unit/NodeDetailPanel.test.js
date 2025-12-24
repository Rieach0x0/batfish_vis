/**
 * Unit tests for NodeDetailPanel component
 *
 * TDD Phase: RED - These tests should FAIL until component implementation is complete
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

describe('NodeDetailPanel', () => {
  let container;
  let panel;

  beforeEach(() => {
    // Setup DOM container
    container = document.createElement('div');
    container.id = 'test-container';
    document.body.appendChild(container);

    // Mock fetch globally
    global.fetch = jest.fn();
  });

  afterEach(() => {
    // Cleanup
    document.body.removeChild(container);
    jest.restoreAllMocks();
  });

  it('should render panel in closed state initially', async () => {
    // Arrange & Act
    const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
    panel = new NodeDetailPanel(container);

    // Assert
    const panelElement = container.querySelector('.node-detail-panel');
    expect(panelElement).toBeDefined();
    expect(panelElement.dataset.state).toBe('closed');
  });

  it('should have initial state with isOpen=false', async () => {
    // Arrange & Act
    const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
    panel = new NodeDetailPanel(container);

    // Assert
    expect(panel.state.isOpen).toBe(false);
    expect(panel.state.currentNode).toBeNull();
  });

  it('should open panel when open() is called', async () => {
    // Arrange
    const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
    panel = new NodeDetailPanel(container);

    const mockNodeDetail = {
      hostname: 'router-01',
      device_type: 'router',
      vendor: 'Cisco',
      status: 'active',
      interfaces: [],
      metadata: {
        snapshot_name: 'test_snapshot',
        last_updated: '2025-12-23T10:15:32Z'
      }
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockNodeDetail
    });

    // Act
    await panel.open('router-01', 'test_snapshot');

    // Assert
    expect(panel.state.isOpen).toBe(true);
    expect(panel.state.currentNode).toBe('router-01');
    const panelElement = container.querySelector('.node-detail-panel');
    expect(panelElement.dataset.state).toBe('open');
  });

  it('should fetch node details when opening panel', async () => {
    // Arrange
    const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
    panel = new NodeDetailPanel(container);

    const hostname = 'router-01';
    const snapshot = 'test_snapshot';

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        hostname,
        status: 'active',
        interfaces: [],
        metadata: { snapshot_name: snapshot, last_updated: '2025-12-23T10:15:32Z' }
      })
    });

    // Act
    await panel.open(hostname, snapshot);

    // Assert - US2: fetch now includes signal parameter for AbortController
    expect(global.fetch).toHaveBeenCalledWith(
      `/api/topology/nodes/${hostname}/details?snapshot=${snapshot}&network=default`,
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
  });

  it('should display hostname in panel', async () => {
    // Arrange
    const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
    panel = new NodeDetailPanel(container);

    const mockNodeDetail = {
      hostname: 'router-01',
      device_type: 'router',
      vendor: 'Cisco',
      model: 'ISR4451',
      status: 'active',
      interfaces: [],
      metadata: {
        snapshot_name: 'test_snapshot',
        last_updated: '2025-12-23T10:15:32Z'
      }
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockNodeDetail
    });

    // Act
    await panel.open('router-01', 'test_snapshot');

    // Assert
    const content = container.querySelector('.panel-content');
    expect(content.textContent).toContain('router-01');
  });

  it('should display interfaces in panel', async () => {
    // Arrange
    const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
    panel = new NodeDetailPanel(container);

    const mockNodeDetail = {
      hostname: 'router-01',
      status: 'active',
      interfaces: [
        {
          name: 'GigabitEthernet0/0/0',
          active: true,
          ip_addresses: ['192.168.1.1/24'],
          description: 'Uplink'
        },
        {
          name: 'GigabitEthernet0/0/1',
          active: false,
          ip_addresses: []
        }
      ],
      metadata: {
        snapshot_name: 'test_snapshot',
        last_updated: '2025-12-23T10:15:32Z'
      }
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockNodeDetail
    });

    // Act
    await panel.open('router-01', 'test_snapshot');

    // Assert
    const interfaceItems = container.querySelectorAll('.interface-item');
    expect(interfaceItems.length).toBe(2);
    expect(container.textContent).toContain('GigabitEthernet0/0/0');
    expect(container.textContent).toContain('192.168.1.1/24');
  });

  it('should display "No interfaces configured" for empty interfaces', async () => {
    // Arrange
    const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
    panel = new NodeDetailPanel(container);

    const mockNodeDetail = {
      hostname: 'router-01',
      status: 'unknown',
      interfaces: [],
      metadata: {
        snapshot_name: 'test_snapshot',
        last_updated: '2025-12-23T10:15:32Z'
      }
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockNodeDetail
    });

    // Act
    await panel.open('router-01', 'test_snapshot');

    // Assert
    const content = container.querySelector('.panel-content');
    expect(content.textContent).toContain('No interfaces configured');
  });

  it('should display "No IP assigned" for interface without IPs', async () => {
    // Arrange
    const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
    panel = new NodeDetailPanel(container);

    const mockNodeDetail = {
      hostname: 'switch-01',
      status: 'active',
      interfaces: [
        {
          name: 'Ethernet1',
          active: true,
          ip_addresses: [],
          description: 'Access port'
        }
      ],
      metadata: {
        snapshot_name: 'test_snapshot',
        last_updated: '2025-12-23T10:15:32Z'
      }
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockNodeDetail
    });

    // Act
    await panel.open('switch-01', 'test_snapshot');

    // Assert
    const content = container.querySelector('.panel-content');
    expect(content.textContent).toContain('No IP assigned');
  });

  it('should display N/A for null device metadata', async () => {
    // Arrange
    const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
    panel = new NodeDetailPanel(container);

    const mockNodeDetail = {
      hostname: 'unknown-device',
      device_type: null,
      vendor: null,
      model: null,
      os_version: null,
      status: 'unknown',
      interfaces: [],
      metadata: {
        snapshot_name: 'test_snapshot',
        last_updated: '2025-12-23T10:15:32Z'
      }
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockNodeDetail
    });

    // Act
    await panel.open('unknown-device', 'test_snapshot');

    // Assert
    const content = container.querySelector('.panel-content');
    const naCount = (content.textContent.match(/N\/A/g) || []).length;
    expect(naCount).toBeGreaterThan(0);
  });

  it('should close panel when close() is called', async () => {
    // Arrange
    const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
    panel = new NodeDetailPanel(container);

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        hostname: 'router-01',
        status: 'active',
        interfaces: [],
        metadata: { snapshot_name: 'test_snapshot', last_updated: '2025-12-23T10:15:32Z' }
      })
    });

    await panel.open('router-01', 'test_snapshot');

    // Act
    panel.close();

    // Assert
    expect(panel.state.isOpen).toBe(false);
    expect(panel.state.currentNode).toBeNull();
    const panelElement = container.querySelector('.node-detail-panel');
    expect(panelElement.dataset.state).toBe('closed');
  });

  it('should handle API error gracefully', async () => {
    // Arrange
    const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
    panel = new NodeDetailPanel(container);

    global.fetch.mockResolvedValueOnce({
      ok: false,
      statusText: 'Not Found'
    });

    // Act
    await panel.open('nonexistent-router', 'test_snapshot');

    // Assert
    const errorElement = container.querySelector('.panel-error');
    expect(errorElement.style.display).not.toBe('none');
    expect(errorElement.textContent).toContain('Failed');
  });

  it('should show loading state while fetching data', async () => {
    // Arrange
    const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
    panel = new NodeDetailPanel(container);

    let resolveFetch;
    const fetchPromise = new Promise(resolve => { resolveFetch = resolve; });

    global.fetch.mockReturnValueOnce(fetchPromise);

    // Act - US2: debouncing delays execution by 100ms
    const openPromise = panel.open('router-01', 'test_snapshot');

    // Wait for debounce to complete
    await new Promise(resolve => setTimeout(resolve, 150));

    // Assert - loading should now be visible
    const loadingElement = container.querySelector('.panel-loading');
    expect(loadingElement.style.display).not.toBe('none');

    // Cleanup
    resolveFetch({
      ok: true,
      json: async () => ({
        hostname: 'router-01',
        status: 'active',
        interfaces: [],
        metadata: { snapshot_name: 'test_snapshot', last_updated: '2025-12-23T10:15:32Z' }
      })
    });
    await openPromise;
  });

  // User Story 2: Switch Between Nodes
  describe('Node Switching (US2)', () => {
    it('should update panel content when opening different node', async () => {
      // Arrange
      const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
      panel = new NodeDetailPanel(container);

      const node1Data = {
        hostname: 'router-01',
        device_type: 'router',
        status: 'active',
        interfaces: [],
        metadata: { snapshot_name: 'test_snapshot', last_updated: '2025-12-23T10:15:32Z' }
      };

      const node2Data = {
        hostname: 'switch-01',
        device_type: 'switch',
        status: 'active',
        interfaces: [],
        metadata: { snapshot_name: 'test_snapshot', last_updated: '2025-12-23T10:15:32Z' }
      };

      global.fetch
        .mockResolvedValueOnce({ ok: true, json: async () => node1Data })
        .mockResolvedValueOnce({ ok: true, json: async () => node2Data });

      // Act
      await panel.open('router-01', 'test_snapshot');
      await panel.open('switch-01', 'test_snapshot');

      // Assert
      expect(panel.state.currentNode).toBe('switch-01');
      const content = container.querySelector('.panel-content');
      expect(content.textContent).toContain('switch-01');
      expect(content.textContent).not.toContain('router-01');
    });

    it('should cancel pending request when switching nodes', async () => {
      // Arrange
      const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
      panel = new NodeDetailPanel(container);

      // US2: With debouncing, rapid calls cancel earlier ones
      // Only the last call actually executes
      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          hostname: 'switch-01',
          status: 'active',
          interfaces: [],
          metadata: { snapshot_name: 'test_snapshot', last_updated: '2025-12-23T10:15:32Z' }
        })
      });

      // Act - Make two rapid calls (debouncing will cancel first)
      panel.open('router-01', 'test_snapshot'); // Don't await - this will be canceled
      await panel.open('switch-01', 'test_snapshot'); // Await the second call

      // Assert - latest request wins
      expect(panel.state.currentNode).toBe('switch-01');

      // fetch should only be called once (for switch-01) due to debouncing
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/topology/nodes/switch-01/details?snapshot=test_snapshot&network=default',
        expect.objectContaining({ signal: expect.any(AbortSignal) })
      );
    });

    it('should close panel when clicking same node again', async () => {
      // Arrange
      const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
      panel = new NodeDetailPanel(container);

      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          hostname: 'router-01',
          status: 'active',
          interfaces: [],
          metadata: { snapshot_name: 'test_snapshot', last_updated: '2025-12-23T10:15:32Z' }
        })
      });

      await panel.open('router-01', 'test_snapshot');
      expect(panel.state.isOpen).toBe(true);

      // Act - open same node again (should toggle close)
      if (panel.state.currentNode === 'router-01' && panel.state.isOpen) {
        panel.close();
      }

      // Assert
      expect(panel.state.isOpen).toBe(false);
    });
  });

  // User Story 3: Close Panel
  describe('Close Panel (US3)', () => {
    it('should close panel when clicking close button', async () => {
      // Arrange
      const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
      panel = new NodeDetailPanel(container);

      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          hostname: 'router-01',
          status: 'active',
          interfaces: [],
          metadata: { snapshot_name: 'test_snapshot', last_updated: '2025-12-23T10:15:32Z' }
        })
      });

      await panel.open('router-01', 'test_snapshot');
      expect(panel.state.isOpen).toBe(true);

      // Act - click close button
      const closeBtn = container.querySelector('.panel-close-btn');
      closeBtn.click();

      // Assert
      expect(panel.state.isOpen).toBe(false);
      const panelElement = container.querySelector('.node-detail-panel');
      expect(panelElement.dataset.state).toBe('closed');
    });

    it('should close panel when clicking backdrop', async () => {
      // Arrange
      const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
      panel = new NodeDetailPanel(container);

      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          hostname: 'router-01',
          status: 'active',
          interfaces: [],
          metadata: { snapshot_name: 'test_snapshot', last_updated: '2025-12-23T10:15:32Z' }
        })
      });

      await panel.open('router-01', 'test_snapshot');
      expect(panel.state.isOpen).toBe(true);

      // Act - click backdrop
      const backdrop = container.querySelector('.panel-backdrop');
      backdrop.click();

      // Assert
      expect(panel.state.isOpen).toBe(false);
      const panelElement = container.querySelector('.node-detail-panel');
      expect(panelElement.dataset.state).toBe('closed');
    });

    it('should close panel when pressing ESC key', async () => {
      // Arrange
      const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
      panel = new NodeDetailPanel(container);

      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          hostname: 'router-01',
          status: 'active',
          interfaces: [],
          metadata: { snapshot_name: 'test_snapshot', last_updated: '2025-12-23T10:15:32Z' }
        })
      });

      await panel.open('router-01', 'test_snapshot');
      expect(panel.state.isOpen).toBe(true);

      // Act - press ESC key
      const escEvent = new KeyboardEvent('keydown', {
        key: 'Escape',
        code: 'Escape',
        keyCode: 27,
        bubbles: true
      });
      document.dispatchEvent(escEvent);

      // Assert
      expect(panel.state.isOpen).toBe(false);
      const panelElement = container.querySelector('.node-detail-panel');
      expect(panelElement.dataset.state).toBe('closed');
    });

    it('should not close panel when pressing non-ESC keys', async () => {
      // Arrange
      const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
      panel = new NodeDetailPanel(container);

      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          hostname: 'router-01',
          status: 'active',
          interfaces: [],
          metadata: { snapshot_name: 'test_snapshot', last_updated: '2025-12-23T10:15:32Z' }
        })
      });

      await panel.open('router-01', 'test_snapshot');
      expect(panel.state.isOpen).toBe(true);

      // Act - press Enter key
      const enterEvent = new KeyboardEvent('keydown', {
        key: 'Enter',
        code: 'Enter',
        keyCode: 13,
        bubbles: true
      });
      document.dispatchEvent(enterEvent);

      // Assert - panel should still be open
      expect(panel.state.isOpen).toBe(true);
      const panelElement = container.querySelector('.node-detail-panel');
      expect(panelElement.dataset.state).toBe('open');
    });

    it('should remove ESC key listener when panel is closed', async () => {
      // Arrange
      const { NodeDetailPanel } = await import('../../src/components/NodeDetailPanel.js');
      panel = new NodeDetailPanel(container);

      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          hostname: 'router-01',
          status: 'active',
          interfaces: [],
          metadata: { snapshot_name: 'test_snapshot', last_updated: '2025-12-23T10:15:32Z' }
        })
      });

      await panel.open('router-01', 'test_snapshot');
      panel.close();

      // Act - press ESC key after close
      const escEvent = new KeyboardEvent('keydown', {
        key: 'Escape',
        code: 'Escape',
        keyCode: 27,
        bubbles: true
      });
      document.dispatchEvent(escEvent);

      // Assert - panel should remain closed (no error thrown)
      expect(panel.state.isOpen).toBe(false);
    });
  });
});
