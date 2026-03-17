# Token Tracking Gap Analysis Report

> **Analysis Type**: Gap Analysis (Design vs Implementation)
>
> **Project**: TENOPA Proposer
> **Analyst**: gap-detector
> **Date**: 2026-03-16
> **Design Doc**: Implementation Plan (inline, conversation)

---

## 1. Analysis Overview

### 1.1 Analysis Purpose

Verify that the "node-level token cost auto-tracking" feature is fully implemented as specified in the design plan. The plan describes a ContextVar + decorator approach that tracks token usage per node without modifying node files.

### 1.2 Analysis Scope

| Category | Path |
|----------|------|
| New: token_pricing.py | `app/services/token_pricing.py` |
| New: token_tracking.py | `app/graph/token_tracking.py` |
| New: 005_token_cost.sql | `database/migrations/005_token_cost.sql` |
| Modified: claude_client.py | `app/services/claude_client.py` |
| Modified: graph.py | `app/graph/graph.py` |
| Modified: routes_workflow.py | `app/api/routes_workflow.py` |
| Unchanged (verify): node files | `app/graph/nodes/*.py` |

---

## 2. Category-by-Category Gap Analysis

### 2.1 token_pricing.py (New File)

| Item | Plan | Implementation | Status |
|------|------|----------------|--------|
| MODEL_PRICING dict | Sonnet ($3/$15), Haiku ($0.80/$4), Opus ($15/$75) + cache prices | Sonnet ($3/$15), Haiku ($0.80/$4), Opus ($15/$75) + cache prices | MATCH |
| Model keys | Sonnet/Haiku/Opus (generic) | `claude-sonnet-4-5-20250929`, `claude-haiku-4-5-20251001`, `claude-opus-4-6` (specific IDs) | MATCH |
| Cache prices (Sonnet) | Not specified in detail | cache_read=$0.30, cache_create=$3.75 | MATCH |
| Cache prices (Haiku) | Not specified in detail | cache_read=$0.08, cache_create=$1.00 | MATCH |
| Cache prices (Opus) | Not specified in detail | cache_read=$1.50, cache_create=$18.75 | MATCH |
| Default pricing | Implied | `_DEFAULT_PRICING` = Sonnet (line 30) | MATCH |
| `calculate_cost()` | Separates regular_input from cache tokens | `regular_input = max(0, input_tokens - cache_read - cache_create)` (line 42) | MATCH |
| `summarize_usage()` | Aggregates records -> {input_tokens, output_tokens, cache_read_tokens, cache_create_tokens, total_tokens, cost_usd, model, num_calls} | Returns exactly those 8 fields (lines 69-78) | MATCH |

**Category Score: 100% (8/8 MATCH)**

---

### 2.2 token_tracking.py (New File)

| Item | Plan | Implementation | Status |
|------|------|----------------|--------|
| `track_tokens(node_name)` async decorator | Yes | Yes, `functools.wraps` + async wrapper (lines 18-53) | MATCH |
| Resets ContextVar before node | Yes | `reset_usage_context()` at line 24 | MATCH |
| Runs node | Yes | `await fn(state, *args, **kwargs)` at line 27 | MATCH |
| Collects usage after node | Yes | `get_accumulated_usage()` at line 30 | MATCH |
| Calculates summary with duration_ms | Yes | `summarize_usage(records)` + `summary["duration_ms"] = duration_ms` (lines 33-34) | MATCH |
| Injects into result["token_usage"][node_name] | Yes | Lines 36-38, merges with existing token_usage | MATCH |
| `_persist_ai_task_log()` fire-and-forget | Yes | try/except with `logger.warning` on failure (lines 41-48) | MATCH |
| DB insert fields | proposal_id, step, status, duration_ms, input/output/cache tokens, cost_usd, model | All fields present (lines 68-79), status="complete" hardcoded | MATCH |
| proposal_id source | `state.get("project_id", "")` | `state.get("project_id", "")` at line 42 | MATCH |
| Lazy import of supabase client | Implied | `from app.utils.supabase_client import get_async_client` inside function (line 65) | MATCH |

**Category Score: 100% (10/10 MATCH)**

---

### 2.3 claude_client.py (Modified)

| Item | Plan | Implementation | Status |
|------|------|----------------|--------|
| ContextVar `_current_call_usage` with default `[]` | Yes | `ContextVar("_current_call_usage", default=[])` at line 25 | MATCH |
| `reset_usage_context()` sets fresh list | Yes | Creates `fresh: list[dict] = []`, calls `.set(fresh)` (lines 28-31) | MATCH |
| `get_accumulated_usage()` returns current list | Yes | Returns `_current_call_usage.get()` with LookupError fallback (lines 35-40) | MATCH |
| Usage append after response.usage | With input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens, model | All 5 fields appended (lines 130-136) | MATCH |
| Append wrapped in try/except LookupError | Yes | `try: ... except LookupError: pass` (lines 129-138) | MATCH |
| Return value unchanged | No impact on callers | `claude_generate()` return value unchanged; ContextVar is side-channel only | MATCH |

