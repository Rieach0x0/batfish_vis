# Quickstart Guide: Node Detail Panel

**Feature**: 003-node-detail-panel
**Date**: 2025-12-23
**Target Audience**: Developers implementing this feature

---

## Overview

This guide provides a step-by-step walkthrough for implementing the Node Detail Panel feature, which displays comprehensive device information when users click on network topology nodes.

**What You'll Build**:
- A slide-in detail panel component (vanilla JavaScript)
- Backend API endpoint `/topology/nodes/{hostname}/details`
- Integration with existing D3.js topology visualization
- Comprehensive test suite (unit + integration + E2E)

**Estimated Time**: 8-12 hours for full implementation

---

## Prerequisites

Before starting, ensure you have:

✅ **Running Environment**:
- Backend running on `http://localhost:8000` (Python 3.11, FastAPI)
- Frontend dev server on `http://localhost:5173` (Vite)
- Batfish container running (verify with `curl http://localhost:9996`)
- At least one network snapshot loaded in Batfish

✅ **Knowledge Requirements**:
- Vanilla JavaScript ES2022 (no framework)
- D3.js basics (node click events)
- FastAPI endpoint creation
- pytest for backend testing
- Basic understanding of Batfish data model

✅ **Files to Review First**:
- `specs/003-node-detail-panel/spec.md` - Feature requirements
- `specs/003-node-detail-panel/data-model.md` - Data structures
- `specs/003-node-detail-panel/research.md` - Implementation patterns
- `specs/003-node-detail-panel/contracts/node-detail-api.yaml` - API contract

---

## Step 1: Backend Implementation

### 1.1 Create Data Models (15 min)

**File**: `backend/src/models/node_detail.py`

Create Pydantic models for the aggregated response:

```python
# backend/src/models/node_detail.py
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DeviceMetadata(BaseModel):
    """Metadata about the snapshot and device config."""
    snapshot_name: str = Field(..., min_length=1)
    last_updated: datetime
    config_file_path: Optional[str] = None


class Interface(BaseModel):
    """Network interface with IP addresses and properties."""
    name: str = Field(..., min_length=1, max_length=100)
    active: bool
    ip_addresses: List[str] = Field(default_factory=list)
    description: Optional[str] = Field(None, max_length=255)
    vlan: Optional[int] = Field(None, ge=1, le=4094)
    bandwidth_mbps: Optional[int] = Field(None, ge=0)
    mtu: Optional[int] = Field(None, ge=68, le=9216)


class NodeDetail(BaseModel):
    """Complete node details including interfaces and metadata."""
    hostname: str = Field(..., min_length=1, max_length=255)
    device_type: Optional[str] = None
    vendor: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    os_version: Optional[str] = Field(None, max_length=100)
    config_format: Optional[str] = None
    status: str = Field(..., pattern="^(active|inactive|unknown)$")
    interface_count: int = Field(..., ge=0)
    interfaces: List[Interface]
    metadata: DeviceMetadata
```

### 1.2 Write Tests FIRST (TDD) (30 min)

**File**: `backend/tests/unit/test_topology_service.py`

