<!--
SYNC IMPACT REPORT
==================
Version Change: [TEMPLATE] → 1.0.0
Modified Principles: N/A (initial constitution)
Added Sections:
  - Core Principles (5 principles for network verification domain)
  - Data Integrity & Validation (network-specific)
  - Development Workflow
  - Governance
Removed Sections: N/A
Templates Status:
  ✅ plan-template.md - reviewed, constitution check section compatible
  ✅ spec-template.md - reviewed, user story format compatible
  ✅ tasks-template.md - reviewed, task organization compatible
Follow-up TODOs: None
-->

# Batfish Visualization & Verification Constitution

## Core Principles

### I. Batfish-First Integration

Every feature MUST integrate with the Batfish container as the authoritative source of network analysis.
Direct container communication via pybatfish library is mandatory; no intermediate layers or custom parsers
for network configuration analysis. The Batfish snapshot model (network configs → snapshot → analysis)
is the foundational workflow that all features must respect.

**Rationale**: Batfish is a proven network verification engine. Re-implementing its analysis logic
introduces bugs, maintenance burden, and reduces accuracy. By treating Batfish as the single source
of truth for network analysis, we ensure consistency and leverage battle-tested validation logic.

### II. Topology Visualization as Contract

Network topology visualization MUST accurately represent Batfish's computed topology model. Any
discrepancy between rendered visualization and Batfish's layer 3 topology data is a critical bug.
Visualization components must consume Batfish topology queries (e.g., `get_layer3_edges()`) directly
without transformation beyond layout/rendering concerns.

**Rationale**: Users rely on topology diagrams to understand network structure. Inaccurate diagrams
cause misdiagnosis of network issues. By treating Batfish's topology as the contract, we ensure
visualizations are trustworthy and debuggable against the source API.

### III. Configuration Validation is Non-Negotiable

All network configuration validation MUST be performed by Batfish, not custom code. Features that
check reachability, ACL correctness, routing behavior, or any network policy MUST use Batfish
questions (e.g., `reachability`, `searchFilters`, `routes`). Results MUST be presented with
traceability to source configurations and line numbers when available.

**Rationale**: Network validation is complex and error-prone. Batfish encodes decades of vendor
configuration semantics. Custom validation logic will miss edge cases and create false confidence.
Validation must be traceable to specific config lines for engineers to fix issues efficiently.

### IV. Test-First Verification Workflow (NON-NEGOTIABLE)

Test-Driven Development is mandatory for all validation and visualization features:
1. Write tests that verify expected Batfish integration behavior
2. Get user/stakeholder approval on test scenarios
3. Ensure tests fail (Red)
4. Implement feature to pass tests (Green)
5. Refactor while maintaining passing tests

For network features: tests MUST include fixture config files representing realistic scenarios
(multi-vendor, VLANs, routing protocols, ACLs) and validate both positive cases (correct behavior)
and negative cases (detecting misconfigurations).

**Rationale**: Network tools that silently fail or produce incorrect results are worse than no tool.
TDD ensures every feature has proof of correctness before deployment. Network scenarios are complex;
comprehensive test fixtures catch regressions that manual testing misses.

### V. Observability & Debuggability

All Batfish interactions MUST be logged with:
- Snapshot name and timestamp
- Question type and parameters
- Response summary (row count, execution time)
- Errors with full Batfish stack traces

Visualization rendering MUST support debug mode showing:
- Raw Batfish data feeding the visualization
- Layout algorithm parameters
- Node/edge counts and filtering decisions

**Rationale**: When network analysis fails or produces unexpected results, engineers need to trace
execution from config file → Batfish processing → visualization rendering. Structured logging and
debug modes make this traceable without guesswork.

## Data Integrity & Validation

### Network Configuration Handling

- Configuration files MUST be stored immutably once loaded (snapshot-based workflow)
- File format detection MUST use Batfish's vendor detection, not custom heuristics
- Configuration updates require new snapshot creation with full re-analysis
- Partial updates or in-memory config modification are prohibited

### Batfish Container Lifecycle

- Container startup MUST verify Batfish service health before accepting user requests
- Snapshot initialization MUST validate that all config files are parseable by Batfish
- Analysis queries MUST handle Batfish exceptions gracefully with user-friendly error messages
- Container version MUST be tracked and logged; version mismatches should warn users

### Topology Data Integrity

- Topology data MUST be cached per-snapshot with invalidation on new snapshots
- Visualization filters (e.g., hide inactive interfaces) MUST preserve raw Batfish data integrity
- Exported topology representations (JSON, GraphML) MUST include Batfish metadata for traceability

## Development Workflow

### Feature Implementation Process

1. **Specification**: Define user scenario with example network configs and expected analysis outcome
2. **Test Fixtures**: Create multi-vendor config fixture set (Cisco, Juniper, Arista minimum)
3. **TDD Cycle**: Write tests → Verify failure → Implement → Verify pass → Refactor
4. **Integration Testing**: Test with realistic snapshots (100+ device networks)
5. **Documentation**: Update quickstart with end-to-end workflow example

### Batfish Integration Standards

- Use `pybatfish` as the exclusive Batfish client library
- All Batfish session setup MUST use environment-based configuration (host, port, API key)
- Question results MUST be validated for expected schema before processing
- Custom Batfish questions (if needed) MUST be documented with rationale in architecture docs

### Visualization Standards

- Topology layouts MUST support multiple algorithms (force-directed, hierarchical, geographic)
- Interactive features (zoom, pan, node inspection) are mandatory for usability
- Visualizations MUST support export to static formats (SVG, PNG) for documentation

## Governance

### Constitution Authority

This constitution supersedes all other project practices and decisions. Any feature, code pattern,
or architectural decision that violates these principles MUST be rejected or requires a formal
amendment with documented justification.

### Amendment Process

1. Propose amendment with clear problem statement and rationale
2. Document impact on existing features and templates
3. Update constitution version according to semantic versioning:
   - MAJOR: Principle removal or incompatible governance change
   - MINOR: New principle or major section addition
   - PATCH: Clarifications, wording improvements
4. Propagate changes to all dependent templates (plan, spec, tasks)
5. Notify all contributors of updated governance

### Compliance & Review

- All pull requests MUST include a constitution compliance checklist
- Reviewers MUST verify adherence to Batfish-First Integration and Test-First principles
- Complexity additions (new dependencies, non-Batfish validation logic) MUST be justified
  against simpler alternatives in the PR description
- Plan phase MUST include Constitution Check gate before Phase 0 research begins

**Version**: 1.0.0 | **Ratified**: 2025-11-21 | **Last Amended**: 2025-11-21
