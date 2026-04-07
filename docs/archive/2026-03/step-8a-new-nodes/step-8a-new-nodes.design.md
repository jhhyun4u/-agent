# STEP 8A: New Nodes with Artifact Versioning — Design Document

**Feature**: step-8a-new-nodes
**Version**: 1.0 Design
**Date**: 2026-03-30
**Status**: Ready for Implementation
**Reference Plan**: `docs/01-plan/features/step-8a-new-nodes.plan.md`

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [State Schema Extensions](#state-schema-extensions)
3. [Node Specifications](#node-specifications)
4. [Graph Integration](#graph-integration)
5. [API Endpoint Design](#api-endpoint-design)
6. [Versioning Integration](#versioning-integration)
7. [Error Handling & Edge Cases](#error-handling--edge-cases)
8. [Implementation Checklist](#implementation-checklist)

---

## 🏗️ Architecture Overview

### 6-Node Pipeline Architecture

```
strategy_generate (Phase 7)
    ↓
proposal_customer_analysis (8A)  ← [NEW] Deep client intelligence
    ↓
proposal_section_validator (8B)  ← [NEW] Quality gate
    ↓
proposal_sections_consolidation (8C)  ← [NEW] Conflict resolution
    ↓
mock_evaluation_analysis (8D)  ← [NEW] Evaluator simulation
    ↓
mock_evaluation_feedback_processor (8E)  ← [NEW] Feedback processing
    ↓
proposal_write_next_v2 (8F)  ← [NEW] Iterative rewrite
    ↓
[Rework Loop] ↔ proposal_section_validator (feedback-driven refinement)
    ↓
presentation_strategy / END
```

### Data Flow with Versioning

```
strategy_generate
    ↓ strategy (v1) → artifact_versions["strategy"]
    ↓
proposal_customer_analysis
    ↓ customer_profile (v1) → artifact_versions["customer_profile"]
    ↓
proposal_section_validator
    ↓ validation_report (v1) → artifact_versions["validation_report"]
    ↓
proposal_sections_consolidation
    ↓ consolidated_proposal (v1) → artifact_versions["consolidated_proposal"]
    ↓ proposal_sections (v2) → artifact_versions["proposal_sections"][1]
    ↓
mock_evaluation_analysis
    ↓ mock_eval_result (v1) → artifact_versions["mock_eval_result"]
    ↓
mock_evaluation_feedback_processor
    ↓ feedback_summary (v1) → artifact_versions["feedback_summary"]
    ↓
proposal_write_next_v2
    ↓ proposal_sections (v3) → artifact_versions["proposal_sections"][2]
```

---

## 📊 State Schema Extensions

### New Pydantic Models

All models inherit from `BaseModel` and use Python 3.11 type hints.

#### 1. CustomerProfile (8A Output)

```python
from pydantic import BaseModel
from typing import Optional

class Stakeholder(BaseModel):
    """Decision-maker or influencer in client organization."""
    name: str
    title: str
    role: str                    # "decision_maker" | "influencer" | "budget_holder" | "user"
    interests: list[str]
    influence_level: int         # 1-5 scale
    contact_info: Optional[str] = None

class CustomerProfile(BaseModel):
    """Deep client intelligence for proposal strategy."""
    client_org: str
    market_segment: str          # Industry/market classification
    organization_size: str       # Small/Medium/Enterprise
    decision_drivers: list[str]  # Top 3-5 factors influencing decision
    budget_authority: str        # Description of how budget approved
    budget_range: Optional[str]  # If disclosed
    internal_politics: str       # Org dynamics, power structures (2-3 sentences)
    pain_points: list[str]       # Problems they're trying to solve
    success_metrics: list[str]   # How they measure project success
    key_stakeholders: list[Stakeholder]
    risk_perception: str         # What concerns them most
    timeline_pressure: str       # Urgency level: "low" | "medium" | "high" | "critical"
    procurement_process: str     # Formal/informal, approval gates
    competitive_landscape: str   # Who else might bid
    prior_experience: Optional[str]  # Similar projects, vendor history
    created_at: str              # ISO timestamp
```

**Size estimate**: ~1.5 KB per profile

---

#### 2. ValidationReport (8B Output)

```python
class ValidationIssue(BaseModel):
    """Single validation finding."""
    section_id: str
    issue_type: str              # "compliance" | "style" | "consistency" | "completeness"
    severity: str                # "error" | "warning" | "info"
    description: str
    location: str                # Where in section (optional line/paragraph reference)
    fix_guidance: Optional[str]
    estimated_fix_effort: str    # "quick" | "medium" | "complex"

class ValidationReport(BaseModel):
    """Quality assurance report for all proposal sections."""
    proposal_id: str
    total_sections: int
    sections_validated: int
    passed_sections: int
    failed_sections: int
    warning_sections: int

    # Categorized findings
    errors: list[ValidationIssue]      # Must fix
    warnings: list[ValidationIssue]    # Should fix
    info: list[ValidationIssue]        # Consider fixing

    # Aggregate analysis
    compliance_gaps: list[str]         # Missing RFP requirements (with severity)
    style_issues: list[str]            # Format, tone, language consistency
    cross_section_conflicts: list[str] # Contradictions between sections

    # Overall assessment
    quality_score: int                 # 0-100
    is_ready_to_submit: bool           # All errors fixed
    primary_concern: Optional[str]     # Top issue if not ready
    recommendations: list[str]         # Priority fixes
    estimated_fix_time: str            # "1-2 hours" | "half day" | "full day" | etc.

    validated_at: str                  # ISO timestamp
```

**Size estimate**: ~3-5 KB per report

---

#### 3. ConsolidatedProposal (8C Output)

```python
class SectionLineage(BaseModel):
    """Track which version of each section was selected."""
    section_id: str
    original_version: int
    selected_version: int
    change_notes: Optional[str]

class ConsolidatedProposal(BaseModel):
    """Merged and validated proposal ready for submission/evaluation."""
    proposal_id: str
    final_sections: list[dict]         # ProposalSection objects (converted to dict)
    section_count: int
    total_word_count: int

    # Lineage tracking
    section_lineage: list[SectionLineage]
    resolved_conflicts: list[str]      # What conflicts were resolved, how
    merge_notes: Optional[str]         # Overall consolidation notes

    # Quality metrics
    quality_metrics: dict              # {coverage: %, compliance: %, style_score: int}
    completeness_score: int            # 0-100
    consistency_score: int             # 0-100
    compliance_score: int              # 0-100

    # Submission readiness
    submission_ready: bool
    blockers: list[str]                # Issues blocking submission (if any)
    warnings: list[str]                # Non-blocking concerns

    consolidated_at: str               # ISO timestamp
```

**Size estimate**: ~20-50 KB (includes full section content)

---

#### 4. MockEvalResult (8D Output)

```python
class ScoreComponent(BaseModel):
    """Individual evaluation criterion score."""
    criterion: str
    max_points: int
    estimated_score: int
    feedback: str
    strengths: list[str]
    weaknesses: list[str]

class MockEvalResult(BaseModel):
    """Simulated evaluation from evaluator perspective."""
    proposal_id: str
    evaluation_method: str             # "A" | "B" (from RFP)
    evaluator_persona: str             # "strict" | "standard" | "lenient"

    # Overall scoring
    total_max_points: int
    estimated_total_score: int        # Sum of component scores
    estimated_percentage: float        # Score as percentage

    # Component breakdown
    score_components: list[ScoreComponent]

    # Analysis
    estimated_rank: str                # "1st" | "2nd-3rd" | "4th+" | "below threshold"
    win_probability: float             # 0.0-1.0
    key_strengths: list[str]           # Top 3 differentiators
    key_weaknesses: list[str]          # Top 3 vulnerabilities
    critical_gaps: list[str]           # Issues losing points

    # Improvement potential
    estimated_max_score: int           # If all weaknesses fixed
    potential_improvement: int         # Points that could be gained
    improvement_recommendations: list[str]

    # Risk assessment
    pass_fail_risk: bool               # Likely to pass minimum threshold
    risk_factors: list[str]            # What could cause failure

    analysis_at: str                   # ISO timestamp
```

**Size estimate**: ~4-6 KB per result

---

#### 5. FeedbackSummary (8E Output)

```python
class FeedbackItem(BaseModel):
    """Prioritized feedback on specific section."""
    section_id: str
    section_title: str
    issue_category: str                # "critical_gap" | "improvement" | "minor"
    priority: int                      # 1-10 (10 = highest)
    issue_description: str
    rewrite_guidance: str              # Specific instructions for fixing
    example_improvement: Optional[str] # Brief example of better approach
    estimated_effort: str              # "quick" | "medium" | "complex"

class FeedbackSummary(BaseModel):
    """Consolidated feedback for proposal improvement."""
    proposal_id: str

    # Feedback categorization
    critical_gaps: list[FeedbackItem]       # Must fix to improve score
    improvement_opportunities: list[FeedbackItem]  # Nice to have

    # Per-section guidance
    section_feedback: dict             # {section_id: [feedback items]}

    # Priority summary
    highest_impact_issues: list[str]   # Top 3 issues affecting score most

    # Rewrite guidance
    rewrite_strategy: str              # Overall approach for improvements
    affected_sections: list[str]       # Which sections to prioritize

    # Effort estimation
    estimated_total_effort: str        # "2-4 hours" | "full day" | "2 days" | etc.
    critical_path_effort: str          # Time to fix just critical gaps

    # Expected improvement
    estimated_score_improvement: int   # Points that could be gained
    estimated_new_score: int           # Score if improvements made
    estimated_new_rank: str            # Potential new ranking

    # Timeline
    recommended_timeline: str          # How long to implement fixes

    processed_at: str                  # ISO timestamp
```

**Size estimate**: ~5-8 KB per summary

---

### State Schema Update

Add to `ProposalState` TypedDict in `app/graph/state.py`:

```python
class ProposalState(TypedDict):
    # ... existing fields ...

    # Phase 1: Artifact Versioning (existing)
    artifact_versions: Annotated[
        dict[str, list[ArtifactVersion]],
        lambda a, b: {**a, **{k: (a.get(k, []) + v) for k, v in b.items()}}
    ]
    active_versions: Annotated[
        dict[str, int],
        lambda a, b: {**a, **b}
    ]

    # Phase 8A-8F: New Node Outputs (new)
    customer_profile: Annotated[Optional[CustomerProfile], _replace]
    validation_report: Annotated[Optional[ValidationReport], _replace]
    consolidated_proposal: Annotated[Optional[ConsolidatedProposal], _replace]
    mock_eval_result: Annotated[Optional[MockEvalResult], _replace]
    feedback_summary: Annotated[Optional[FeedbackSummary], _replace]
```

---

## 🔧 Node Specifications

### Node 8A: proposal_customer_analysis

**File**: `app/graph/nodes/step8a_customer_analysis.py`

**Function Signature**:
```python
async def proposal_customer_analysis(state: ProposalState) -> dict:
    """
    Deep client intelligence analysis.

    Input: rfp_analysis, strategy, kb_refs
    Output: customer_profile (versioned)

    Purpose: Extract and synthesize client decision-making patterns,
    budget authority, pain points, and stakeholder analysis.
    """
```

**Implementation Steps**:

1. **Extract client info from RFP**
   - Organization name & size from bid_detail
   - Industry/market from rfp_analysis.domain
   - Budget range from rfp_analysis.budget
   - Contact info from bid_detail.attachments

2. **Query KB for client intel**
   - Look up existing client records in `kb_references`
   - Search competitor_refs for market context
   - Find prior proposals to same client (if any)

3. **Claude Analysis**
   - Use CUSTOMER_INTELLIGENCE_PROMPT
   - Input: RFP text, strategy positioning, KB references
   - Output: Structured customer_profile
   - Token budget: ~3,000 tokens

4. **Version Creation**
   ```python
   version_num, artifact_version = await execute_node_and_create_version(
       proposal_id=UUID(state["project_id"]),
       node_name="proposal_customer_analysis",
       output_key="customer_profile",
       artifact_data=customer_profile.model_dump(),
       user_id=UUID(state["created_by"]),
       state=state,
       parent_node_name="strategy_generate",
       parent_version=state["active_versions"].get("strategy_generate_strategy", 1)
   )
   ```

5. **Return state update**
   ```python
   return {
       "customer_profile": customer_profile,
       "artifact_versions": {"customer_profile": [artifact_version]},
       "active_versions": {f"proposal_customer_analysis_customer_profile": version_num}
   }
   ```

**Error Handling**:
- Missing RFP data → Use defaults, log warning
- Claude API failure → Log error, return empty profile with error flag
- KB lookup failure → Continue without KB references

**Prompt Template**: `app/prompts/step8a.py`
```python
CUSTOMER_INTELLIGENCE_PROMPT = """
You are a business strategist analyzing a prospect organization for a proposal.

RFP Information:
{rfp_analysis}

Our Strategy:
{strategy}

Known Client Intelligence:
{kb_references}

Generate a detailed customer profile that includes:
1. Decision drivers: What factors will most influence their decision?
2. Budget authority: How is their budget controlled and approved?
3. Internal politics: Key organizational dynamics and power structures
4. Pain points: What problems are they trying to solve?
5. Success metrics: How will they measure project success?
6. Key stakeholders: Who are decision-makers, influencers, users?
7. Risk perception: What are their biggest concerns?
8. Timeline pressure: How urgent is this for them?

Respond in JSON format matching CustomerProfile schema.
"""
```

**Performance**:
- Expected execution time: 5-10 seconds
- Token usage: ~2,500-3,500
- Artifact size: ~1-2 KB

---

### Node 8B: proposal_section_validator

**File**: `app/graph/nodes/step8b_section_validator.py`

**Function Signature**:
```python
async def proposal_section_validator(state: ProposalState) -> dict:
    """
    Quality assurance and compliance validation.

    Input: proposal_sections, rfp_analysis, strategy
    Output: validation_report (versioned)

    Purpose: Check compliance against RFP requirements, style consistency,
    cross-section conflicts, and readiness for submission.
    """
```

**Implementation Steps**:

1. **Compliance Check**
   - Extract mandatory requirements from rfp_analysis.mandatory_reqs
   - Check if proposal_sections cover all requirements
   - Flag missing requirements as errors

2. **Style Consistency Check**
   - Language tone (consistent formality level)
   - Section length (similar depth/length across sections)
   - Format compliance (headers, formatting, structure)
   - Key message repetition (win themes mentioned consistently)

3. **Cross-Section Conflict Detection**
   - Budget numbers consistent across sections
   - Timeline consistent across sections
   - Positioning message consistent
   - Staffing/roles consistent

4. **Claude Validation**
   - Use PROPOSAL_VALIDATION_PROMPT
   - Input: All sections, RFP requirements, strategy
   - Output: Structured validation_report
   - Token budget: ~4,000 tokens

5. **Version Creation** (same pattern as 8A)

**Error Handling**:
- No sections provided → Return empty report with warning
- Claude API failure → Return partial report with available checks
- RFP requirements incomplete → Note limitation in report

**Prompt Template**: `app/prompts/step8b.py`
```python
PROPOSAL_VALIDATION_PROMPT = """
You are a proposal quality assurance expert validating a response to an RFP.

RFP Requirements:
{mandatory_requirements}

Proposal Sections to Validate:
{sections_text}

Our Positioning:
{positioning}

Validate the proposal across these dimensions:

1. Compliance: Does it address all mandatory RFP requirements?
2. Completeness: Are all required topics covered?
3. Consistency: Are messages, budget, timeline, staffing consistent across sections?
4. Quality: Is the writing clear, professional, compelling?
5. Alignment: Does it support our positioning and win themes?

Identify:
- Critical errors (must fix to be compliant)
- Warnings (should fix to strengthen)
- Info messages (consider fixing to improve)

Respond in JSON format matching ValidationReport schema.
"""
```

**Performance**:
- Expected execution time: 10-15 seconds (more data to validate)
- Token usage: ~3,500-4,500
- Artifact size: ~3-5 KB

---

### Node 8C: proposal_sections_consolidation

**File**: `app/graph/nodes/step8c_consolidation.py`

**Function Signature**:
```python
async def proposal_sections_consolidation(state: ProposalState) -> dict:
    """
    Merge validated sections and resolve conflicts.

    Input: proposal_sections (multiple versions), validation_report, selected versions
    Output: consolidated_proposal + proposal_sections_v2 (versioned)

    Purpose: Accept validated sections, apply user selections from version
    modal, merge into final proposal, ensure cross-section consistency.
    """
```

**Implementation Steps**:

1. **Accept User Selections**
   - Get selected_versions from state (set during node move)
   - Extract relevant section versions based on selections
   - Track lineage (which version of each section was chosen)

2. **Merge Sections**
   - Combine selected sections into single proposal_sections list
   - Ensure section order matches dynamic_sections plan
   - Preserve metadata (created_at, created_by, version numbers)

3. **Consistency Enforcement**
   - Use validation_report to identify issues
   - Apply corrections where possible (budget, timeline, staffing)
   - Generate conflict resolution notes

4. **Version Creation** (creates TWO artifacts)
   ```python
   # First artifact: consolidated_proposal metadata
   v1_consolidated, art1 = await execute_node_and_create_version(
       node_name="proposal_sections_consolidation",
       output_key="consolidated_proposal",
       artifact_data=consolidated_proposal.model_dump(),
       state=state
   )

   # Second artifact: proposal_sections (next version)
   v2_sections, art2 = await execute_node_and_create_version(
       node_name="proposal_sections_consolidation",
       output_key="proposal_sections",
       artifact_data=[s.model_dump() for s in final_sections],
       state=state,
       parent_node_name="proposal_section_validator"
   )
   ```

5. **Return state update**
   ```python
   return {
       "consolidated_proposal": consolidated_proposal,
       "proposal_sections": final_sections,
       "artifact_versions": {
           "consolidated_proposal": [art1],
           "proposal_sections": (state.get("artifact_versions", {}).get("proposal_sections", []) + [art2])
       },
       "active_versions": {
           "proposal_sections_consolidation_consolidated_proposal": v1_consolidated,
           "proposal_sections_consolidation_proposal_sections": v2_sections
       }
   }
   ```

**Error Handling**:
- Missing validation_report → Consolidate without validation feedback
- Version mismatch → Use latest available version
- Merge conflicts → Flag in consolidated_proposal.warnings

**Logic**: No Claude call needed (deterministic merging)

**Performance**:
- Expected execution time: 2-3 seconds
- Token usage: 0 (no API calls)
- Artifact size: ~50-100 KB (includes sections)

---

### Node 8D: mock_evaluation_analysis

**File**: `app/graph/nodes/step8d_mock_evaluation.py`

**Function Signature**:
```python
async def mock_evaluation_analysis(state: ProposalState) -> dict:
    """
    Simulate evaluator perspective and scoring.

    Input: proposal_sections, rfp_analysis, strategy
    Output: mock_eval_result (versioned)

    Purpose: Predict evaluation score, identify strengths/weaknesses,
    estimate win probability, provide improvement recommendations.
    """
```

**Implementation Steps**:

1. **Extract Evaluation Criteria**
   - Parse rfp_analysis.eval_items (evaluation criteria)
   - Determine scoring method (A: tech+price, B: other method)
   - Extract point values per criterion

2. **Claude Evaluation Simulation**
   - Use MOCK_EVALUATION_PROMPT
   - Simulate strict/standard/lenient evaluator personas
   - Score each criterion with justification
   - Input: sections, criteria, RFP context
   - Token budget: ~4,500 tokens

3. **Win Probability Calculation**
   ```python
   # Simple heuristic
   estimated_score = sum of criterion scores
   threshold = rfp_analysis.threshold or 70
   if estimated_score >= threshold:
       win_probability = 0.6 + (estimated_score - threshold) * 0.01
   else:
       win_probability = max(0.1, estimated_score / threshold * 0.5)
   ```

4. **Improvement Recommendations**
   - Identify lowest-scoring criteria
   - Suggest specific improvements for each weakness
   - Estimate potential score increase if fixed

5. **Version Creation** (same pattern)

**Prompt Template**: `app/prompts/step8d.py`
```python
MOCK_EVALUATION_PROMPT = """
You are an expert RFP evaluator reviewing a proposal submission.

Evaluation Criteria:
{evaluation_criteria}

Proposal Content:
{proposal_sections}

Our Strategy & Positioning:
{strategy}

Evaluate the proposal as a '{evaluator_type}' evaluator would.

For each criterion:
1. Score: Award points based on criterion definition
2. Feedback: Explain the score
3. Strengths: What the proposal does well here
4. Weaknesses: What's missing or weak

Then provide:
- Overall score assessment
- Win probability estimation
- Key strengths of this proposal
- Critical gaps to address
- Improvement recommendations (if score is low)

Respond in JSON format matching MockEvalResult schema.
"""
```

**Performance**:
- Expected execution time: 15-20 seconds (complex analysis)
- Token usage: ~4,000-5,000
- Artifact size: ~4-6 KB

---

### Node 8E: mock_evaluation_feedback_processor

**File**: `app/graph/nodes/step8e_feedback_processor.py`

**Function Signature**:
```python
async def mock_evaluation_feedback_processor(state: ProposalState) -> dict:
    """
    Process mock evaluation results into actionable feedback.

    Input: mock_eval_result, proposal_sections
    Output: feedback_summary (versioned)

    Purpose: Prioritize issues, generate rewrite guidance per section,
    estimate effort and improvement potential.
    """
```

**Implementation Steps**:

1. **Extract Key Issues**
   - Identify critical gaps (below-threshold criteria)
   - Identify improvement opportunities (medium scores)
   - Calculate impact on final score

2. **Prioritization**
   - Score each issue by impact (how many points it affects)
   - Score by effort (estimated effort to fix)
   - Rank by impact/effort ratio

3. **Generate Rewrite Guidance**
   - For each critical gap, generate specific guidance
   - Suggest examples or approaches to improve
   - Link guidance to specific proposal sections

4. **Claude Processing**
   - Use FEEDBACK_PROCESSING_PROMPT
   - Input: mock_eval_result, sections, weak criteria
   - Output: detailed feedback_summary
   - Token budget: ~3,500 tokens

5. **Version Creation** (same pattern)

**Prompt Template**: `app/prompts/step8e.py`
```python
FEEDBACK_PROCESSING_PROMPT = """
You are a proposal improvement strategist.

Mock Evaluation Results:
{mock_eval_result}

Current Proposal Sections:
{proposal_sections}

RFP Requirements:
{rfp_analysis}

Process the evaluation feedback into actionable improvements:

1. Identify critical gaps (what must be fixed to improve score)
2. Identify opportunities (what could strengthen the proposal)
3. For each section with issues, provide specific rewrite guidance
4. Estimate effort needed to implement each improvement
5. Project improvement if all issues are fixed
6. Prioritize which sections to rewrite first

Respond in JSON format matching FeedbackSummary schema.
"""
```

**Performance**:
- Expected execution time: 10-12 seconds
- Token usage: ~3,000-3,500
- Artifact size: ~5-8 KB

---

### Node 8F: proposal_write_next_v2

**File**: `app/graph/nodes/step8f_rewrite.py`

**Function Signature**:
```python
async def proposal_write_next_v2(state: ProposalState) -> dict:
    """
    Iterative section rewriting based on feedback.

    Input: feedback_summary, dynamic_sections, current_section_index
    Output: proposal_sections_v3 (versioned)

    Purpose: Rewrite sections following feedback guidance, maintain
    consistency, support rework loop (return to 8B if needed).
    """
```

**Implementation Steps**:

1. **Get Rewrite Guidance**
   - Extract feedback_summary for current_section_index
   - Get section-specific guidance and examples

2. **Rewrite Section**
   - Use PROPOSAL_REWRITE_PROMPT
   - Input: current section, feedback guidance, strategy
   - Output: improved section
   - Token budget: ~3,500 per section

3. **Update Section Index**
   ```python
   next_index = state.get("current_section_index", 0) + 1
   # Check if all sections rewritten
   if next_index >= len(state["dynamic_sections"]):
       all_done = True
   else:
       all_done = False
   ```

4. **Version Creation**
   ```python
   version_num, artifact_version = await execute_node_and_create_version(
       node_name="proposal_write_next_v2",
       output_key="proposal_sections",
       artifact_data=[s.model_dump() for s in updated_sections],
       state=state,
       parent_node_name="proposal_sections_consolidation"
   )
   ```

5. **Routing Decision**
   - If all sections rewritten: route to presentation_strategy
   - If feedback indicates more validation needed: route back to 8B
   - If iteration limit reached (e.g., 3 times): force to END

**Prompt Template**: `app/prompts/step8f.py`
```python
PROPOSAL_REWRITE_PROMPT = """
You are an expert proposal writer improving a proposal section.

Original Section:
{original_section}

Feedback Guidance:
{feedback_guidance}

Our Positioning & Strategy:
{strategy}

Rewrite this section to address the feedback while:
- Maintaining our key messages and positioning
- Improving clarity and persuasiveness
- Staying within appropriate length
- Ensuring consistency with other sections

Respond with the rewritten section in the same format as the original.
"""
```

**Performance**:
- Expected execution time: 10-15 seconds per section
- Token usage: ~3,000-3,500 per section
- Artifact size: Variable (updated sections)

**Edge Cases**:
- feedback_summary missing → Use default rewrite prompt
- Invalid section_index → Reset to 0
- Max iterations reached → Force completion

---

## 🔀 Graph Integration

### Graph Construction Updates

**File**: `app/graph/graph.py`

Add nodes to graph builder:

```python
def build_graph() -> StateGraph:
    graph_builder = StateGraph(ProposalState)

    # ... existing nodes ...

    # Phase 8A-8F: New analysis nodes
    graph_builder.add_node("proposal_customer_analysis", proposal_customer_analysis)
    graph_builder.add_node("proposal_section_validator", proposal_section_validator)
    graph_builder.add_node("proposal_sections_consolidation", proposal_sections_consolidation)
    graph_builder.add_node("mock_evaluation_analysis", mock_evaluation_analysis)
    graph_builder.add_node("mock_evaluation_feedback_processor", mock_evaluation_feedback_processor)
    graph_builder.add_node("proposal_write_next_v2", proposal_write_next_v2)

    # Add edges
    graph_builder.add_edge("strategy_generate", "proposal_customer_analysis")
    graph_builder.add_edge("proposal_customer_analysis", "proposal_section_validator")
    graph_builder.add_conditional_edges(
        "proposal_section_validator",
        route_after_validation,  # New routing function
        {
            "consolidate": "proposal_sections_consolidation",
            "review": "review_node",  # Interrupt for human review
            "rework": "proposal_write_next",  # Back to writing
        }
    )
    graph_builder.add_edge("proposal_sections_consolidation", "mock_evaluation_analysis")
    graph_builder.add_edge("mock_evaluation_analysis", "mock_evaluation_feedback_processor")
    graph_builder.add_conditional_edges(
        "mock_evaluation_feedback_processor",
        route_after_feedback,  # New routing function
        {
            "rewrite": "proposal_write_next_v2",
            "review": "review_node",
        }
    )
    graph_builder.add_conditional_edges(
        "proposal_write_next_v2",
        route_after_rewrite,  # New routing function
        {
            "revalidate": "proposal_section_validator",
            "next_phase": "presentation_strategy",
            "complete": END,
        }
    )

    return graph_builder.compile()
```

### Routing Functions

**File**: `app/graph/edges.py`

```python
def route_after_validation(state: ProposalState) -> str:
    """Route after 8B validation."""
    validation_report = state.get("validation_report")

    if not validation_report:
        return "consolidate"

    # If critical errors, interrupt for review
    if validation_report.errors:
        return "review"

    # Otherwise proceed
    return "consolidate"


def route_after_feedback(state: ProposalState) -> str:
    """Route after 8E feedback processing."""
    feedback_summary = state.get("feedback_summary")
    mock_eval = state.get("mock_eval_result")

    if not feedback_summary or not mock_eval:
        return "rewrite"

    # If win probability < 30%, return for rewrite
    if mock_eval.win_probability < 0.3:
        return "rewrite"

    # Otherwise review
    return "review"


def route_after_rewrite(state: ProposalState) -> str:
    """Route after 8F rewrite."""
    section_index = state.get("current_section_index", 0)
    dynamic_sections = state.get("dynamic_sections", [])

    # If more sections to rewrite, stay in rewrite loop
    if section_index < len(dynamic_sections) - 1:
        return "rewrite"

    # Check if feedback indicates more validation needed
    feedback_summary = state.get("feedback_summary")
    if feedback_summary and feedback_summary.critical_gaps:
        # After first pass, could revalidate
        return "revalidate"

    # Move to next phase
    return "next_phase"
```

---

## 📡 API Endpoint Design

### New Routes File

**File**: `app/api/routes_step8a.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID
from app.graph.graph import get_graph
from app.services.version_manager import validate_move_and_resolve_versions
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/proposals", tags=["step-8a"])

@router.get("/{proposal_id}/node-status/{node_name}")
async def get_node_status(
    proposal_id: UUID,
    node_name: str,
    current_user = Depends(get_current_user)
) -> dict:
    """
    Get status and output of specific node in workflow.

    Returns: {
        node_name: str,
        status: "pending" | "running" | "completed" | "error",
        output: dict (if completed),
        version_info: {
            latest_version: int,
            active_version: int,
            total_versions: int
        },
        error: str (if failed),
        updated_at: str (ISO timestamp)
    }
    """
    # Get workflow state
    graph = get_graph()
    state = await graph.aget_state(proposal_id)

    if not state:
        raise HTTPException(404, "Proposal not found")

    # Extract node output
    output_key = _get_output_key_for_node(node_name)
    node_output = state.get(output_key)

    # Get version info
    artifact_versions = state.get("artifact_versions", {})
    versions = artifact_versions.get(output_key, [])
    active_versions = state.get("active_versions", {})
    active_v = active_versions.get(f"{node_name}_{output_key}")

    return {
        "node_name": node_name,
        "status": "completed" if node_output else "pending",
        "output": node_output.model_dump() if node_output else None,
        "version_info": {
            "latest_version": len(versions),
            "active_version": active_v or 0,
            "total_versions": len(versions)
        },
        "updated_at": versions[-1].created_at if versions else None
    }


@router.post("/{proposal_id}/validate-node/{node_name}")
async def validate_node_execution(
    proposal_id: UUID,
    node_name: str,
    current_user = Depends(get_current_user)
) -> dict:
    """
    Pre-validate node can execute with current state.

    Returns: {
        feasible: bool,
        required_inputs: [input_keys],
        missing_inputs: [input_keys],
        blockers: [strings],
        warnings: [strings]
    }
    """
    graph = get_graph()
    state = await graph.aget_state(proposal_id)

    if not state:
        raise HTTPException(404, "Proposal not found")

    # Define input requirements per node
    requirements = {
        "proposal_customer_analysis": ["rfp_analysis", "strategy"],
        "proposal_section_validator": ["proposal_sections", "rfp_analysis"],
        "proposal_sections_consolidation": ["proposal_sections", "validation_report"],
        "mock_evaluation_analysis": ["proposal_sections", "rfp_analysis"],
        "mock_evaluation_feedback_processor": ["mock_eval_result", "proposal_sections"],
        "proposal_write_next_v2": ["feedback_summary", "dynamic_sections"]
    }

    required = requirements.get(node_name, [])
    missing = [k for k in required if not state.get(k)]

    return {
        "feasible": len(missing) == 0,
        "required_inputs": required,
        "missing_inputs": missing,
        "blockers": [f"Missing {k}" for k in missing] if missing else [],
        "warnings": []
    }


@router.get("/{proposal_id}/versions/{output_key}")
async def get_artifact_versions(
    proposal_id: UUID,
    output_key: str,
    current_user = Depends(get_current_user)
) -> dict:
    """
    List all versions of specific artifact output.

    Returns: {
        output_key: str,
        versions: [
            {
                version: int,
                created_at: str,
                created_by: str,
                created_reason: str,
                is_active: bool,
                artifact_size: int,
                used_by: [strings]
            }
        ],
        active_version: int
    }
    """
    graph = get_graph()
    state = await graph.aget_state(proposal_id)

    if not state:
        raise HTTPException(404, "Proposal not found")

    artifacts = state.get("artifact_versions", {})
    versions = artifacts.get(output_key, [])
    active_versions = state.get("active_versions", {})

    return {
        "output_key": output_key,
        "versions": [v.model_dump() for v in versions],
        "active_version": active_versions.get(f"*_{output_key}", 1)
    }
```

### Endpoint Integration

Add to `app/main.py`:
```python
from app.api.routes_step8a import router as step8a_router
app.include_router(step8a_router)
```

---

## 🔄 Versioning Integration

### Automatic Versioning Pattern

Each node follows this pattern (as specified in artifact-version-system):

```python
# At end of node execution
from app.services.version_manager import execute_node_and_create_version

version_num, artifact_version = await execute_node_and_create_version(
    proposal_id=UUID(state["project_id"]),
    node_name="node_name_here",
    output_key="output_key_here",
    artifact_data=output_object.model_dump(),  # Convert Pydantic to dict
    user_id=UUID(state["created_by"]),
    state=state,
    parent_node_name=optional_parent,
    parent_version=optional_parent_version
)

# Update state with version info
return {
    "output_key": output_object,  # Store the object itself
    "artifact_versions": {
        "output_key": [artifact_version]  # Store in list (per-key merge reducer)
    },
    "active_versions": {
        **state.get("active_versions", {}),
        f"node_name_output_key": version_num
    }
}
```

### Version Selection During Move

When user moves between nodes with versions:

1. **Frontend detects versioned inputs** (via VersionSelectionModal)
2. **User selects which version to use** for each required input
3. **Move updates state** with selected_versions dict
4. **Target node receives selected inputs** from artifact_versions
5. **Audit trail captures decision** in version_selection_history

---

## 🚨 Error Handling & Edge Cases

### Error Scenarios

| Scenario | Node | Handling |
|----------|------|----------|
| Missing RFP data | 8A | Use defaults, log warning, continue |
| Claude API timeout | Any | Retry once, fallback to partial result |
| State corruption | Any | Return error, log incident |
| Version mismatch | 8C-8F | Use latest available, log discrepancy |
| Circular reference | Graph | Validate DAG structure on build |
| Token overflow | Any AI node | Truncate input, log warning |
| Empty validation report | 8B | Return pass-all report, flag as incomplete |
| No improvements found | 8E | Return "already optimized" feedback |

### Implementation Details

```python
# Standard error handling pattern
try:
    result = await operation()
    return result
except ClaudeAPIError as e:
    logger.error(f"Claude API error in {node_name}: {str(e)}")
    # Return fallback state
    return fallback_state()
except ValidationError as e:
    logger.error(f"Validation error: {str(e)}")
    raise TenopAPIError(
        code="VALIDATION_ERROR",
        message=f"Invalid data in {node_name}",
        status_code=400
    )
except Exception as e:
    logger.exception(f"Unexpected error in {node_name}")
    raise TenopAPIError(
        code="INTERNAL_ERROR",
        message="Processing failed",
        status_code=500
    )
```

### Edge Case Handling

**Empty proposal_sections**:
- Validator: Return report with "no sections to validate"
- Consolidation: Return empty consolidated_proposal with warning
- Evaluation: Return "cannot evaluate" result

**Invalid selection during move**:
- Check selected_versions against available_versions
- Filter out invalid selections
- Use active version as fallback

**State not found**:
- Verify proposal_id exists in database
- Return 404 with helpful message
- Don't create partial state

---

## ✅ Implementation Checklist

### Phase 0: Setup (Prep)
- [ ] Create `app/graph/nodes/step8a_customer_analysis.py`
- [ ] Create `app/graph/nodes/step8b_section_validator.py`
- [ ] Create `app/graph/nodes/step8c_consolidation.py`
- [ ] Create `app/graph/nodes/step8d_mock_evaluation.py`
- [ ] Create `app/graph/nodes/step8e_feedback_processor.py`
- [ ] Create `app/graph/nodes/step8f_rewrite.py`
- [ ] Create `app/prompts/step8a.py` through `step8f.py`
- [ ] Create `app/api/routes_step8a.py`
- [ ] Create `tests/test_step8a_nodes.py`
- [ ] Update `app/graph/state.py` with new Pydantic models
- [ ] Update `app/graph/graph.py` with new nodes and edges

### Phase 1: Implementation (Do)
- [ ] **Week 1**: Implement nodes 8A + 8B (parallel)
  - [ ] Define Pydantic models (CustomerProfile, ValidationReport)
  - [ ] Write prompt templates
  - [ ] Implement node logic
  - [ ] Add versioning calls
  - [ ] Write unit tests (≥80% coverage)
  - [ ] Verify mypy + ruff pass

- [ ] **Week 1-2**: Implement nodes 8C + 8D
  - [ ] Define Pydantic models (ConsolidatedProposal, MockEvalResult)
  - [ ] Write prompt templates
  - [ ] Implement node logic
  - [ ] Add versioning calls
  - [ ] Write unit tests
  - [ ] Verify mypy + ruff pass

- [ ] **Week 2**: Implement nodes 8E + 8F
  - [ ] Define Pydantic models (FeedbackSummary)
  - [ ] Write prompt templates
  - [ ] Implement node logic
  - [ ] Add versioning calls
  - [ ] Write unit tests
  - [ ] Verify mypy + ruff pass

- [ ] Graph Integration
  - [ ] Add all nodes to graph builder
  - [ ] Define routing functions
  - [ ] Test edges are connected
  - [ ] Verify no orphaned nodes

- [ ] API Routes
  - [ ] Implement all 3 endpoints in routes_step8a.py
  - [ ] Add proper auth checks
  - [ ] Add error handling
  - [ ] Test endpoint responses

### Phase 2: Testing
- [ ] Unit tests for each node (~15 tests per node = 90 tests total)
- [ ] Integration tests (multi-node workflows)
- [ ] Version tracking validation
- [ ] Error handling & edge cases
- [ ] Performance testing (token usage)
- [ ] E2E workflow test

### Phase 3: Gap Analysis
- [ ] Run `/pdca analyze step-8a-new-nodes`
- [ ] Review gap analysis report
- [ ] Address any HIGH/MEDIUM gaps

### Phase 4: Code Quality
- [ ] `mypy --strict app/graph/nodes/step8*.py` (0 errors)
- [ ] `ruff check app/graph/nodes/step8*.py` (0 violations)
- [ ] Update `requirements.txt` with any new dependencies
- [ ] Code review for patterns & consistency

### Pre-Deployment
- [ ] All tests passing (unit + integration + E2E)
- [ ] Gap analysis ≥90% match
- [ ] No blocking issues
- [ ] Documentation complete
- [ ] Runbook created for common issues

---

## 📚 Reference Files Structure

```
app/
├── graph/
│   ├── state.py                 ← Update with new Pydantic models
│   ├── graph.py                 ← Add nodes & edges
│   ├── edges.py                 ← Add routing functions
│   └── nodes/
│       ├── step8a_customer_analysis.py      ← NEW
│       ├── step8b_section_validator.py      ← NEW
│       ├── step8c_consolidation.py          ← NEW
│       ├── step8d_mock_evaluation.py        ← NEW
│       ├── step8e_feedback_processor.py     ← NEW
│       ├── step8f_rewrite.py                ← NEW
│       └── versioning_integration_guide.md  ← Reference
│
├── prompts/
│   ├── step8a.py                ← NEW
│   ├── step8b.py                ← NEW
│   ├── step8c.py                ← NEW (if needed)
│   ├── step8d.py                ← NEW
│   ├── step8e.py                ← NEW
│   └── step8f.py                ← NEW
│
├── api/
│   └── routes_step8a.py         ← NEW
│
└── services/
    └── version_manager.py       ← Use existing

tests/
└── test_step8a_nodes.py         ← NEW

docs/
├── 01-plan/features/
│   └── step-8a-new-nodes.plan.md    ← Reference
└── 02-design/features/
    └── step-8a-new-nodes.design.md  ← THIS FILE
```

---

## 🎯 Design Goals Met

✅ **Extensibility**: 6-node pipeline designed for future additions
✅ **Modularity**: Each node standalone, reusable prompts
✅ **Type Safety**: Full Pydantic models with validation
✅ **Auditability**: Version tracking, audit trail via version_selection_history
✅ **Error Resilience**: Fallback behavior, comprehensive error handling
✅ **Testability**: Clear separation of concerns, mockable components
✅ **Performance**: Token budget targets, async/await patterns

---

**Design Status**: ✅ Ready for Implementation

**Next Step**: `/pdca do step-8a-new-nodes`

---

*Design Document v1.0 — 2026-03-30*
