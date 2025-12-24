# Implementation Plan: Node Detail Panel

**Branch**: `003-node-detail-panel` | **Date**: 2025-12-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-node-detail-panel/spec.md`

## Summary

Implement an interactive detail panel that displays comprehensive node information when users click on network topology nodes. The panel shows hostname, interfaces, IP addresses, and device metadata (type, vendor, OS version, status). Users can switch between nodes, and close the panel via button or clicking outside.

**Technical Approach**: Vanilla JavaScript component integrated with existing D3.js topology visualization, leveraging existing FastAPI endpoints (`/topology/interfaces`, `/topology/nodes`) to fetch detailed node data on click.

## Technical Context

**Language/Version**: Python 3.11 (backend), JavaScript ES2022 (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.109.0, pybatfish 2025.7.7.2423, Uvicorn 0.25.0
- Frontend: D3.js v7.8.5, Vite 4.5.0 (vanilla JavaScript, no framework)
**Storage**: Batfish internal storage (snapshot data), filesystem (temporary config files)
**Testing**:
- Backend: pytest 7.4.3, pytest-asyncio 0.21.1, pytest-cov 4.1.0
- Frontend: Jest 29.7.0, @testing-library/dom, Playwright 1.40.1 (E2E)
**Target Platform**: Web application (Linux backend via WSL2, browser frontend)
**Project Type**: Web (frontend + backend)
**Performance Goals**:
- Panel opens within 1 second of node click (SC-001)
- Supports nodes with up to 100 interfaces without lag (SC-004)
- Smooth transitions when switching between nodes (SC-002)
**Constraints**:
- Panel must not overlap topology visualization (FR-006)
- Must handle partial/missing device metadata gracefully (FR-013)
- Support rapid node switching without race conditions
**Scale/Scope**:
- Single-page application feature
- ~2 new frontend components (NodeDetailPanel, integration with TopologyVisualization)
- API endpoint enhancement for node details aggregation
- ~500-800 lines of new code (300 frontend, 200 backend, 200 tests)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Batfish-First Integration ✅ PASS

**Evaluation**: Feature relies exclusively on Batfish-derived data via existing endpoints:
- `/topology/nodes` (provides hostname, device type, vendor, model)
- `/topology/interfaces` (provides interface names, IP addresses, status)
- No custom network analysis or config parsing

**Compliance**: All device metadata comes from Batfish's snapshot analysis. The detail panel is a pure presentation layer consuming Batfish's authoritative data.

### II. Topology Visualization as Contract ✅ PASS

**Evaluation**: Feature enhances but does not modify topology visualization contract.
- Node selection uses existing D3.js node data (already computed by Batfish)
- Detail panel displays supplementary information; topology graph remains accurate
- No transformation of Batfish topology queries

**Compliance**: Visualization integrity maintained. Panel is additive, not transformative.

### III. Configuration Validation is Non-Negotiable ✅ PASS

**Evaluation**: Feature does not perform any validation logic.
- Pure data display component
- No reachability checks, ACL analysis, or policy validation
- If metadata includes status (e.g., "interface active"), it's sourced from Batfish

**Compliance**: No custom validation. All displayed data originates from Batfish analysis.

### IV. Test-First Verification Workflow ⚠️ CONDITIONAL PASS

**Evaluation**: Constitution requires TDD with realistic config fixtures.
- **Gap**: Current codebase has test frameworks configured but zero tests written
- **Feature Plan**: Phase 1 includes comprehensive test suite (unit + integration)
- **Fixtures**: Will use existing network snapshots in `networks/` directory

**Compliance Path**:
1. Write tests before implementation (Red-Green-Refactor)
2. Backend: Test API endpoint responses with fixture snapshots
3. Frontend: Test panel rendering, node click handling, close interactions
4. Integration: Test full click-to-display workflow with real Batfish data

**Status**: PASS with commitment to TDD in implementation phase. Must ensure tests written BEFORE feature code.

### V. Observability & Debuggability ✅ PASS

**Evaluation**: Feature will leverage existing logging infrastructure.
- Backend has structured logging (`src/utils/logger.py`)
- API calls already logged with snapshot name, timestamp, response time
- Frontend can log panel state transitions (open, switch node, close)

**Planned Additions**:
- Log node click events with hostname and snapshot context
- Log API fetch timing for `/topology/interfaces?hostname={X}`
- Debug mode: Display raw Batfish response data in panel footer (toggle)

**Compliance**: Follows existing observability patterns. Debug mode satisfies "raw data" requirement.

### Constitution Check Summary

**Status**: ✅ **PASS** - All principles satisfied

- **Batfish-First**: ✅ Exclusively uses Batfish data via API
- **Topology Contract**: ✅ Additive feature, no topology transformation
- **No Custom Validation**: ✅ Pure presentation layer
- **Test-First**: ⚠️ Committed to TDD; tests before code
- **Observability**: ✅ Leverages existing logging + debug mode

**Proceed to Phase 0**: ✅ Approved

---

## Post-Phase 1 Constitution Re-evaluation

*Conducted after completing research, data model, and API contracts.*

### Re-evaluation Results

**I. Batfish-First Integration**: ✅ **CONFIRMED PASS**
- Designed aggregated endpoint `/topology/nodes/{hostname}/details` calls only Batfish APIs
- `get_node_details()` service method uses `BatfishService.get_node_properties()` and `BatfishService.get_interfaces()`
- No custom parsing or analysis logic introduced
- **Verdict**: Fully compliant. Design maintains Batfish as single source of truth.

**II. Topology Visualization as Contract**: ✅ **CONFIRMED PASS**
- D3.js integration adds click handler to existing node elements
- No modification to topology data or layout algorithm
- Detail panel is separate UI component consuming Batfish data
- **Verdict**: Fully compliant. Visualization contract preserved.

**III. Configuration Validation is Non-Negotiable**: ✅ **CONFIRMED PASS**
- NodeDetailPanel is pure presentation layer
- All validation (interface active status, IP parsing) comes from Batfish
- No custom validation logic in frontend or backend
- **Verdict**: Fully compliant. Zero custom validation.

**IV. Test-First Verification Workflow**: ✅ **UPGRADED TO FULL PASS**
- Quickstart guide demonstrates TDD with test-first examples
- Backend unit tests written before service implementation (Red-Green-Refactor)
- Frontend unit tests for component rendering and interactions
- E2E Playwright tests for full workflow
- **Verdict**: Fully compliant. TDD workflow documented and required.

**V. Observability & Debuggability**: ✅ **CONFIRMED PASS**
- Logging plan includes node click events, API timing, snapshot context
- Debug mode design (toggle to show raw Batfish JSON in panel footer)
- Leverages existing structured logging infrastructure
- **Verdict**: Fully compliant. Observability enhanced as planned.

### Final Constitution Status

**Status**: ✅ **ALL CHECKS PASS** - Feature design fully compliant with constitution

No violations. No complexity justifications required. Ready to proceed to `/speckit.tasks` command.

---

## Project Structure

### Documentation (this feature)

```text
specs/003-node-detail-panel/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── node-detail-api.yaml  # OpenAPI spec for enhanced endpoint
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── topology_api.py          # [MODIFY] Add GET /topology/nodes/{hostname}/details endpoint
│   │   └── __init__.py
│   ├── services/
│   │   ├── topology_service.py      # [MODIFY] Add get_node_details() method
│   │   └── batfish_service.py
│   ├── models/
│   │   ├── device.py                # [EXTEND] Add NodeDetailResponse model
│   │   ├── interface.py
│   │   └── node_detail.py           # [NEW] Aggregated node detail model
│   └── utils/
│       └── logger.py
└── tests/
    ├── unit/
    │   ├── test_topology_service.py      # [NEW] Test get_node_details()
    │   └── test_node_detail_api.py       # [NEW] Test new endpoint
    ├── integration/
    │   └── test_node_detail_workflow.py  # [NEW] End-to-end test with fixture
    └── fixtures/
        └── sample_network/               # [USE EXISTING] Network configs for testing

frontend/
├── src/
│   ├── components/
│   │   ├── TopologyVisualization.js  # [MODIFY] Add node click handler, integrate panel
│   │   ├── NodeDetailPanel.js        # [NEW] Detail panel component
│   │   └── VerificationPanel.js
│   ├── services/
│   │   ├── topologyService.js        # [MODIFY] Add fetchNodeDetails(snapshot, hostname)
│   │   └── apiClient.js
│   ├── styles/
│   │   └── node-detail-panel.css     # [NEW] Panel-specific styles
│   └── main.js
└── tests/
    ├── unit/
    │   ├── NodeDetailPanel.test.js         # [NEW] Component unit tests
    │   └── TopologyVisualization.test.js   # [MODIFY] Add click handler tests
    └── e2e/
        └── node-detail-workflow.spec.js    # [NEW] Playwright E2E test
```

**Structure Decision**: Web application (Option 2) with existing frontend/backend separation. Feature adds 1 new frontend component (`NodeDetailPanel.js`), 1 new backend model (`node_detail.py`), and enhances existing topology API with aggregated node details endpoint. Test structure follows existing conventions (unit/integration/e2e).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - All constitution checks passed. No complexity violations requiring justification.
