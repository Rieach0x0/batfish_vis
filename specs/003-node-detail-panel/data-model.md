# Data Model: Node Detail Panel

**Feature**: 003-node-detail-panel
**Date**: 2025-12-23
**Source**: Extracted from [spec.md](./spec.md) Key Entities section

---

## Overview

This document defines the data structures used to represent node details, interfaces, and device metadata for the Node Detail Panel feature. All entities derive from Batfish snapshot analysis and are consumed by the frontend detail panel component.

---

## Entities

### 1. NodeDetail (Aggregated Response)

**Purpose**: Complete node information returned by `/topology/nodes/{hostname}/details` endpoint.

**Attributes**:

| Attribute | Type | Required | Description | Validation Rules | Source |
|-----------|------|----------|-------------|------------------|--------|
| `hostname` | `string` | Yes | Network device hostname | Non-empty string, max 255 chars | Batfish node properties |
| `device_type` | `string \| null` | No | Device type (router, switch, firewall, host, unknown) | Enum: `router`, `switch`, `firewall`, `host`, `unknown`, or `null` | Batfish device config analysis |
| `vendor` | `string \| null` | No | Device vendor/manufacturer | Max 100 chars or `null` | Batfish vendor detection |
| `model` | `string \| null` | No | Device hardware model | Max 100 chars or `null` | Batfish device properties |
| `os_version` | `string \| null` | No | Operating system version | Max 100 chars or `null` | Batfish OS detection (from config) |
| `config_format` | `string \| null` | No | Configuration file format | Enum: `CISCO_IOS`, `JUNIPER`, `ARISTA`, etc. or `null` | Batfish config parser |
| `status` | `string` | Yes | Operational status | Enum: `active`, `inactive`, `unknown` | Derived from interface states (default: `unknown`) |
| `interface_count` | `integer` | Yes | Total number of interfaces | >= 0 | Count of `interfaces` array |
| `interfaces` | `Interface[]` | Yes | Array of network interfaces | Can be empty array | Batfish interface properties |
| `metadata` | `DeviceMetadata` | Yes | Additional device metadata | Always present (may contain nulls) | Aggregated from Batfish queries |

**Relationships**:
- **Has Many**: `Interface` (one-to-many via `interfaces` array)
- **Embeds**: `DeviceMetadata` (composition)

**State Transitions**:
- N/A (read-only data structure)

**Example**:
```json
{
  "hostname": "router-01",
  "device_type": "router",
  "vendor": "Cisco",
  "model": "ISR4451",
  "os_version": "IOS XE 17.3.4a",
  "config_format": "CISCO_IOS",
  "status": "active",
  "interface_count": 12,
  "interfaces": [
    {
      "name": "GigabitEthernet0/0/0",
      "active": true,
      "ip_addresses": ["192.168.1.1/24"],
      "description": "Uplink to core",
      "vlan": null,
      "bandwidth_mbps": 1000,
      "mtu": 1500
    },
    {
      "name": "GigabitEthernet0/0/1",
      "active": false,
      "ip_addresses": [],
      "description": null,
      "vlan": null,
      "bandwidth_mbps": null,
      "mtu": 1500
    }
  ],
  "metadata": {
    "snapshot_name": "prod_network_2025-12-23",
    "last_updated": "2025-12-23T10:15:32Z",
    "config_file_path": "/snapshots/prod_network/configs/router-01.cfg"
  }
}
```

---

### 2. Interface

**Purpose**: Represents a network interface on a device.

**Attributes**:

| Attribute | Type | Required | Description | Validation Rules | Source |
|-----------|------|----------|-------------|------------------|--------|
| `name` | `string` | Yes | Interface name/identifier | Non-empty, max 100 chars (e.g., "GigabitEthernet0/0/0", "eth0", "Vlan10") | Batfish interface name |
| `active` | `boolean` | Yes | Whether interface is administratively up | `true` or `false` | Batfish interface active status |
| `ip_addresses` | `string[]` | Yes | IP addresses in CIDR notation | Array of valid IPv4/IPv6 CIDR strings (e.g., "192.168.1.1/24"), can be empty | Batfish interface IPs |
| `description` | `string \| null` | No | Interface description/comment | Max 255 chars or `null` | Batfish interface description |
| `vlan` | `integer \| null` | No | VLAN ID if applicable | Integer 1-4094 or `null` | Batfish VLAN assignment |
| `bandwidth_mbps` | `integer \| null` | No | Bandwidth in Mbps | Positive integer or `null` | Batfish interface bandwidth |
| `mtu` | `integer \| null` | No | Maximum transmission unit | Integer 68-9216 or `null` | Batfish interface MTU |

