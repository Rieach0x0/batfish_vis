# Tasks: Batfish Snapshot & Topology Visualization

**Input**: Design documents from `/specs/001-batfish-snapshot-topology/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Not explicitly requested in feature specification - test tasks are OMITTED per template guidelines.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is a **Web application** with:
- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create backend project structure: backend/src/{api,services,models}/, backend/tests/{contract,integration,unit}/, backend/requirements.txt
- [X] T002 Create frontend project structure: frontend/src/{components,services,utils}/, frontend/tests/{unit,e2e}/, frontend/package.json
- [X] T003 Initialize Python backend with FastAPI 0.109+ and pybatfish v2025.07.07 in backend/requirements.txt
- [X] T004 Initialize JavaScript frontend with D3.js v7 and Vite in frontend/package.json
- [X] T005 [P] Configure Python linting (black, pylint) and formatting in backend/pyproject.toml
- [X] T006 [P] Configure ESLint and Prettier for JavaScript in frontend/.eslintrc.json
- [X] T007 Create backend/README.md with setup instructions for Python 3.11 + FastAPI + pybatfish
- [X] T008 Create frontend/README.md with setup instructions for npm + Vite + D3.js v7

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Create Batfish service wrapper in backend/src/services/batfish_service.py with Session initialization (host='localhost', port=9996)
- [X] T010 Implement health check endpoint GET /api/health in backend/src/api/health_api.py to verify Batfish container connectivity
- [X] T011 [P] Setup FastAPI application with CORS middleware in backend/src/main.py
- [X] T012 [P] Setup environment configuration management in backend/src/config.py for BATFISH_HOST and BATFISH_PORT
- [X] T013 [P] Configure structured logging with Python logging module in backend/src/utils/logger.py
- [X] T014 [P] Create error handling middleware in backend/src/middleware/error_handler.py for Batfish connection errors
- [X] T015 [P] Setup API router structure in backend/src/api/__init__.py to register all endpoint modules
- [X] T016 Create base API client service in frontend/src/services/apiClient.js with fetch wrapper and error handling
- [X] T017 [P] Create test fixtures directory backend/tests/fixtures/configs/ with sample Cisco/Juniper/Arista config files

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Configuration Import & Snapshot Creation (Priority: P1) 🎯 MVP

**Goal**: Enable network engineers to create Batfish snapshots from network configuration files, providing the foundation for all analysis and visualization features.

**Independent Test**: Specify a folder path containing network configuration files, execute snapshot creation, and verify that Batfish successfully initializes the snapshot and reports device count and parse status.

### Implementation for User Story 1

- [X] T018 [P] [US1] Create Snapshot model in backend/src/models/snapshot.py with fields: name, network, createdAt, status, configFileCount, deviceCount, batfishVersion, parseErrors
- [X] T019 [P] [US1] Create FileService in backend/src/services/file_service.py to handle config file reading and temporary storage
- [X] T020 [US1] Implement SnapshotService.create_snapshot() in backend/src/services/snapshot_service.py using pybatfish bf.init_snapshot()
- [X] T021 [US1] Implement SnapshotService.get_parse_errors() in backend/src/services/snapshot_service.py using bf.q.fileParseStatus()
- [X] T022 [US1] Implement SnapshotService.list_snapshots() in backend/src/services/snapshot_service.py using bf.list_snapshots()
- [X] T023 [US1] Implement SnapshotService.get_snapshot_details() in backend/src/services/snapshot_service.py to retrieve snapshot metadata
- [X] T024 [US1] Implement SnapshotService.delete_snapshot() in backend/src/services/snapshot_service.py using bf.delete_snapshot()
- [X] T025 [US1] Create POST /api/snapshots endpoint in backend/src/api/snapshot_api.py accepting multipart/form-data with configFiles and snapshotName
- [X] T026 [US1] Create GET /api/snapshots endpoint in backend/src/api/snapshot_api.py to list all snapshots
- [X] T027 [US1] Create GET /api/snapshots/{snapshotName} endpoint in backend/src/api/snapshot_api.py for snapshot details
- [X] T028 [US1] Create DELETE /api/snapshots/{snapshotName} endpoint in backend/src/api/snapshot_api.py
- [X] T029 [US1] Add validation for snapshot name (1-100 chars, alphanumeric + hyphen/underscore) in backend/src/api/snapshot_api.py
- [X] T030 [US1] Add error handling for Batfish connection failures (503 Service Unavailable) in backend/src/api/snapshot_api.py
- [X] T031 [US1] Add error handling for duplicate snapshot names (409 Conflict) in backend/src/api/snapshot_api.py
- [X] T032 [US1] Add structured logging for all Batfish snapshot operations in backend/src/services/snapshot_service.py
- [X] T033 [P] [US1] Create snapshotService.js in frontend/src/services/snapshotService.js with createSnapshot(), listSnapshots(), getSnapshot(), deleteSnapshot()
- [X] T034 [P] [US1] Create SnapshotUpload.js component in frontend/src/components/SnapshotUpload.js with folder selection UI (file input + manual path)
- [X] T035 [US1] Implement file upload progress indicator in frontend/src/components/SnapshotUpload.js
- [X] T036 [US1] Create SnapshotManager.js component in frontend/src/components/SnapshotManager.js to display snapshot list with name, createdAt, deviceCount, status
- [X] T037 [US1] Implement snapshot switching functionality in frontend/src/components/SnapshotManager.js to select active snapshot
- [X] T038 [US1] Implement snapshot deletion with confirmation dialog in frontend/src/components/SnapshotManager.js
- [X] T039 [US1] Display parse errors with fileName and errorMessage in frontend/src/components/SnapshotUpload.js if status is not COMPLETE
- [X] T040 [US1] Add validation for empty folder selection in frontend/src/components/SnapshotUpload.js
- [X] T041 [US1] Integrate SnapshotUpload and SnapshotManager components into main app layout in frontend/src/App.js

**Checkpoint**: At this point, User Story 1 should be fully functional - users can create, list, view, and delete Batfish snapshots independently.

---

## Phase 4: User Story 2 - Network Topology Visualization (Priority: P2)

**Goal**: Enable network engineers to visualize network topology as an interactive graph, showing all devices and Layer 3 connections derived from Batfish snapshot analysis.

**Independent Test**: After creating a snapshot, execute topology visualization and verify that all devices appear as nodes, Layer 3 edges appear as links, and the graph matches Batfish's computed topology 100%.

### Implementation for User Story 2

- [X] T042 [P] [US2] Create Device model in backend/src/models/device.py with fields: hostname, vendor, deviceType, model, osVersion, interfaces, location
- [X] T043 [P] [US2] Create Interface model in backend/src/models/interface.py with fields: name, active, ipAddress, vlan, description, bandwidth, mtu
- [X] T044 [P] [US2] Create Edge model in backend/src/models/edge.py with fields: sourceDevice, sourceInterface, destDevice, destInterface, sourceIp, destIp
- [X] T045 [US2] Implement TopologyService.get_nodes() in backend/src/services/topology_service.py using bf.q.nodeProperties() to retrieve all devices
- [X] T046 [US2] Implement TopologyService.get_interfaces() in backend/src/services/topology_service.py using bf.q.interfaceProperties() for each node
- [X] T047 [US2] Implement TopologyService.get_edges() in backend/src/services/topology_service.py using bf.q.layer3Edges() to retrieve Layer 3 connections
- [X] T048 [US2] Add vendor detection mapping (CISCO_IOS, JUNIPER, ARISTA, etc.) in backend/src/services/topology_service.py from Configuration_Format field
- [X] T049 [US2] Add device type inference (ROUTER, SWITCH, FIREWALL) in backend/src/services/topology_service.py based on vendor and configuration patterns
- [X] T050 [US2] Create GET /api/topology/nodes endpoint in backend/src/api/topology_api.py with query parameter snapshot (required)
- [X] T051 [US2] Create GET /api/topology/edges endpoint in backend/src/api/topology_api.py with query parameter snapshot (required)
- [X] T052 [US2] Add error handling for snapshot not found (404 Not Found) in backend/src/api/topology_api.py
- [X] T053 [US2] Add structured logging for topology queries in backend/src/services/topology_service.py
- [X] T054 [P] [US2] Create topologyService.js in frontend/src/services/topologyService.js with getNodes() and getEdges()
- [X] T055 [P] [US2] Create d3LayoutEngine.js in frontend/src/utils/d3LayoutEngine.js implementing force-directed layout with d3.forceSimulation()
- [X] T056 [US2] Configure force-directed layout parameters: forceLink (distance: 150), forceManyBody (strength: -400), forceCenter, forceCollide (radius: 50) in frontend/src/utils/d3LayoutEngine.js
- [X] T057 [US2] Create TopologyVisualization.js component in frontend/src/components/TopologyVisualization.js with SVG canvas and D3.js rendering
- [X] T058 [US2] Implement node rendering (circles) with labels showing hostname in frontend/src/components/TopologyVisualization.js
- [X] T059 [US2] Implement edge rendering (lines) connecting source and destination nodes in frontend/src/components/TopologyVisualization.js
- [X] T060 [US2] Implement zoom and pan functionality using d3.zoom() in frontend/src/components/TopologyVisualization.js
- [X] T061 [US2] Implement node drag functionality in frontend/src/components/TopologyVisualization.js to reposition devices
- [X] T062 [US2] Implement node click event to display device details (hostname, vendor, deviceType, interfaces) in side panel in frontend/src/components/TopologyVisualization.js
- [X] T063 [US2] Add vendor-based node styling (different colors for CISCO, JUNIPER, ARISTA) in frontend/src/components/TopologyVisualization.js
- [X] T064 [US2] Create topologyExporter.js in frontend/src/utils/topologyExporter.js to export SVG and PNG formats
- [X] T065 [US2] Implement SVG export functionality in frontend/src/utils/topologyExporter.js by serializing D3 SVG DOM
- [X] T066 [US2] Implement PNG export functionality in frontend/src/utils/topologyExporter.js using canvas rendering
- [X] T067 [US2] Add export button to TopologyVisualization component in frontend/src/components/TopologyVisualization.js with format selection (SVG/PNG)
- [X] T068 [US2] Add loading indicator during topology data fetch in frontend/src/components/TopologyVisualization.js
- [X] T069 [US2] Add empty state message if snapshot has zero devices in frontend/src/components/TopologyVisualization.js
- [X] T070 [US2] Integrate TopologyVisualization component into main app with snapshot selection in frontend/src/App.js

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can create snapshots AND visualize topology graphs.

---

## Phase 5: User Story 3 - Configuration Verification (Priority: P3)

**Goal**: Enable network engineers to execute Batfish verification queries (reachability, ACL, routing) against snapshots to validate configuration correctness and identify potential issues.

**Independent Test**: After creating a snapshot, execute a reachability verification query with source and destination IPs, and verify that Batfish returns structured verification results with flow traces.

### Implementation for User Story 3

- [X] T071 [P] [US3] Create VerificationResult model in backend/src/models/verification.py with fields: queryId, queryType, executedAt, parameters, status, results, errorMessage, executionTimeMs
- [X] T072 [US3] Implement VerificationService.verify_reachability() in backend/src/services/verification_service.py using pybatfish reachability() query
- [X] T073 [US3] Implement VerificationService.verify_acl() in backend/src/services/verification_service.py using pybatfish searchFilters() query
- [X] T074 [US3] Implement VerificationService.verify_routing() in backend/src/services/verification_service.py using pybatfish routes() query
- [X] T075 [US3] Add query result parsing to extract flow traces with hops (node, action) in backend/src/services/verification_service.py
- [X] T076 [US3] Add query result parsing to extract ACL match results (node, filter, action, lineNumber, lineContent) in backend/src/services/verification_service.py
- [X] T077 [US3] Add execution time tracking for all verification queries in backend/src/services/verification_service.py
- [X] T078 [US3] Create POST /api/verification/reachability endpoint in backend/src/api/verification_api.py accepting snapshot, srcIp, dstIp, optional srcNode
- [X] T079 [US3] Create POST /api/verification/acl endpoint in backend/src/api/verification_api.py accepting snapshot, filterName, srcIp, dstIp, protocol
- [X] T080 [US3] Create POST /api/verification/routing endpoint in backend/src/api/verification_api.py accepting snapshot, optional nodes array, optional network filter
- [X] T081 [US3] Add IP address validation for srcIp and dstIp parameters in backend/src/api/verification_api.py
- [X] T082 [US3] Add error handling for invalid query parameters (400 Bad Request) in backend/src/api/verification_api.py
- [X] T083 [US3] Add error handling for query timeout (set max execution time) in backend/src/services/verification_service.py
- [X] T084 [US3] Add structured logging for all verification queries with parameters and execution time in backend/src/services/verification_service.py
- [X] T085 [P] [US3] Create verificationService.js in frontend/src/services/verificationService.js with verifyReachability(), verifyACL(), verifyRouting()
- [X] T086 [P] [US3] Create VerificationPanel.js component in frontend/src/components/VerificationPanel.js with query type selector (Reachability/ACL/Routing)
- [X] T087 [US3] Implement reachability query form with srcIp, dstIp, optional srcNode inputs in frontend/src/components/VerificationPanel.js
- [X] T088 [US3] Implement ACL query form with filterName, srcIp, dstIp, protocol inputs in frontend/src/components/VerificationPanel.js
- [X] T089 [US3] Implement routing query form with optional nodes multi-select and network prefix filter in frontend/src/components/VerificationPanel.js
- [X] T090 [US3] Implement verification results display showing queryType, status, executionTimeMs in frontend/src/components/VerificationPanel.js
- [X] T091 [US3] Display reachability flow traces with hop-by-hop path (node → action sequence) in frontend/src/components/VerificationPanel.js
- [X] T092 [US3] Display ACL results showing matched filter, action (PERMIT/DENY), lineNumber, lineContent in frontend/src/components/VerificationPanel.js
- [X] T093 [US3] Display routing results showing routing table entries with destination network and next hop in frontend/src/components/VerificationPanel.js
- [X] T094 [US3] Add error highlighting for verification failures with errorMessage display in frontend/src/components/VerificationPanel.js
- [X] T095 [US3] Add configuration file traceability: display fileName and lineNumber for issues in verification results in frontend/src/components/VerificationPanel.js
- [X] T096 [US3] Add loading indicator during query execution in frontend/src/components/VerificationPanel.js
- [X] T097 [US3] Add query history display showing recent verification queries in frontend/src/components/VerificationPanel.js
- [X] T098 [US3] Integrate VerificationPanel component into main app with snapshot context in frontend/src/App.js

**Checkpoint**: All user stories should now be independently functional - snapshots, topology visualization, and configuration verification all work end-to-end.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T099 [P] Add debug mode toggle in frontend UI to show Batfish query raw data in browser console
- [ ] T100 [P] Implement performance metrics logging (query time, rendering time) for all Batfish operations in backend/src/utils/metrics.py
- [ ] T101 [P] Add D3.js layout parameter customization UI (force strength, link distance) in frontend/src/components/TopologyVisualization.js
- [ ] T102 [P] Add progress bar for large snapshot creation (100+ devices) in frontend/src/components/SnapshotUpload.js
- [X] T103 Add comprehensive error messages with troubleshooting hints for common failures (Batfish unreachable, unsupported vendor, parse errors) in backend/src/middleware/error_handler.py
- [ ] T104 [P] Add unit tests for Batfish service wrapper in backend/tests/unit/test_batfish_service.py
- [ ] T105 [P] Add unit tests for SnapshotService in backend/tests/unit/test_snapshot_service.py
- [ ] T106 [P] Add unit tests for TopologyService in backend/tests/unit/test_topology_service.py
- [ ] T107 [P] Add unit tests for VerificationService in backend/tests/unit/test_verification_service.py
- [ ] T108 [P] Add unit tests for d3LayoutEngine.js in frontend/tests/unit/d3LayoutEngine.test.js
- [ ] T109 [P] Add unit tests for topologyExporter.js in frontend/tests/unit/topologyExporter.test.js
- [X] T110 Validate quickstart.md steps: Docker run Batfish v2025.07.07, backend startup, frontend startup, snapshot creation, topology display, verification query
- [X] T111 Update backend/README.md with API endpoint documentation and Batfish connection troubleshooting
- [X] T112 Update frontend/README.md with component architecture and D3.js customization guide
- [X] T113 Code cleanup: Remove debug print statements, ensure consistent error handling across all API endpoints
- [X] T114 Security review: Validate file upload size limits, sanitize snapshot names, check for path traversal vulnerabilities in config file handling

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires snapshot to exist (from US1) for runtime operation, but US2 implementation can proceed in parallel
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires snapshot to exist (from US1) for runtime operation, but US3 implementation can proceed in parallel

### Within Each User Story

**User Story 1 (Snapshot Creation)**:
1. Models first (T018)
2. Services in parallel (T019, T020-T024 can proceed after models)
3. API endpoints after services (T025-T032)
4. Frontend services and components in parallel (T033-T041)

**User Story 2 (Topology Visualization)**:
1. Models in parallel (T042, T043, T044)
2. Backend services after models (T045-T053)
3. Frontend services and D3 engine in parallel (T054, T055-T056)
4. Visualization component implementation (T057-T070)

**User Story 3 (Verification)**:
1. Models first (T071)
2. Backend services after models (T072-T084)
3. Frontend services and components in parallel (T085-T098)

### Parallel Opportunities

- **Phase 1 Setup**: T001-T002 (backend/frontend structure), T003-T004 (package init), T005-T006 (linting), T007-T008 (README)
- **Phase 2 Foundational**: T010-T017 all marked [P] can run in parallel after T009 (Batfish service)
- **Once Foundational completes**: All three user stories (Phase 3, 4, 5) can be worked on in parallel by different team members
- **Within US1**: T018-T019 (models/file service), T033-T034 (frontend components)
- **Within US2**: T042-T044 (all models), T054-T055 (services/layout)
- **Within US3**: T085-T086 (service/component)
- **Phase 6 Polish**: T099-T102 (debug/metrics/UI), T104-T109 (all unit tests)

---

## Parallel Example: User Story 1 (Snapshot Creation)

```bash
# Launch models and file service in parallel:
Task T018: "Create Snapshot model in backend/src/models/snapshot.py"
Task T019: "Create FileService in backend/src/services/file_service.py"