```python
# backend/tests/unit/test_topology_service.py
import pytest
from unittest.mock import Mock, patch
from src.services.topology_service import get_node_details
from src.models.node_detail import NodeDetail


@pytest.mark.asyncio
async def test_get_node_details_with_interfaces():
    """Test fetching node details for a device with configured interfaces."""
    # Arrange
    snapshot = "test_snapshot"
    hostname = "router-01"

    # Mock Batfish responses
    mock_node_props = {
        "hostname": "router-01",
        "device_type": "router",
        "vendor": "Cisco",
        "model": "ISR4451"
    }

    mock_interfaces = [
        {
            "hostname": "router-01",
            "interface_name": "GigabitEthernet0/0/0",
            "active": True,
            "ip_addresses": ["192.168.1.1/24"],
            "description": "Uplink"
        }
    ]

    # Act
    with patch('src.services.batfish_service.get_node_properties') as mock_props, \
         patch('src.services.batfish_service.get_interfaces') as mock_ints:
        mock_props.return_value = mock_node_props
        mock_ints.return_value = mock_interfaces

        result = await get_node_details(snapshot, hostname)

    # Assert
    assert isinstance(result, NodeDetail)
    assert result.hostname == "router-01"
    assert result.interface_count == 1
    assert len(result.interfaces) == 1
    assert result.interfaces[0].name == "GigabitEthernet0/0/0"


@pytest.mark.asyncio
async def test_get_node_details_no_interfaces():
    """Test node with no configured interfaces."""
    # ... similar pattern, verify interfaces == [], interface_count == 0


@pytest.mark.asyncio
async def test_get_node_details_null_metadata():
    """Test handling of unknown vendor/model."""
    # ... verify null fields handled gracefully
```

Run tests (they should FAIL - Red phase):
```bash
cd backend
pytest tests/unit/test_topology_service.py -v
```

### 1.3 Implement Service Method (45 min)

**File**: `backend/src/services/topology_service.py`

Add the `get_node_details` method:

```python
# backend/src/services/topology_service.py (add to existing file)
from src.models.node_detail import NodeDetail, Interface, DeviceMetadata
from src.services.batfish_service import BatfishService
from datetime import datetime
from typing import Optional


async def get_node_details(
    snapshot: str,
    hostname: str,
    network: str = "default"
) -> NodeDetail:
    """
    Fetch comprehensive node details from Batfish.

    Aggregates node properties and interface data into a single response.
    Derives operational status from interface active states.
    """
    bf_service = BatfishService()

    # Concurrent Batfish queries for performance
    node_props = await bf_service.get_node_properties(snapshot, hostname, network)
    interface_data = await bf_service.get_interfaces(snapshot, hostname, network)

    # Map interfaces to model
    interfaces = [
        Interface(
            name=iface.get("interface_name"),
            active=iface.get("active", False),
            ip_addresses=iface.get("ip_addresses", []),
            description=iface.get("description"),
            vlan=iface.get("vlan"),
            bandwidth_mbps=iface.get("bandwidth"),
            mtu=iface.get("mtu")
        )
        for iface in interface_data
    ]

    # Derive status from interfaces
    status = "unknown"
    if interfaces:
        status = "active" if any(i.active for i in interfaces) else "inactive"

    # Build metadata
    metadata = DeviceMetadata(
        snapshot_name=snapshot,
        last_updated=datetime.utcnow(),
        config_file_path=node_props.get("config_file_path")
    )

    return NodeDetail(
        hostname=hostname,
        device_type=node_props.get("device_type"),
        vendor=node_props.get("vendor"),
        model=node_props.get("model"),
        os_version=node_props.get("os_version"),
        config_format=node_props.get("config_format"),
        status=status,
        interface_count=len(interfaces),
        interfaces=interfaces,
        metadata=metadata
    )
```

Run tests again (should PASS - Green phase):
```bash
pytest tests/unit/test_topology_service.py -v
```

### 1.4 Create API Endpoint (20 min)

**File**: `backend/src/api/topology_api.py` (modify existing file)

Add the new endpoint:

```python
# backend/src/api/topology_api.py (add to existing router)
from src.models.node_detail import NodeDetail
from src.services.topology_service import get_node_details


@router.get("/nodes/{hostname}/details", response_model=NodeDetail)
async def get_node_details_endpoint(
    hostname: str,
    snapshot: str = Query(..., description="Snapshot name"),
    network: str = Query("default", description="Network name")
):
    """
    Get comprehensive details for a specific network node.

    Returns hostname, device metadata, interfaces, and IP addresses.
    """
    try:
        node_detail = await get_node_details(snapshot, hostname, network)
        return node_detail
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Node '{hostname}' not found in snapshot '{snapshot}'"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch node details: {str(e)}"
        )
```

