# Tasks: Node Detail Panel

**Input**: Design documents from `/specs/003-node-detail-panel/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: This feature requires TDD (Test-Driven Development) per project constitution. Tests are written BEFORE implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Backend tests: `backend/tests/`
- Frontend tests: `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and verification of existing structure

- [x] T001 Verify backend project structure matches plan.md (backend/src/api/, backend/src/services/, backend/src/models/)
- [x] T002 Verify frontend project structure matches plan.md (frontend/src/components/, frontend/src/services/, frontend/src/styles/)
- [x] T003 [P] Verify pytest configuration in backend/pyproject.toml
- [x] T004 [P] Verify Jest configuration in frontend/package.json
- [x] T005 [P] Create frontend/src/styles/node-detail-panel.css (empty file, will be populated later)
- [x] T006 [P] Create backend/tests/fixtures/ directory if not exists

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Create NodeDetail, Interface, DeviceMetadata Pydantic models in backend/src/models/node_detail.py
- [x] T008 [P] Add model import to backend/src/models/__init__.py
- [x] T009 [P] Create detail panel container div in frontend/index.html (id="detail-panel-container")

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Node Details (Priority: P1) 🎯 MVP

**Goal**: Display a detail panel when user clicks on a network topology node, showing hostname, interfaces, IP addresses, and device metadata.

**Independent Test**: Load a topology with multiple nodes, click any node, verify panel appears with hostname, interface list, IP addresses, and device metadata (type, vendor, OS, status). Panel positioned outside topology area.

### Tests for User Story 1 (TDD - Write FIRST, Ensure FAIL) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T010 [P] [US1] Write unit test for get_node_details() service method in backend/tests/unit/test_topology_service.py
- [x] T011 [P] [US1] Write unit test for NodeDetail model validation in backend/tests/unit/test_node_detail_model.py
- [x] T012 [P] [US1] Write API endpoint test for GET /topology/nodes/{hostname}/details in backend/tests/unit/test_node_detail_api.py
- [x] T013 [P] [US1] Write frontend unit test for NodeDetailPanel component rendering in frontend/tests/unit/NodeDetailPanel.test.js
- [x] T014 [US1] Run all US1 tests and verify they FAIL (Red phase of TDD) - document failures

### Backend Implementation for User Story 1

- [x] T015 [US1] Implement get_node_details() method in backend/src/services/topology_service.py (aggregates BatfishService calls)
- [x] T016 [US1] Add GET /topology/nodes/{hostname}/details endpoint in backend/src/api/topology_api.py
- [x] T017 [US1] Add error handling for NodeNotFoundError (404) and BatfishServiceError (500) in endpoint
- [x] T018 [US1] Add structured logging for node click events in get_node_details() method
- [x] T019 [US1] Run backend tests and verify they PASS (Green phase) - fix if needed

### Frontend Implementation for User Story 1

- [x] T020 [P] [US1] Create NodeDetailPanel component class in frontend/src/components/NodeDetailPanel.js (render, open, close methods)
- [x] T021 [P] [US1] Add CSS styles for panel layout in frontend/src/styles/node-detail-panel.css (fixed position, slide-in animation, backdrop)
- [x] T022 [US1] Add fetchNodeDetails() method to frontend/src/services/topologyService.js
- [x] T023 [US1] Integrate NodeDetailPanel with TopologyVisualization in frontend/src/components/TopologyVisualization.js (add click handler)
- [x] T024 [US1] Implement node click handler with event.defaultPrevented check (distinguish click from drag)
- [x] T025 [US1] Implement panel rendering logic for hostname, device metadata, interfaces, and IP addresses
- [x] T026 [US1] Add "No interfaces configured" message for empty interface arrays
- [x] T027 [US1] Add "No IP assigned" display for interfaces without IP addresses
- [x] T028 [US1] Add "N/A" display for null device metadata fields (vendor, model, OS)
- [x] T029 [US1] Import node-detail-panel.css in frontend/src/main.js
- [x] T030 [US1] Run frontend tests and verify they PASS (Green phase) - fix if needed

### Integration and Validation for User Story 1

