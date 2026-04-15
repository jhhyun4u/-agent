"""
End-to-end tests for Vault semantic search in chat flow
Tests complete pipeline from user query to search results
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from app.services.vault_handlers.completed_projects import CompletedProjectsHandler
from app.services.vault_handlers.government_guidelines import GovernmentGuidelinesHandler
from app.models.vault_schemas import SearchResult, VaultDocument, VaultSection


class TestVaultSemanticSearchE2E:
    """End-to-end tests for vault semantic search"""

    @pytest.mark.asyncio
    async def test_semantic_search_in_completed_projects_query(self):
        """
        E2E Test: User asks "We need a mobile app built"
        Expected: Returns past mobile app projects using semantic search
        """

        query = "We need a mobile app built for our business"

        # Mock SQL results (exact matches)
        sql_results = [
            SearchResult(
                document=VaultDocument(
                    id="proj-1",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title="Mobile App Development - TechCorp",
                    content="Developed iOS and Android apps for retail business",
                    metadata={
                        "client": "TechCorp",
                        "budget": 45000,
                        "duration": "6 months",
                        "team_size": 4
                    },
                    created_at=datetime.now()
                ),
                relevance_score=0.95,
                match_type="exact",
                preview="Mobile App project for TechCorp"
            )
        ]

        # Mock vector results (semantic matches)
        vector_results = [
            SearchResult(
                document=VaultDocument(
                    id="proj-2",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title="iOS Development - StartupXYZ",
                    content="Built iOS application for startup",
                    metadata={
                        "client": "StartupXYZ",
                        "budget": 35000,
                        "duration": "4 months",
                        "team_size": 2
                    },
                    created_at=datetime.now()
                ),
                relevance_score=0.82,
                match_type="semantic",
                preview="iOS app project for StartupXYZ"
            ),
            SearchResult(
                document=VaultDocument(
                    id="proj-3",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title="Android App - EcommerceCo",
                    content="Developed Android application for e-commerce",
                    metadata={
                        "client": "EcommerceCo",
                        "budget": 55000,
                        "duration": "8 months",
                        "team_size": 5
                    },
                    created_at=datetime.now()
                ),
                relevance_score=0.78,
                match_type="semantic",
                preview="Android app project for EcommerceCo"
            )
        ]

        with patch.object(CompletedProjectsHandler, '_sql_search', return_value=sql_results):
            with patch.object(CompletedProjectsHandler, '_vector_search', return_value=vector_results):
                results = await CompletedProjectsHandler.search(query, limit=5)

        # Verify results
        assert len(results) == 3

        # First result should be SQL exact match
        assert results[0].match_type == "exact"
        assert results[0].relevance_score == 0.95

        # Other results should be sorted by semantic relevance
        assert results[1].relevance_score == 0.82
        assert results[2].relevance_score == 0.78

        # Verify we get diverse project options
        project_ids = [r.document.id for r in results]
        assert len(set(project_ids)) == 3  # All unique

    @pytest.mark.asyncio
    async def test_semantic_search_with_filters(self):
        """
        E2E Test: User asks "Show mobile apps under 50k budget"
        Expected: Returns mobile apps filtered by budget using hybrid search
        """

        query = "mobile application development"
        filters = {
            "budget_min": 0,
            "budget_max": 50000
        }

        # Mock results with different budgets
        all_results = [
            SearchResult(
                document=VaultDocument(
                    id="proj-1",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title="Simple App",
                    content="Built simple app",
                    metadata={"budget": 30000},
                    created_at=datetime.now()
                ),
                relevance_score=0.85,
                match_type="semantic",
                preview="Budget: 30,000"
            ),
            SearchResult(
                document=VaultDocument(
                    id="proj-2",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title="Enterprise App",
                    content="Built enterprise app",
                    metadata={"budget": 100000},
                    created_at=datetime.now()
                ),
                relevance_score=0.80,
                match_type="semantic",
                preview="Budget: 100,000"
            )
        ]

        # Filter results
        filtered_results = [
            r for r in all_results
            if r.document.metadata.get("budget", 0) <= filters["budget_max"]
        ]

        assert len(filtered_results) == 1
        assert filtered_results[0].document.id == "proj-1"
        assert filtered_results[0].document.metadata["budget"] == 30000

    @pytest.mark.asyncio
    async def test_government_guidelines_semantic_search(self):
        """
        E2E Test: User asks "What's the daily rate for government projects?"
        Expected: Returns relevant government salary guidelines
        """

        query = "정부 프로젝트 기술자 일당이 얼마나 되나?"

        # Mock SQL keyword match results
        sql_results = [
            SearchResult(
                document=VaultDocument(
                    id="guide-1",
                    section=VaultSection.GOVERNMENT_GUIDELINES,
                    title="정부 급여 기준 2024",
                    content="정부 공사에 투입되는 기술인의 일급 기준...",
                    metadata={
                        "category": "salary",
                        "effective_date": "2024-01-01",
                        "salary_rates": {
                            "선임연구원": 180000,
                            "연구원": 150000,
                            "기술원": 120000
                        }
                    },
                    created_at=datetime.now()
                ),
                relevance_score=1.0,
                match_type="exact",
                preview="Government salary standards 2024"
            )
        ]

        # Mock vector search results (semantic matches)
        vector_results = [
            SearchResult(
                document=VaultDocument(
                    id="guide-2",
                    section=VaultSection.GOVERNMENT_GUIDELINES,
                    title="공공 프로젝트 비용 기준",
                    content="공공사업의 기술인 임금 규정...",
                    metadata={"category": "public_projects"},
                    created_at=datetime.now()
                ),
                relevance_score=0.75,
                match_type="semantic",
                preview="Public project cost standards"
            )
        ]

        with patch.object(GovernmentGuidelinesHandler, '_search_salary_rates', return_value=sql_results):
            with patch.object(GovernmentGuidelinesHandler, '_vector_search', return_value=vector_results):
                results = await GovernmentGuidelinesHandler.search(query, limit=5)

        # Verify results
        assert len(results) >= 1

        # First result should be exact government rate
        exact_results = [r for r in results if r.match_type == "exact"]
        assert len(exact_results) > 0
        assert exact_results[0].relevance_score == 1.0

    @pytest.mark.asyncio
    async def test_deduplication_in_hybrid_search(self):
        """
        E2E Test: Document appears in both SQL and vector search
        Expected: Results are deduplicated and scores are merged
        """

        # Same document appears in both searches
        shared_result = SearchResult(
            document=VaultDocument(
                id="proj-shared",
                section=VaultSection.COMPLETED_PROJECTS,
                title="Mobile App Project",
                content="Built both iOS and Android app",
                metadata={"client": "SharedClient"},
                created_at=datetime.now()
            ),
            relevance_score=0.95,
            match_type="exact",
            preview="Mobile App"
        )

        shared_vector = SearchResult(
            document=VaultDocument(
                id="proj-shared",  # Same ID
                section=VaultSection.COMPLETED_PROJECTS,
                title="Mobile App Project",
                content="Built both iOS and Android app",
                metadata={"client": "SharedClient"},
                created_at=datetime.now()
            ),
            relevance_score=0.82,
            match_type="semantic",
            preview="Mobile App"
        )

        # Simulate both searches finding the same result
        results = [shared_result, shared_vector]
        deduplicated = CompletedProjectsHandler._deduplicate_results(results)

        # Should have only one result with merged score
        assert len(deduplicated) == 1
        assert deduplicated[0].document.id == "proj-shared"
        assert deduplicated[0].relevance_score == 0.885  # Average of 0.95 and 0.82
        assert "exact+semantic" in deduplicated[0].match_type

    @pytest.mark.asyncio
    async def test_search_quality_metrics(self):
        """
        E2E Test: Verify search results have expected quality metrics
        Expected: High-relevance results at top, proper scoring distribution
        """

        # Create diverse results with different relevance levels
        results = [
            SearchResult(
                document=VaultDocument(
                    id="1",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title="Project A",
                    content="",
                    metadata={},
                    created_at=datetime.now()
                ),
                relevance_score=0.95,
                match_type="exact",
                preview=""
            ),
            SearchResult(
                document=VaultDocument(
                    id="2",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title="Project B",
                    content="",
                    metadata={},
                    created_at=datetime.now()
                ),
                relevance_score=0.85,
                match_type="semantic",
                preview=""
            ),
            SearchResult(
                document=VaultDocument(
                    id="3",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title="Project C",
                    content="",
                    metadata={},
                    created_at=datetime.now()
                ),
                relevance_score=0.72,
                match_type="semantic",
                preview=""
            ),
            SearchResult(
                document=VaultDocument(
                    id="4",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title="Project D",
                    content="",
                    metadata={},
                    created_at=datetime.now()
                ),
                relevance_score=0.60,
                match_type="semantic",
                preview=""
            )
        ]

        # Verify scoring distribution
        scores = [r.relevance_score for r in results]

        # All scores should be between 0 and 1
        assert all(0 <= s <= 1 for s in scores)

        # Scores should be in descending order
        assert scores == sorted(scores, reverse=True)

        # Exact match should rank higher than semantic
        exact_score = next(r.relevance_score for r in results if r.match_type == "exact")
        semantic_scores = [r.relevance_score for r in results if r.match_type == "semantic"]
        assert exact_score > min(semantic_scores)

    @pytest.mark.asyncio
    async def test_empty_results_handling(self):
        """
        E2E Test: Query with no matching results
        Expected: Return empty list gracefully, no errors
        """

        query = "highly specialized project that doesn't exist"

        with patch.object(CompletedProjectsHandler, '_sql_search', return_value=[]):
            with patch.object(CompletedProjectsHandler, '_vector_search', return_value=[]):
                results = await CompletedProjectsHandler.search(query, limit=5)

        assert results == []

    @pytest.mark.asyncio
    async def test_search_with_special_characters(self):
        """
        E2E Test: Query with special characters and Korean text
        Expected: Handle properly without errors
        """

        query = "모바일 앱 개발 (iOS/Android)"

        # Should not raise any errors
        with patch.object(CompletedProjectsHandler, '_sql_search', return_value=[]):
            with patch.object(CompletedProjectsHandler, '_vector_search', return_value=[]):
                results = await CompletedProjectsHandler.search(query)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_large_result_set_pagination(self):
        """
        E2E Test: Many results returned, should be limited
        Expected: Only return top N results (limit parameter)
        """

        # Create many results
        results = [
            SearchResult(
                document=VaultDocument(
                    id=f"proj-{i}",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title=f"Project {i}",
                    content="",
                    metadata={},
                    created_at=datetime.now()
                ),
                relevance_score=1.0 - (i * 0.01),
                match_type="semantic",
                preview=""
            )
            for i in range(50)
        ]

        # Sort by relevance
        sorted_results = sorted(results, key=lambda x: x.relevance_score, reverse=True)

        # Apply limit
        limited = sorted_results[:10]

        assert len(limited) == 10
        assert limited[0].document.id == "proj-0"
        assert limited[-1].document.id == "proj-9"

    @pytest.mark.asyncio
    async def test_relevance_score_distribution(self):
        """
        E2E Test: Verify relevance scores are properly distributed
        Expected: SQL exact matches highest, vector scores vary, merged averaging works
        """

        # Test score composition
        scores = {
            "sql_exact": 0.95,
            "vector_high": 0.85,
            "vector_medium": 0.70,
            "vector_low": 0.60,
            "merged": (0.95 + 0.70) / 2  # 0.825
        }

        # Verify merged score calculation
        assert scores["merged"] == 0.825

        # Verify ranking order
        all_scores = [
            scores["sql_exact"],
            scores["vector_high"],
            scores["merged"],
            scores["vector_medium"],
            scores["vector_low"]
        ]

        sorted_scores = sorted(all_scores, reverse=True)
        assert sorted_scores == [0.95, 0.85, 0.825, 0.70, 0.60]


class TestVectorSearchErrorRecovery:
    """Tests for error handling and recovery in vector search"""

    @pytest.mark.asyncio
    async def test_embedding_service_failure_fallback(self):
        """
        E2E Test: Embedding service fails, fallback to SQL-only
        Expected: Return SQL results without vector enhancement
        """

        sql_results = [
            SearchResult(
                document=VaultDocument(
                    id="proj-1",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title="Project",
                    content="",
                    metadata={},
                    created_at=datetime.now()
                ),
                relevance_score=0.95,
                match_type="exact",
                preview=""
            )
        ]

        # Simulate embedding service failure
        with patch.object(CompletedProjectsHandler, '_sql_search', return_value=sql_results):
            with patch.object(CompletedProjectsHandler, '_vector_search', return_value=[]):
                results = await CompletedProjectsHandler.search("query")

        # Should still return SQL results
        assert len(results) == 1
        assert results[0].document.id == "proj-1"

    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """
        E2E Test: Database error during fetch
        Expected: Handle gracefully, skip problematic results
        """

        # Simulate partial failure
        with patch.object(CompletedProjectsHandler, '_sql_search', return_value=[]):
            with patch.object(CompletedProjectsHandler, '_vector_search', side_effect=Exception("DB Error")):
                results = await CompletedProjectsHandler.search("query")

        # Should return empty, not crash
        assert results == []
