# STEP 8A: New Nodes with Artifact Versioning

**Feature**: step-8a-new-nodes
**Status**: Planning
**Date**: 2026-03-30
**Owner**: Proposal Workflow Team

---

## 📋 Executive Summary

Implement 6 new LangGraph nodes for advanced proposal processing with integrated artifact versioning system (Phase 1). These nodes extend the workflow into specialized analysis, validation, and evaluation phases, each creating versioned artifacts for audit trail and rework capability.

**Key Deliverable**: 6 production-ready nodes with automatic version tracking, dependency validation, and human choice resolution.

---

## 🎯 Goals & Objectives

### Primary Goals
1. **Extend Workflow**: Add 6 specialized nodes to STEP 8A-8F workflow phases
2. **Artifact Versioning**: Integrate versioning for each node's output (auto version creation)
3. **Dependency Validation**: Use existing validate_move_and_resolve_versions() for inter-node dependencies
4. **Human Choice Support**: Enable version selection when moving between nodes
5. **Maintain Code Quality**: Follow existing patterns (prompts, pydantic models, error handling)

### Success Criteria
- ✅ All 6 nodes syntax-valid (mypy + ruff pass)
- ✅ Each node creates artifacts with version tracking
- ✅ Unit tests cover core logic (≥80% coverage per node)
- ✅ Integration with existing graph.py (edges + routing)
- ✅ API endpoints expose node status/output
- ✅ Match Rate ≥90% in gap analysis

---

## 📊 Scope & Requirements

### 6 Nodes to Implement

| Node | Phase | Input | Output | Purpose |
|------|-------|-------|--------|---------|
| **proposal_customer_analysis** | 8A | rfp_analysis, strategy, kb_refs | customer_profile | Deep client intelligence (needs, decision drivers, budget authority) |
| **proposal_section_validator** | 8B | proposal_sections, rfp_analysis, strategy | validation_report | Quality gate: compliance, style, consistency checks |
| **proposal_sections_consolidation** | 8C | proposal_sections (multiple versions), validation_report | consolidated_sections | Merge approved sections, resolve conflicts, finalize |
| **mock_evaluation_analysis** | 8D | proposal_sections, rfp_analysis, evaluation_criteria | mock_eval_result | Simulate evaluation scoring, identify weaknesses |
| **mock_evaluation_feedback_processor** | 8E | mock_eval_result, proposal_sections | feedback_summary | Process mock scores, generate improvement recommendations |
| **proposal_write_next_v2** | 8F | feedback_summary, dynamic_sections | proposal_sections_v2 | Sequential rewrite with mock feedback integration |

### Integration Requirements

**Versioning Pattern** (from `versioning_integration_guide.md`):
```python
# At end of node execution:
version_num, artifact_version = await execute_node_and_create_version(
    proposal_id=UUID(state.get("project_id")),
    node_name="node_name_here",
    output_key="output_key_here",
    artifact_data=output_object.model_dump(),  # Convert to dict
    user_id=UUID(state.get("created_by")),
    state=state
)

# Update state with versioned artifact
state["artifact_versions"] = {
    "output_key": (state.get("artifact_versions", {}).get("output_key", []) + [artifact_version])
}
state["active_versions"] = {
    **state.get("active_versions", {}),
    f"node_name_{output_key}": version_num
}
```

**State Extensions**:
- Add Pydantic models to state.py: CustomerProfile, ValidationReport, ConsolidatedProposal, MockEvalResult, FeedbackSummary
- Update ProposalState annotations with new fields
- Configure reducers (merge for lists, replace for single objects)

**API Endpoints**:
- GET /api/proposals/{id}/node-status/{node_name} - Get node output + version info
- POST /api/proposals/{id}/validate-node/{node_name} - Pre-validate node execution
- GET /api/proposals/{id}/versions/{output_key} - List all versions of specific output

### Dependencies

**External**:
- LangGraph graph.py integration (existing)
- version_manager.py (Phase 1 ✅)
- Supabase RLS policies (existing)
- Claude API client (existing)

