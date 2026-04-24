"""
STEP 4A: Wiki suggestion node for LLM-Wiki integration.

Retrieves Top-5 wiki templates based on section content using HybridSearch.
Re-ranks results using RecommendationEngine (multi-signal: acceptance, freshness, confidence).
Applies confidence filtering and caches results.
"""

import logging
import hashlib
from typing import Optional
from datetime import datetime

from app.graph.state import ProposalState
from app.services.llm_wiki.hybrid_search import HybridSearch
from app.services.llm_wiki.recommendation_engine import RecommendationEngine
from app.services.llm_wiki.embedding_service import EmbeddingService
from app.services.wiki_embedding_cache import get_wiki_cache

logger = logging.getLogger(__name__)

# Configuration
CONFIDENCE_THRESHOLD = 0.7
SEARCH_TOP_K = 5
CACHE_TTL_SECONDS = 3600


def _build_cache_key(section_id: str, section_content: str, org_id: str) -> str:
    """Build deterministic cache key from section metadata.
    
    Args:
        section_id: Section identifier
        section_content: Section content (will be truncated)
        org_id: Organization ID (for multi-org scoping)
    
    Returns:
        SHA256 hash as cache key
    """
    # Truncate content to first 2000 chars for key stability
    content_truncated = section_content[:2000]
    combined = f"{section_id}:{content_truncated}:{org_id}"
    return hashlib.sha256(combined.encode()).hexdigest()


async def wiki_suggestion_node(state: ProposalState) -> dict:
    """
    Retrieve wiki template suggestions for current section.
    
    Flow:
    1. Get current section from proposal_sections[current_section_index]
    2. Build cache key from section_id + content truncated + org_id
    3. Check cache (get_wiki_cache)
    4. If cache miss:
       - Call HybridSearch.search(section_content, org_id, top_k=5)
       - Filter results where confidence_score > 0.7
       - Cache results (TTL=1 hour)
    5. Return {"current_wiki_suggestions": filtered_results}
    
    Args:
        state: ProposalState with current_section_index set
    
    Returns:
        Dict with current_wiki_suggestions key containing Top-5 templates
    """
    start_time = datetime.utcnow()
    
    try:
        # Step 1: Resolve current section
        current_idx = state.get("current_section_index", -1)
        proposal_sections = state.get("proposal_sections", [])
        
        if current_idx < 0 or current_idx >= len(proposal_sections):
            logger.warning(f"Invalid section index: {current_idx}, skipping wiki suggestions")
            return {"current_wiki_suggestions": []}
        
        current_section = proposal_sections[current_idx]
        section_id = current_section.section_id
        section_content = current_section.content
        org_id = state.get("project_id", "unknown_org")  # Use project_id as org proxy
        
        # Step 2: Build cache key
        cache_key = _build_cache_key(section_id, section_content, org_id)
        
        # Step 3: Check cache
        cache = await get_wiki_cache()
        cached_results = await cache.get(cache_key)
        
        if cached_results is not None:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(
                f"Wiki suggestions (cache hit): section_id={section_id}, "
                f"count={len(cached_results)}, latency_ms={elapsed_ms:.1f}"
            )
            return {"current_wiki_suggestions": cached_results}
        
        # Step 4: Search on cache miss
        logger.debug(f"Cache miss for section {section_id}, querying HybridSearch...")

        try:
            hybrid_search = HybridSearch(top_k=SEARCH_TOP_K)
            search_results = await hybrid_search.search(
                query=section_content,
                org_id=org_id,
                top_k=SEARCH_TOP_K
            )
        except Exception as e:
            logger.error(f"HybridSearch failed for section {section_id}: {e}")
            return {"current_wiki_suggestions": []}

        # Step 4b: Re-rank using RecommendationEngine (multi-signal scoring)
        try:
            recommender = RecommendationEngine()
            ranked_results = await recommender.rerank(search_results, org_id=org_id)
        except Exception as e:
            logger.warning(f"RecommendationEngine re-ranking failed, using HybridSearch scores: {e}")
            # Fallback: use search_results as-is
            ranked_results = search_results

        # Filter by confidence threshold and convert to dict
        filtered_results = [
            {
                "section_id": r.section_id,
                "title": r.title,
                "content": r.content,
                "keyword_score": r.keyword_score,
                "semantic_score": r.semantic_score,
                "acceptance_rate": getattr(r, "acceptance_rate", 0.0),  # RecommendationEngine only
                "freshness_score": getattr(r, "freshness_score", 0.5),  # RecommendationEngine only
                "final_score": getattr(r, "final_score", None),  # Use final_score if available
                "rank": r.rank,
            }
            for r in ranked_results
            if getattr(r, "final_score", None) is not None and getattr(r, "final_score") > CONFIDENCE_THRESHOLD
        ]
        
        # Step 5: Cache results
        await cache.set(cache_key, filtered_results, ttl_seconds=CACHE_TTL_SECONDS)
        
        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(
            f"Wiki suggestions (cache miss): section_id={section_id}, "
            f"total_results={len(search_results)}, filtered={len(filtered_results)}, "
            f"latency_ms={elapsed_ms:.1f}"
        )
        
        return {"current_wiki_suggestions": filtered_results}
    
    except Exception as e:
        logger.error(f"Unexpected error in wiki_suggestion_node: {e}", exc_info=True)
        return {"current_wiki_suggestions": []}