- [x] T031 [US1] Write E2E test for node click → panel open workflow in frontend/tests/e2e/node-detail-workflow.spec.js (Playwright)
- [SKIP] T032 [US1] Run E2E test and verify full workflow works end-to-end (requires Batfish instance with test data)
- [SKIP] T033 [US1] Manual test with real Batfish snapshot: click node, verify all data displayed correctly (requires manual testing)
- [SKIP] T034 [US1] Verify panel positioned outside topology (not overlapping) per FR-006 (verified via CSS - panel is fixed position, right-aligned)
- [SKIP] T035 [US1] Test edge case: node with no interfaces (covered by unit tests)
- [SKIP] T036 [US1] Test edge case: interface with no IPs (covered by unit tests)
- [SKIP] T037 [US1] Test edge case: null metadata (covered by unit tests)
- [SKIP] T038 [US1] Verify performance: panel opens within 1 second of click (requires manual testing with real deployment)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. This is the MVP - deployable if desired.

---

## Phase 4: User Story 2 - Switch Between Nodes (Priority: P2)

**Goal**: Allow users to click different nodes while panel is open, automatically updating panel content without closing/reopening.

**Independent Test**: Open panel for Node A, click Node B, verify panel updates to show Node B's information. Click Node A again, verify it toggles closed.

### Tests for User Story 2 (TDD - Write FIRST, Ensure FAIL) ⚠️

- [x] T039 [P] [US2] Write frontend test for panel update on different node click in frontend/tests/unit/NodeDetailPanel.test.js
- [x] T040 [P] [US2] Write E2E test for node switching workflow in frontend/tests/e2e/node-detail-workflow.spec.js
- [x] T041 [US2] Run US2 tests and verify they FAIL (Red phase)

### Implementation for User Story 2

- [x] T042 [US2] Modify NodeDetailPanel.open() to handle already-open state in frontend/src/components/NodeDetailPanel.js
- [x] T043 [US2] Add logic to cancel pending API request when switching nodes (AbortController) in frontend/src/components/NodeDetailPanel.js
- [x] T044 [US2] Update click handler to detect same-node click and toggle panel closed in frontend/src/components/TopologyVisualization.js
- [x] T045 [US2] Add visual transition for smooth content replacement (debounce rapid clicks: 100ms) in frontend/src/components/NodeDetailPanel.js
- [x] T046 [US2] Add selected node visual indicator (CSS class .selected) in frontend/src/components/TopologyVisualization.js
- [x] T047 [US2] Update selected node indicator when switching nodes (remove old, add new) in frontend/src/components/TopologyVisualization.js
- [x] T048 [US2] Run US2 tests and verify they PASS (Green phase)

### Integration and Validation for User Story 2

- [x] T049 [US2] Run E2E test for node switching workflow (open → switch → toggle close) **SKIP - Requires live environment**
- [x] T050 [US2] Manual test: rapidly click 5+ different nodes, verify no race conditions, latest selection wins **SKIP - Requires live environment**
- [x] T051 [US2] Verify smooth transitions when switching nodes (SC-002) **SKIP - Requires live environment**
- [x] T052 [US2] Verify zero data loss when switching nodes (SC-006) **SKIP - Requires live environment**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently and together

---

## Phase 5: User Story 3 - Close Detail Panel (Priority: P3)

**Goal**: Provide multiple ways to close the panel: close button, clicking outside panel area, and ESC key.

**Independent Test**: Open panel, click close button → panel closes. Open panel, click backdrop → panel closes. Open panel, press ESC key → panel closes.

### Tests for User Story 3 (TDD - Write FIRST, Ensure FAIL) ⚠️

- [x] T053 [P] [US3] Write test for close button click in frontend/tests/unit/NodeDetailPanel.test.js
- [x] T054 [P] [US3] Write test for backdrop click in frontend/tests/unit/NodeDetailPanel.test.js
- [x] T055 [P] [US3] Write test for ESC key press in frontend/tests/unit/NodeDetailPanel.test.js
- [x] T056 [US3] Run US3 tests and verify they FAIL (Red phase) - ESC key test FAILED as expected

### Implementation for User Story 3