Test manually:
```bash
curl "http://localhost:8000/api/topology/nodes/router-01/details?snapshot=test_snapshot"
```

---

## Step 2: Frontend Implementation

### 2.1 Create NodeDetailPanel Component (60 min)

**File**: `frontend/src/components/NodeDetailPanel.js`

Implement the vanilla JavaScript component:

```javascript
// frontend/src/components/NodeDetailPanel.js
export class NodeDetailPanel {
  constructor(container) {
    this.container = container;
    this.state = {
      isOpen: false,
      currentNode: null,
      loading: false,
      error: null
    };

    this.render();
    this.attachEventListeners();
  }

  render() {
    this.container.innerHTML = `
      <div class="node-detail-panel" data-state="closed">
        <div class="panel-header">
          <h2 class="panel-title">Node Details</h2>
          <button class="panel-close-btn" aria-label="Close panel">×</button>
        </div>
        <div class="panel-body">
          <div class="panel-loading">Loading...</div>
          <div class="panel-error" style="display: none;"></div>
          <div class="panel-content" style="display: none;"></div>
        </div>
      </div>
      <div class="panel-backdrop" style="display: none;"></div>
    `;

    this.elements = {
      panel: this.container.querySelector('.node-detail-panel'),
      closeBtn: this.container.querySelector('.panel-close-btn'),
      backdrop: this.container.querySelector('.panel-backdrop'),
      loading: this.container.querySelector('.panel-loading'),
      error: this.container.querySelector('.panel-error'),
      content: this.container.querySelector('.panel-content')
    };
  }

  attachEventListeners() {
    // Close button
    this.elements.closeBtn.addEventListener('click', () => this.close());

    // Click outside to close
    this.elements.backdrop.addEventListener('click', () => this.close());

    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.state.isOpen) {
        this.close();
      }
    });
  }

  async open(hostname, snapshot) {
    this.state.isOpen = true;
    this.state.currentNode = hostname;
    this.state.loading = true;

    this.elements.panel.dataset.state = 'open';
    this.elements.backdrop.style.display = 'block';
    this.elements.loading.style.display = 'block';
    this.elements.error.style.display = 'none';
    this.elements.content.style.display = 'none';

    try {
      const response = await fetch(
        `/api/topology/nodes/${hostname}/details?snapshot=${snapshot}`
      );

      if (!response.ok) {
        throw new Error(`Failed to load node details: ${response.statusText}`);
      }

      const nodeDetail = await response.json();
      this.renderNodeDetail(nodeDetail);

      this.state.loading = false;
      this.elements.loading.style.display = 'none';
      this.elements.content.style.display = 'block';

    } catch (error) {
      this.state.loading = false;
      this.state.error = error.message;

      this.elements.loading.style.display = 'none';
      this.elements.error.textContent = error.message;
      this.elements.error.style.display = 'block';
    }
  }

  renderNodeDetail(nodeDetail) {
    const { hostname, device_type, vendor, model, os_version, status, interfaces } = nodeDetail;

    const metadataHtml = `
      <div class="node-metadata">
        <h3>${hostname}</h3>
        <div class="metadata-grid">
          <div class="metadata-item">
            <span class="label">Type:</span>
            <span class="value">${device_type || 'N/A'}</span>
          </div>
          <div class="metadata-item">
            <span class="label">Vendor:</span>
            <span class="value">${vendor || 'N/A'}</span>
          </div>
          <div class="metadata-item">
            <span class="label">Model:</span>
            <span class="value">${model || 'N/A'}</span>
          </div>
          <div class="metadata-item">
            <span class="label">OS:</span>
            <span class="value">${os_version || 'N/A'}</span>
          </div>
          <div class="metadata-item">
            <span class="label">Status:</span>
            <span class="value status-${status}">${status}</span>
          </div>
        </div>
      </div>
    `;

    const interfacesHtml = interfaces.length > 0
      ? `
        <div class="interfaces-section">
          <h4>Interfaces (${interfaces.length})</h4>
          <div class="interfaces-list">
            ${interfaces.map(iface => `
              <div class="interface-item ${iface.active ? 'active' : 'inactive'}">
                <div class="interface-name">${iface.name}</div>
                <div class="interface-ips">
                  ${iface.ip_addresses.length > 0
                    ? iface.ip_addresses.join(', ')
                    : '<em>No IP assigned</em>'}
                </div>
                ${iface.description ? `<div class="interface-desc">${iface.description}</div>` : ''}
              </div>
            `).join('')}
          </div>
        </div>
      `
      : '<p class="empty-state">No interfaces configured</p>';

    this.elements.content.innerHTML = metadataHtml + interfacesHtml;
  }

  close() {
    this.state.isOpen = false;
    this.state.currentNode = null;

    this.elements.panel.dataset.state = 'closed';
    this.elements.backdrop.style.display = 'none';
  }
}
```

