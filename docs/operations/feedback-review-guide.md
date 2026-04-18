# Feedback Review Process Guide

**Date**: 2026-04-18  
**Phase**: STEP 4A Gap 3 (Feedback Automation - Phase 1: Manual Process)  
**Status**: ✅ Documented

---

## Overview

This guide documents the manual feedback review process for the Harness accuracy improvement system. This process collects user feedback on AI-generated sections and uses it to improve weights and model accuracy.

### Process Flow

```
User Reviews Proposal Section
        ↓
Provides Feedback (APPROVE/REJECT)
        ↓
Feedback Stored in Database
        ↓
Weekly Team Review Meeting
        ↓
Analyze Patterns & Metrics
        ↓
Recommend Weight Adjustments
        ↓
Test New Weights
        ↓
Deploy If Validation Passes
```

---

## Weekly Feedback Review Meeting

**Frequency**: Every Friday (2026-04-19, 2026-04-26, ...)  
**Duration**: 30-45 minutes  
**Attendees**: AI Engineering, Product, QA teams  
**Time**: 14:00 KST (or your timezone)

### Meeting Agenda

1. **Feedback Summary** (5 min)
   - Total feedback collected this week
   - Approval vs Rejection rate
   - Key sections with low feedback

2. **Analysis Phase** (15 min)
   - Review rejected sections
   - Identify common patterns
   - Categorize issues:
     * Accuracy issues (wrong facts)
     * Style issues (formatting, tone)
     * Completeness issues (missing content)
     * Clarity issues (hard to understand)

3. **Decision Phase** (15 min)
   - Weight adjustment recommendations
   - Affected section types
   - Expected impact

4. **Testing & Deployment** (10 min)
   - Test new weights on sample dataset
   - Validation against success criteria
   - Schedule deployment

---

## Feedback Analysis Template

Use this template during weekly meetings to analyze feedback systematically.

### Section Analysis Form

**Section Type**: [executive_summary / technical_details / team / strategy / implementation]

**Feedback This Week**: [X approved, Y rejected]

**Approval Rate**: [X / (X+Y) %]

**Rejected Feedback Reasons**:
- [ ] Factual inaccuracy (%)
- [ ] Style/formatting (%)
- [ ] Incomplete content (%)
- [ ] Clarity issues (%)
- [ ] Other (%)

**Key Issues**:
1. [Issue description and frequency]
2. [Issue description and frequency]
3. [Issue description and frequency]

**Recommended Adjustments**:

| Weight | Current | Recommended | Reasoning |
|--------|---------|-------------|-----------|
| Hallucination | 0.X | 0.X | [Lower = more factual] |
| Persuasiveness | 0.X | 0.X | [Higher = more convincing] |
| Completeness | 0.X | 0.X | [Higher = more thorough] |
| Clarity | 0.X | 0.X | [Higher = clearer] |

**Expected Impact**: F1-Score improvement of ±X%

---

## Database Structure for Feedback

### feedback_entry Table

```sql
CREATE TABLE feedback_entries (
    id UUID PRIMARY KEY,
    proposal_id UUID NOT NULL,
    section_id TEXT NOT NULL,
    section_type TEXT NOT NULL,  -- executive_summary, technical_details, etc.
    user_decision TEXT NOT NULL,  -- APPROVE, REJECT
    reason TEXT,                  -- User explanation
    rating_hallucination INT,     -- 1-5 (1=high hallucination, 5=factual)
    rating_persuasiveness INT,    -- 1-5
    rating_completeness INT,      -- 1-5
    rating_clarity INT,           -- 1-5
    created_at TIMESTAMP,
    reviewed_at TIMESTAMP NULL,
    weight_version INT            -- Which weight version created this section
);
```

### Sample Query for Weekly Review

```python
# Get this week's feedback summary
SELECT 
    section_type,
    COUNT(*) as total_feedback,
    SUM(CASE WHEN user_decision='APPROVE' THEN 1 ELSE 0 END) as approved,
    SUM(CASE WHEN user_decision='REJECT' THEN 1 ELSE 0 END) as rejected,
    AVG(rating_hallucination) as avg_hallucination,
    AVG(rating_persuasiveness) as avg_persuasiveness,
    AVG(rating_completeness) as avg_completeness,
    AVG(rating_clarity) as avg_clarity
FROM feedback_entries
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
  AND reviewed_at IS NULL  -- Not yet analyzed
GROUP BY section_type
ORDER BY total_feedback DESC;
```