**Relationships**:
- **Belongs To**: `NodeDetail` (many-to-one)

**Validation Rules**:
- At least one of `ip_addresses`, `vlan`, or `description` should be present for meaningful display (soft validation)
- If `active` is `false` and `ip_addresses` is empty, interface is considered "unconfigured"

**Display Rules**:
- **Active interfaces**: Display with green indicator, bold text
- **Inactive interfaces**: Display with gray text, dimmed
- **No IP addresses**: Show "No IP assigned" instead of empty list
- **Large interface lists (100+)**: Use virtual scrolling for performance

---

### 3. DeviceMetadata

**Purpose**: Additional context about the device and snapshot.

**Attributes**:

| Attribute | Type | Required | Description | Validation Rules | Source |
|-----------|------|----------|-------------|------------------|--------|
| `snapshot_name` | `string` | Yes | Batfish snapshot identifier | Non-empty string | Batfish session context |
| `last_updated` | `string` | Yes | ISO 8601 timestamp of snapshot initialization | Valid ISO 8601 datetime | Batfish snapshot metadata |
| `config_file_path` | `string \| null` | No | Path to device config file in snapshot | Valid file path or `null` | Batfish file system |

**Relationships**:
- **Embedded In**: `NodeDetail` (composition)

**Usage**:
- Displayed in panel footer or debug mode
- Used for traceability (linking detail panel to source snapshot)
- Helps users understand data freshness

---

### 4. IPAddress (Value Object)

**Purpose**: Represents an IP address with subnet information.

**Attributes**:

| Attribute | Type | Required | Description | Validation Rules |
|-----------|------|----------|-------------|------------------|
| `address` | `string` | Yes | IP address in CIDR notation | Valid IPv4 (e.g., "192.168.1.1/24") or IPv6 (e.g., "2001:db8::1/64") |
| `network` | `string` | Derived | Network address (extracted from CIDR) | Calculated from `address` |
| `prefix_length` | `integer` | Derived | Subnet prefix length | Extracted from CIDR notation |
| `type` | `string` | Derived | Address type | Enum: `ipv4`, `ipv6` |

**Note**: This is a **value object** - immutable representation derived from the `ip_addresses` strings in the `Interface` model. Not stored separately in the backend; calculated on-demand in the frontend for display purposes.

**Example Parsing**:
```javascript
// Input: "192.168.1.1/24"
{
  address: "192.168.1.1/24",
  network: "192.168.1.0",
  prefix_length: 24,
  type: "ipv4"
}
```

---

## Data Flow

### Backend Data Flow

```
Batfish Snapshot
    ↓
[BatfishService.get_node_properties(hostname)]
    ↓ (device metadata: type, vendor, model, config_format)
[BatfishService.get_interfaces(hostname)]
    ↓ (interface list with IPs, status, descriptions)
[TopologyService.get_node_details(snapshot, hostname)]
    ↓ (aggregates both queries + derives status from interface states)
[NodeDetail Model] (Pydantic validation)
    ↓
API Response: GET /topology/nodes/{hostname}/details
```

### Frontend Data Flow

```
User clicks node in D3.js topology
    ↓
[TopologyVisualization] dispatches "node:selected" event
    ↓
[NodeDetailPanel] receives event with hostname
    ↓
[topologyService.fetchNodeDetails(snapshot, hostname)]
    ↓
API call: GET /topology/nodes/{hostname}/details
    ↓
[NodeDetailPanel.render(nodeDetail)]
    ↓
DOM update: populate panel with hostname, metadata, interface list
```

---

## Validation Rules Summary

### Backend Validation (Pydantic Models)

**NodeDetail**:
- `hostname`: Required, non-empty string
- `interface_count`: Must match `len(interfaces)`
- `status`: Must be one of `active`, `inactive`, `unknown`