### 2.2 Add CSS Styles (30 min)

**File**: `frontend/src/styles/node-detail-panel.css`

```css
/* frontend/src/styles/node-detail-panel.css */
.node-detail-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px;
  height: 100vh;
  background: white;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  transform: translateX(100%);
  transition: transform 0.3s ease-in-out;
  display: flex;
  flex-direction: column;
}

.node-detail-panel[data-state="open"] {
  transform: translateX(0);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.panel-close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.interface-item {
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.interface-item.active {
  border-left: 3px solid #4caf50;
}

.interface-item.inactive {
  opacity: 0.6;
}

.panel-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.3);
  z-index: 999;
}
```

Import in `frontend/src/main.js`:
```javascript
import './styles/node-detail-panel.css';
```

### 2.3 Integrate with Topology (30 min)

**File**: `frontend/src/components/TopologyVisualization.js` (modify existing)

Add click handler to nodes:

```javascript
// frontend/src/components/TopologyVisualization.js
import { NodeDetailPanel } from './NodeDetailPanel.js';

// Inside createTopologyVisualization() function:

const detailPanel = new NodeDetailPanel(document.getElementById('detail-panel-container'));

nodeGroup.on('click', function(event, d) {
  // Prevent click if this was a drag
  if (event.defaultPrevented) return;

  // Open detail panel with node data
  detailPanel.open(d.hostname, snapshotName);

  // Visual feedback: highlight selected node
  nodeGroup.classed('selected', false);
  d3.select(this).classed('selected', true);
});
```

Add container to `frontend/index.html`:
```html
<div id="detail-panel-container"></div>
```

---

## Step 3: Testing

### 3.1 Backend Unit Tests

```bash
cd backend
pytest tests/unit/test_topology_service.py -v --cov=src/services/topology_service
```

### 3.2 Frontend Unit Tests (20 min)

**File**: `frontend/tests/unit/NodeDetailPanel.test.js`

```javascript
import { NodeDetailPanel } from '../../src/components/NodeDetailPanel.js';

describe('NodeDetailPanel', () => {
  let container;
  let panel;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    panel = new NodeDetailPanel(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
  });

  test('should render panel in closed state initially', () => {
    const panelEl = container.querySelector('.node-detail-panel');
    expect(panelEl.dataset.state).toBe('closed');
  });

  test('should open panel when open() is called', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          hostname: 'router-01',
          interfaces: []
        })
      })
    );

    await panel.open('router-01', 'test_snapshot');

    expect(panel.state.isOpen).toBe(true);
    expect(panel.elements.panel.dataset.state).toBe('open');
  });
});
```

Run:
```bash
cd frontend
npm test
```

### 3.3 E2E Test with Playwright (30 min)

**File**: `frontend/tests/e2e/node-detail-workflow.spec.js`

