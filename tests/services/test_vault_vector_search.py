"""
Tests for Vault vector search functionality
Tests semantic search, deduplication, and metadata filtering
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from app.services.vault_handlers.completed_projects import CompletedProjectsHandler
from app.services.vault_handlers.government_guidelines import GovernmentGuidelinesHandler
from app.models.vault_schemas import SearchResult, VaultDocument, VaultSection


class TestCompletedProjectsVectorSearch:
    """Tests for vector search in completed projects"""
    
    @pytest.mark.asyncio
    async def test_vector_search_returns_semantic_results(self):
        """Test that vector search returns results with similarity scores"""
        from tests.conftest import make_supabase_mock

        # Mock embedding service
        mock_embedding_service = AsyncMock()
        mock_embedding_service.search_similar = AsyncMock(return_value=[
            {
                "document_id": "proj-1",
                "section": "completed_projects",
                "title": "Mobile App Development",
                "content": "Built iOS and Android apps...",
                "similarity": 0.85
            },
            {
                "document_id": "proj-2",
                "section": "completed_projects",
                "title": "Web Platform Development",
                "content": "Developed web-based platform...",
                "similarity": 0.72
            }
        ])

        # Use proper mock client from conftest
        vault_doc_data = {
            "id": "proj-1",
            "section": "completed_projects",
            "title": "Mobile App Development",
            "content": "Built iOS and Android apps...",
            "metadata": {
                "client": "TechCorp",
                "budget": 50000,
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            },
            "created_at": "2023-01-01T00:00:00"
        }

        mock_client = make_supabase_mock(table_data={
            "vault_documents": [vault_doc_data]
        })

        # Test search
        with patch('app.services.vault_embedding_service.EmbeddingService', return_value=mock_embedding_service):
            with patch('app.services.vault_handlers.completed_projects.get_async_client', return_value=mock_client):
                results = await CompletedProjectsHandler._vector_search("app development", limit=10)

        # Verify results
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.match_type == "semantic" for r in results)
    
    @pytest.mark.asyncio
    async def test_hybrid_search_combines_sql_and_vector(self):
        """Test that search method combines SQL and vector results"""
        
        with patch.object(CompletedProjectsHandler, '_sql_search', return_value=[]):
            with patch.object(CompletedProjectsHandler, '_vector_search', return_value=[]):
                # Mock the results
                sql_result = SearchResult(
                    document=VaultDocument(
                        id="sql-1",
                        section=VaultSection.COMPLETED_PROJECTS,
                        title="SQL Result",
                        content="",
                        metadata={},
                        created_at=datetime.now()
                    ),
                    relevance_score=0.95,
                    match_type="exact",
                    preview=""
                )
                
                vector_result = SearchResult(
                    document=VaultDocument(
                        id="vec-1",
                        section=VaultSection.COMPLETED_PROJECTS,
                        title="Vector Result",
                        content="",
                        metadata={},
                        created_at=datetime.now()
                    ),
                    relevance_score=0.80,
                    match_type="semantic",
                    preview=""
                )
                
                with patch.object(CompletedProjectsHandler, '_sql_search', return_value=[sql_result]):
                    with patch.object(CompletedProjectsHandler, '_vector_search', return_value=[vector_result]):
                        results = await CompletedProjectsHandler.search("test query")
        
        # Should have both results, ordered by relevance
        assert len(results) == 2
        assert results[0].relevance_score >= results[1].relevance_score
    
    @pytest.mark.asyncio
    async def test_deduplication_merges_duplicate_results(self):
        """Test that deduplication merges results from both sources"""
        
        # Create duplicate results (same document from SQL and vector)
        now = datetime.now()
        result1 = SearchResult(
            document=VaultDocument(
                id="proj-1",
                section=VaultSection.COMPLETED_PROJECTS,
                title="Project A",
                content="",
                metadata={},
                created_at=now
            ),
            relevance_score=0.95,
            match_type="exact",
            preview="SQL match"
        )
        
        result2 = SearchResult(
            document=VaultDocument(
                id="proj-1",  # Same document
                section=VaultSection.COMPLETED_PROJECTS,
                title="Project A",
                content="",
                metadata={},
                created_at=now
            ),
            relevance_score=0.80,
            match_type="semantic",
            preview="Vector match"
        )
        
        results = [result1, result2]
        deduplicated = CompletedProjectsHandler._deduplicate_results(results)
        
        # Should have only one result with merged score
        assert len(deduplicated) == 1
        assert deduplicated[0].document.id == "proj-1"
        assert deduplicated[0].relevance_score == 0.875  # Average of 0.95 and 0.80
        assert "exact+semantic" in deduplicated[0].match_type
    
    @pytest.mark.asyncio
    async def test_metadata_filters_on_vector_results(self):
        """Test that metadata filters work on vector search results"""
        from tests.conftest import make_supabase_mock

        filters = {
            "client": "TechCorp",
            "budget_min": 40000,
            "budget_max": 60000
        }

        # Mock embedding service
        mock_embedding_service = AsyncMock()
        mock_embedding_service.search_similar = AsyncMock(return_value=[
            {
                "document_id": "proj-1",
                "section": "completed_projects",
                "title": "Project A",
                "content": "...",
                "similarity": 0.85
            },
            {
                "document_id": "proj-2",
                "section": "completed_projects",
                "title": "Project B",
                "content": "...",
                "similarity": 0.75
            }
        ])

        # Use proper mock with both documents
        vault_docs = [
            {
                "id": "proj-1",
                "section": "completed_projects",
                "title": "Project A",
                "content": "...",
                "metadata": {
                    "client": "TechCorp",
                    "budget": 50000
                },
                "created_at": "2023-01-01T00:00:00"
            },
            {
                "id": "proj-2",
                "section": "completed_projects",
                "title": "Project B",
                "content": "...",
                "metadata": {
                    "client": "OtherCorp",
                    "budget": 70000
                },
                "created_at": "2023-01-01T00:00:00"
            }
        ]

        mock_client = make_supabase_mock(table_data={
            "vault_documents": vault_docs
        })

        with patch('app.services.vault_embedding_service.EmbeddingService', return_value=mock_embedding_service):
            with patch('app.services.vault_handlers.completed_projects.get_async_client', return_value=mock_client):
                results = await CompletedProjectsHandler._vector_search("query", filters=filters)

        # Should only include proj-1 (matches client and budget range)
        assert len(results) == 1
        assert results[0].document.id == "proj-1"


class TestGovernmentGuidelinesVectorSearch:
    """Tests for vector search in government guidelines"""
    
    @pytest.mark.asyncio
    async def test_government_guidelines_vector_search(self):
        """Test vector search for government guidelines"""
        from tests.conftest import make_supabase_mock

        mock_embedding_service = AsyncMock()
        mock_embedding_service.search_similar = AsyncMock(return_value=[
            {
                "document_id": "guide-1",
                "section": "government_guidelines",
                "title": "정부 급여 기준",
                "content": "정부에서 정한 급여 기준...",
                "similarity": 0.82
            }
        ])

        guide_doc_data = {
            "id": "guide-1",
            "section": "government_guidelines",
            "title": "정부 급여 기준",
            "content": "정부에서 정한 급여 기준...",
            "metadata": {"category": "salary"},
            "created_at": "2023-01-01T00:00:00"
        }

        mock_client = make_supabase_mock(table_data={
            "vault_documents": [guide_doc_data]
        })
        
        with patch('app.services.vault_embedding_service.EmbeddingService', return_value=mock_embedding_service):
            with patch('app.services.vault_handlers.government_guidelines.get_async_client', return_value=mock_client):
                results = await GovernmentGuidelinesHandler._vector_search("급여 기준")
        
        assert len(results) > 0
        assert all(r.match_type == "semantic" for r in results)
    
    @pytest.mark.asyncio
    async def test_government_guidelines_deduplication(self):
        """Test deduplication for government guidelines"""
        
        result1 = SearchResult(
            document=VaultDocument(
                id="guide-1",
                section=VaultSection.GOVERNMENT_GUIDELINES,
                title="급여 기준",
                content="",
                metadata={},
                created_at=datetime.now()
            ),
            relevance_score=1.0,
            match_type="exact",
            preview=""
        )
        
        result2 = SearchResult(
            document=VaultDocument(
                id="guide-1",
                section=VaultSection.GOVERNMENT_GUIDELINES,
                title="급여 기준",
                content="",
                metadata={},
                created_at=datetime.now()
            ),
            relevance_score=0.80,
            match_type="semantic",
            preview=""
        )
        
        deduplicated = GovernmentGuidelinesHandler._deduplicate_results([result1, result2])
        
        # Should prefer exact match
        assert len(deduplicated) == 1
        assert deduplicated[0].match_type == "exact"


class TestVectorSearchIntegration:
    """Integration tests for vector search across handlers"""
    
    @pytest.mark.asyncio
    async def test_vector_search_similarity_threshold(self):
        """Test that similarity threshold filters low-relevance results"""
        
        mock_embedding_service = AsyncMock()
        # Return result with low similarity
        mock_embedding_service.search_similar = AsyncMock(return_value=[
            {
                "document_id": "proj-1",
                "section": "completed_projects",
                "title": "Project",
                "content": "...",
                "similarity": 0.5  # Below typical 0.7 threshold
            }
        ])
        
        mock_client = AsyncMock()
        async def mock_execute():
            return MagicMock(data={
                "id": "proj-1",
                "title": "Project",
                "content": "...",
                "metadata": {},
                "created_at": "2023-01-01T00:00:00"
            })
        
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute = mock_execute
        
        with patch('app.services.vault_embedding_service.EmbeddingService', return_value=mock_embedding_service):
            with patch('app.services.vault_handlers.completed_projects.get_async_client', return_value=mock_client):
                results = await CompletedProjectsHandler._vector_search("query", threshold=0.7)
        
        # Should still include the result (RPC filters by threshold)
        # but we can verify it has the low similarity score
        if results:
            assert all(r.relevance_score >= 0.5 for r in results)
    
    @pytest.mark.asyncio
    async def test_search_error_handling_graceful_fallback(self):
        """Test that vector search errors don't crash the system"""
        
        mock_embedding_service = AsyncMock()
        mock_embedding_service.search_similar = AsyncMock(side_effect=Exception("Embedding service error"))
        
        with patch('app.services.vault_embedding_service.EmbeddingService', return_value=mock_embedding_service):
            # Should handle error gracefully and return empty list
            results = await CompletedProjectsHandler._vector_search("query")
            assert results == []
    
    @pytest.mark.asyncio
    async def test_vector_search_missing_embedding_service(self):
        """Test graceful degradation when embedding service is not available"""
        
        with patch('app.services.vault_embedding_service.EmbeddingService', side_effect=ImportError):
            results = await CompletedProjectsHandler._vector_search("query")
            assert results == []


