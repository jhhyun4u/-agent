# STEP 4A Phase 3: Harness Accuracy Integration & Live Testing

**Date**: 2026-04-18  
**Status**: PLANNING  
**Objective**: Integrate AccuracyEnhancementEngine with harness_proposal_write node and validate F1-score improvement

---

## Overview

Phase 3 integrates the three accuracy-improvement strategies (Confidence Thresholding, Ensemble Voting, Cross-Validation) with the live proposal generation workflow. Instead of pure argmax selection, the harness will use ensemble voting to select the best variant.

### Current State (Phase 2 Complete)

- ✓ ConfidenceThresholder: Ready
- ✓ EnsembleVoter: Ready
- ✓ CrossValidator: Ready
- ✓ All unit tests passing (12/12)

### Integration Point

**File**: `app/graph/nodes/harness_proposal_write.py`
- **Function**: `harness_proposal_write_next(state)` (lines 112-411)
- **Current Logic**: Line 220 uses `harness_result.get("score", 0.0)` (pure argmax)
- **Enhancement Target**: Apply ensemble voting before final score selection

---

## Phase 3 Tasks

### Task 1: Integrate AccuracyEnhancementEngine into harness_proposal_write

**File**: `app/graph/nodes/harness_proposal_write.py`

**Changes**:
```python
# Line 220 (current):
best_score = harness_result.get("score", 0.0)

# Phase 3 (new):
# 1. Extract 3 variant scores and details from harness_result
variant_scores = harness_result.get("scores", {})  # {"conservative": 0.75, "balanced": 0.78, "creative": 0.68}
variant_details = harness_result.get("variant_details", {})  # {"conservative": EvaluationMetrics, ...}

# 2. Apply ensemble voting
if variant_scores and len(variant_scores) == 3:
    ensemble_voter = EnsembleVoter()
    ensemble_result = ensemble_voter.vote(variant_scores, variant_details)
    
    # Use ensemble score instead of argmax
    best_score = ensemble_result.aggregated_score
    harness_result["ensemble_applied"] = True
    harness_result["ensemble_result"] = ensemble_result.to_dict()
else:
    # Fallback to argmax if variants not available
    best_score = harness_result.get("score", 0.0)
    harness_result["ensemble_applied"] = False
```

### Task 2: Add Confidence Estimation to Section Selection

**File**: `app/graph/nodes/harness_proposal_write.py`

**Changes**:
```python
# After ensemble voting (line 240 approx):

# Compute confidence on final selection
if variant_scores:
    thresholder = ConfidenceThresholder()
    confidence_result = thresholder.compute_confidence(variant_scores)
    
    harness_result["confidence"] = confidence_result.confidence
    harness_result["confidence_agreement"] = confidence_result.agreement_level
    harness_result["should_accept"] = confidence_result.should_accept
    
    # Log confidence for monitoring
    logger.info(f"Ensemble confidence: {confidence_result.confidence:.2f} ({confidence_result.agreement_level})")
```

### Task 3: Add Feedback Loop Enhancement

**File**: `app/graph/nodes/harness_proposal_write.py`

**Motivation**: Current feedback loop uses simple score < 0.75 threshold. Phase 3 adds confidence-aware triggering.

**Changes**:
```python
# Line 250 (current):
if best_score < 0.75:

# Phase 3 (improved):
should_run_feedback_loop = (
    best_score < 0.75 or 
    (confidence_result.agreement_level == "LOW" and best_score < 0.85)
)

if should_run_feedback_loop:
    logger.info(f"Feedback loop triggered: score={best_score:.2f}, confidence={confidence_result.agreement_level}")
    # ... feedback loop logic ...
```

### Task 4: Update Logging & Monitoring

**File**: `app/graph/nodes/harness_proposal_write.py`