---

## Weight Adjustment Decision Criteria

### When to Adjust Weights

**Increase Hallucination Filter** (lower weight tolerance):
- Rejection rate > 30% for factual issues
- Multiple feedback entries mentioning "wrong facts"
- F1-Score degradation in test evaluation

**Increase Persuasiveness Weight**:
- Rejection rate for "weak argument" feedback
- Customer feedback indicating weak positioning
- Low engagement in proposal content

**Increase Completeness Weight**:
- Rejection for "missing sections" or "incomplete"
- Feedback indicating insufficient detail
- Compliance matrix gaps

**Increase Clarity Weight**:
- Rejection for "confusing" or "hard to understand"
- Grammar/style issues
- Structure/flow problems

### Success Criteria for New Weights

- [ ] F1-Score >= 0.96
- [ ] False Negative < 5%
- [ ] False Positive < 8%
- [ ] Latency < 21s (unchanged)
- [ ] Sample test passes (10 random sections)

---

## Monthly Performance Report

Generate monthly report to track improvement over time.

### Report Contents

1. **Feedback Metrics**
   - Total feedback collected
   - Approval rate trend
   - Feedback per section type

2. **Weight History**
   - Weight versions deployed
   - Effectiveness of each version
   - Improvement/degradation

3. **Quality Metrics**
   - F1-Score trend
   - False rate trends
   - Latency trends

4. **Recommendations for Next Month**
   - Sections needing attention
   - Potential optimizations
   - Phase 2 automation readiness

---

## Phase 2: Automated Retraining (Future)

When ready to automate (estimated: May 2026):

1. **Daily Batch Job** (11 PM KST)
   - Collect feedback from last 24 hours
   - Run weight tuning grid search
   - Validate on test dataset

2. **Auto-Deployment**
   - If metrics improve and pass criteria
   - Create version record
   - Deploy new weights
   - Notify team via Slack

3. **Monitoring**
   - Track accuracy in production
   - Alert on degradation
   - Rollback if needed

---

## Quick Reference: Feedback Collection API

### User Provides Feedback

```python
POST /api/proposal/{proposal_id}/feedback
{
    "section_id": "executive_summary",
    "decision": "REJECT",
    "reason": "Factual error about company size",
    "ratings": {
        "hallucination": 2,      # 1=hallucinated, 5=factual
        "persuasiveness": 4,
        "completeness": 4,
        "clarity": 5
    }
}
```

### Team Analyzes Weekly

```python
GET /api/metrics/feedback/weekly-summary
# Returns aggregated feedback for this week

GET /api/metrics/feedback/by-section-type
# Returns feedback grouped by section type for analysis
```

### Implements Weight Adjustment

```python
POST /api/weights/update
{
    "section_type": "technical_details",
    "weights": {
        "hallucination": 0.95,   # Stricter
        "persuasiveness": 0.85,
        "completeness": 0.90,
        "clarity": 0.88
    },
    "notes": "Based on week of 2026-04-18 feedback analysis"
}
```

---

## Troubleshooting

### Low Feedback Rate
- **Issue**: Users not providing feedback
- **Solution**: Add prominent feedback UI, send reminders, incentivize

### Inconsistent Feedback
- **Issue**: Same section gets both APPROVE and REJECT
- **Solution**: Add context clues, improve feedback UI instructions

### Weights Not Improving
- **Issue**: Weight adjustments don't improve F1-Score
- **Solution**: Check feedback quality, review sample sizes, consider other factors

### Performance Degradation
- **Issue**: New weights lower F1-Score
- **Solution**: Rollback to previous version, analyze issue, retry

---

## Support & Questions

For questions about the feedback process:
- Check Phase 2 automation roadmap
- Review historical weight adjustments
- Consult with AI Engineering team

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-18  
**Next Review**: 2026-04-25
