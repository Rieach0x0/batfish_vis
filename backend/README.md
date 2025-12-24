# Batfish Visualization Backend

Python FastAPI backend for Batfish network configuration analysis and visualization.

## Requirements

- Python 3.11 or higher
- Batfish container v2025.07.07 running on port 9996

## Setup

### 1. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Batfish container

```bash
docker run -d \
  --name batfish \
  -p 9996:9996 \
  batfish/allinone:v2025.07.07
```

### 4. Configure environment

Create a `.env` file in the backend directory:

```env
BATFISH_HOST=localhost
BATFISH_PORT=9996
LOG_LEVEL=INFO
```

### 5. Run the development server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### API Endpoints

#### Health Check
- **GET** `/api/health` - Check Batfish container connectivity
  - Returns: `{ status, batfishVersion, apiVersion }`

#### Snapshot Management
- **POST** `/api/snapshots` - Create a new snapshot from configuration files
  - Body: `multipart/form-data` with `snapshotName`, `networkName`, `configFiles[]`
  - Returns: `Snapshot` object with parse errors if any
- **GET** `/api/snapshots` - List all snapshots
  - Query: `network` (optional)
  - Returns: Array of `Snapshot` objects
- **GET** `/api/snapshots/{snapshotName}` - Get snapshot details
  - Params: `snapshotName`, `network` (optional)
  - Returns: `Snapshot` object
- **DELETE** `/api/snapshots/{snapshotName}` - Delete a snapshot
  - Params: `snapshotName`, `network` (optional)
  - Returns: `{ message, deleted }`

#### Topology Visualization
- **GET** `/api/topology/nodes` - Get all devices in snapshot
  - Query: `snapshot` (required), `network` (optional)
  - Returns: Array of `Device` objects
- **GET** `/api/topology/nodes/{hostname}/details` - Get detailed node information (Feature 003)
  - Path: `hostname` (required)
  - Query: `snapshot` (required), `network` (optional)
  - Returns: `NodeDetail` object with device metadata, interfaces, and IP addresses
- **GET** `/api/topology/edges` - Get Layer 3 edges
  - Query: `snapshot` (required), `network` (optional)
  - Returns: Array of `Edge` objects
- **GET** `/api/topology/interfaces` - Get network interfaces
  - Query: `snapshot` (required), `network` (optional), `hostname` (optional)
  - Returns: Array of `Interface` objects
- **GET** `/api/topology` - Get complete topology (nodes + edges)
  - Query: `snapshot` (required), `network` (optional)
  - Returns: `{ nodes, edges }`

#### Configuration Verification
- **POST** `/api/verification/reachability` - Verify network reachability
  - Body: `{ snapshot, src_ip, dst_ip, network?, src_node? }`
  - Returns: `VerificationResult` with flow traces
- **POST** `/api/verification/acl` - Test ACL/filter rules
  - Body: `{ snapshot, filter_name, src_ip, dst_ip, network?, protocol? }`
  - Returns: `VerificationResult` with ACL match results
- **POST** `/api/verification/routing` - Query routing tables
  - Body: `{ snapshot, network?, nodes?, network_filter? }`
  - Returns: `VerificationResult` with route entries

### Data Models

#### NodeDetail (Feature 003)
```python
{
  "hostname": str,              # Device hostname
  "device_type": str | None,    # Device type (router, switch, firewall, etc.)
  "vendor": str | None,         # Vendor name (Cisco, Juniper, etc.)
  "model": str | None,          # Hardware model
  "os_version": str | None,     # Operating system version
  "status": str,                # Device status (active, inactive, unknown)
  "interfaces": [               # List of interfaces
    {
      "name": str,              # Interface name
      "active": bool,           # Interface status
      "ip_addresses": [str],    # List of IP addresses (CIDR format)
      "description": str | None,
      "vlan": int | None,
      "bandwidth_mbps": float | None,
      "mtu": int | None
    }
  ],
  "interface_count": int,       # Total number of interfaces
  "metadata": {
    "snapshot_name": str,
    "network_name": str,
    "last_updated": str         # ISO 8601 timestamp
  }
}
```

## Key Technologies

- **FastAPI 0.109+**: Modern Python web framework
- **pybatfish v2025.07.07**: Batfish Python client library
- **Uvicorn**: ASGI server

## Project Structure

```
backend/
├── src/
│   ├── api/              # REST API endpoints
│   ├── services/         # Business logic and Batfish integration
│   ├── models/           # Pydantic data models
│   ├── middleware/       # Error handling, logging
│   ├── utils/            # Utility functions
│   └── main.py           # FastAPI application
└── tests/
    ├── contract/         # API contract tests
    ├── integration/      # Integration tests
    ├── unit/             # Unit tests
    └── fixtures/         # Test data
```

## Development

### Run tests

```bash
pytest
```

### Code formatting

```bash
black src/ tests/
```

### Linting

```bash
pylint src/
```

## Troubleshooting

### Batfish container not reachable

**Symptom**: API returns `503 Service Unavailable` with `BATFISH_UNREACHABLE`

**Solutions**:
```bash
# Check if container is running
docker ps | grep batfish

# Start Batfish container if not running
docker run -d --name batfish -p 9996:9996 batfish/allinone:v2025.07.07

# Check container logs
docker logs batfish

# Test connectivity
curl http://localhost:9996/v2/version
```

### Configuration parse errors

**Symptom**: Snapshot created with `parseErrors` array populated

**Solutions**:
1. Verify configuration files are from supported vendors (Cisco IOS, Juniper JunOS, Arista EOS, Palo Alto)
2. Check file encoding is UTF-8 or ASCII
3. Ensure configuration files are complete (not truncated)
4. Review Batfish grammar support: https://github.com/batfish/batfish/tree/master/projects/batfish/src/main/antlr4/org/batfish/grammar

### Verification query timeout

**Symptom**: Queries take too long or return `TIMEOUT` status

**Solutions**:
1. Increase Batfish container resources: `docker run --cpus=4 --memory=8g ...`
2. Reduce network size (split large snapshots into smaller ones)
3. Query specific nodes instead of all nodes: `nodes=["router1", "router2"]`

### Port already in use

Change the port in the uvicorn command:

```bash
uvicorn src.main:app --reload --port 8001
```

Update frontend Vite proxy configuration in `frontend/vite.config.js`:
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8001',  // Changed port
    changeOrigin: true,
  },
}
```
