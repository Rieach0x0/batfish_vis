# Batfish Visualization Frontend

Interactive web interface for Batfish network topology visualization and configuration verification.

## Requirements

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000/api
```

### 3. Run the development server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Key Technologies

- **D3.js v7**: Data visualization library for topology graphs
- **Vite**: Fast build tool and development server
- **JavaScript ES2022**: Modern JavaScript

## Features

- **Snapshot Management**: Upload and manage Batfish snapshots
- **Topology Visualization**: Interactive D3.js force-directed graph
  - Zoom and pan
  - Node dragging
  - Device detail inspection
  - Hover information display (Feature 002)
  - SVG/PNG export
- **Configuration Verification**: Execute Batfish verification queries
  - Reachability analysis with flow traces
  - ACL testing with permit/deny results
  - Routing table inspection

## Project Structure

```
frontend/
├── src/
│   ├── components/       # React-like UI components
│   │   ├── SnapshotUpload.js
│   │   ├── SnapshotManager.js
│   │   ├── TopologyVisualization.js
│   │   └── VerificationPanel.js
│   ├── services/         # API client services
│   │   ├── apiClient.js
│   │   ├── snapshotService.js
│   │   ├── topologyService.js
│   │   └── verificationService.js
│   ├── utils/            # Utility functions
│   │   ├── d3LayoutEngine.js
│   │   └── topologyExporter.js
│   ├── main.js           # Application entry point
│   └── index.html        # HTML template
└── tests/
    ├── unit/             # Component unit tests
    └── e2e/              # End-to-end tests
```

## Development

### Run tests

```bash
npm test
```

### Run E2E tests

```bash
npm run test:e2e
```

### Linting

```bash
npm run lint
```

### Code formatting

```bash
npm run format
```

### Build for production

```bash
npm run build
```

## Component Architecture

The application follows a modular component-based architecture:

### Core Components

**SnapshotUpload** (`src/components/SnapshotUpload.js`)
- File selection UI with drag-and-drop support
- Multipart file upload to backend
- Progress indicator during upload
- Parse error display
- **API**: `createSnapshotUpload(container, onSnapshotCreated)`

**SnapshotManager** (`src/components/SnapshotManager.js`)
- Snapshot list with active selection
- Snapshot metadata display (name, devices, created date)
- Delete with confirmation dialog
- **API**: `createSnapshotManager(container, onSnapshotSelected)`

**TopologyVisualization** (`src/components/TopologyVisualization.js`)
- D3.js v7 force-directed layout
- Interactive features: zoom, pan, drag
- Node hover displays device info (hostname, vendor, type, interfaces)
- Link hover displays connection info (source/target, interfaces, IPs)
- Export to SVG/PNG
- **API**: `createTopologyVisualization(container, snapshotName, networkName)`

**VerificationPanel** (`src/components/VerificationPanel.js`)
- Query type selector (Reachability / ACL / Routing)
- Dynamic form generation based on query type
- Result visualization:
  - Flow traces with hop-by-hop paths
  - ACL results with permit/deny actions
  - Routing table with protocols and metrics
- Query history (last 10 queries)
- **API**: `createVerificationPanel(container, snapshotName, networkName)`

### Service Layer

**apiClient** (`src/services/apiClient.js`)
- Base HTTP client with error handling
- Methods: `get()`, `post()`, `postForm()`, `delete()`
- Automatic JSON parsing
- Error response handling

**snapshotService** (`src/services/snapshotService.js`)
- `createSnapshot(name, network, files)` - Upload configuration files
- `listSnapshots(network?)` - Get all snapshots
- `getSnapshot(name, network?)` - Get snapshot details
- `deleteSnapshot(name, network?)` - Remove snapshot

**topologyService** (`src/services/topologyService.js`)
- `getNodes(snapshot, network?)` - Get devices
- `getEdges(snapshot, network?)` - Get Layer 3 links
- `getInterfaces(snapshot, network?, hostname?)` - Get interfaces
- `getTopology(snapshot, network?)` - Get complete graph

**verificationService** (`src/services/verificationService.js`)
- `verifyReachability(snapshot, srcIp, dstIp, network?, srcNode?)`
- `verifyACL(snapshot, filterName, srcIp, dstIp, network?, protocol?)`
- `verifyRouting(snapshot, network?, nodes?, networkFilter?)`

## D3.js Topology Customization

The force-directed layout parameters are configured in `TopologyVisualization.js`:

```javascript
// Force simulation parameters
d3.forceSimulation(nodes)
  .force('link', d3.forceLink(links).id(d => d.id).distance(150))
  .force('charge', d3.forceManyBody().strength(-300))
  .force('center', d3.forceCenter(width / 2, height / 2))
  .force('collision', d3.forceCollide().radius(40))
```

**Customization tips**:
- **distance**: Increase for more spacing between connected nodes
- **strength**: More negative = stronger repulsion between nodes
- **radius**: Collision detection radius (prevents node overlap)

## Troubleshooting

### Backend API not reachable

1. Ensure backend is running: `curl http://localhost:8000/api/health`
2. Check CORS settings in backend
3. Verify `VITE_API_URL` in `.env`

### D3.js visualization not rendering

1. Check browser console for errors
2. Verify snapshot has devices: `GET /api/topology/nodes?snapshot=<name>`
3. Check network connectivity in browser DevTools

### Build fails

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```