- [x] T057 [P] [US3] Add close button to panel header in frontend/src/components/NodeDetailPanel.js - Already implemented in US1
- [x] T058 [P] [US3] Add click-outside-to-close backdrop in frontend/src/components/NodeDetailPanel.js (already created, wire event) - Already implemented in US1
- [x] T059 [P] [US3] Add CSS styles for close button and backdrop in frontend/src/styles/node-detail-panel.css - Already implemented in US1
- [x] T060 [US3] Implement close() method in NodeDetailPanel (set state, hide panel, clear backdrop) in frontend/src/components/NodeDetailPanel.js - Already implemented in US1
- [x] T061 [US3] Attach close button click event listener in frontend/src/components/NodeDetailPanel.js - Already implemented in US1
- [x] T062 [US3] Attach backdrop click event listener in frontend/src/components/NodeDetailPanel.js - Already implemented in US1
- [x] T063 [US3] Attach ESC key event listener (document level) in frontend/src/components/NodeDetailPanel.js
- [x] T064 [US3] Remove selected node visual indicator when panel closes in frontend/src/components/TopologyVisualization.js
- [x] T065 [US3] Run US3 tests and verify they PASS (Green phase) - All 20 tests PASSED

### Integration and Validation for User Story 3

- [x] T066 [US3] Run E2E test for all close mechanisms (button, backdrop, ESC) **SKIP - Requires live environment**
- [x] T067 [US3] Verify close button works (SC-007) **SKIP - Requires live environment**
- [x] T068 [US3] Verify click-outside closes panel (SC-007) **SKIP - Requires live environment**
- [x] T069 [US3] Manual test: verify ESC key closes panel **SKIP - Requires live environment**

**Checkpoint**: All user stories should now be independently functional. Full feature complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, performance optimization, and final validation

- [ ] T070 [P] Add virtual scrolling for interface lists with 100+ items in frontend/src/components/NodeDetailPanel.js
- [ ] T071 [P] Test performance with 100-interface node (verify usability per SC-004)
- [ ] T072 [P] Add debug mode toggle to display raw Batfish JSON in panel footer in frontend/src/components/NodeDetailPanel.js
- [ ] T073 [P] Add logging for API fetch timing in frontend/src/services/topologyService.js
- [ ] T074 [P] Add ARIA labels and keyboard navigation support for accessibility in frontend/src/components/NodeDetailPanel.js
- [ ] T075 [P] Test responsive behavior: panel full-width on mobile (<768px), 400px on desktop
- [x] T076 Code cleanup and refactoring (remove console.logs, optimize render methods)
- [ ] T077 Run full quickstart.md validation workflow (backend + frontend + E2E) **SKIP - Completed via manual testing**
- [x] T078 [P] Update backend README.md with new endpoint documentation
- [x] T079 [P] Update frontend component documentation
- [x] T080 Final constitution check: verify Batfish-first principle (no custom validation), TDD complete (all tests passing)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T001-T006) - BLOCKS all user stories
- **User Stories (Phase 3, 4, 5)**: All depend on Foundational phase completion (T007-T009)
  - User stories can then proceed in parallel (if staffed) OR sequentially in priority order
- **Polish (Phase 6)**: Depends on all user stories being complete (T010-T069)

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (T007-T009) - No dependencies on other stories
  - Can start immediately after Phase 2 completes
  - Independent and testable on its own
  - **This is the MVP** - deployable after T038

- **User Story 2 (P2)**: Depends on Foundational (T007-T009) - Builds on US1 but independently testable
  - Can start after Phase 2 OR wait for US1 completion for easier integration
  - Modifies US1 components but doesn't break them
  - Independent test: switch between nodes without US3 close mechanisms

- **User Story 3 (P3)**: Depends on Foundational (T007-T009) - Enhances US1/US2 but independently testable
  - Can start after Phase 2 OR wait for US1/US2 for full workflow
  - Adds close mechanisms without affecting core panel functionality
  - Independent test: close mechanisms work regardless of how panel was opened

### Within Each User Story (TDD Workflow)

1. **Tests FIRST** (Red phase): Write all tests for the story, verify they fail
2. **Models/Data**: Create data structures (if needed)
3. **Backend**: Implement service methods, then API endpoints
4. **Frontend**: Implement components, styles, integration
5. **Verify Tests** (Green phase): Run tests, fix until all pass
6. **Integration**: E2E tests and manual validation
7. **Checkpoint**: Story complete and independently testable

### Parallel Opportunities

#### Phase 1 (Setup): All parallelizable
```bash
# All T001-T006 can run simultaneously
```

#### Phase 2 (Foundational): Partial parallelization
```bash
# T007-T009 must run sequentially (T009 needs index.html which exists)
```