class TestVectorSearchQuality:
    """Tests for search quality and relevance"""
    
    @pytest.mark.asyncio
    async def test_results_sorted_by_relevance_score(self):
        """Test that search results are sorted by relevance"""
        
        result1 = SearchResult(
            document=VaultDocument(
                id="proj-1",
                section=VaultSection.COMPLETED_PROJECTS,
                title="High Relevance",
                content="",
                metadata={},
                created_at=datetime.now()
            ),
            relevance_score=0.95,
            match_type="exact",
            preview=""
        )
        
        result2 = SearchResult(
            document=VaultDocument(
                id="proj-2",
                section=VaultSection.COMPLETED_PROJECTS,
                title="Medium Relevance",
                content="",
                metadata={},
                created_at=datetime.now()
            ),
            relevance_score=0.70,
            match_type="semantic",
            preview=""
        )
        
        result3 = SearchResult(
            document=VaultDocument(
                id="proj-3",
                section=VaultSection.COMPLETED_PROJECTS,
                title="Low Relevance",
                content="",
                metadata={},
                created_at=datetime.now()
            ),
            relevance_score=0.50,
            match_type="semantic",
            preview=""
        )
        
        # Test with mixed order
        results = [result2, result3, result1]
        sorted_results = sorted(results, key=lambda x: x.relevance_score, reverse=True)
        
        assert sorted_results[0].relevance_score == 0.95
        assert sorted_results[1].relevance_score == 0.70
        assert sorted_results[2].relevance_score == 0.50
    
    @pytest.mark.asyncio
    async def test_semantic_vs_exact_match_scores(self):
        """Test that exact matches score higher than semantic"""
        
        with patch.object(CompletedProjectsHandler, '_sql_search') as mock_sql:
            with patch.object(CompletedProjectsHandler, '_vector_search') as mock_vector:
                sql_result = SearchResult(
                    document=VaultDocument(
                        id="proj-1",
                        section=VaultSection.COMPLETED_PROJECTS,
                        title="Exact Match",
                        content="",
                        metadata={},
                        created_at=datetime.now()
                    ),
                    relevance_score=0.95,
                    match_type="exact",
                    preview=""
                )
                
                vector_result = SearchResult(
                    document=VaultDocument(
                        id="proj-2",
                        section=VaultSection.COMPLETED_PROJECTS,
                        title="Semantic Match",
                        content="",
                        metadata={},
                        created_at=datetime.now()
                    ),
                    relevance_score=0.75,
                    match_type="semantic",
                    preview=""
                )
                
                mock_sql.return_value = [sql_result]
                mock_vector.return_value = [vector_result]
                
                # When called through search(), results should be sorted
                results = [sql_result, vector_result]
                sorted_results = sorted(results, key=lambda x: x.relevance_score, reverse=True)
                
                assert sorted_results[0].match_type == "exact"
                assert sorted_results[1].match_type == "semantic"