**Add to return dict** (line 400 approx):
```python
update = {
    "proposal_sections": existing_sections,
    "current_step": "section_written",
    "harness_results": {
        section_id: {
            "score": final_score,
            "ensemble_score": ensemble_result.aggregated_score if ensemble_applied else None,
            "confidence": confidence_result.confidence if ensemble_applied else None,
            "variant": harness_result.get("selected_variant"),
            "variant_scores": variant_scores,
            "improved": improved,
        }
    },
}
```

### Task 5: Create Integration Tests

**File**: `tests/integration/test_harness_accuracy_integration.py` (NEW)

**Tests**:
1. `test_ensemble_voting_applied_in_proposal_write`
   - Verify ensemble voting is called with correct variant data
   - Check aggregated score replaces argmax score

2. `test_confidence_estimation_with_variants`
   - Verify confidence is computed from 3 variants
   - Check agreement level classification

3. `test_feedback_loop_triggered_by_confidence`
   - Low confidence + low score triggers feedback loop
   - High confidence prevents unnecessary feedback

4. `test_end_to_end_proposal_with_ensemble`
   - Generate full proposal section using ensemble
   - Validate score improvement over argmax baseline

### Task 6: Performance Validation

**File**: `scripts/validate_accuracy_improvement.py` (NEW)

**Script logic**:
```python
# 1. Generate 10 sections with old method (argmax only)
old_scores = []
for section in test_sections:
    # harness_result with 3 variants
    best_score = max(scores.values())  # argmax
    old_scores.append(best_score)

# 2. Generate same 10 sections with new method (ensemble)
new_scores = []
for section in test_sections:
    ensemble_result = voter.vote(scores, metrics)
    new_scores.append(ensemble_result.aggregated_score)

# 3. Compare metrics
old_avg = mean(old_scores)
new_avg = mean(new_scores)
improvement = (new_avg - old_avg) / old_avg

print(f"Average score: {old_avg:.4f} → {new_avg:.4f} ({improvement:+.1%})")
print(f"Stability (std): {std(old_scores):.4f} → {std(new_scores):.4f}")
```

---

## Expected Outcomes

| Metric | Baseline | Target | Method |
|--------|----------|--------|--------|
| F1-Score | 0.85 | 0.92 | Ensemble voting |
| Confidence | N/A | 0.80+ | Thresholding |
| Stability | N/A | 0.90+ | k-fold CV |
| False Positive Rate | N/A | <5% | Outlier rejection |

---

## Implementation Timeline

| Task | Estimated Time | Dependencies |
|------|----------------|--------------|
| Task 1: Ensemble Integration | 2-3 hours | Phase 2 complete ✓ |
| Task 2: Confidence Estimation | 1-2 hours | Task 1 complete |
| Task 3: Feedback Loop Enhancement | 1 hour | Task 2 complete |
| Task 4: Logging & Monitoring | 1 hour | Task 3 complete |
| Task 5: Integration Tests | 2-3 hours | Tasks 1-4 complete |
| Task 6: Performance Validation | 1-2 hours | Tasks 1-5 complete |

**Total**: ~8-12 hours (1 day)

---

## Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Ensemble breaks existing harness API | HIGH | Fallback to argmax if variants missing |
| Performance regression | HIGH | Run baseline comparison before/after |
| Integration with feedback loop | MEDIUM | Test confidence-aware triggering |
| Monitoring overhead | LOW | Log only key metrics (score, confidence) |

---

## Rollback Plan

If Phase 3 causes regressions:
1. Revert harness_proposal_write.py to phase 2 state
2. Keep AccuracyEnhancementEngine as standalone (Phase 2 complete)
3. Re-plan Phase 3 with different integration approach

---

## Success Criteria

✓ All integration tests passing (4+ tests)  
✓ No regression in Phase 1/2 tests  
✓ Average section score improved by 5%+  
✓ Confidence estimation functional in 10+ live proposals  
✓ Documentation updated  
✓ Ready for Phase 4: Metrics Monitoring

---

**Next Step**: Confirm Phase 3 scope and begin Task 1 implementation