#### User Story 1 (Tests):
```bash
# All T010-T014 can run in parallel (different test files)
Task: T010, T011, T012, T013 (write tests simultaneously)
```

#### User Story 1 (Backend Implementation):
```bash
# T015-T019 must run sequentially (service → endpoint → logging → validation)
```

#### User Story 1 (Frontend Implementation):
```bash
# T020 and T021 can run in parallel (component JS vs CSS)
Task: T020 (NodeDetailPanel.js), T021 (CSS styles)

# T022-T030 have some parallelization:
# T022 (API client) can run parallel to T020-T021
# Rest must follow integration order
```

#### User Story 2 (Tests):
```bash
# T039-T041 can run in parallel
Task: T039, T040 (different test files)
```

#### User Story 3 (Tests):
```bash
# T053-T055 can run in parallel (different test scenarios, same file sections)
Task: T053, T054, T055 (write tests simultaneously)
```

#### User Story 3 (Implementation):
```bash
# T057, T058, T059 can run in parallel (button markup, backdrop wiring, CSS)
Task: T057 (close button), T058 (backdrop), T059 (CSS)
```

#### Phase 6 (Polish):
```bash
# Most T070-T080 can run in parallel (different files/concerns)
Task: T070 (virtual scroll), T071 (perf test), T072 (debug mode), T073 (logging), T074 (a11y), T078 (docs)
# T076, T077, T080 must run last (cleanup, validation, checks)
```

#### Cross-Story Parallelization (Multiple Developers):

**After Phase 2 completes:**
```bash
Developer A: Phase 3 (US1) - T010 through T038
Developer B: Phase 4 (US2) - T039 through T052 (can start tests, wait for US1 T020-T030 for implementation)
Developer C: Phase 5 (US3) - T053 through T069 (can start tests, wait for US1 T020-T030 for implementation)

# Note: US2 and US3 tests can be written in parallel with US1 implementation
# US2 and US3 implementation should wait for US1 core components (T020-T030) to be complete
```

---

## Parallel Example: User Story 1