**Category Score: 100% (6/6 MATCH)**

---

### 2.4 graph.py (Modified -- Node Wrapping)

**Plan: 16 AI nodes wrapped with `track_tokens()`**

| Node | Plan: Wrapped | Implementation | Status |
|------|:---:|----------------|--------|
| rfp_search | Yes | `track_tokens("rfp_search")(rfp_search)` (line 105) | MATCH |
| rfp_analyze | Yes | `track_tokens("rfp_analyze")(rfp_analyze)` (line 110) | MATCH |
| research_gather | Yes | `track_tokens("research_gather")(research_gather)` (line 114) | MATCH |
| go_no_go | Yes | `track_tokens("go_no_go")(go_no_go)` (line 117) | MATCH |
| strategy_generate | Yes | `track_tokens("strategy_generate")(strategy_generate)` (line 121) | MATCH |
| plan_team | Yes | `track_tokens("plan_team")(plan_team)` (line 126) | MATCH |
| plan_assign | Yes | `track_tokens("plan_assign")(plan_assign)` (line 127) | MATCH |
| plan_schedule | Yes | `track_tokens("plan_schedule")(plan_schedule)` (line 128) | MATCH |
| plan_story | Yes | `track_tokens("plan_story")(plan_story)` (line 129) | MATCH |
| plan_price | Yes | `track_tokens("plan_price")(plan_price)` (line 130) | MATCH |
| proposal_write_next | Yes | `track_tokens("proposal_write_next")(proposal_write_next)` (line 136) | MATCH |
| self_review | Yes | `track_tokens("self_review")(self_review_with_auto_improve)` (line 138) | MATCH |
| presentation_strategy | Yes | `track_tokens("presentation_strategy")(presentation_strategy)` (line 142) | MATCH |
| ppt_toc | Yes | `track_tokens("ppt_toc")(ppt_toc)` (line 145) | MATCH |
| ppt_visual_brief | Yes | `track_tokens("ppt_visual_brief")(ppt_visual_brief)` (line 146) | MATCH |
| ppt_storyboard | Yes | `track_tokens("ppt_storyboard")(ppt_storyboard_node)` (line 147) | MATCH |

**Plan: NOT wrapped (non-AI nodes)**

| Node | Plan: Not Wrapped | Implementation | Status |
|------|:---:|----------------|--------|
| review_node variants | Not wrapped | `review_node("search")` etc. -- no track_tokens | MATCH |
| review_section_node | Not wrapped | Direct reference (line 137) | MATCH |
| plan_merge | Not wrapped | Direct reference (line 131) | MATCH |
| rfp_fetch | Not wrapped | Direct reference (line 107) | MATCH |
| _passthrough | Not wrapped | Direct reference (line 125) | MATCH |
| _proposal_start_gate | Not wrapped | Direct reference (line 135) | MATCH |

**Import of track_tokens** | `from app.graph.token_tracking import track_tokens` at line 68 | MATCH |

**Category Score: 100% (23/23 MATCH)**

---

### 2.5 routes_workflow.py (Modified)

| Item | Plan | Implementation | Status |
|------|------|----------------|--------|
| `GET /{proposal_id}/token-usage` endpoint | Yes | Lines 287-311 | MATCH |
| Returns `by_node` | Yes | `"by_node": token_usage` (line 303) | MATCH |
| Returns `total.input_tokens` | Yes | Line 305 | MATCH |
| Returns `total.output_tokens` | Yes | Line 306 | MATCH |
| Returns `total.total_tokens` | Yes | `total_input + total_output` (line 307) | MATCH |
| Returns `total.cost_usd` | Yes | `round(total_cost, 4)` (line 308) | MATCH |
| Returns `total.nodes_executed` | Yes | `len(token_usage)` (line 309) | MATCH |
| `get_workflow_state` enhanced with `token_summary` | Yes | Lines 163-176, `total_cost_usd` + `nodes_tracked` | MATCH |

**Category Score: 100% (8/8 MATCH)**

---

### 2.6 DB Migration (005_token_cost.sql)

| Item | Plan | Implementation | Status |
|------|------|----------------|--------|
| ALTER TABLE ai_task_logs | Yes | `ALTER TABLE ai_task_logs` (line 2) | MATCH |
| ADD cache_read_tokens | Yes | `ADD COLUMN IF NOT EXISTS cache_read_tokens INTEGER DEFAULT 0` (line 3) | MATCH |
| ADD cache_create_tokens | Yes | `ADD COLUMN IF NOT EXISTS cache_create_tokens INTEGER DEFAULT 0` (line 4) | MATCH |
| ADD cost_usd | Yes | `ADD COLUMN IF NOT EXISTS cost_usd NUMERIC(10, 6) DEFAULT 0` (line 5) | MATCH |

**Category Score: 100% (4/4 MATCH)**

---

### 2.7 Node Files Unchanged (Verification)

Grep for `token_tracking`, `track_tokens`, `ContextVar`, `_current_call_usage` inside `app/graph/nodes/` returned **zero results**. Node files are confirmed unmodified.

