"""
Shared constants for STEP 8A-8F nodes.

Context window and truncation limits for Claude API calls.
Tuned for optimal accuracy vs. token budget.
"""

from typing import Dict, Any


def normalize_proposal_section(section: Any) -> Dict[str, Any]:
    """
    Normalize proposal section to dictionary format.

    Handles both Pydantic ProposalSection models and dict objects.

    Args:
        section: ProposalSection model or dict

    Returns:
        Dictionary representation of the section
    """
    if hasattr(section, 'model_dump'):
        return section.model_dump()
    return section

# Section content limits for Claude context
# Based on 200K context window and Pre-Flight Check budgets

SECTION_CONTENT_LIMIT_VALIDATION = 2500  # 8B: per-section validation
SECTION_CONTENT_LIMIT_EVALUATION = 2000  # 8D: per-section mock eval
SECTION_CONTENT_LIMIT_FEEDBACK = 2000  # 8E: per-section feedback
SECTION_CONTENT_LIMIT_REWRITE = 4000  # 8F: per-section rewrite (needs full context)

# Combined sections limits
COMBINED_SECTIONS_LIMIT = 8000  # Total sections text across all sections
FEEDBACK_GUIDANCE_LIMIT = 2000  # Feedback text for rewrite guidance
ORIGINAL_SECTION_LIMIT = 4000  # Original section content for rewrite

# Metadata limits
RFP_ANALYSIS_LIMIT = 3000  # RFP analysis text
STRATEGY_LIMIT = 2000  # Strategy text
KB_CONTEXT_LIMIT = 1500  # Knowledge base references

# Rewrite loop protection
MAX_REWRITE_ITERATIONS = 3  # Maximum rewrite cycles per proposal section

# Logging thresholds
WARN_IF_TRUNCATED_OVER_THRESHOLD = True  # Log warnings when content truncated