**Internal**:
- Pydantic models in state.py (extend)
- Prompts in app/prompts/ (new files or existing)
- Routes in routes_proposal.py or new routes_step8a.py
- Tests in tests/test_step8a_nodes.py

---

## 🔄 Implementation Order

### Phase 0: Planning & Design (2-3 days)
- [x] Define node specifications (inputs/outputs/logic)
- [x] Design Pydantic models for each node
- [x] Plan prompt templates for AI-driven nodes
- [x] Design state extensions
- [ ] **CURRENT**: Create this plan document
- [ ] Review with team, refine scope

### Phase 1: Core Implementation (4-5 days)
- [ ] **Week 1**: proposal_customer_analysis + proposal_section_validator (parallel)
  - Create Pydantic models in state.py
  - Write prompt templates
  - Implement node logic
  - Add versioning calls
  - Write unit tests
- [ ] **Week 1-2**: proposal_sections_consolidation + mock_evaluation_analysis
- [ ] **Week 2**: mock_evaluation_feedback_processor + proposal_write_next_v2
- [ ] Integrate all nodes into graph.py (edges, routing logic)

### Phase 2: Testing & Validation (2-3 days)
- [ ] Unit tests for each node (core logic)
- [ ] Integration tests (multi-node workflows)
- [ ] Version tracking validation
- [ ] Error handling & fallback scenarios
- [ ] Performance testing (token usage per node)

### Phase 3: API & Frontend Integration (2-3 days)
- [ ] Create routes_step8a.py or extend routes_proposal.py
- [ ] Add node-status endpoint
- [ ] Add validate-node endpoint
- [ ] Update frontend to show 8A-8F node statuses
- [ ] Wire up version selection for STEP 8 nodes

### Phase 4: Gap Analysis & Improvement (1-2 days)
- [ ] Run gap analysis: `/pdca analyze step-8a-new-nodes`
- [ ] Identify gaps vs design
- [ ] Auto-iterate if match < 90%
- [ ] Final validation

### Phase 5: Documentation & Deployment (1 day)
- [ ] Generate completion report: `/pdca report step-8a-new-nodes`
- [ ] Document node integration patterns
- [ ] Create runbooks for common scenarios
- [ ] Deploy to staging/production

---

## 📝 Design Specifications

### 8A: proposal_customer_analysis

**Input**:
- rfp_analysis (existing): Budget, scope, domain
- strategy (existing): Positioning, win themes
- kb_refs (existing): Client intel references

**Output** (New Pydantic model):
```python
class CustomerProfile(BaseModel):
    decision_drivers: list[str]          # What influences their decision
    budget_authority: str                # Who controls budget
    internal_politics: str               # Organizational dynamics
    pain_points: list[str]               # Problems to solve
    success_metrics: list[str]           # How they measure success
    key_stakeholders: list[dict]         # Names, roles, interests
    risk_perception: str                 # What scares them
    timeline_pressure: str               # Urgency level
```

**Logic**:
1. Extract client info from RFP + strategy context
2. Query KB for existing client intel
3. Generate customer profile via Claude
4. Store as version, update active_versions

**Versioning**:
- output_key: "customer_profile"
- node_name: "proposal_customer_analysis"
- created_reason: "initial_analysis" | "reanalysis_after_change"

---

### 8B: proposal_section_validator

**Input**:
- proposal_sections (existing list)
- rfp_analysis (existing)
- strategy (existing)

**Output** (New Pydantic model):
```python
class ValidationReport(BaseModel):
    total_sections: int
    passed: int
    failed: int
    warnings: list[dict]                 # {section_id, issue, severity}
    compliance_gaps: list[str]           # Missing RFP requirements
    style_issues: list[str]              # Formatting, tone inconsistencies
    cross_section_conflicts: list[str]   # Contradictions between sections
    recommendations: list[str]
    is_ready_to_submit: bool
```

**Logic**:
1. Validate each section against rfp_analysis requirements
2. Check style consistency across sections
3. Detect compliance gaps (missing mandatory requirements)
4. Generate validation report via Claude
5. Create version

**Versioning**:
- output_key: "validation_report"
- node_name: "proposal_section_validator"
- created_reason: "initial_validation" | "revalidation_after_revision"

