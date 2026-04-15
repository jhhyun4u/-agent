"""
Knowledge Management System (llm-wiki) Service.

Unified service for:
- Auto-classification of knowledge chunks
- Semantic + keyword hybrid search
- Context-aware recommendations
- Knowledge health metrics
- Multi-tenant RLS enforcement

Design Ref: §5.1 — Pragmatic Balance architecture
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.models.knowledge_schemas import (
    ClassificationResult,
    SearchRequest,
    SearchFilters,
    SearchResultItem,
    SearchResponse,
    ProposalContext,
    RecommendationResponse,
    RecommendationResultItem,
    FlatHealthMetrics,
    HealthMetrics,
    KnowledgeType,
)
from app.services.claude_client import claude_generate
from app.prompts.knowledge import (
    KNOWLEDGE_CLASSIFICATION_SYSTEM_PROMPT,
    KNOWLEDGE_CLASSIFICATION_USER_TEMPLATE,
)
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


class ClassificationError(Exception):
    """Error during knowledge classification."""
    pass


class KnowledgeManager:
    """
    Unified service for knowledge management operations.

    Handles classification, search, recommendations, and health tracking.
    All operations respect multi-tenant RLS policies via Supabase.
    """

    # ========================================================================
    # CLASSIFICATION (Module-2)
    # ========================================================================

    async def classify_chunk(
        self,
        chunk_id: UUID,
        content: str,
        document_context: Optional[Dict[str, Any]] = None,
    ) -> ClassificationResult:
        """
        Auto-classify a knowledge chunk using Claude API.

        Plan SC-1: Classification must be accurate and confidence-scored
        Design Ref: §5.1 — Unified KnowledgeManager

        Args:
            chunk_id: Document chunk UUID
            content: Chunk content to classify
            document_context: Optional metadata (title, date, source, author)

        Returns:
            ClassificationResult with type, confidence, and any multi-type IDs

        Raises:
            ClassificationError: If classification fails
        """
        try:
            # Prepare LLM prompt
            user_message = KNOWLEDGE_CLASSIFICATION_USER_TEMPLATE.format(
                document_title=document_context.get("title", "Untitled") if document_context else "Untitled",
                created_date=document_context.get("created_date", datetime.utcnow().isoformat()) if document_context else datetime.utcnow().isoformat(),
                document_source=document_context.get("source", "Unknown") if document_context else "Unknown",
                chunk_content=content[:2000]  # Limit to 2000 chars for token efficiency
            )

            # Call Claude API for classification
            response = await claude_generate(
                prompt=user_message,
                system_prompt=KNOWLEDGE_CLASSIFICATION_SYSTEM_PROMPT,
                model="claude-opus-4-6",
                temperature=0.3,  # Low temperature for consistent classification
                max_tokens=1000,
                response_format="json",
                step_name="knowledge_classification"
            )

            # Parse classification response
            # Response is already parsed JSON from claude_generate
            classification_data = response

            # Validate and convert knowledge type
            primary_type_str = classification_data.get("primary_type", "unclassified")
            if primary_type_str == "unclassified":
                # Handle unclassified as lowest confidence
                knowledge_type = KnowledgeType.CAPABILITY
                confidence = Decimal("0.3")
            else:
                # Map string to KnowledgeType enum
                type_mapping = {
                    "capability": KnowledgeType.CAPABILITY,
                    "client_intel": KnowledgeType.CLIENT_INTEL,
                    "market_price": KnowledgeType.MARKET_PRICE,
                    "lesson_learned": KnowledgeType.LESSON_LEARNED,
                }
                knowledge_type = type_mapping.get(primary_type_str, KnowledgeType.CAPABILITY)
                confidence = Decimal(str(classification_data.get("confidence", 0.0)))

            # Check for multi-type classification
            secondary_types = classification_data.get("secondary_types", [])
            is_multi_type = len(secondary_types) > 0
            multi_type_ids = None

            # Create classification result
            result = ClassificationResult(
                chunk_id=chunk_id,
                knowledge_type=knowledge_type,
                classification_confidence=confidence,
                is_multi_type=is_multi_type,
                multi_type_ids=multi_type_ids,
                reasoning=classification_data.get("reasoning", "")
            )

            logger.info(
                f"Classified chunk {chunk_id}: {knowledge_type.value} "
                f"(confidence={float(confidence):.2f})"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude classification response: {e}")
            raise ClassificationError(f"Invalid LLM response format: {e}")
        except Exception as e:
            logger.error(f"Classification failed for chunk {chunk_id}: {e}")
            raise ClassificationError(f"Classification failed: {e}")

    async def store_classification(
        self,
        chunk_id: UUID,
        classification: ClassificationResult,
        updated_by: Optional[UUID] = None,
    ) -> UUID:
        """
        Store classification result in knowledge_metadata table.

        Args:
            chunk_id: Document chunk UUID
            classification: ClassificationResult object
            updated_by: User ID of knowledge manager (optional)

        Returns:
            Created knowledge_metadata UUID

        Raises:
            ClassificationError: If database insert fails
        """
        try:
            # Prepare data for insertion
            data = {
                "chunk_id": str(chunk_id),
                "knowledge_type": classification.knowledge_type.value,
                "classification_confidence": float(classification.classification_confidence),
                "is_deprecated": False,
                "freshness_score": 100.0,  # New knowledge starts at max freshness
                "updated_by": str(updated_by) if updated_by else None,
                "multi_type_ids": classification.multi_type_ids,
                "created_at": datetime.utcnow().isoformat(),
            }

            # Insert into knowledge_metadata via Supabase RLS
            client = await get_async_client()
            response = await client.table("knowledge_metadata").insert(
                data
            ).execute()

            if response.data:
                knowledge_id = response.data[0]["id"]
                logger.info(f"Stored classification for chunk {chunk_id}: {knowledge_id}")
                return UUID(knowledge_id)
            else:
                raise ClassificationError("Failed to insert classification record")

        except Exception as e:
            logger.error(f"Failed to store classification for chunk {chunk_id}: {e}")
            raise ClassificationError(f"Storage failed: {e}")

    # ========================================================================
    # SEARCH (Module-3)
    # ========================================================================

    async def search(
        self,
        request: SearchRequest,
        user_team_id: UUID,
    ) -> SearchResponse:
        """
        Semantic + keyword hybrid search for knowledge.

        Plan SC-1: Must respond in <500ms for 5000+ document KB
        Design Ref: §4.1, §5.1

        Algorithm:
        1. Generate embedding for query (or skip on failure)
        2. Try pgvector cosine similarity search
        3. If no results or embedding fails → fallback to BM25
        4. Apply filters (type, freshness, team)
        5. Rank by similarity + freshness penalty
        6. Return paginated results with RLS enforcement

        Args:
            request: SearchRequest with query and filters
            user_team_id: User's team UUID (for RLS)

        Returns:
            SearchResponse with ranked results

        Raises:
            SearchError: If search fails critically
        """
        try:
            client = await get_async_client()

            # Attempt semantic search first
            results = await self._semantic_search(
                query=request.query,
                filters=request.filters,
                user_team_id=user_team_id,
                client=client,
                limit=request.limit,
            )

            # If semantic search fails or returns no results, try BM25 fallback
            if not results:
                logger.info(
                    f"Semantic search returned no results for '{request.query}'. "
                    "Falling back to keyword search."
                )
                results = await self._keyword_search(
                    query=request.query,
                    filters=request.filters,
                    user_team_id=user_team_id,
                    client=client,
                    limit=request.limit,
                )

            # Get total count for pagination
            total = len(results)

            # Apply pagination
            paginated_results = results[
                request.offset : request.offset + request.limit
            ]

            return SearchResponse(
                items=paginated_results,
                total=total,
                limit=request.limit,
                offset=request.offset,
            )

        except Exception as e:
            logger.error(f"Search failed for query '{request.query}': {e}")
            # Return empty results on error instead of raising
            # Allows graceful fallback behavior
            return SearchResponse(
                items=[],
                total=0,
                limit=request.limit,
                offset=request.offset,
            )

    async def _semantic_search(
        self,
        query: str,
        filters: SearchFilters,
        user_team_id: UUID,
        client: Any,
        limit: int = 20,
    ) -> List[SearchResultItem]:
        """Execute pgvector cosine similarity semantic search."""
        try:
            # Generate embedding for query
            from app.services.embedding_service import generate_embedding
            embedding = await generate_embedding(query)

            if not embedding or all(e == 0.0 for e in embedding):
                logger.warning("Failed to generate embedding for query")
                return []

            # Query pgvector via Supabase RPC
            response = await client.rpc(
                "search_document_chunks_by_embedding",
                {
                    "query_embedding": embedding,
                    "match_org_id": str(user_team_id),
                    "match_count": limit,
                    "filter_doc_type": None,
                },
            ).execute()

            if not response.data:
                logger.info(f"No semantic search results for query: {query}")
                return []

            # Convert RPC results to SearchResultItem
            results = []
            for row in response.data:
                similarity = row.get("similarity", 0.0)
                if similarity < 0.7:  # Minimum similarity threshold
                    continue

                item = await self._format_search_result(
                    chunk_id=row.get("id"),
                    content=row.get("content"),
                    doc_type=row.get("doc_type"),
                    filename=row.get("filename"),
                    section_title=row.get("section_title"),
                    client=client,
                    embedding_similarity=Decimal(str(similarity)),
                )
                if item:
                    results.append(item)

            # Apply knowledge_types filter (I3)
            if filters and filters.knowledge_types:
                allowed = {kt.value for kt in filters.knowledge_types}
                results = [r for r in results if r.knowledge_type.value in allowed]

            # Apply freshness_min filter (I3)
            if filters and filters.freshness_min is not None:
                threshold = Decimal(str(filters.freshness_min))
                results = [r for r in results if r.freshness_score >= threshold]

            logger.info(
                f"Semantic search returned {len(results)} results for query: {query}"
            )
            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    async def _keyword_search(
        self,
        query: str,
        filters: SearchFilters,
        user_team_id: UUID,
        client: Any,
        limit: int = 50,
    ) -> List[SearchResultItem]:
        """Execute PostgreSQL full-text search (BM25 fallback)."""
        try:
            where_clause = f"org_id.eq.{str(user_team_id)}"

            response = (
                await client.from_("document_chunks")
                .select(
                    "id, content, section_title, "
                    "document_id:intranet_documents(filename, doc_type)"
                )
                .filter(where_clause)
                .ilike("content", f"%{query}%")
                .limit(limit)
                .execute()
            )

            if not response.data:
                logger.info(f"No keyword search results for query: {query}")
                return []

            results = []
            for row in response.data:
                doc_info = row.get("document_id", {}) or {}
                item = await self._format_search_result(
                    chunk_id=row.get("id"),
                    content=row.get("content"),
                    doc_type=doc_info.get("doc_type"),
                    filename=doc_info.get("filename"),
                    section_title=row.get("section_title"),
                    client=client,
                    match_type="keyword_fallback",
                )
                if item:
                    results.append(item)

            # Apply knowledge_types filter (I3)
            if filters and filters.knowledge_types:
                allowed = {kt.value for kt in filters.knowledge_types}
                results = [r for r in results if r.knowledge_type.value in allowed]

            # Apply freshness_min filter (I3)
            if filters and filters.freshness_min is not None:
                threshold = Decimal(str(filters.freshness_min))
                results = [r for r in results if r.freshness_score >= threshold]

            logger.info(f"Keyword search returned {len(results)} results for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Keyword search fallback failed: {e}")
            return []

    async def _format_search_result(
        self,
        chunk_id: UUID,
        content: str,
        doc_type: str,
        filename: str,
        section_title: Optional[str],
        client: Any,
        embedding_similarity: Optional[Decimal] = None,
        match_type: str = "semantic",
    ) -> Optional[SearchResultItem]:
        """Format search result with metadata and freshness scoring."""
        try:
            # Fetch knowledge metadata (classification + freshness)
            metadata_response = (
                await client.from_("knowledge_metadata")
                .select("*")
                .eq("chunk_id", str(chunk_id))
                .single()
                .execute()
            )

            metadata = metadata_response.data if metadata_response.data else {}

            knowledge_type_str = metadata.get("knowledge_type", "capability")
            try:
                knowledge_type = KnowledgeType(knowledge_type_str)
            except (ValueError, KeyError):
                knowledge_type = KnowledgeType.CAPABILITY

            classification_confidence = Decimal(
                str(metadata.get("classification_confidence", 0.5))
            )
            freshness_score = Decimal(str(metadata.get("freshness_score", 100)))
            is_deprecated = metadata.get("is_deprecated", False)

            content_preview = content[:200] if content else ""

            return SearchResultItem(
                id=chunk_id,
                knowledge_type=knowledge_type,
                confidence_score=classification_confidence,
                freshness_score=freshness_score,
                source_doc=section_title or filename or "Unknown Document",
                source_author=None,
                created_at=metadata.get("created_at"),
                content_preview=content_preview,
                embedding_similarity=embedding_similarity,
                is_deprecated=is_deprecated,
            )

        except Exception as e:
            logger.warning(f"Failed to format search result for chunk {chunk_id}: {e}")
            return None

    # ========================================================================
    # RECOMMENDATIONS (Module-4 stub)
    # ========================================================================

    async def recommend(
        self,
        proposal_context: ProposalContext,
        user_team_id: UUID,
        limit: int = 5,
    ) -> RecommendationResponse:
        """
        Generate context-aware knowledge recommendations.

        Plan SC-2: Recommendation relevance >80% (user acceptance rate)
        Design Ref: §4.2, §5.1

        Algorithm:
        1. Search for candidate knowledge using RFP summary
        2. Score each candidate using Claude API against proposal context
        3. Rank by relevance score (0-100)
        4. Extract matching context dimensions
        5. Return top N recommendations with reasoning

        Args:
            proposal_context: Proposal RFP context (RFP summary, client type, bid amount, strategy)
            user_team_id: User's team UUID (for RLS)
            limit: Number of recommendations (default 5, max 20)

        Returns:
            RecommendationResponse with ranked recommendations
        """
        try:
            # Step 1: Search for candidate knowledge using RFP summary
            search_request = SearchRequest(
                query=proposal_context.rfp_summary,
                limit=20  # Get more candidates than final limit for ranking
            )

            candidate_results = await self.search(
                request=search_request,
                user_team_id=user_team_id
            )

            if not candidate_results.items:
                logger.info("No candidate knowledge found for recommendation")
                return RecommendationResponse(
                    items=[],
                    context_matched=[],
                    fallback_used=False,
                )

            # Step 2: Score candidates using Claude API
            candidates_text = "\n\n".join([
                f"[{i+1}] ID: {item.id}\n"
                f"Type: {item.knowledge_type.value}\n"
                f"Source: {item.source_doc}\n"
                f"Preview: {item.content_preview}\n"
                f"Confidence: {item.confidence_score}"
                for i, item in enumerate(candidate_results.items)
            ])

            ranking_prompt = f"""제안 맥락:
