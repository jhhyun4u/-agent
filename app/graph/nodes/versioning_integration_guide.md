# Artifact Versioning Integration Guide

## Overview

This document describes how to integrate artifact versioning into any LangGraph node.

## Integration Pattern

### Step 1: Add Import

```python
from app.services.version_manager import execute_node_and_create_version
```

### Step 2: Add Versioning Call After Artifact Generation

After your node generates an artifact (dict/object), add this code:

```python
# After generating artifact_data dict
artifact_data = {...}  # Your generated artifact

# Create version
version_num, artifact_version = await execute_node_and_create_version(
    proposal_id=UUID(state.get("project_id")),
    node_name="your_node_name",
    output_key="your_output_key",
    artifact_data=artifact_data if isinstance(artifact_data, dict) else artifact_data.model_dump(),
    user_id=UUID(state.get("created_by")),
    parent_node_name=None,  # Or parent node if applicable
    state=state
)
```

### Step 3: Update Return Statement

Return the state with the updated artifact:

```python
return {
    "your_output_key": artifact_data,  # Or the model object
    "current_step": "next_step_name",
}
```

## Node Integration Checklist

### Nodes Requiring Versioning (Phase 1 Focus)

For Phase 1, focus on these nodes that already exist or will be created in STEP 8A:

#### Already Exist (Can Update Now)

- [ ] strategy_generate (→ strategy)
- [ ] plan_nodes - plan_story (→ plan.storylines)
- [ ] plan_nodes - plan_team (→ plan.team)
- [ ] proposal_nodes (→ proposal_sections)

#### STEP 8A Nodes (Create With Versioning)

- [ ] proposal_customer_analysis (→ customer_context)
- [ ] proposal_section_validator (→ section_validation_results)
- [ ] proposal_sections_consolidation (→ sections_consolidation_result)
- [ ] mock_evaluation_analysis (→ mock_evaluation_analysis)
- [ ] mock_evaluation_feedback_processor (→ mock_eval_feedback, rework_instructions)
- [ ] proposal_write_next (→ proposal_sections with version increment)

## Example: strategy_generate Node

### Before

```python
async def strategy_generate(state: ProposalState) -> dict:
    # ... existing code ...
    strategy = Strategy(
        positioning=positioning,
        # ...
    )

    return {
        "strategy": strategy,
        "current_step": "strategy_complete",
    }
```

### After

```python
from app.services.version_manager import execute_node_and_create_version
from uuid import UUID

async def strategy_generate(state: ProposalState) -> dict:
    # ... existing code ...
    strategy = Strategy(
        positioning=positioning,
        # ...
    )

    # Create version
    strategy_data = strategy.model_dump() if hasattr(strategy, "model_dump") else strategy
    version_num, artifact_version = await execute_node_and_create_version(
        proposal_id=UUID(state.get("project_id")),
        node_name="strategy_generate",
        output_key="strategy",
        artifact_data=strategy_data,
        user_id=UUID(state.get("created_by")),
        state=state
    )

    logger.info(f"Strategy v{version_num} created for proposal {state.get('project_id')}")

    return {
        "strategy": strategy,
        "current_step": "strategy_complete",
    }
```

## State Key Mapping

| Node Name                            | Output Key                    | State Field                            | Model                 |
| ------------------------------------ | ----------------------------- | -------------------------------------- | --------------------- |
| strategy_generate                    | strategy                      | state["strategy"]                      | Strategy              |
| proposal_nodes                       | proposal_sections             | state["proposal_sections"]             | list[ProposalSection] |
| plan_nodes                           | plan                          | state["plan"]                          | ProposalPlan          |
| proposal_customer_analysis\*         | customer_context              | state["customer_context"]              | dict                  |
| proposal_section_validator\*         | section_validation_results    | state["section_validation_results"]    | list[dict]            |
| proposal_sections_consolidation\*    | sections_consolidation_result | state["sections_consolidation_result"] | dict                  |
| mock_evaluation_analysis\*           | mock_evaluation_analysis      | state["mock_evaluation_analysis"]      | dict                  |
| mock_evaluation_feedback_processor\* | mock_eval_feedback            | state["mock_eval_feedback"]            | dict                  |
| mock_evaluation_feedback_processor\* | rework_instructions           | state["rework_instructions"]           | dict                  |
| proposal_write_next\*                | proposal_sections             | state["proposal_sections"]             | list[ProposalSection] |

\*STEP 8A nodes (to be created with versioning integrated)

## Testing Pattern

```python
# tests/test_version_integration.py

async def test_strategy_generate_creates_version():
    """Verify strategy_generate creates artifact version"""
    state = {
        "project_id": "test-uuid",
        "created_by": "user-uuid",
        "org_id": "org-uuid",
        # ... other required state fields ...
    }

    result = await strategy_generate(state)

    # Verify version was created in DB
    from app.utils.supabase_client import supabase_async
    versions = await supabase_async.table("proposal_artifacts").select(
        "version"
    ).match({
        "proposal_id": "test-uuid",
        "node_name": "strategy_generate"
    }).execute()

    assert len(versions.data) > 0
    assert result["current_step"] == "strategy_complete"
```

## Important Notes

1. **Always use UUID()** when passing project_id/created_by to execute_node_and_create_version
2. **Convert models to dicts** before passing as artifact_data
3. **Use consistent node_name** - should match the function name
4. **use consistent output_key** - should match the state field name
5. **Pass state parameter** to enable state updates during versioning
6. **Handle async properly** - execute_node_and_create_version is async

## Phase Roadmap

- **Phase 1**: Add versioning to strategy_generate + plan nodes
- **Phase 2**: Add versioning to proposal_nodes (proposal_sections)
- **STEP 8A**: Create all new nodes with versioning integrated from start