---

### 8C: proposal_sections_consolidation

**Input**:
- proposal_sections (existing multiple versions)
- validation_report (from 8B)
- selected section versions (user choice during move)

**Output** (New Pydantic model):
```python
class ConsolidatedProposal(BaseModel):
    final_sections: list[ProposalSection]
    section_lineage: dict                # {section_id: {original_version, selected_version}}
    resolved_conflicts: list[str]
    quality_metrics: dict                # Coverage %, compliance %, style score
    submission_ready: bool
```

**Logic**:
1. Accept validated sections + user choices
2. Merge sections, resolve any conflicts
3. Ensure cross-section consistency
4. Generate final consolidated version
5. Create version artifact

**Versioning**:
- output_key: "consolidated_proposal"
- node_name: "proposal_sections_consolidation"
- parent_node_name: "proposal_section_validator"
- parent_version: (from validation_report version)

---

### 8D: mock_evaluation_analysis

**Input**:
- proposal_sections (from 8C)
- rfp_analysis (evaluation criteria)
- strategy (positioning)

**Output** (New Pydantic model):
```python
class MockEvalResult(BaseModel):
    estimated_score: int                 # 0-100
    score_breakdown: dict                # {criterion: score}
    strengths: list[str]                 # Evaluator would favor
    weaknesses: list[str]                # Likely to lose points
    win_probability: float               # 0.0-1.0
    key_risks: list[str]
    recommendations: list[str]           # How to strengthen
```

**Logic**:
1. Simulate evaluator perspective
2. Score against RFP evaluation criteria
3. Identify strengths/weaknesses
4. Generate recommendations
5. Create version

**Versioning**:
- output_key: "mock_eval_result"
- node_name: "mock_evaluation_analysis"
- parent_node_name: "proposal_sections_consolidation"

---

### 8E: mock_evaluation_feedback_processor

**Input**:
- mock_eval_result (from 8D)
- proposal_sections (current version)

**Output** (New Pydantic model):
```python
class FeedbackSummary(BaseModel):
    critical_gaps: list[dict]            # Must fix {section, issue, priority}
    improvement_opportunities: list[dict] # Nice to have
    rewrite_guidance: dict               # Per-section guidance
    estimated_improvement: int           # Expected score gain
    timeline_estimate: str               # How long to fix
```

**Logic**:
1. Process mock evaluation results
2. Prioritize issues by impact
3. Generate rewrite guidance per section
4. Estimate effort required
5. Create version

**Versioning**:
- output_key: "feedback_summary"
- node_name: "mock_evaluation_feedback_processor"

---

### 8F: proposal_write_next_v2

**Input**:
- feedback_summary (from 8E)
- dynamic_sections (from plan_story)
- current_section_index (state tracking)

**Output** (Existing ProposalSection, updated):
- proposal_sections (list, next version)

**Logic**:
1. Accept feedback summary
2. Rewrite sections based on guidance
3. Update current_section_index
4. Create new version of proposal_sections
5. Support rework loop (return to 8B if needed)

**Versioning**:
- output_key: "proposal_sections"
- node_name: "proposal_write_next_v2"
- created_reason: "rewrite_after_mock_eval"

---

## 🔀 Graph Integration

### New Edges in graph.py

```python
# 8A: After strategy complete
strategy_generate → proposal_customer_analysis

# 8B: After customer analysis
proposal_customer_analysis → proposal_section_validator

# 8C: After validation (possibly conditional review)
proposal_section_validator → proposal_sections_consolidation

# 8D: After consolidation
proposal_sections_consolidation → mock_evaluation_analysis

# 8E: After mock eval
mock_evaluation_analysis → mock_evaluation_feedback_processor

# 8F: After feedback
mock_evaluation_feedback_processor → proposal_write_next_v2

# Rework loop (conditional)
proposal_write_next_v2 → proposal_section_validator (if revalidation needed)
proposal_write_next_v2 → END (if complete) or → presentation_strategy
```

### Routing Logic