- RFP 요약: {proposal_context.rfp_summary}
- 고객 유형: {proposal_context.client_type or 'Unknown'}
- 입찰 규모: {proposal_context.bid_amount or 'Unknown'}
- 선택 전략: {proposal_context.selected_strategy or 'Unknown'}
- 추가 맥락: {proposal_context.additional_context or 'None'}

---후보 지식---
{candidates_text}

각 후보 지식의 관련성 점수(0~100)를 JSON 배열로 응답하세요. 더 높은 점수는 제안 맥락과 더 관련성이 높음을 의미합니다:
[
  {{
    "chunk_id": "...",
    "relevance_score": <0~100>,
    "match_reason": "관련성 설명 (1문장)",
    "matching_dimensions": ["dimension1", "dimension2"]
  }}
]

**중요**: JSON만 응답하세요 (설명 제외)."""

            ranking_response = await claude_generate(
                prompt=ranking_prompt,
                system_prompt="당신은 제안 맥락에서 조직 지식의 관련성을 평가하는 전문가입니다.",
                model="claude-opus-4-6",
                temperature=0.5,  # Moderate temperature for ranking
                max_tokens=2000,
                response_format="json",
                step_name="knowledge_recommendation_ranking"
            )

            # Parse ranking response
            ranked_scores = ranking_response if isinstance(ranking_response, list) else []

            # Step 3: Create scoring map
            score_map = {
                str(item.get("chunk_id")): item
                for item in ranked_scores
            }

            # Step 4: Build recommendation items
            recommendations: List[RecommendationResultItem] = []
            all_matching_dimensions: set = set()

            for search_item in candidate_results.items:
                chunk_id_str = str(search_item.id)
                if chunk_id_str not in score_map:
                    continue

                score_data = score_map[chunk_id_str]
                relevance_score = int(score_data.get("relevance_score", 0))

                # Only include recommendations with meaningful relevance (>30)
                if relevance_score < 30:
                    continue

                matching_dims = score_data.get("matching_dimensions", [])
                all_matching_dimensions.update(matching_dims)

                recommendations.append(
                    RecommendationResultItem(
                        rank=len(recommendations) + 1,
                        chunk_id=search_item.id,
                        knowledge_type=search_item.knowledge_type,
                        confidence_score=search_item.confidence_score,
                        source_doc=search_item.source_doc,
                        content_preview=search_item.content_preview,
                        relevance_reason=score_data.get("match_reason", "관련성 있음"),
                        freshness_score=search_item.freshness_score,
                        match_type="semantic" if search_item.embedding_similarity else "keyword_fallback",
                    )
                )

                if len(recommendations) >= limit:
                    break

            # Sort by rank (already ranked by Claude)
            recommendations.sort(key=lambda x: x.rank)

            fallback_used = any(r.match_type == "keyword_fallback" for r in recommendations)

            logger.info(
                f"Generated {len(recommendations)} recommendations for proposal context. "
                f"Matching dimensions: {all_matching_dimensions}"
            )

            return RecommendationResponse(
                items=recommendations,
                context_matched=list(all_matching_dimensions),
                fallback_used=fallback_used,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude ranking response: {e}")
            # Fallback: return top results by search confidence
            candidate_results = await self.search(
                request=SearchRequest(query=proposal_context.rfp_summary, limit=limit),
                user_team_id=user_team_id
            )

            recommendations = [
                RecommendationResultItem(
                    rank=i + 1,
                    chunk_id=item.id,
                    knowledge_type=item.knowledge_type,
                    confidence_score=item.confidence_score,
                    source_doc=item.source_doc,
                    content_preview=item.content_preview,
                    relevance_reason="검색 결과 기반 추천",
                    freshness_score=item.freshness_score,
                    match_type="semantic" if item.embedding_similarity else "keyword_fallback",
                )
                for i, item in enumerate(candidate_results.items)
            ]

            return RecommendationResponse(
                items=recommendations,
                context_matched=[],
                fallback_used=True,
            )

        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return RecommendationResponse(
                items=[],
                context_matched=[],
                fallback_used=False,
            )

    # ========================================================================
    # HEALTH METRICS (Module-2)
    # ========================================================================

    async def get_health_metrics(
        self,
        team_id: Optional[UUID] = None,
    ) -> "HealthMetrics":
        """
        Aggregate knowledge base health metrics.

        Design Ref: §4.3, §5.1

        Args:
            team_id: Optional team filter (defaults to org-wide)

        Returns:
            HealthMetrics with KB size, coverage, freshness, analytics
        """
        from app.models.knowledge_schemas import (
            HealthMetrics,
            KnowledgeBaseSize,
            CoverageMetrics,
            CoverageItem,
            FreshnessMetrics,
            SearchAnalytics,
            RecommendationFeedback,
        )

        client = await get_async_client()

        # --- KB size ---
        docs_resp = await client.table("intranet_documents").select(
            "id", count="exact"
        ).execute()
        total_documents = docs_resp.count or 0

        chunks_query = client.table("document_chunks").select("id", count="exact")
        if team_id:
            chunks_query = chunks_query.eq("org_id", str(team_id))
        chunks_resp = await chunks_query.execute()
        total_chunks = chunks_resp.count or 0

        kb_size = KnowledgeBaseSize(
            total_documents=total_documents,
            total_chunks=total_chunks,
            storage_bytes=0,
        )

        # --- Coverage by knowledge type ---
        km_query = client.table("knowledge_metadata").select(
            "knowledge_type"
        )
        km_resp = await km_query.execute()
        km_rows = km_resp.data or []

        type_counts: Dict[str, int] = {
            "capability": 0,
            "client_intel": 0,
            "market_price": 0,
            "lesson_learned": 0,
        }
        for row in km_rows:
            kt = row.get("knowledge_type", "")
            if kt in type_counts:
                type_counts[kt] += 1

        total_classified = sum(type_counts.values()) or 1
        coverage = CoverageMetrics(
            capability=CoverageItem(
                count=type_counts["capability"],
                percentage=int(type_counts["capability"] * 100 / total_classified),
            ),
            client_intel=CoverageItem(
                count=type_counts["client_intel"],
                percentage=int(type_counts["client_intel"] * 100 / total_classified),
            ),
            market_price=CoverageItem(
                count=type_counts["market_price"],
                percentage=int(type_counts["market_price"] * 100 / total_classified),
            ),
            lesson_learned=CoverageItem(
                count=type_counts["lesson_learned"],
                percentage=int(type_counts["lesson_learned"] * 100 / total_classified),
            ),
        )

        # --- Freshness distribution ---
        # freshness 100 = < 1 yr, 75 = 1-2 yr, 50 = > 2 yr, deprecated
        less_than_1yr = sum(1 for r in km_rows if float(r.get("freshness_score", 0)) >= 90)
        between_1_2yr = sum(
            1 for r in km_rows
            if 60 <= float(r.get("freshness_score", 0)) < 90
        )
        more_than_2yr = sum(
            1 for r in km_rows
            if float(r.get("freshness_score", 0)) < 60 and not r.get("is_deprecated", False)
        )
        deprecated = sum(1 for r in km_rows if r.get("is_deprecated", False))

        freshness = FreshnessMetrics(
            less_than_1yr=less_than_1yr,
            between_1_2yr=between_1_2yr,
            more_than_2yr=more_than_2yr,
            deprecated=deprecated,
        )

        # --- Search analytics (stub - no analytics table yet) ---
        search_analytics = SearchAnalytics(
            total_searches_last_30d=0,
            zero_result_queries=0,
            top_queries=[],
        )

        # --- Recommendation feedback (stub - no feedback table yet) ---
        recommendation_feedback = RecommendationFeedback(
            thumbs_up=0,
            thumbs_down=0,
            acceptance_rate=Decimal("0.0"),
        )

        logger.info(
            f"Health metrics computed: {total_documents} docs, "
            f"{total_chunks} chunks, {total_classified} classified"
        )

        return HealthMetrics(
            kb_size=kb_size,
            coverage=coverage,
            freshness=freshness,
            search_analytics=search_analytics,
            recommendation_feedback=recommendation_feedback,
        )

    async def get_flat_health_metrics(
        self,
        team_id: Optional[UUID] = None,
    ) -> "FlatHealthMetrics":
        """
        Return health metrics flattened for the frontend KnowledgeHealthDashboard.

        Calls get_health_metrics() internally and transforms the nested structure
        into the flat FlatHealthMetrics shape expected by the frontend interface.

        Design Ref: §4.3, §5.1
        """
        from app.models.knowledge_schemas import FlatHealthMetrics

        metrics = await self.get_health_metrics(team_id=team_id)

        # Derive coverage_percentage: ratio of classified chunks to total chunks
        total_chunks = metrics.kb_size.total_chunks or 1
        total_classified = (
            metrics.coverage.capability.count
            + metrics.coverage.client_intel.count
            + metrics.coverage.market_price.count
            + metrics.coverage.lesson_learned.count
        )
        coverage_pct = min(100.0, (total_classified / total_chunks) * 100.0)

        # Derive avg_freshness_score from freshness distribution
        # Approximate bucket midpoints: <1yr=95, 1-2yr=75, >2yr=40, deprecated=0
        total_freshness_records = (
            metrics.freshness.less_than_1yr
            + metrics.freshness.between_1_2yr
            + metrics.freshness.more_than_2yr
            + metrics.freshness.deprecated
        ) or 1
        weighted_freshness = (
            metrics.freshness.less_than_1yr * 95
            + metrics.freshness.between_1_2yr * 75
            + metrics.freshness.more_than_2yr * 40
            + metrics.freshness.deprecated * 0
        )
        avg_freshness = weighted_freshness / total_freshness_records

        # Deprecation rate
        deprecation_rate = (
            (metrics.freshness.deprecated / total_freshness_records) * 100.0
            if total_freshness_records > 0
            else 0.0
        )

        # Knowledge type distribution map
        knowledge_type_distribution = {
            "capability": metrics.coverage.capability.count,
            "client_intel": metrics.coverage.client_intel.count,
            "market_price": metrics.coverage.market_price.count,
            "lesson_learned": metrics.coverage.lesson_learned.count,
        }

        # Confidence distribution — query knowledge_metadata for confidence tiers
        client = await get_async_client()
        conf_resp = await client.table("knowledge_metadata").select(
            "classification_confidence"
        ).execute()
        conf_rows = conf_resp.data or []

        high = sum(1 for r in conf_rows if float(r.get("classification_confidence", 0)) >= 0.8)
        medium = sum(
            1 for r in conf_rows
            if 0.5 <= float(r.get("classification_confidence", 0)) < 0.8
        )
        low = sum(1 for r in conf_rows if float(r.get("classification_confidence", 0)) < 0.5)
        confidence_distribution = {"high": high, "medium": medium, "low": low}

        # Trending topics — derive from top_queries in search_analytics (stub)
        trending_topics = [
            {"topic": q, "occurrences": 1}
            for q in (metrics.search_analytics.top_queries or [])
        ]

        # Total shares from knowledge_sharing_audit
        shares_resp = await client.table("knowledge_sharing_audit").select(
            "id", count="exact"
        ).execute()
        total_shares = shares_resp.count or 0

        return FlatHealthMetrics(
            kb_size_chunks=metrics.kb_size.total_chunks,
            kb_size_bytes=metrics.kb_size.storage_bytes,
            coverage_percentage=round(coverage_pct, 2),
            avg_freshness_score=round(avg_freshness, 2),
            total_organizations=0,  # Populated from org membership table when available
            total_shares=total_shares,
            deprecation_rate=round(deprecation_rate, 2),
            knowledge_type_distribution=knowledge_type_distribution,
            confidence_distribution=confidence_distribution,
            trending_topics=trending_topics,
        )

    async def record_feedback(
        self,
        chunk_id: UUID,
        feedback_type: str,
        user_id: UUID,
        proposal_context: Optional[dict] = None,
    ) -> dict:
        """
        Log recommendation feedback (thumbs up/down) for analytics.

        Inserts a record into knowledge_feedback_log if the table exists,
        or returns a stub response if the table is not yet created.

        Design Ref: §4.3 Recommendation Feedback Analytics

        Args:
            chunk_id: Knowledge chunk that received feedback
            feedback_type: 'positive' or 'negative'
            user_id: User providing feedback
            proposal_context: Optional proposal metadata for analytics

        Returns:
            dict with chunk_id, feedback_type, recorded, recorded_at
        """
        from datetime import datetime as _dt

        recorded_at = _dt.utcnow().isoformat()

        try:
            client = await get_async_client()
            feedback_data = {
                "chunk_id": str(chunk_id),
                "feedback_type": feedback_type,
                "user_id": str(user_id),
                "proposal_context": proposal_context or {},
                "created_at": recorded_at,
            }
            await client.table("knowledge_feedback_log").insert(feedback_data).execute()
            logger.info(
                f"Recorded {feedback_type} feedback for chunk {chunk_id} "
                f"by user {user_id}"
            )
        except Exception as e:
            # Table may not exist yet — log warning and continue gracefully
            logger.warning(
                f"Could not persist feedback for chunk {chunk_id}: {e}. "
                "knowledge_feedback_log table may not exist yet."
            )

        return {
            "chunk_id": str(chunk_id),
            "feedback_type": feedback_type,
            "recorded": True,
            "recorded_at": recorded_at,
        }

    # ========================================================================
    # LIFECYCLE MANAGEMENT (Module-2)
    # ========================================================================

    async def mark_deprecated(
        self,
        chunk_id: UUID,
        reason: str,
        user_id: UUID,
    ) -> dict:
        """
        Mark knowledge as deprecated (soft delete).

        Updates is_deprecated=True and sets freshness_score=0 on the
        knowledge_metadata record for the given chunk.

        Design Ref: §6 Knowledge Lifecycle

        Args:
            chunk_id: Knowledge chunk UUID
            reason: Reason for deprecation (stored in updated_by audit log)
            user_id: User ID marking as deprecated

        Returns:
            Updated knowledge metadata record
        """
        client = await get_async_client()

        # Check the record exists first
        existing = (
            await client.table("knowledge_metadata")
            .select("id")
            .eq("chunk_id", str(chunk_id))
            .maybe_single()
            .execute()
        )

        if not existing.data:
            from app.exceptions import TenopAPIError
            raise TenopAPIError(
                "KNOWLEDGE_NOT_FOUND",
                f"No knowledge metadata found for chunk {chunk_id}",
                404,
            )

        update_data = {
            "is_deprecated": True,
            "freshness_score": 0.0,
            "last_updated_at": datetime.utcnow().isoformat(),
            "updated_by": str(user_id),
        }

        result = await (
            client.table("knowledge_metadata")
            .update(update_data)
            .eq("chunk_id", str(chunk_id))
            .execute()
        )

        logger.info(
            f"Marked chunk {chunk_id} as deprecated by user {user_id}. "
            f"Reason: {reason}"
        )

        return result.data[0] if result.data else update_data

    async def share_to_org(
        self,
        chunk_id: UUID,
        reason: str,
        shared_by: UUID,
        team_id: UUID,
    ) -> UUID:
        """
        Promote team knowledge to org-wide scope.

        Inserts an audit record into knowledge_sharing_audit and marks
        shared_to_org=true.

        Design Ref: §5 RLS Policies, §6 Knowledge Lifecycle

        Args:
            chunk_id: Knowledge chunk UUID
            reason: Reason for sharing
            shared_by: User ID sharing the knowledge
            team_id: Original team UUID

        Returns:
            Audit record UUID
        """
        client = await get_async_client()

        audit_data = {
            "chunk_id": str(chunk_id),
            "shared_by": str(shared_by),
            "shared_from_team_id": str(team_id),
            "shared_to_org": True,
            "shared_at": datetime.utcnow().isoformat(),
            "reason": reason,
        }

        response = (
            await client.table("knowledge_sharing_audit")
            .insert(audit_data)
            .execute()
        )

        if not response.data:
            from app.exceptions import TenopAPIError
            raise TenopAPIError(
                "SHARING_FAILED",
                f"Failed to create sharing audit record for chunk {chunk_id}",
                500,
            )

        audit_id = UUID(response.data[0]["id"])

        logger.info(
            f"Shared chunk {chunk_id} org-wide by user {shared_by} "
            f"from team {team_id}. Audit ID: {audit_id}"
        )

        return audit_id

    # ========================================================================
    # BACKGROUND JOBS (Module-2)
    # ========================================================================

    async def retry_failed_embeddings(
        self,
        batch_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Background job to retry embedding generation for unprocessed chunks.

        Queries document_chunks where embedding IS NULL (or is_knowledge_indexed
        is false), attempts to re-embed, and updates the record.

        Design Ref: §5.1 Background Jobs

        Args:
            batch_size: Number of chunks to process per run (default 50)

        Returns:
            Dict with keys: processed, succeeded, failed
        """
        from app.services.embedding_service import generate_embedding

        client = await get_async_client()

        # Find chunks with missing embeddings
        response = (
            await client.table("document_chunks")
            .select("id, content")
            .is_("embedding", "null")
            .limit(batch_size)
            .execute()
        )

        chunks = response.data or []
        if not chunks:
            logger.info("retry_failed_embeddings: no unembedded chunks found")
            return {"processed": 0, "succeeded": 0, "failed": 0}

        processed = len(chunks)
        succeeded = 0
        failed = 0

        for chunk in chunks:
            chunk_id = chunk["id"]
            content = chunk.get("content", "")
            if not content:
                failed += 1
                continue
            try:
                embedding = await generate_embedding(content[:8000])
                if embedding and not all(e == 0.0 for e in embedding):
                    await (
                        client.table("document_chunks")
                        .update({"embedding": embedding})
                        .eq("id", chunk_id)
                        .execute()
                    )
                    succeeded += 1
                else:
                    failed += 1
            except Exception as e:
                logger.warning(f"retry_failed_embeddings: chunk {chunk_id} failed: {e}")
                failed += 1

        logger.info(
            f"retry_failed_embeddings complete: "
            f"processed={processed}, succeeded={succeeded}, failed={failed}"
        )

        return {"processed": processed, "succeeded": succeeded, "failed": failed}


# ============================================================================
# SERVICE FACTORY
# ============================================================================

_knowledge_manager: Optional[KnowledgeManager] = None


def get_knowledge_manager() -> KnowledgeManager:
    """
    Get or create the singleton KnowledgeManager instance.

    Returns:
        KnowledgeManager instance
    """
    global _knowledge_manager
    if _knowledge_manager is None:
        _knowledge_manager = KnowledgeManager()
    return _knowledge_manager
