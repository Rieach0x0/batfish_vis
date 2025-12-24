# Node Detail Panel Implementation Research

**Research Date:** 2025-12-23
**Purpose:** Technical research for implementing a node detail panel in D3.js-based network topology visualization
**Project:** batfish_vis - Network Topology Visualization Tool

---

## Table of Contents

1. [Vanilla JavaScript Panel Component Patterns](#1-vanilla-javascript-panel-component-patterns)
2. [D3.js Node Click Integration](#2-d3js-node-click-integration)
3. [API Aggregation Strategy](#3-api-aggregation-strategy)
4. [Layout Strategies for Side Panels](#4-layout-strategies-for-side-panels)
5. [Testing Strategies for Interactive UI Components](#5-testing-strategies-for-interactive-ui-components)

---

## 1. Vanilla JavaScript Panel Component Patterns

### Decision: Use Class-Based Component with Event Delegation

**Recommended Approach:**

Implement a class-based vanilla JavaScript component using the module pattern with event delegation for event handling and Proxy-based reactive state management for panel state.

### Rationale

1. **Browser Native Standards (2025)**: Modern approaches leverage the native HTML `<dialog>` element combined with custom classes for enhanced accessibility and focus management without dependencies ([Building a Side Drawer with Web Standards](https://pixari.dev/building-a-side-drawer-with-web-standards-using-the-dialog-element/)).

2. **Component Pattern Principles**: Components should be plain objects as sets of pure functions connecting data with DOM, avoiding side effects and external data coupling ([The Vanilla Javascript Component Pattern](https://dev.to/megazear7/the-vanilla-javascript-component-pattern-37la)).

3. **State Management**: Modern vanilla JS (2025-2026) uses Proxy API for reactive state, Structured Cloning for immutability, and ES Modules for shared state across components ([Modern State Management in Vanilla JavaScript: 2026 Patterns](https://medium.com/@orami98/modern-state-management-in-vanilla-javascript-2026-patterns-and-beyond-ce00425f7ac5)).

4. **Project Alignment**: The existing codebase already uses ES2022 module patterns (see `TopologyVisualization.js`), making this approach consistent with current architecture.

### Alternatives Considered

**Alternative 1: Web Components (Custom Elements)**
- **Pros**: Native browser API, encapsulated styles, reusable across projects
- **Cons**: Overkill for single-use component, Shadow DOM complicates styling integration with existing CSS, browser support edge cases
- **Why Not Chosen**: Adds complexity without significant benefits for internal component

**Alternative 2: Simple Function-Based Component**
- **Pros**: Minimal code, easy to understand
- **Cons**: Difficult to manage state, lacks encapsulation, harder to test
- **Why Not Chosen**: Poor scalability for complex panel interactions (click outside, keyboard nav, data updates)

**Alternative 3: Third-Party Library (e.g., drawer components)**
- **Pros**: Battle-tested, feature-complete
- **Cons**: Adds dependencies, bundle size increase, learning curve
- **Why Not Chosen**: Project uses "Vanilla JS" approach explicitly, avoiding frameworks

### Code Example: Panel Component Pattern

```javascript
/**
 * NodeDetailPanel.js
 * Side panel component for displaying detailed node information
 */

export class NodeDetailPanel {
  constructor(container) {
    this.container = container;
    this.panel = null;
    this.closeHandler = null;

    // Reactive state using Proxy (2025 pattern)
    this._state = {
      isOpen: false,
      selectedNode: null,
      interfaces: []
    };

    this.state = new Proxy(this._state, {
      set: (target, property, value) => {
        target[property] = value;
        this.render();
        return true;
      }
    });

    this.init();
  }

  init() {
    // Create panel element
    this.panel = document.createElement('div');
    this.panel.className = 'node-detail-panel';
    this.panel.setAttribute('role', 'complementary');
    this.panel.setAttribute('aria-label', 'Node Details Panel');
    this.panel.setAttribute('tabindex', '-1');

    this.container.appendChild(this.panel);

    // Setup event delegation
    this.panel.addEventListener('click', this.handlePanelClick.bind(this));

    // Initial render
    this.render();
  }

  handlePanelClick(event) {
    // Event delegation for close button
    if (event.target.closest('.panel-close')) {
      this.close();
    }
  }

  open(nodeData) {
    this.state.selectedNode = nodeData;
    this.state.isOpen = true;

    // Setup click-outside-to-close listener
    // Best practice: Use setTimeout to avoid immediate trigger
    setTimeout(() => {
      this.closeHandler = this.handleClickOutside.bind(this);
      document.addEventListener('click', this.closeHandler);
    }, 0);

    // Accessibility: Focus management
    this.panel.focus();
  }

  close() {
    this.state.isOpen = false;
    this.state.selectedNode = null;

    // Remove click-outside listener
    if (this.closeHandler) {
      document.removeEventListener('click', this.closeHandler);
      this.closeHandler = null;
    }
  }

  handleClickOutside(event) {
    // Click-outside pattern: check if click is outside panel
    if (!this.panel.contains(event.target)) {
      this.close();
    }
  }

  render() {
    const { isOpen, selectedNode, interfaces } = this.state;

    // Toggle visibility
    this.panel.classList.toggle('panel-open', isOpen);
    this.panel.setAttribute('aria-hidden', !isOpen);

    if (!isOpen) {
      this.panel.innerHTML = '';
      return;
    }

    // Render panel content
    this.panel.innerHTML = `
      <div class="panel-header">
        <h3>${selectedNode?.hostname || 'Node Details'}</h3>
        <button class="panel-close" aria-label="Close panel">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="panel-content">
        ${this.renderNodeInfo(selectedNode)}
        ${this.renderInterfaceList(interfaces)}
      </div>
    `;
  }

  renderNodeInfo(node) {
    if (!node) return '';

    return `
      <section class="node-info" aria-labelledby="node-info-heading">
        <h4 id="node-info-heading">Device Information</h4>
        <dl>
          <dt>Hostname</dt>
          <dd>${node.hostname}</dd>
          <dt>Type</dt>
          <dd>${node.device_type || 'Unknown'}</dd>
          <dt>Vendor</dt>
          <dd>${node.vendor || 'Unknown'}</dd>
          <dt>Model</dt>
          <dd>${node.model || 'N/A'}</dd>
        </dl>
      </section>
    `;
  }

  renderInterfaceList(interfaces) {
    if (!interfaces.length) {
      return '<p class="empty-state">Loading interfaces...</p>';
    }

    // Virtual scrolling for 100+ interfaces (see section on performance)
    return `
      <section class="interface-list" aria-labelledby="interface-heading">
        <h4 id="interface-heading">Interfaces (${interfaces.length})</h4>
        <div class="interface-scroll-container">
          ${interfaces.map(iface => `
            <div class="interface-item">
              <div class="interface-name">${iface.interface_name}</div>
              <div class="interface-status ${iface.active ? 'active' : 'inactive'}">
                ${iface.active ? 'Active' : 'Inactive'}
              </div>
              ${iface.ip_addresses?.length ? `
                <div class="interface-ip">${iface.ip_addresses.join(', ')}</div>
              ` : ''}
            </div>
          `).join('')}
        </div>
      </section>
    `;
  }

  async loadInterfaces(hostname, snapshotName) {
    try {
      // Fetch interfaces from API
      const response = await fetch(
        `/api/snapshots/${snapshotName}/topology/interfaces?hostname=${hostname}`
      );
      const interfaces = await response.json();
      this.state.interfaces = interfaces;
    } catch (error) {
      console.error('Failed to load interfaces:', error);
      this.state.interfaces = [];
    }
  }

  destroy() {
    if (this.closeHandler) {
      document.removeEventListener('click', this.closeHandler);
    }
    this.panel.remove();
  }
}
```

### Best Practices for Event Handling

**Click-Outside-to-Close Pattern:**

Based on 2025 best practices ([Detecting clicks outside](https://gomakethings.com/detecting-clicks-outside-of-an-element-with-vanilla-js/), [Closing on outside click](https://kittygiraudel.com/2021/03/18/close-on-outside-click/)):

1. Use `setTimeout` to delay adding the document click listener to avoid immediate re-closing
2. Use `Element.contains()` to check if click target is inside panel
3. Remove listener when panel closes to avoid memory leaks
4. Consider using `closest()` for more complex DOM structures

**State Management Pattern:**

Based on modern vanilla JS patterns ([State Management in Vanilla JS: 2026 Trends](https://medium.com/@chirag.dave/state-management-in-vanilla-js-2026-trends-f9baed7599de)):

1. Use Proxy API for reactive state updates
2. Structured cloning for immutable state where needed
3. Observer pattern for component communication
4. Local state for UI-specific concerns (panel visibility, loading states)

### Performance Considerations for Large Lists (100+ interfaces)

**Decision: Implement Virtual Scrolling for Lists > 50 Items**

Based on research ([Rendering Large Lists in Vanilla JS](https://tghosh.hashnode.dev/rendering-large-lists-in-vanilla-js-list-virtualization), [List Virtualization](https://medium.com/@ethanhaller02/list-virtualization-how-to-smoothly-scroll-through-10-000-items-cad39bfa7f3e)):

**Virtual Scrolling Benefits:**
- Reduces initial render from 5+ seconds to <100ms for 10,000 items
- Maintains smooth 60fps scrolling
- Only renders visible items + small buffer

**Implementation Approach:**

```javascript
class VirtualList {
  constructor(container, items, itemHeight = 60) {
    this.container = container;
    this.items = items;
    this.itemHeight = itemHeight;
    this.visibleCount = Math.ceil(container.clientHeight / itemHeight);
    this.startIndex = 0;

    this.init();
  }

  init() {
    this.container.style.height = `${this.items.length * this.itemHeight}px`;
    this.container.style.position = 'relative';

    this.container.addEventListener('scroll', () => {
      this.startIndex = Math.floor(this.container.scrollTop / this.itemHeight);
      this.render();
    });

    this.render();
  }

  render() {
    // Only render visible items + buffer
    const endIndex = Math.min(
      this.startIndex + this.visibleCount + 5,
      this.items.length
    );

    const html = this.items
      .slice(this.startIndex, endIndex)
      .map((item, idx) => {
        const actualIndex = this.startIndex + idx;
        return `
          <div class="virtual-item"
               style="position: absolute; top: ${actualIndex * this.itemHeight}px; height: ${this.itemHeight}px;">
            ${this.renderItem(item)}
          </div>
        `;
      })
      .join('');

    this.container.innerHTML = html;
  }

  renderItem(item) {
    // Override in subclass
    return `<div>${item.interface_name}</div>`;
  }
}
```

**Recommendation for batfish_vis:**
- Use simple rendering for < 50 interfaces
- Implement virtual scrolling for >= 50 interfaces
- Use libraries like [hyperlist](https://github.com/tbranyen/hyperlist) if complexity grows

---

## 2. D3.js Node Click Integration

### Decision: Use Click Handler with `event.defaultPrevented` Check

**Recommended Approach:**

Add click event listeners to node elements and check `event.defaultPrevented` to distinguish clicks from drag operations. Use CSS classes for selection highlighting and SVG element reordering for z-index control.

### Rationale

1. **Standard D3.js Pattern**: The D3.js drag behavior automatically sets `event.defaultPrevented` when a drag occurs, providing a clean way to distinguish clicks from drags ([D3.js Click vs Drag](https://observablehq.com/@d3/click-vs-drag), [D3 GitHub Issue #1445](https://github.com/d3/d3/issues/1445)).

2. **Browser Compatibility**: This approach works consistently across all modern browsers without additional libraries.

3. **Maintains Existing Hover**: Click handlers can coexist with existing hover tooltips without interference.

4. **Project Context**: Current implementation already has drag behavior on nodes (lines 172-175 in TopologyVisualization.js), making this the natural extension.

### Alternatives Considered

**Alternative 1: Replace Drag with Click-Only**
- **Pros**: Simplest implementation, no conflict handling needed
- **Cons**: Loses valuable drag-to-reposition functionality users expect
- **Why Not Chosen**: Degrades user experience

**Alternative 2: Use Double-Click for Selection**
- **Pros**: No conflict with drag
- **Cons**: Poor discoverability, accessibility issues, non-standard interaction
- **Why Not Chosen**: Violates usability conventions

**Alternative 3: Add Select Button to Tooltip**
- **Pros**: Clear affordance, no gesture conflicts
- **Cons**: Extra click required, complicates tooltip UI, tooltip may disappear
- **Why Not Chosen**: Friction in user workflow

### Code Example: D3.js Click Handler Implementation

```javascript
// In TopologyVisualization.js

function renderTopology() {
  // ... existing code ...

  let selectedNode = null;

  // Draw nodes (existing code)
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

  // Node circles (modify existing code)
  node.append('circle')
    .attr('r', 20)
    .attr('fill', d => deviceColors[d.device_type] || deviceColors.default)
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .on('mouseover', handleNodeMouseOver)
    .on('mouseout', handleMouseOut)
    .on('click', handleNodeClick);  // ADD: Click handler

  // ... rest of existing code ...

  /**
   * Handle node click event (NEW FUNCTION)
   * Distinguishes clicks from drags using event.defaultPrevented
   */
  function handleNodeClick(event, d) {
    // CRITICAL: Check if this was a drag operation
    if (event.defaultPrevented) return;

    // Prevent click from bubbling to document (would close panel)
    event.stopPropagation();

    // Update selection state
    if (selectedNode === d) {
      // Clicking same node again - deselect
      deselectNode();
    } else {
      // Select new node
      selectNode(d);
    }
  }

  /**
   * Select a node and show detail panel
   */
  function selectNode(nodeData) {
    // Clear previous selection
    deselectNode();

    selectedNode = nodeData;

    // Highlight selected node
    node.selectAll('circle')
      .filter(d => d === nodeData)
      .classed('node-selected', true)
      .attr('stroke', '#fbbf24')
      .attr('stroke-width', 4)
      .raise();  // Bring to front (z-index simulation)

    // Optionally dim other nodes
    node.selectAll('circle')
      .filter(d => d !== nodeData)
      .classed('node-dimmed', true)
      .style('opacity', 0.5);

    // Open detail panel with node data
    if (window.nodeDetailPanel) {
      window.nodeDetailPanel.open(nodeData);
      window.nodeDetailPanel.loadInterfaces(
        nodeData.hostname,
        snapshotName
      );
    }

    // Dispatch custom event for other components
    container.dispatchEvent(new CustomEvent('nodeSelected', {
      detail: { node: nodeData }
    }));
  }

  /**
   * Deselect current node
   */
  function deselectNode() {
    if (!selectedNode) return;

    // Remove selection highlight
    node.selectAll('circle')
      .classed('node-selected', false)
      .classed('node-dimmed', false)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('opacity', 1);

    selectedNode = null;

    // Close detail panel
    if (window.nodeDetailPanel) {
      window.nodeDetailPanel.close();
    }

    container.dispatchEvent(new CustomEvent('nodeDeselected'));
  }

  // Public API extension
  return {
    refresh,
    destroy,
    exportSVG,
    exportPNG,
    selectNode,      // NEW: Programmatic selection
    deselectNode,    // NEW: Programmatic deselection
    getSelectedNode: () => selectedNode  // NEW: Get current selection
  };
}
```

### Best Practices for Click/Drag Disambiguation

Based on D3.js community recommendations ([D3 Click vs Drag Observable](https://observablehq.com/@d3/click-vs-drag), [Google Groups Discussion](https://groups.google.com/g/d3-js/c/qJQuCX1ZhjM)):

1. **Always check `event.defaultPrevented`** - This is set automatically by D3's drag behavior
2. **Use `event.stopPropagation()`** - Prevent click from bubbling to document listener
3. **Avoid re-appending elements on drag** - This can break click detection
4. **Use `.raise()`** for z-index** - SVG doesn't support z-index, use element reordering

### Highlighting Selected Nodes

**CSS Classes Approach:**

```css
/* Add to styles.css */

.node-selected {
  filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.8));
}

.node-dimmed {
  transition: opacity 0.3s ease;
}

/* Focus ring for keyboard navigation */
.node-focused {
  outline: 3px solid #3b82f6;
  outline-offset: 4px;
}
```

**SVG Element Ordering (Z-Index Simulation):**

SVG renders elements in document order, so use D3's `.raise()` method to move selected elements to the end of their parent, making them appear on top ([D3 GitHub Issue #252](https://github.com/d3/d3/issues/252)):

```javascript
selection.raise();  // Move to end (on top)
selection.lower();  // Move to start (behind)
```

### Keyboard Navigation Support

For accessibility, support keyboard-based node selection:

```javascript
// Add keyboard handler to SVG
svg.on('keydown', function(event) {
  if (event.key === 'Tab') {
    // Navigate between nodes
    focusNextNode();
  } else if (event.key === 'Enter' || event.key === ' ') {
    // Select focused node
    if (focusedNode) {
      selectNode(focusedNode);
    }
  } else if (event.key === 'Escape') {
    deselectNode();
  }
});
```

---

## 3. API Aggregation Strategy

### Decision: Create Aggregated Endpoint `/topology/nodes/{hostname}/details`

**Recommended Approach:**

Implement a new FastAPI endpoint that aggregates node information and interfaces in a single request, with response caching for frequently accessed nodes.

### Rationale

1. **Reduced Network Overhead**: Single HTTP request instead of 2 reduces latency by 100-300ms on typical networks, improving perceived performance.

2. **FastAPI Strengths**: FastAPI's async capabilities enable efficient parallel Batfish queries within the endpoint, leveraging I/O concurrency ([FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices), [FastAPI Performance Guide](https://pytutorial.com/fastapi-performance-optimization-guide/)).

3. **Caching Benefits**: Aggregated responses are better caching candidates since they're complete data sets, enabling effective use of Redis or in-memory caching ([FastAPI + Redis Caching](https://medium.com/@mahdijafaridev/caching-with-redis-boost-your-fastapi-applications-with-speed-and-scalability-af45626a57f3)).

4. **Client Simplification**: Frontend makes one call instead of orchestrating multiple requests, reducing error handling complexity.

5. **Bandwidth Efficiency**: Prevents redundant data transfer (node info is included in `/topology/nodes` response but needed again).

### Alternatives Considered

**Alternative 1: Multiple Separate Requests**
- **Pros**: RESTful resource separation, individual caching, reuses existing endpoints
- **Cons**: 2+ network round-trips, frontend orchestration complexity, race conditions
- **Why Not Chosen**: Poor performance for detail panel use case, especially on high-latency networks

**Alternative 2: GraphQL-Style Query Parameters**
- **Pros**: Flexible field selection, single endpoint
- **Cons**: Adds query parsing complexity, overkill for simple use case, requires new patterns
- **Why Not Chosen**: Introduces new paradigm inconsistent with existing REST API

**Alternative 3: WebSocket Real-Time Updates**
- **Pros**: Instant updates, bidirectional communication
- **Cons**: Overkill for static topology data, connection management overhead, complexity
- **Why Not Chosen**: Topology data doesn't require real-time streaming

### Code Example: Aggregated API Endpoint

```python
# backend/src/api/topology_api.py

from typing import Dict, List
from fastapi import APIRouter, HTTPException, Query, status
from fastapi_cache.decorator import cache  # Using fastapi-cache2
from ..models.device import Device
from ..models.interface import Interface
from ..services.topology_service import TopologyService
from ..exceptions import BatfishException
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/topology", tags=["topology"])

# ... existing endpoints ...

@router.get("/nodes/{hostname}/details", response_model=Dict)
@cache(expire=300)  # Cache for 5 minutes
async def get_node_details(
    hostname: str,
    snapshot: str = Query(..., description="Snapshot name"),
    network: str = Query(default="default", description="Network name")
):
    """
    Get aggregated node details including device info and all interfaces.

    This endpoint combines data from nodeProperties and interfaceProperties
    Batfish queries for efficient single-request detail panel loading.

    Args:
        hostname: Device hostname
        snapshot: Snapshot name
        network: Network name (default: "default")

    Returns:
        Dictionary containing:
        - device: Device object with node properties
        - interfaces: List of Interface objects
        - statistics: Summary statistics (total interfaces, active count, etc.)

    Raises:
        HTTPException: If node not found or query fails
    """
    try:
        logger.info(
            f"Getting node details for '{hostname}' in snapshot '{snapshot}'"
        )

        # Use async/await for concurrent Batfish queries
        import asyncio

        # Execute both queries concurrently (FastAPI best practice for I/O)
        device_task = topology_service.get_device_async(
            snapshot, network, hostname
        )
        interfaces_task = topology_service.get_interfaces_async(
            snapshot, network, hostname
        )

        device, interfaces = await asyncio.gather(
            device_task,
            interfaces_task
        )

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device '{hostname}' not found in snapshot '{snapshot}'"
            )

        # Calculate statistics
        statistics = {
            "total_interfaces": len(interfaces),
            "active_interfaces": sum(1 for i in interfaces if i.active),
            "inactive_interfaces": sum(1 for i in interfaces if not i.active),
            "interfaces_with_ip": sum(
                1 for i in interfaces if i.ip_addresses
            )
        }

        return {
            "device": device.dict(),
            "interfaces": [iface.dict() for iface in interfaces],
            "statistics": statistics,
            "snapshot": snapshot,
            "network": network,
            "timestamp": datetime.utcnow().isoformat()
        }

    except BatfishException as e:
        logger.error(f"Batfish error getting node details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve node details: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting node details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
```

```python
# backend/src/services/topology_service.py

# Add async versions of existing methods for concurrent execution

async def get_device_async(
    self,
    snapshot_name: str,
    network_name: str,
    hostname: str
) -> Optional[Device]:
    """
    Async version of get_devices for a single hostname.
    Enables concurrent execution with other async queries.
    """
    try:
        self.bf_session.set_network(network_name)
        self.bf_session.set_snapshot(snapshot_name)

        # Filter by hostname in Batfish query
        node_props = self.bf.q.nodeProperties(
            nodes=hostname
        ).answer().frame()

        if node_props.empty:
            return None

        row = node_props.iloc[0]
        device = Device(
            hostname=row.get('Node', ''),
            vendor=self._extract_vendor(row),
            model=row.get('Model', None),
            device_type=self._infer_device_type(row),
            config_format=row.get('Configuration_Format', None),
            interfaces_count=0  # Will be updated by caller
        )

        return device

    except Exception as e:
        logger.error(f"Failed to get device {hostname}: {str(e)}")
        raise BatfishException(f"Failed to retrieve device: {str(e)}")

async def get_interfaces_async(
    self,
    snapshot_name: str,
    network_name: str,
    hostname: str
) -> List[Interface]:
    """
    Async version of get_interfaces for concurrent execution.
    """
    # Reuse existing synchronous implementation
    # (Batfish Python client is thread-safe)
    return self.get_interfaces(snapshot_name, network_name, hostname)
```

### Caching Strategy

**Recommended Approach: Redis-backed Response Caching**

Based on 2025 best practices ([FastAPI + Redis](https://redis.io/learn/develop/python/fastapi), [Caching in FastAPI](https://dev.to/sivakumarmanoharan/caching-in-fastapi-unlocking-high-performance-development-20ej)):

1. **Use `fastapi-cache2` library** - Provides decorator-based caching with Redis backend
2. **Cache TTL: 5 minutes** - Topology data changes infrequently
3. **Cache Key**: `{snapshot}:{network}:{hostname}` - Automatic per-node caching
4. **Invalidation**: Clear cache on snapshot update/delete

**Setup:**

```python
# backend/src/main.py

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

app = FastAPI()

@app.on_event("startup")
async def startup():
    # Initialize Redis cache
    redis = aioredis.from_url(
        "redis://localhost:6379",
        encoding="utf8",
        decode_responses=False  # CRITICAL: Must be False for fastapi-cache
    )
    FastAPICache.init(RedisBackend(redis), prefix="batfish-cache")
```

### API Design Considerations

**Anti-Pattern to Avoid:**

Do NOT have one endpoint call another endpoint internally ([FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)). Instead, share logic via service layers:

```python
# BAD - Don't do this
@router.get("/nodes/{hostname}/details")
async def get_node_details(hostname: str):
    # Calling another endpoint - ANTI-PATTERN
    device = requests.get(f"http://localhost:8000/api/topology/nodes?hostname={hostname}")
    interfaces = requests.get(f"http://localhost:8000/api/topology/interfaces?hostname={hostname}")
    return {"device": device.json(), "interfaces": interfaces.json()}

# GOOD - Use shared service layer
@router.get("/nodes/{hostname}/details")
async def get_node_details(hostname: str):
    device = await topology_service.get_device_async(snapshot, network, hostname)
    interfaces = await topology_service.get_interfaces_async(snapshot, network, hostname)
    return {"device": device, "interfaces": interfaces}
```

### Performance Benchmarks

Expected performance improvements:

| Approach | Requests | Network RTT | Total Time | Caching Benefit |
|----------|----------|-------------|------------|-----------------|
| Multiple Requests | 2 | 2 × 50ms = 100ms | ~150-200ms | Partial |
| Aggregated | 1 | 1 × 50ms = 50ms | ~75-100ms | Full |
| Aggregated + Cached | 1 | 1 × 50ms = 50ms | ~5-10ms | Immediate |

---

## 4. Layout Strategies for Side Panels

### Decision: CSS Grid Layout with Overlay Behavior

**Recommended Approach:**

Use CSS Grid for main layout (topology + panel) with the panel as an overlay that appears on top using fixed positioning and transform animations. Support responsive behavior with media queries.

### Rationale

1. **Modern Standard (2025)**: CSS Grid is the established standard for two-dimensional layouts in 2025, with excellent browser support and powerful layout capabilities ([Modern CSS Layout Techniques 2025](https://dev.to/frontendtoolstech/modern-css-layout-techniques-flexbox-grid-and-subgrid-2025-guide-112f)).

2. **Flexbox + Grid Combination**: Grid for overall layout, Flexbox for panel internals follows 2025 best practices ([Mastering Advanced CSS Grid and Flexbox](https://dev.to/sharique_siddiqui_8242dad/mastering-advanced-css-grid-and-flexbox-techniques-for-responsive-layouts-5fa8)).

3. **Overlay vs Push**: Overlay preserves topology viewport dimensions, avoiding disruptive layout shifts that would require D3 re-initialization. Push content forces expensive re-rendering.

4. **Project Alignment**: Existing codebase uses basic Flexbox layout (`.app-main { display: flex; }`), making Grid a natural evolution.

### Alternatives Considered

**Alternative 1: Flexbox-Only Layout**
- **Pros**: Simpler, already partially implemented
- **Cons**: Less powerful for complex 2D layouts, requires more manual calculations
- **Why Not Chosen**: Grid better suited for app-level layout with multiple regions

**Alternative 2: Push Content (Non-Overlay)**
- **Pros**: Traditional desktop pattern, no z-index issues
- **Cons**: Forces D3 canvas resize, expensive re-layout, disruptive to user focus
- **Why Not Chosen**: Poor UX for graph visualization that user is actively exploring

**Alternative 3: Modal Dialog (Full Overlay)**
- **Pros**: Clear context switch, built-in focus trap
- **Cons**: Blocks entire interface, prevents comparing panel to graph
- **Why Not Chosen**: Users need to see topology while viewing details

### Code Example: Layout Implementation

**HTML Structure:**

```html
<!-- frontend/index.html -->
<div id="app">
  <header class="app-header">
    <!-- Existing header -->
  </header>

  <main class="app-main">
    <!-- Left sidebar (existing) -->
    <aside class="app-sidebar">
      <!-- Snapshot manager -->
    </aside>

    <!-- Main content area -->
    <div class="app-content">
      <!-- Topology visualization -->
      <div id="topology-container"></div>
    </div>

    <!-- Node detail panel (NEW - overlay) -->
    <aside id="node-detail-panel" class="node-detail-panel" aria-hidden="true">
      <!-- Panel content injected by JavaScript -->
    </aside>
  </main>

  <footer class="app-footer">
    <!-- Existing footer -->
  </footer>
</div>
```

**CSS Implementation:**

```css
/* Add to frontend/src/styles.css */

/* Main Layout - CSS Grid */
.app-main {
  display: grid;
  grid-template-columns: 350px 1fr; /* Sidebar + content */
  grid-template-rows: 1fr;
  flex: 1;
  position: relative; /* For panel positioning */
  overflow: hidden;
}

.app-sidebar {
  grid-column: 1;
  background: white;
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
}

.app-content {
  grid-column: 2;
  padding: 2rem;
  overflow-y: auto;
  position: relative;
}

/* Node Detail Panel - Overlay */
.node-detail-panel {
  position: fixed; /* Fixed positioning for overlay */
  top: 0;
  right: 0;
  bottom: 0;
  width: 400px;
  max-width: 90vw; /* Responsive width */
  background: white;
  border-left: 2px solid var(--border-color);
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;

  /* Transform for slide-in animation */
  transform: translateX(100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  /* Flexbox for internal layout */
  display: flex;
  flex-direction: column;

  /* Accessibility */
  outline: none; /* Remove default focus outline, use custom */
}

/* Panel open state */
.node-detail-panel.panel-open {
  transform: translateX(0);
}

/* Focus ring for keyboard navigation */
.node-detail-panel:focus-visible {
  box-shadow:
    -4px 0 12px rgba(0, 0, 0, 0.15),
    inset 0 0 0 3px var(--primary-color);
}

/* Panel header (fixed) */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  background: white;
  flex-shrink: 0;
}

.panel-header h3 {
  margin: 0;
  color: var(--primary-color);
  font-size: 1.25rem;
}

.panel-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.panel-close:hover {
  background: #f3f4f6;
  color: var(--text-color);
}

.panel-close:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

/* Panel content (scrollable) */
.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

/* Responsive behavior */
@media (max-width: 768px) {
  .app-main {
    grid-template-columns: 1fr; /* Stack sidebar on mobile */
  }

  .app-sidebar {
    display: none; /* Hide sidebar on mobile, or make toggle */
  }

  .node-detail-panel {
    width: 100vw; /* Full width on mobile */
    max-width: 100vw;
  }
}

@media (max-width: 1024px) {
  .node-detail-panel {
    width: 350px; /* Narrower on tablets */
  }
}

/* Window resize handling */
@media (min-width: 1400px) {
  .node-detail-panel {
    width: 500px; /* Wider on large screens */
  }
}

/* Node info section */
.node-info {
  margin-bottom: 2rem;
}

.node-info h4 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: var(--text-color);
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.node-info dl {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 0.75rem;
  margin: 0;
}

.node-info dt {
  font-weight: 600;
  color: #6b7280;
}

.node-info dd {
  margin: 0;
  color: var(--text-color);
}

/* Interface list */
.interface-list h4 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: var(--text-color);
}

.interface-scroll-container {
  max-height: 400px;
  overflow-y: auto;
}

.interface-item {
  padding: 1rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  margin-bottom: 0.75rem;
  background: #f9fafb;
  transition: background 0.2s;
}

.interface-item:hover {
  background: #f3f4f6;
}

.interface-name {
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 0.5rem;
}

.interface-status {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.interface-status.active {
  background: #d1fae5;
  color: #065f46;
}

.interface-status.inactive {
  background: #fee2e2;
  color: #991b1b;
}

.interface-ip {
  font-size: 0.875rem;
  color: #6b7280;
  font-family: 'Courier New', monospace;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
  font-style: italic;
}

/* Backdrop (optional - for mobile) */
@media (max-width: 768px) {
  .panel-backdrop {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
    opacity: 0;
    transition: opacity 0.3s;
  }

  .panel-backdrop.visible {
    display: block;
    opacity: 1;
  }
}
```

### Responsive Behavior

**Desktop (> 1024px):**
- Panel slides in from right as overlay
- Topology remains fully visible
- Panel width: 400-500px

**Tablet (768px - 1024px):**
- Panel slides in from right as overlay
- Panel width: 350px
- Sidebar may collapse to icons

**Mobile (< 768px):**
- Panel covers full screen width
- Semi-transparent backdrop behind panel
- Sidebar hidden or hamburger menu
- Topology pauses simulation when panel opens

### Window Resize Handling

```javascript
// In TopologyVisualization.js or App.js

let resizeTimeout;
window.addEventListener('resize', () => {
  // Debounce resize handling
  clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    // Update SVG dimensions if panel is closed
    if (!window.nodeDetailPanel?.state.isOpen) {
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;

      svg.attr('width', newWidth).attr('height', newHeight);

      // Recenter force simulation
      simulation.force('center', d3.forceCenter(newWidth / 2, newHeight / 2));
      simulation.alpha(0.3).restart();
    }
  }, 250);
});
```

### Accessibility Considerations

Based on 2025 WCAG 2.2 standards ([ARIA Labels for Web Accessibility 2025](https://www.allaccessible.org/blog/implementing-aria-labels-for-web-accessibility), [Accessible nav drawer](https://www.makethingsaccessible.com/guides/accessible-nav-drawer-disclosure-widgets/)):

**Required ARIA Attributes:**

```html
<aside
  id="node-detail-panel"
  class="node-detail-panel"
  role="complementary"
  aria-label="Node Details Panel"
  aria-hidden="true"
  tabindex="-1">
  <!-- Content -->
</aside>
```

**Keyboard Navigation:**

- `Tab`: Navigate through panel elements
- `Escape`: Close panel
- `Shift+Tab`: Reverse navigation
- Focus trap: Keep focus within panel when open

**Focus Management:**

```javascript
class NodeDetailPanel {
  open(nodeData) {
    // ... existing code ...

    // Set aria-hidden to false
    this.panel.setAttribute('aria-hidden', 'false');

    // Focus the panel
    this.panel.focus();

    // Trap focus within panel
    this.setupFocusTrap();
  }

  close() {
    // ... existing code ...

    // Set aria-hidden to true
    this.panel.setAttribute('aria-hidden', 'true');

    // Return focus to trigger element (the clicked node)
    if (this.triggerElement) {
      this.triggerElement.focus();
    }

    // Remove focus trap
    this.removeFocusTrap();
  }

  setupFocusTrap() {
    // Find all focusable elements in panel
    const focusableSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    const focusableElements = this.panel.querySelectorAll(focusableSelector);

    if (focusableElements.length === 0) return;

    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    this.focusTrapHandler = (event) => {
      if (event.key === 'Tab') {
        if (event.shiftKey && document.activeElement === firstFocusable) {
          event.preventDefault();
          lastFocusable.focus();
        } else if (!event.shiftKey && document.activeElement === lastFocusable) {
          event.preventDefault();
          firstFocusable.focus();
        }
      } else if (event.key === 'Escape') {
        this.close();
      }
    };

    this.panel.addEventListener('keydown', this.focusTrapHandler);
  }

  removeFocusTrap() {
    if (this.focusTrapHandler) {
      this.panel.removeEventListener('keydown', this.focusTrapHandler);
      this.focusTrapHandler = null;
    }
  }
}
```

**Screen Reader Announcements:**

```javascript
// Announce panel opening to screen readers
const announcement = document.createElement('div');
announcement.setAttribute('role', 'status');
announcement.setAttribute('aria-live', 'polite');
announcement.className = 'sr-only'; // Visually hidden
announcement.textContent = `Node details panel opened for ${nodeData.hostname}`;
document.body.appendChild(announcement);

setTimeout(() => announcement.remove(), 1000);
```

---

## 5. Testing Strategies for Interactive UI Components

### Decision: Playwright for E2E, Jest with JSDOM for Unit Tests

**Recommended Approach:**

Use Playwright for end-to-end testing of click workflows and panel interactions (runs in real browser), and Jest with JSDOM for unit testing individual component methods and DOM manipulation logic.

### Rationale

1. **Playwright Advantages (2025)**: Runs in real browsers, has built-in waiting for async operations, superior to Node-based emulated browsers that are often out-of-sync with real DOM features ([How to use Playwright for unit testing](https://gomakethings.com/how-to-use-playwright-for-unit-testing/)).

2. **Jest + JSDOM for Units**: Fast, good for testing component methods, state changes, and DOM manipulation without full browser overhead ([DOM Manipulation with Jest](https://jestjs.io/docs/tutorial-jquery)).

3. **Already Installed**: Project already has both Playwright (`@playwright/test`) and Jest in package.json, making this a zero-setup decision.

4. **Separation of Concerns**: E2E tests verify user workflows, unit tests verify component logic - clear boundaries.

### Alternatives Considered

**Alternative 1: Jest + JSDOM Only**
- **Pros**: Single testing framework, faster test execution, no browser startup
- **Cons**: JSDOM limitations (no layout engine, limited CSS support, no real events)
- **Why Not Chosen**: Can't test D3.js graph interactions reliably, click/drag conflicts untestable

**Alternative 2: Playwright Only**
- **Pros**: Tests exactly as users experience, one framework
- **Cons**: Slower execution, overkill for simple unit tests, harder to debug
- **Why Not Chosen**: Inefficient for testing pure logic, wastes CI time

**Alternative 3: Cypress**
- **Pros**: Popular, great developer experience, time-travel debugging
- **Cons**: Not already installed, larger bundle, slower than Playwright
- **Why Not Chosen**: Playwright already available and equally capable

### Code Example: Unit Tests with Jest

```javascript
// frontend/src/components/__tests__/NodeDetailPanel.test.js

import { NodeDetailPanel } from '../NodeDetailPanel.js';

describe('NodeDetailPanel', () => {
  let container;
  let panel;

  beforeEach(() => {
    // Setup DOM container
    container = document.createElement('div');
    document.body.appendChild(container);

    // Create panel instance
    panel = new NodeDetailPanel(container);
  });

  afterEach(() => {
    // Cleanup
    panel.destroy();
    document.body.removeChild(container);
  });

  describe('initialization', () => {
    test('creates panel element with correct attributes', () => {
      const panelElement = container.querySelector('.node-detail-panel');

      expect(panelElement).toBeTruthy();
      expect(panelElement.getAttribute('role')).toBe('complementary');
      expect(panelElement.getAttribute('aria-label')).toBe('Node Details Panel');
      expect(panelElement.getAttribute('aria-hidden')).toBe('true');
    });

    test('initializes with closed state', () => {
      expect(panel.state.isOpen).toBe(false);
      expect(panel.state.selectedNode).toBeNull();
    });
  });

  describe('open()', () => {
    const mockNode = {
      hostname: 'router-01',
      device_type: 'router',
      vendor: 'cisco',
      model: 'ISR4451'
    };

    test('updates state when opening panel', () => {
      panel.open(mockNode);

      expect(panel.state.isOpen).toBe(true);
      expect(panel.state.selectedNode).toEqual(mockNode);
    });

    test('adds panel-open class', () => {
      panel.open(mockNode);

      const panelElement = container.querySelector('.node-detail-panel');
      expect(panelElement.classList.contains('panel-open')).toBe(true);
    });

    test('sets aria-hidden to false', () => {
      panel.open(mockNode);

      const panelElement = container.querySelector('.node-detail-panel');
      expect(panelElement.getAttribute('aria-hidden')).toBe('false');
    });

    test('renders node information', () => {
      panel.open(mockNode);

      const hostname = container.querySelector('.panel-header h3');
      expect(hostname.textContent).toBe('router-01');
    });

    test('sets up click-outside listener asynchronously', (done) => {
      panel.open(mockNode);

      // Listener added in setTimeout, so wait a tick
      setTimeout(() => {
        expect(panel.closeHandler).toBeTruthy();
        done();
      }, 10);
    });
  });

  describe('close()', () => {
    beforeEach(() => {
      const mockNode = { hostname: 'router-01' };
      panel.open(mockNode);
    });

    test('updates state when closing panel', () => {
      panel.close();

      expect(panel.state.isOpen).toBe(false);
      expect(panel.state.selectedNode).toBeNull();
    });

    test('removes panel-open class', () => {
      panel.close();

      const panelElement = container.querySelector('.node-detail-panel');
      expect(panelElement.classList.contains('panel-open')).toBe(false);
    });

    test('removes click-outside listener', (done) => {
      setTimeout(() => {
        panel.close();
        expect(panel.closeHandler).toBeNull();
        done();
      }, 10);
    });
  });

  describe('handleClickOutside()', () => {
    beforeEach(() => {
      const mockNode = { hostname: 'router-01' };
      panel.open(mockNode);
    });

    test('closes panel when clicking outside', (done) => {
      setTimeout(() => {
        // Simulate click outside panel
        const outsideElement = document.createElement('div');
        document.body.appendChild(outsideElement);

        const clickEvent = new MouseEvent('click', { bubbles: true });
        outsideElement.dispatchEvent(clickEvent);

        expect(panel.state.isOpen).toBe(false);

        document.body.removeChild(outsideElement);
        done();
      }, 10);
    });

    test('does not close panel when clicking inside', (done) => {
      setTimeout(() => {
        const panelElement = container.querySelector('.node-detail-panel');

        const clickEvent = new MouseEvent('click', { bubbles: true });
        panelElement.dispatchEvent(clickEvent);

        expect(panel.state.isOpen).toBe(true);
        done();
      }, 10);
    });
  });

  describe('renderInterfaceList()', () => {
    const mockInterfaces = [
      {
        interface_name: 'GigabitEthernet0/0',
        active: true,
        ip_addresses: ['192.168.1.1']
      },
      {
        interface_name: 'GigabitEthernet0/1',
        active: false,
        ip_addresses: []
      }
    ];

    test('renders interface count', () => {
      panel.state.interfaces = mockInterfaces;
      panel.render();

      const heading = container.querySelector('.interface-list h4');
      expect(heading.textContent).toContain('2');
    });

    test('renders all interfaces', () => {
      panel.state.interfaces = mockInterfaces;
      panel.render();

      const items = container.querySelectorAll('.interface-item');
      expect(items.length).toBe(2);
    });

    test('shows active/inactive status correctly', () => {
      panel.state.interfaces = mockInterfaces;
      panel.render();

      const statuses = container.querySelectorAll('.interface-status');
      expect(statuses[0].classList.contains('active')).toBe(true);
      expect(statuses[1].classList.contains('inactive')).toBe(true);
    });
  });
});
```

### Code Example: E2E Tests with Playwright

```javascript
// frontend/tests/e2e/node-detail-panel.spec.js

import { test, expect } from '@playwright/test';

test.describe('Node Detail Panel', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app and wait for topology to load
    await page.goto('http://localhost:5173');

    // Assuming a test snapshot is already loaded
    await page.waitForSelector('.topology-svg', { timeout: 10000 });

    // Wait for nodes to render
    await page.waitForSelector('.nodes circle', { timeout: 5000 });
  });

  test('opens detail panel when clicking a node', async ({ page }) => {
    // Click first node
    const firstNode = page.locator('.nodes circle').first();
    await firstNode.click();

    // Panel should slide in
    await expect(page.locator('.node-detail-panel')).toHaveClass(/panel-open/);

    // Panel should be visible
    await expect(page.locator('.node-detail-panel')).toBeVisible();

    // Should show node information
    await expect(page.locator('.panel-header h3')).toBeVisible();
  });

  test('does not open panel when dragging node', async ({ page }) => {
    const firstNode = page.locator('.nodes circle').first();

    // Get node position
    const box = await firstNode.boundingBox();

    // Simulate drag (not click)
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x + box.width / 2 + 50, box.y + box.height / 2 + 50);
    await page.mouse.up();

    // Panel should NOT open
    await expect(page.locator('.node-detail-panel')).not.toHaveClass(/panel-open/);
  });

  test('closes panel when clicking close button', async ({ page }) => {
    // Open panel
    await page.locator('.nodes circle').first().click();
    await expect(page.locator('.node-detail-panel')).toHaveClass(/panel-open/);

    // Click close button
    await page.locator('.panel-close').click();

    // Panel should close
    await expect(page.locator('.node-detail-panel')).not.toHaveClass(/panel-open/);
  });

  test('closes panel when clicking outside', async ({ page }) => {
    // Open panel
    await page.locator('.nodes circle').first().click();
    await expect(page.locator('.node-detail-panel')).toHaveClass(/panel-open/);

    // Click outside panel (on topology canvas)
    await page.locator('.topology-svg').click({ position: { x: 100, y: 100 } });

    // Panel should close
    await expect(page.locator('.node-detail-panel')).not.toHaveClass(/panel-open/);
  });

  test('does not close panel when clicking inside panel', async ({ page }) => {
    // Open panel
    await page.locator('.nodes circle').first().click();
    await expect(page.locator('.node-detail-panel')).toHaveClass(/panel-open/);

    // Click inside panel content
    await page.locator('.panel-content').click();

    // Panel should remain open
    await expect(page.locator('.node-detail-panel')).toHaveClass(/panel-open/);
  });

  test('loads and displays interface list', async ({ page }) => {
    // Open panel
    await page.locator('.nodes circle').first().click();

    // Wait for interfaces to load
    await page.waitForSelector('.interface-item', { timeout: 5000 });

    // Should display interface items
    const interfaceCount = await page.locator('.interface-item').count();
    expect(interfaceCount).toBeGreaterThan(0);

    // Each interface should have name and status
    await expect(page.locator('.interface-item').first()).toContainText(/GigabitEthernet|Ethernet/);
    await expect(page.locator('.interface-status').first()).toBeVisible();
  });

  test('supports keyboard navigation', async ({ page }) => {
    // Open panel
    await page.locator('.nodes circle').first().click();
    await expect(page.locator('.node-detail-panel')).toHaveClass(/panel-open/);

    // Press Escape to close
    await page.keyboard.press('Escape');

    // Panel should close
    await expect(page.locator('.node-detail-panel')).not.toHaveClass(/panel-open/);
  });

  test('traps focus within panel when open', async ({ page }) => {
    // Open panel
    await page.locator('.nodes circle').first().click();

    // Focus should be in panel
    const activeElement = await page.evaluate(() => {
      return document.activeElement.className;
    });
    expect(activeElement).toContain('node-detail-panel');

    // Tab through all focusable elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Focus should still be within panel
    const stillInPanel = await page.evaluate(() => {
      return document.querySelector('.node-detail-panel').contains(document.activeElement);
    });
    expect(stillInPanel).toBe(true);
  });

  test('displays correct node information', async ({ page }) => {
    // Click specific node (if we know test data)
    const firstNode = page.locator('.nodes circle').first();
    await firstNode.click();

    // Check node info fields are present
    await expect(page.locator('.node-info dt:has-text("Hostname")')).toBeVisible();
    await expect(page.locator('.node-info dt:has-text("Type")')).toBeVisible();
    await expect(page.locator('.node-info dt:has-text("Vendor")')).toBeVisible();
    await expect(page.locator('.node-info dt:has-text("Model")')).toBeVisible();
  });

  test('highlights selected node in topology', async ({ page }) => {
    const firstNode = page.locator('.nodes circle').first();

    // Get initial stroke width
    const initialStroke = await firstNode.getAttribute('stroke-width');

    // Click node
    await firstNode.click();

    // Stroke width should increase (selection highlight)
    const selectedStroke = await firstNode.getAttribute('stroke-width');
    expect(parseInt(selectedStroke)).toBeGreaterThan(parseInt(initialStroke));

    // Should have selection class
    await expect(firstNode).toHaveClass(/node-selected/);
  });

  test('handles rapid node switching', async ({ page }) => {
    const nodes = page.locator('.nodes circle');

    // Click first node
    await nodes.nth(0).click();
    await expect(page.locator('.panel-header h3')).toBeVisible();
    const firstHostname = await page.locator('.panel-header h3').textContent();

    // Quickly click second node
    await nodes.nth(1).click();
    await expect(page.locator('.panel-header h3')).toBeVisible();
    const secondHostname = await page.locator('.panel-header h3').textContent();

    // Should show different node
    expect(firstHostname).not.toBe(secondHostname);

    // Panel should still be open
    await expect(page.locator('.node-detail-panel')).toHaveClass(/panel-open/);
  });
});
```

### Mocking D3.js Events in Tests

For unit tests that need to simulate D3 events:

```javascript
// Test helper for creating D3-like events
function createD3Event(type, options = {}) {
  const event = new MouseEvent(type, {
    bubbles: true,
    cancelable: true,
    ...options
  });

  // Add D3-specific properties
  event.defaultPrevented = options.defaultPrevented || false;

  return event;
}

// Usage in tests
test('distinguishes click from drag', () => {
  const clickEvent = createD3Event('click', { defaultPrevented: false });
  const dragEvent = createD3Event('click', { defaultPrevented: true });

  // Click should trigger selection
  handleNodeClick(clickEvent, mockNode);
  expect(panel.state.isOpen).toBe(true);

  // Drag should not trigger selection
  handleNodeClick(dragEvent, mockNode);
  expect(panel.state.isOpen).toBe(false);
});
```

### Integration Testing Strategy

For testing panel + topology interaction:

```javascript
// frontend/tests/integration/topology-panel-integration.test.js

import { createTopologyVisualization } from '../../src/components/TopologyVisualization.js';
import { NodeDetailPanel } from '../../src/components/NodeDetailPanel.js';

describe('Topology + Panel Integration', () => {
  let container, topologyViz, detailPanel;

  beforeEach(() => {
    container = document.createElement('div');
    container.style.width = '800px';
    container.style.height = '600px';
    document.body.appendChild(container);

    // Create both components
    topologyViz = createTopologyVisualization(container, 'test-snapshot');
    detailPanel = new NodeDetailPanel(document.body);

    // Wire them together
    container.addEventListener('nodeSelected', (event) => {
      detailPanel.open(event.detail.node);
    });
  });

  afterEach(() => {
    topologyViz.destroy();
    detailPanel.destroy();
    document.body.removeChild(container);
  });

  test('selecting node opens panel', async () => {
    // Simulate node data load
    const mockNodes = [
      { hostname: 'router-01', device_type: 'router' }
    ];

    // Trigger node selection via topology API
    topologyViz.selectNode(mockNodes[0]);

    // Panel should open
    expect(detailPanel.state.isOpen).toBe(true);
    expect(detailPanel.state.selectedNode.hostname).toBe('router-01');
  });
});
```

### CI/CD Integration

**GitHub Actions workflow for testing:**

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Run unit tests
        run: cd frontend && npm test
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/lcov.info

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install Playwright browsers
        run: cd frontend && npx playwright install --with-deps
      - name: Start backend
        run: |
          cd backend
          python -m venv .venv
          source .venv/bin/activate
          pip install -r requirements.txt
          uvicorn src.main:app --host 0.0.0.0 --port 8000 &
      - name: Start frontend
        run: |
          cd frontend
          npm ci
          npm run dev &
      - name: Wait for services
        run: npx wait-on http://localhost:5173 http://localhost:8000/api/health
      - name: Run E2E tests
        run: cd frontend && npx playwright test
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

---

## Summary of Recommendations

| Topic | Decision | Key Rationale |
|-------|----------|---------------|
| **Panel Component** | Class-based vanilla JS with Proxy state | Modern 2025 patterns, aligns with existing codebase |
| **Event Handling** | Event delegation + click-outside pattern | Best practice for performance and memory |
| **D3 Click Integration** | Check `event.defaultPrevented` | Standard D3 pattern, no library needed |
| **Node Highlighting** | CSS classes + `raise()` for z-index | Clean separation, performant |
| **API Strategy** | Aggregated `/nodes/{hostname}/details` endpoint | Reduced latency, better caching, simpler client |
| **API Caching** | Redis-backed with 5min TTL | FastAPI best practice, significant speedup |
| **Layout** | CSS Grid + fixed overlay panel | Modern standard, no topology resize |
| **Responsive** | Media queries, full-width on mobile | Progressive enhancement approach |
| **Performance (Lists)** | Virtual scrolling for 50+ interfaces | 100x faster render, smooth scrolling |
| **Testing** | Playwright (E2E) + Jest (Unit) | Real browser + fast units, both installed |
| **Accessibility** | ARIA labels + keyboard nav + focus trap | WCAG 2.2 compliance, 2025 standard |

---

## References and Sources

### Vanilla JavaScript Components
- [Building a Side Drawer with Web Standards](https://pixari.dev/building-a-side-drawer-with-web-standards-using-the-dialog-element/)
- [The Vanilla Javascript Component Pattern](https://dev.to/megazear7/the-vanilla-javascript-component-pattern-37la)
- [Vanilla JavaScript Components (Medium)](https://medium.com/bunnyllc/vanilla-js-components-8d20c58b69f4)
- [Modern State Management in Vanilla JavaScript: 2026 Patterns](https://medium.com/@orami98/modern-state-management-in-vanilla-javascript-2026-patterns-and-beyond-ce00425f7ac5)
- [State Management in Vanilla JS: 2026 Trends](https://medium.com/@chirag.dave/state-management-in-vanilla-js-2026-trends-f9baed7599de)

### Click-Outside Pattern
- [Detecting clicks outside of an element with vanilla JS](https://gomakethings.com/detecting-clicks-outside-of-an-element-with-vanilla-js/)
- [Closing on outside click](https://kittygiraudel.com/2021/03/18/close-on-outside-click/)
- [How to Close a Modal Window when users Click Outside it](https://techstacker.com/close-modal-click-outside-vanilla-javascript/)

### D3.js Click and Drag
- [D3.js Click vs Drag (Observable)](https://observablehq.com/@d3/click-vs-drag)
- [End of drag event also fires click - D3 GitHub Issue #1445](https://github.com/d3/d3/issues/1445)
- [force.drag lets click event propagate - D3 GitHub Issue #1446](https://github.com/d3/d3/issues/1446)
- [z-index or "bring-to-top" on svg elements - D3 GitHub Issue #252](https://github.com/d3/d3/issues/252)

### FastAPI Best Practices
- [FastAPI Best Practices GitHub](https://github.com/zhanymkanov/fastapi-best-practices)
- [FastAPI Best Practices: Complete Guide (Medium)](https://medium.com/@abipoongodi1211/fastapi-best-practices-a-complete-guide-for-building-production-ready-apis-bb27062d7617)
- [Scaling a FastAPI Application (Medium)](https://medium.com/@aahana.khanal11/scaling-a-fastapi-application-handling-multiple-requests-at-once-e5c128720c95)
- [FastAPI + Redis example](https://python-dependency-injector.ets-labs.org/examples/fastapi-redis.html)
- [Caching with Redis: Boost Your FastAPI Applications (Medium)](https://medium.com/@mahdijafaridev/caching-with-redis-boost-your-fastapi-applications-with-speed-and-scalability-af45626a57f3)
- [Using Redis with FastAPI](https://redis.io/learn/develop/python/fastapi)

### CSS Layout (2025)
- [Modern CSS Layout Techniques: Flexbox, Grid, and Subgrid (2025 Guide)](https://dev.to/frontendtoolstech/modern-css-layout-techniques-flexbox-grid-and-subgrid-2025-guide-112f)
- [Mastering Advanced CSS Grid and Flexbox](https://dev.to/sharique_siddiqui_8242dad/mastering-advanced-css-grid-and-flexbox-techniques-for-responsive-layouts-5fa8)
- [Building a Responsive Layout in 2025: CSS Grid vs Flexbox](https://dev.to/smriti_webdev/building-a-responsive-layout-in-2025-css-grid-vs-flexbox-vs-container-queries-234m)
- [Left Sidebar 2-Column Responsive Layout](https://matthewjamestaylor.com/left-sidebar-layout)

### Performance - Virtual Scrolling
- [Rendering Large Lists in Vanilla JS: List Virtualization](https://tghosh.hashnode.dev/rendering-large-lists-in-vanilla-js-list-virtualization)
- [List Virtualization: How to Smoothly Scroll Through 10,000 Items (Medium)](https://medium.com/@ethanhaller02/list-virtualization-how-to-smoothly-scroll-through-10-000-items-cad39bfa7f3e)
- [Virtual Scrolling: Boost Web App Performance](https://jsschools.com/web_dev/virtual-scrolling-boost-web-app-performance-with-/)
- [Virtual list in vanilla JavaScript](https://sergimansilla.com/blog/virtual-scrolling/)
- [HyperList GitHub](https://github.com/tbranyen/hyperlist)

### Accessibility (WCAG 2.2 / 2025)
- [ARIA Labels for Web Accessibility: Complete 2025 Implementation Guide](https://www.allaccessible.org/blog/implementing-aria-labels-for-web-accessibility)
- [Accessible nav drawer disclosure widgets](https://www.makethingsaccessible.com/guides/accessible-nav-drawer-disclosure-widgets/)
- [Developing a Keyboard Interface - W3C WAI](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)
- [ARIA: navigation role - MDN](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/navigation_role)

### Testing
- [How to use Playwright for unit testing](https://gomakethings.com/how-to-use-playwright-for-unit-testing/)
- [DOM Manipulation - Jest](https://jestjs.io/docs/tutorial-jquery)
- [Testing Vanilla JavaScript](https://vanillajsguides.com/testing/)
- [jest-playwright GitHub](https://github.com/playwright-community/jest-playwright)

---

**End of Research Document**
