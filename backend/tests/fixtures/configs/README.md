# Test Fixture Configurations

Sample network configuration files for testing Batfish snapshot creation and topology visualization.

## Topology

```
┌──────────────────┐
│ core-router-1    │  Cisco IOS Router
│ 10.0.0.1         │
│ (Cisco)          │
└────┬────────┬────┘
     │        │
     │        │ 192.168.1.4/30
     │        │
     │        └──────────────┐
     │                       │
     │ 192.168.1.0/30       │
     │                       │
┌────┴────────────────┐  ┌──┴──────────────┐
│ distribution-       │  │ edge-router-3   │
│ switch-2            │  │ 10.0.0.3        │
│ 10.0.0.2            │  │ (Juniper)       │
│ (Cisco)             │  └─────────────────┘
└──────┬──────────────┘
       │
       │ 10.0.100.0/24
       │
  ┌────┴────────────┐
  │ access-switch-4 │
  │ 10.0.0.4        │
  │ (Arista)        │
  └─────────────────┘
```

## Devices

### core-router-1 (Cisco IOS)
- **File**: `cisco-router1.cfg`
- **Vendor**: Cisco IOS
- **Type**: Router
- **Interfaces**:
  - GigabitEthernet0/0/1: 192.168.1.1/30 → distribution-switch-2
  - GigabitEthernet0/0/2: 192.168.1.5/30 → edge-router-3
  - Loopback0: 10.0.0.1/32
- **Routing**: OSPF Area 0
- **ACL**: OUTSIDE-IN (denies SSH/Telnet to 10.0.1.50)

### distribution-switch-2 (Cisco IOS)
- **File**: `cisco-switch2.cfg`
- **Vendor**: Cisco IOS
- **Type**: Switch (Layer 3)
- **Interfaces**:
  - TenGigabitEthernet1/0/24: 192.168.1.2/30 → core-router-1
  - Vlan100: 10.0.100.1/24 (Data VLAN)
  - Loopback0: 10.0.0.2/32
- **Routing**: OSPF Area 0

### edge-router-3 (Juniper JunOS)
- **File**: `juniper-router3.conf`
- **Vendor**: Juniper JunOS
- **Type**: Router
- **Interfaces**:
  - ge-0/0/0.0: 192.168.1.6/30 → core-router-1
  - lo0.0: 10.0.0.3/32
- **Routing**: OSPF Area 0

### access-switch-4 (Arista EOS)
- **File**: `arista-switch4.cfg`
- **Vendor**: Arista EOS
- **Type**: Switch (Layer 3)
- **Interfaces**:
  - Ethernet1: 10.0.100.10/24 → distribution-switch-2
  - Vlan100: 10.0.100.254/24
  - Loopback0: 10.0.0.4/32
- **Routing**: OSPF Area 0

## Expected Batfish Snapshot Results

When creating a snapshot from these configurations:

- **Device Count**: 4 devices
- **Parse Status**: All files should parse successfully
- **Layer 3 Edges**: 2 edges
  - core-router-1 ↔ distribution-switch-2
  - core-router-1 ↔ edge-router-3
- **OSPF**: All devices in Area 0
- **Reachability**: All loopbacks should be reachable

## Usage

```bash
# Create snapshot using these configs
curl -X POST http://localhost:8000/api/snapshots \
  -F "snapshotName=test-snapshot" \
  -F "networkName=test-network" \
  -F "configFiles=@cisco-router1.cfg" \
  -F "configFiles=@cisco-switch2.cfg" \
  -F "configFiles=@juniper-router3.conf" \
  -F "configFiles=@arista-switch4.cfg"
```