**Interface**:
- `name`: Required, non-empty string
- `active`: Required boolean
- `ip_addresses`: Must be array (can be empty)
- `vlan`: If present, must be 1-4094

**DeviceMetadata**:
- `snapshot_name`: Required, non-empty string
- `last_updated`: Required, valid ISO 8601 datetime

### Frontend Validation (Pre-Display)

- Check for `null`/missing metadata fields → display "N/A"
- Empty `ip_addresses` array → display "No IP assigned"
- Empty `interfaces` array → display "No interfaces configured" message
- Invalid CIDR notation → log warning, display raw string

---

## Edge Cases & Error Handling

### 1. Node with No Interfaces
**Scenario**: Device has no interfaces configured (rare but possible for placeholder configs)
**Handling**:
- Backend: Return `interfaces: []`, `interface_count: 0`
- Frontend: Display message "No interfaces configured for this device"

### 2. Interface with No IP Addresses
**Scenario**: Interface exists but has no IP assignments (common for access ports)
**Handling**:
- Backend: Return `ip_addresses: []`
- Frontend: Display "No IP assigned" for that interface

### 3. Partial Metadata (vendor/model/OS unknown)
**Scenario**: Batfish cannot determine vendor or OS from config
**Handling**:
- Backend: Set fields to `null`
- Frontend: Display "N/A" or "Unknown" for null fields

### 4. Large Interface Count (100+)
**Scenario**: Core switches with 48+ ports, large routers
**Handling**:
- Backend: Return all interfaces (no pagination at API level)
- Frontend: Implement virtual scrolling (render only visible 20-30 items, scroll to render more)

### 5. Rapid Node Switching
**Scenario**: User clicks multiple nodes in quick succession
**Handling**:
- Frontend: Cancel pending API requests using AbortController
- Only render the most recent selection's data

### 6. API Error (Batfish unavailable, invalid hostname)
**Scenario**: API returns 404, 500, or network error
**Handling**:
- Frontend: Display error message in panel: "Unable to load node details. Please try again."
- Log error with hostname and snapshot context for debugging

---

## Performance Considerations

### Caching Strategy
- **Backend**: Cache `NodeDetail` responses for 5 minutes (TTL) using Redis
  - Cache key: `node_detail:{snapshot_name}:{hostname}`
  - Invalidate on new snapshot upload
- **Frontend**: No client-side caching (rely on HTTP cache headers from backend)

### Lazy Loading
- Interfaces are fetched only when node is clicked (not pre-loaded)
- Avoids unnecessary API calls for nodes user doesn't inspect

### Rendering Optimization
- **Virtual Scrolling**: For interface lists >50 items, render only visible portion
- **Debouncing**: Debounce rapid click events (100ms threshold)

---

## Testing Considerations

### Unit Tests (Backend)
- Test `NodeDetail` model validation with valid/invalid data
- Test `get_node_details()` service method with mocked Batfish responses
- Test edge cases: null metadata, empty interfaces, missing fields

### Integration Tests (Backend)
- Test `/topology/nodes/{hostname}/details` endpoint with real Batfish snapshot
- Verify response schema matches `NodeDetail` model
- Test error cases: invalid hostname, snapshot not found

### Unit Tests (Frontend)
- Test `NodeDetailPanel` rendering with mock data
- Test rendering edge cases: null metadata, empty interfaces, 100+ interfaces
- Test event handlers: close button, click outside, node switch

### E2E Tests (Playwright)
- Test full workflow: load topology → click node → panel opens → verify data displayed
- Test node switching: click node A → click node B → verify panel updates
- Test close mechanisms: close button, click outside, toggle (click same node)

---

## Future Enhancements (Out of Scope for Phase 1)

- **Interface Filtering**: Search/filter interfaces by name or IP
- **Configuration Preview**: Show relevant config snippets for selected interface
- **Real-Time Status**: WebSocket updates for interface up/down events
- **Multi-Node Comparison**: Side-by-side comparison of multiple nodes
- **Export**: Export node details to JSON/CSV

---

**Document Version**: 1.0
**Last Updated**: 2025-12-23