| Node File | Modified? | Status |
|-----------|:---------:|--------|
| rfp_search.py | No | MATCH |
| rfp_analyze.py | No | MATCH |
| research_gather.py | No | MATCH |
| go_no_go.py | No | MATCH |
| strategy_generate.py | No | MATCH |
| plan_nodes.py | No | MATCH |
| proposal_nodes.py | No | MATCH |
| ppt_nodes.py | No | MATCH |

**Category Score: 100% (8/8 MATCH)**

---

### 2.8 State Schema (Implicit Requirement)

| Item | Plan | Implementation | Status |
|------|------|----------------|--------|
| `token_usage` field in ProposalState | Implied (decorator injects into result["token_usage"]) | `token_usage: Annotated[dict, _merge_dict]` in state.py | MATCH |
| Merge reducer for parallel nodes | Plan fan-out (5 parallel) each produces independent usage | `_merge_dict` reducer merges dicts from parallel nodes | MATCH |

**Category Score: 100% (2/2 MATCH)**

---

### 2.9 Parallel Node Behavior

| Item | Plan | Implementation | Status |
|------|------|----------------|--------|
| ContextVar copy per asyncio task | Plan says each asyncio task inherits ContextVar copy | Python ContextVar semantics: `asyncio.create_task()` copies context automatically. `reset_usage_context()` sets fresh list per node. | MATCH |
| Sequential nodes: no residual data | ContextVar reset each time | `reset_usage_context()` called at wrapper start (line 24 of token_tracking.py) | MATCH |

**Category Score: 100% (2/2 MATCH)**

---

## 3. Overall Scores

| Category | Items | Matched | Score | Status |
|----------|:-----:|:-------:|:-----:|:------:|
| 2.1 token_pricing.py | 8 | 8 | 100% | PASS |
| 2.2 token_tracking.py | 10 | 10 | 100% | PASS |
| 2.3 claude_client.py | 6 | 6 | 100% | PASS |
| 2.4 graph.py (node wrapping) | 23 | 23 | 100% | PASS |
| 2.5 routes_workflow.py | 8 | 8 | 100% | PASS |
| 2.6 DB migration | 4 | 4 | 100% | PASS |
| 2.7 Node files unchanged | 8 | 8 | 100% | PASS |
| 2.8 State schema | 2 | 2 | 100% | PASS |
| 2.9 Parallel behavior | 2 | 2 | 100% | PASS |
| **Overall** | **71** | **71** | **100%** | **PASS** |

```
+---------------------------------------------+
|  Overall Match Rate: 100% (71/71)           |
+---------------------------------------------+
|  MATCH:  71 items (100%)                    |
|  GAP:     0 items (0%)                      |
|  PARTIAL: 0 items (0%)                      |
+---------------------------------------------+
```

---

## 4. Missing Features (Design O, Implementation X)

None.

---

## 5. Added Features (Design X, Implementation O)

| Item | Implementation Location | Description | Severity |
|------|------------------------|-------------|----------|
| Default pricing fallback | token_pricing.py:30 | `_DEFAULT_PRICING` falls back to Sonnet for unknown model strings | LOW (beneficial) |
| `reset_usage_context()` returns the fresh list | claude_client.py:31 | Return value not specified in plan but harmless | LOW (beneficial) |

These are minor implementation enhancements that do not conflict with the design.

---

## 6. Changed Features (Design != Implementation)

None. All specified behaviors match exactly.

---

## 7. Architecture Compliance

| Check | Status |
|-------|--------|
| ContextVar side-channel (no return value change in claude_generate) | PASS |
| Decorator pattern (node files untouched) | PASS |
| Fire-and-forget DB persistence (try/except, non-blocking) | PASS |
| Lazy import of supabase_client in _persist_ai_task_log | PASS |
| State reducer for parallel merge (Annotated[dict, _merge_dict]) | PASS |
| Dependency direction: token_tracking -> claude_client, token_pricing (correct) | PASS |

**Architecture Score: 100%**

---

## 8. Recommended Actions

### 8.1 No Immediate Actions Required

The implementation matches the design plan completely across all 71 verification items.

### 8.2 Minor Observations (Informational)

1. **Model ID specificity**: The plan mentions generic names (Sonnet/Haiku/Opus) while the implementation uses exact model IDs (`claude-sonnet-4-5-20250929`). This is correct -- exact IDs are needed for runtime matching. When Anthropic releases new model versions, `MODEL_PRICING` will need updating.

2. **Streaming calls not tracked**: `claude_generate_streaming()` does not append to ContextVar. This is acceptable since streaming is only used for SSE output, not for node-level generation. If streaming is later used inside graph nodes, usage tracking should be added.

3. **`status: "complete"` hardcoded**: In `_persist_ai_task_log` the status field is always `"complete"`. If a node fails mid-execution (exception before the persist call), no log is written. This is acceptable for a fire-and-forget approach but could be enhanced with error-status logging if needed.

---

## 9. Design Document Updates Needed

None required. Implementation faithfully follows the design.

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-03-16 | Initial gap analysis | gap-detector |