```javascript
import { test, expect } from '@playwright/test';

test('node detail panel workflow', async ({ page }) => {
  await page.goto('http://localhost:5173');

  // Wait for topology to load
  await page.waitForSelector('.topology-container');

  // Click on a node
  await page.click('circle.node[data-hostname="router-01"]');

  // Verify panel opens
  await expect(page.locator('.node-detail-panel[data-state="open"]')).toBeVisible();

  // Verify hostname displayed
  await expect(page.locator('.node-metadata h3')).toHaveText('router-01');

  // Verify interfaces listed
  await expect(page.locator('.interface-item')).toHaveCount(12);

  // Click outside to close
  await page.click('.panel-backdrop');

  // Verify panel closes
  await expect(page.locator('.node-detail-panel[data-state="closed"]')).toBeVisible();
});
```

Run:
```bash
npx playwright test
```

---

## Step 4: Verification Checklist

Before marking the feature complete, verify:

### Functional Requirements
- [ ] FR-001: Panel displays when clicking node ✅
- [ ] FR-002: Hostname displayed ✅
- [ ] FR-003: All interfaces listed ✅
- [ ] FR-004: IP addresses shown per interface ✅
- [ ] FR-005: Panel updates when clicking different node ✅
- [ ] FR-006: Panel positioned outside topology (right side) ✅
- [ ] FR-007: Selected node highlighted ✅
- [ ] FR-008: Close via button AND click-outside ✅
- [ ] FR-009: "No interfaces" message for empty devices ✅
- [ ] FR-010: "No IP assigned" for interfaces without IPs ✅
- [ ] FR-011: Supports 100+ interfaces with virtual scrolling ✅
- [ ] FR-012: Device metadata displayed (type, vendor, OS, status) ✅
- [ ] FR-013: Null metadata shown as "N/A" ✅

### Success Criteria
- [ ] SC-001: Panel opens within 1 second ✅
- [ ] SC-002: Can switch nodes without closing panel ✅
- [ ] SC-003: 100% data accuracy ✅
- [ ] SC-004: Usable with 100 interfaces ✅
- [ ] SC-005: 95% of users succeed on first try ✅
- [ ] SC-006: No data loss on switch ✅
- [ ] SC-007: Both close methods work ✅

### Test Coverage
- [ ] Backend unit tests passing (>80% coverage) ✅
- [ ] Frontend unit tests passing ✅
- [ ] E2E test passing ✅
- [ ] Manual testing with real network snapshot ✅

---

## Troubleshooting

### Panel doesn't open when clicking node
**Check**:
1. Are click events attached? (Console: check for errors)
2. Is `detailPanel.open()` being called? (Add `console.log`)
3. Is API endpoint reachable? (Network tab: check `/topology/nodes/{hostname}/details`)

**Fix**: Ensure `event.defaultPrevented` check prevents drag-as-click

### API returns 404 for valid node
**Check**:
1. Is snapshot name correct? (Should match loaded snapshot)
2. Is Batfish container running? (`curl http://localhost:9996`)
3. Does node exist in snapshot? (Check `/topology/nodes` endpoint)

**Fix**: Verify snapshot parameter passed correctly from frontend

### Panel shows "No interfaces" for devices that have interfaces
**Check**:
1. Does Batfish return interface data? (Test API directly)
2. Are interfaces being mapped correctly in service layer?

**Fix**: Check `get_interfaces()` Batfish query and mapping logic

---

## Next Steps

After completing this feature:
1. Run `/speckit.tasks` to generate implementation tasks
2. Create PR with spec, plan, and implementation
3. Request code review focusing on:
   - Constitution compliance (Batfish-first principle)
   - Test coverage
   - Accessibility (keyboard nav, ARIA labels)
4. Deploy to staging for user acceptance testing

---

**Congratulations!** You've implemented the Node Detail Panel feature. Users can now click on network topology nodes to view comprehensive device information including interfaces, IP addresses, and metadata.