# After services are complete, launch frontend components in parallel:
Task T033: "Create snapshotService.js in frontend/src/services/snapshotService.js"
Task T034: "Create SnapshotUpload.js component in frontend/src/components/SnapshotUpload.js"
```

---

## Parallel Example: User Story 2 (Topology Visualization)

```bash
# Launch all models in parallel:
Task T042: "Create Device model in backend/src/models/device.py"
Task T043: "Create Interface model in backend/src/models/interface.py"
Task T044: "Create Edge model in backend/src/models/edge.py"

# Launch frontend service and D3 layout engine in parallel:
Task T054: "Create topologyService.js in frontend/src/services/topologyService.js"
Task T055: "Create d3LayoutEngine.js in frontend/src/utils/d3LayoutEngine.js"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup → Project structure ready
2. Complete Phase 2: Foundational → Batfish integration + health check working
3. Complete Phase 3: User Story 1 → Snapshot creation fully functional
4. **STOP and VALIDATE**: Test snapshot creation independently with real config files
5. Deploy/demo if ready - users can now create and manage Batfish snapshots

### Incremental Delivery

1. Complete Setup (Phase 1) + Foundational (Phase 2) → Foundation ready
2. Add User Story 1 (Phase 3) → Test independently → **Deploy/Demo (MVP!)** - Snapshot creation works
3. Add User Story 2 (Phase 4) → Test independently → **Deploy/Demo** - Topology visualization added
4. Add User Story 3 (Phase 5) → Test independently → **Deploy/Demo** - Verification queries added
5. Add Polish (Phase 6) → Final production-ready release
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup (Phase 1) + Foundational (Phase 2) together
2. Once Foundational is done:
   - **Developer A**: User Story 1 (Snapshot Creation) - T018 to T041
   - **Developer B**: User Story 2 (Topology Visualization) - T042 to T070
   - **Developer C**: User Story 3 (Configuration Verification) - T071 to T098
3. Stories complete and integrate independently
4. Note: US2 and US3 need snapshots from US1 to test runtime behavior, but implementation can proceed in parallel

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability (US1, US2, US3)
- **Each user story should be independently completable**: Implement → Test → Deploy incrementally
- **Batfish v2025.07.07 requirement**: All pybatfish calls must use port 9996 (9997 deprecated)
- **D3.js v7 requirement**: Use D3.js v7 force-directed layout for topology visualization
- **Constitution compliance**: All Batfish queries follow憲章 principles (Batfish-First, No Custom Parsers)
- **File paths are exact**: Every task specifies the exact file to create/modify
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