**proposal_section_validator** routing:
- If passed & ready → proposal_sections_consolidation
- If failed & critical → interrupt for human review
- If passed & warnings → conditional path (auto-continue or review)

**proposal_write_next_v2** routing:
- If approved → next_phase (presentation_strategy or END)
- If needs_revalidation → proposal_section_validator
- If max_iterations → force to END (quality gate)

---

## 🧪 Testing Strategy

### Unit Tests (≥80% coverage per node)
- Test core logic isolation (no LangGraph state)
- Mock Claude API responses
- Test Pydantic model validation
- Test versioning calls

### Integration Tests
- Multi-node workflow execution
- State accumulation across nodes
- Version artifact creation & storage
- Dependency validation

### E2E Tests
- Full STEP 8A-8F workflow
- User version selection during move
- Rollback to earlier node
- Re-execution with modified inputs

### Performance Tests
- Token usage per node (aim: <5K per node)
- Execution time per node
- Database query performance for version lookups

---

## 📋 Acceptance Criteria

### Code Quality
- [ ] No type errors (mypy strict)
- [ ] No lint issues (ruff)
- [ ] All requirements.txt dependencies documented
- [ ] Error handling for all failure scenarios
- [ ] Logging for debugging (JSON format)

### Functionality
- [ ] Each node creates versioned artifacts
- [ ] Dependency validation works across all nodes
- [ ] Version selection modal works for STEP 8 moves
- [ ] State propagates correctly through graph
- [ ] Audit trail captures all version decisions

### Testing
- [ ] ≥80% code coverage per node
- [ ] All unit tests pass
- [ ] Integration tests validate multi-node workflows
- [ ] E2E workflow passes end-to-end
- [ ] Error scenarios handled gracefully

### Documentation
- [ ] README for STEP 8A implementation
- [ ] Docstrings on all public functions
- [ ] Integration guide for future nodes
- [ ] Runbooks for common issues

### Deployment
- [ ] Gap analysis ≥90% match rate
- [ ] Code review approval
- [ ] Staging environment validation
- [ ] Production deployment plan

---

## 🚨 Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| State schema conflicts | Medium | High | Review state.py changes early, test with existing workflows |
| Token overflow (Claude API) | Medium | High | Monitor per-node token usage, implement prompt optimization |
| Circular dependencies in graph | Low | High | Careful edge definition, validate DAG structure |
| Version storage explosion | Low | Medium | Implement checksum deduplication (already in place) |
| Performance regression | Medium | Medium | Benchmark before/after, optimize indexes |
| Integration bugs with legacy code | Medium | Medium | Comprehensive E2E testing |

---

## 📅 Timeline Estimate

| Phase | Duration | Key Milestones |
|-------|----------|-----------------|
| Plan & Design | 1-2 days | ✓ This document, team review |
| Implementation | 4-5 days | 2 nodes/day (parallel), versioning integrated |
| Testing | 2-3 days | Unit tests, integration tests, performance |
| Gap Analysis | 1 day | `/pdca analyze` run, fix gaps |
| Documentation & Deploy | 1 day | Final report, deployment |
| **Total** | **10-12 days** | **Ready by mid-April** |

---

## 👥 Team & Responsibilities

| Role | Responsibility | Effort |
|------|-----------------|--------|
| Backend Developer | Implement 6 nodes, versioning integration | 80% |
| QA Engineer | Unit & integration tests, performance validation | 15% |
| Product Owner | Review designs, acceptance criteria | 5% |

---

## 📚 Reference Materials

- **Existing Implementation**: `docs/02-design/ARTIFACT_VERSION_IMPLEMENTATION_SUMMARY.md`
- **Versioning Guide**: `app/graph/nodes/versioning_integration_guide.md`
- **Service Layer**: `app/services/version_manager.py`
- **State Schema**: `app/graph/state.py`
- **Integration Pattern**: `app/graph/nodes/strategy_generate.py` (example)

---

## ✅ Sign-Off

**Plan Status**: Ready for Design
**Next Step**: `/pdca design step-8a-new-nodes`
**Estimated Design Duration**: 2-3 days

---

*Plan created: 2026-03-30*