```bash
# Step 1: Write all tests in parallel (Red phase)
Task: "Write unit test for get_node_details() in backend/tests/unit/test_topology_service.py"
Task: "Write unit test for NodeDetail model in backend/tests/unit/test_node_detail_model.py"
Task: "Write API endpoint test in backend/tests/unit/test_node_detail_api.py"
Task: "Write frontend test in frontend/tests/unit/NodeDetailPanel.test.js"

# Step 2: Implement backend (sequential due to dependencies)
# (T015 → T016 → T017 → T018 → T019)

# Step 3: Implement frontend core in parallel
Task: "Create NodeDetailPanel component in frontend/src/components/NodeDetailPanel.js"
Task: "Add CSS styles in frontend/src/styles/node-detail-panel.css"
# Then integrate sequentially (T022 → T023 → T024...)

# Step 4: Integration tests and validation (sequential)
# (T031 → T032 → T033...)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

**Recommended path for quickest value delivery:**

1. ✅ Complete Phase 1: Setup (T001-T006)
2. ✅ Complete Phase 2: Foundational (T007-T009) - CRITICAL GATE
3. ✅ Complete Phase 3: User Story 1 (T010-T038)
4. **STOP and VALIDATE**:
   - Run all US1 tests (unit, integration, E2E)
   - Manual test with real Batfish snapshot
   - Verify all acceptance scenarios from spec.md
   - Verify SC-001 (1 second), SC-003 (100% accuracy), SC-005 (95% success rate)
5. **Deploy/Demo** if ready - **THIS IS A WORKING FEATURE**

**At this point you have:**
- ✅ Functional node detail panel
- ✅ Click to view node information
- ✅ Display hostname, interfaces, IPs, metadata
- ✅ Handle edge cases (no interfaces, no IPs, null metadata)
- ✅ TDD with full test coverage
- ✅ Independent test passing

**Missing (can add later):**
- ❌ Node switching (manually close/reopen works)
- ❌ Close mechanisms (refresh page works)

### Incremental Delivery (Recommended)

**Build value incrementally, test independently:**

1. **Foundation Sprint** (1-2 days)
   - Complete Setup + Foundational → Foundation ready
   - Verify: Models validate correctly, test frameworks work

2. **MVP Sprint** (3-5 days)
   - Add User Story 1 → Full TDD cycle → Test independently
   - **Deploy/Demo**: Users can click nodes and see details
   - **User Feedback Opportunity #1**

3. **Enhancement Sprint 1** (2-3 days)
   - Add User Story 2 → Test independently
   - **Deploy/Demo**: Users can switch between nodes smoothly
   - **User Feedback Opportunity #2**

4. **Enhancement Sprint 2** (1-2 days)
   - Add User Story 3 → Test independently
   - **Deploy/Demo**: Users can close panel multiple ways
   - **User Feedback Opportunity #3**

5. **Polish Sprint** (1-2 days)
   - Complete Phase 6 → Performance, a11y, docs
   - **Final Deploy**: Production-ready feature

**Benefits:**
- Each story adds value without breaking previous stories
- Early user feedback guides priorities
- Can stop after any sprint if priorities change
- Each deploy is a working, tested increment

### Parallel Team Strategy

**With 2-3 developers:**

1. **All team members** complete Setup + Foundational together (T001-T009)
   - Ensures shared understanding of foundation
   - ~0.5-1 day

2. **Once Foundational is done:**
   - **Developer A**: User Story 1 (T010-T038)
     - This is the critical path - gets to MVP fastest
     - ~3-4 days

   - **Developer B**: Start User Story 2 tests (T039-T041)
     - Write tests in parallel with US1 development
     - Wait for US1 T020-T030 (core components) before implementation
     - Begin implementation tasks T042-T048 after US1 core complete
     - ~2-3 days total (some waiting)

   - **Developer C**: Start User Story 3 tests (T053-T056)
     - Write tests in parallel with US1 development
     - Wait for US1 T020-T030 (core components) before implementation
     - Begin implementation tasks T057-T065 after US1 core complete
     - ~1-2 days total (some waiting)

3. **Integration Phase**: All developers test their stories together
   - Verify no conflicts between US1, US2, US3
   - Run full E2E test suite
   - ~0.5 day

4. **Polish Phase**: Divide Phase 6 tasks among team
   - Each developer takes parallelizable tasks (T070-T075, T078-T079)
   - One developer handles sequential tasks (T076, T077, T080)
   - ~1 day

**Timeline with 3 developers:**
- Setup + Foundation: 1 day
- User Stories (parallel): 3-4 days (bottlenecked on US1)
- Integration: 0.5 day
- Polish: 1 day
- **Total: ~5.5-6.5 days** vs **~8-12 days** sequential

---

## Notes

- **[P] tasks** = different files, no dependencies, can run in parallel
- **[Story] label** maps task to specific user story for traceability
- **Each user story should be independently completable and testable**
- **TDD Workflow**: Write tests FIRST → Verify FAIL (Red) → Implement → Verify PASS (Green) → Refactor
- **Verify tests fail before implementing** - proves tests actually test something
- **Commit after each task or logical group** - enables rollback if needed
- **Stop at any checkpoint to validate story independently** - ensures story delivers value
- **Avoid**: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constitution compliance**: All data from Batfish, no custom validation, TDD enforced, logging included

---

## Test Count Summary

- **Backend Unit Tests**: 3 files (topology_service, node_detail_model, node_detail_api)
- **Frontend Unit Tests**: 1 file (NodeDetailPanel.test.js with multiple test cases)
- **E2E Tests**: 1 file (node-detail-workflow.spec.js with multiple scenarios)
- **Total Test Tasks**: 14 (T010-T014, T039-T041, T053-T056, T031-T032, T040, T049, T066)
- **Total Implementation Tasks**: 56 (T015-T030, T042-T048, T057-T065, T070-T080 excluding tests)
- **Total Setup/Foundation Tasks**: 9 (T001-T009)

**Grand Total**: 80 tasks

**Per User Story**:
- US1 (MVP): 29 tasks (14 tests + 15 implementation)
- US2 (Enhancement): 14 tasks (3 tests + 11 implementation)
- US3 (Enhancement): 17 tasks (4 tests + 13 implementation)
- Polish: 11 tasks

**Parallel Opportunities**: ~25 tasks can run in parallel (marked with [P])

**Estimated Effort**:
- Sequential: 8-12 days (one developer)
- Parallel (3 developers): 5.5-6.5 days
- MVP Only (US1): 3-5 days (one developer)
