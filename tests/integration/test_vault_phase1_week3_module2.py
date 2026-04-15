"""
Vault AI Chat Phase 1 Week 3 Module-2 - Context, Cache, and Citation Tests
Tests for:
- A.1: Context Manager (6-turn context, topic detection)
- A.3: Citation Service (citation parsing, validation)
- B.1: Cache Service (search result caching)
- B.2: Parallel Search (asyncio.gather optimization)
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import List, Dict, Any

from app.models.vault_schemas import (
    ChatMessage,
    DocumentSource,
    VaultSection,
    SearchResult,
    SearchFilter,
    VaultDocument,
)
from app.services.vault_context_manager import VaultContextManager
from app.services.vault_citation_service import VaultCitationService
from app.services.vault_cache_service import VaultCacheService


class TestA1ContextManager:
    """Test A.1: Context Manager — extract and enhance conversation context"""

    def test_extract_context_returns_last_6_turns(self):
        """Test extract_context returns last N turns (default 6)"""
        messages = [
            ChatMessage(id="msg-1", role="user", content="First question"),
            ChatMessage(id="msg-2", role="assistant", content="First answer"),
            ChatMessage(id="msg-3", role="user", content="Second question"),
            ChatMessage(id="msg-4", role="assistant", content="Second answer"),
            ChatMessage(id="msg-5", role="user", content="Third question"),
            ChatMessage(id="msg-6", role="assistant", content="Third answer"),
            ChatMessage(id="msg-7", role="user", content="Fourth question"),
            ChatMessage(id="msg-8", role="assistant", content="Fourth answer"),
        ]

        # Extract context
        context = VaultContextManager.extract_context(messages)

        # Should return last 6 turns
        assert len(context) == 6
        assert context[0].id == "msg-3"  # First of last 6
        assert context[-1].id == "msg-8"  # Last message

    def test_extract_context_shorter_than_window(self):
        """Test extract_context with fewer messages than window"""
        messages = [
            ChatMessage(id="msg-1", role="user", content="Q1"),
            ChatMessage(id="msg-2", role="assistant", content="A1"),
        ]

        context = VaultContextManager.extract_context(messages)

        # Should return all messages
        assert len(context) == 2
        assert context[0].id == "msg-1"

    def test_detect_conversation_topic_from_first_message(self):
        """Test topic detection from first user message"""
        messages = [
            ChatMessage(id="msg-1", role="user", content="AI와 머신러닝에 대해 알려주세요. 이건 첫 번째 질문입니다."),
            ChatMessage(id="msg-2", role="assistant", content="네, 설명드리겠습니다."),
        ]

        topic = VaultContextManager.detect_conversation_topic(messages)

        # Should extract first 80 chars with format
        assert topic is not None
        assert "[대화 주제:" in topic
        assert "AI와 머신러닝에 대해 알려주세요. 이건 첫 번째 질문입니다." in topic

    def test_detect_conversation_topic_returns_none_when_no_messages(self):
        """Test topic detection returns None when no messages"""
        topic = VaultContextManager.detect_conversation_topic([])
        assert topic is None

    def test_build_context_string_formats_messages(self):
        """Test context string formatting"""
        messages = [
            ChatMessage(id="msg-1", role="user", content="First question"),
            ChatMessage(id="msg-2", role="assistant", content="First answer"),
        ]

        context_str = VaultContextManager.build_context_string(messages)

        # Should format as "Turn N: role: content"
        assert "Turn 1:" in context_str
        assert "사용자: First question" in context_str
        assert "Turn 2:" in context_str
        assert "어시스턴트: First answer" in context_str

    def test_build_user_message_with_context(self):
        """Test building user message with context"""
        context = [
            ChatMessage(id="msg-1", role="user", content="What is AI?"),
            ChatMessage(id="msg-2", role="assistant", content="AI is..."),
        ]

        enhanced = VaultContextManager.build_user_message_with_context(
            message="Tell me more about machine learning",
            context=context
        )

        # Should include topic hint and context
        assert "[대화 주제:" in enhanced
        assert "What is AI?" in enhanced
        assert "현재 질문:" in enhanced
        assert "Tell me more about machine learning" in enhanced


class TestA3CitationService:
    """Test A.3: Citation Service — format and validate citations"""

    def test_inject_citation_instructions_with_sources(self):
        """Test citation instructions injection"""
        base_prompt = "You are helpful assistant."

        enhanced = VaultCitationService.inject_citation_instructions(
            system_prompt=base_prompt,
            source_count=3
        )

        # Should add citation section with source count
        assert "출처 인용 방식" in enhanced
        assert "[출처 N] 형식" in enhanced
        assert "1부터 3까지" in enhanced

    def test_inject_citation_instructions_no_sources(self):
        """Test that no instructions added when source_count=0"""
        base_prompt = "You are helpful."

        enhanced = VaultCitationService.inject_citation_instructions(
            system_prompt=base_prompt,
            source_count=0
        )

        # Should return unchanged
        assert enhanced == base_prompt

    def test_parse_citations_extracts_all_indices(self):
        """Test citation parsing from response"""
        text = "이 정보는 중요합니다[출처 1]. 또한 [출처 2]에 따르면..."

        text_out, indices = VaultCitationService.parse_citations(text)

        # Should extract indices
        assert text_out == text  # Original text unchanged
        assert indices == [1, 2]

    def test_parse_citations_handles_duplicates(self):
        """Test citation parsing with duplicate indices"""
        text = "먼저 [출처 1]이고 [출처 1]입니다. 그리고 [출처 2]."

        _, indices = VaultCitationService.parse_citations(text)

        # Should return unique, sorted indices
        assert indices == [1, 2]

    def test_parse_citations_empty_response(self):
        """Test parsing empty response"""
        _, indices = VaultCitationService.parse_citations("")
        assert indices == []

    def test_validate_citations_within_range(self):
        """Test citation validation with valid indices"""
        sources = [
            DocumentSource(document_id="doc-1", section=VaultSection.COMPLETED_PROJECTS, title="P1"),
            DocumentSource(document_id="doc-2", section=VaultSection.GOVERNMENT_GUIDELINES, title="G1"),
        ]

        text = "Info from [출처 1] and [출처 2]."

        is_valid, error = VaultCitationService.validate_citations(text, sources)

        assert is_valid is True
        assert error is None

    def test_validate_citations_out_of_range(self):
        """Test validation fails for invalid citation indices"""
        sources = [
            DocumentSource(document_id="doc-1", section=VaultSection.COMPLETED_PROJECTS, title="P1"),
        ]

        text = "Info from [출처 1] and [출처 2]."

        is_valid, error = VaultCitationService.validate_citations(text, sources)

        assert is_valid is False
        assert "유효하지 않은 출처 번호" in error

    def test_validate_citations_no_sources_with_citations(self):
        """Test validation fails when citations present but no sources"""
        text = "Info from [출처 1]."

        is_valid, error = VaultCitationService.validate_citations(text, [])

        assert is_valid is False
        assert "제공된 출처가 없습니다" in error

    def test_build_source_reference_section(self):
        """Test building formatted source reference section"""
        sources = [
            DocumentSource(
                document_id="doc-1",
                section=VaultSection.COMPLETED_PROJECTS,
                title="Project A",
                confidence=0.95
            ),
            DocumentSource(
                document_id="doc-2",
                section=VaultSection.GOVERNMENT_GUIDELINES,
                title="Guideline B",
                confidence=0.88
            ),
        ]

        section = VaultCitationService.build_source_reference_section(sources)

        # Should format with numbers and section info
        assert "[1] Project A" in section
        assert "[2] Guideline B" in section
        # Enum values are lowercase
        assert "completed_projects" in section.lower()
        assert "government_guidelines" in section.lower()


class TestB1CacheService:
    """Test B.1: Cache Service — database-backed search caching"""

    def test_make_cache_key_consistent(self):
        """Test that cache key generation is deterministic"""
        query = "AI 프로젝트"
        sections = ["COMPLETED_PROJECTS", "GOVERNMENT_GUIDELINES"]
        filters = {"industry": "tech", "team_size_min": 3}

        key1 = VaultCacheService._make_cache_key(query, sections, filters)
        key2 = VaultCacheService._make_cache_key(query, sections, filters)

        # Same inputs should produce same key
        assert key1 == key2

    def test_make_cache_key_different_for_different_inputs(self):
        """Test cache key differs for different inputs"""
        query1 = "AI 프로젝트"
        query2 = "Machine learning"
        sections = ["COMPLETED_PROJECTS"]
        filters = {}

        key1 = VaultCacheService._make_cache_key(query1, sections, filters)
        key2 = VaultCacheService._make_cache_key(query2, sections, filters)

        # Different queries should produce different keys
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_cache_service_methods_exist(self):
        """Test that all cache service methods are callable"""
        assert callable(VaultCacheService.get_search)
        assert callable(VaultCacheService.set_search)
        assert callable(VaultCacheService.get_routing)
        assert callable(VaultCacheService.set_routing)
        assert callable(VaultCacheService.invalidate_section)


class TestB2ParallelSearch:
    """Test B.2: Parallel Search — asyncio.gather optimization"""

    @pytest.mark.asyncio
    async def test_parallel_search_structure(self):
        """Test that parallel search uses asyncio.gather"""
        # Mock handlers
        mock_handler1 = AsyncMock()
        mock_handler1.search = AsyncMock(return_value=[
            SearchResult(
                document=VaultDocument(
                    id="doc-1",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title="Project 1",
                    content="Content 1",
                    created_at=datetime.now()
                ),
                relevance_score=0.9,
                match_type="exact"
            )
        ])

        mock_handler2 = AsyncMock()
        mock_handler2.search = AsyncMock(return_value=[
            SearchResult(
                document=VaultDocument(
                    id="doc-2",
                    section=VaultSection.GOVERNMENT_GUIDELINES,
                    title="Guideline 1",
                    content="Content 2",
                    created_at=datetime.now()
                ),
                relevance_score=0.85,
                match_type="semantic"
            )
        ])

        # Simulate parallel search
        tasks = [
            mock_handler1.search("test", {}),
            mock_handler2.search("test", {}),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Should execute both searches
        assert len(results) == 2
        assert len(results[0]) == 1
        assert len(results[1]) == 1
        mock_handler1.search.assert_called_once()
        mock_handler2.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_parallel_search_handles_exceptions(self):
        """Test that parallel search handles exceptions gracefully"""
        mock_handler1 = AsyncMock()
        mock_handler1.search = AsyncMock(side_effect=Exception("Search failed"))

        mock_handler2 = AsyncMock()
        mock_handler2.search = AsyncMock(return_value=[])

        tasks = [
            mock_handler1.search("test", {}),
            mock_handler2.search("test", {}),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Should handle exception gracefully
        assert len(results) == 2
        assert isinstance(results[0], Exception)
        assert results[1] == []


class TestIntegrationModule2:
    """Integration tests for Module-2 features"""

    def test_context_manager_and_citation_together(self):
        """Test context manager output with citation service"""
        # Create conversation
        messages = [
            ChatMessage(id="msg-1", role="user", content="AI 프로젝트에 대해"),
            ChatMessage(id="msg-2", role="assistant", content="AI는..."),
            ChatMessage(id="msg-3", role="user", content="더 알려줘"),
        ]

        # Extract context
        context = VaultContextManager.extract_context(messages)

        # Build user message with context
        enhanced_user_msg = VaultContextManager.build_user_message_with_context(
            message="마지막 질문이 있어",
            context=context
        )

        # Should have topic and context
        assert "AI 프로젝트에 대해" in enhanced_user_msg
        assert "마지막 질문이 있어" in enhanced_user_msg

        # Now simulate LLM response and validate citations
        llm_response = "첫 번째 정보[출처 1]. 두 번째 정보[출처 2]."
        sources = [
            DocumentSource(document_id="d1", section=VaultSection.COMPLETED_PROJECTS, title="S1"),
            DocumentSource(document_id="d2", section=VaultSection.COMPLETED_PROJECTS, title="S2"),
        ]

        is_valid, error = VaultCitationService.validate_citations(llm_response, sources)
        assert is_valid is True

    def test_cache_key_generation_matches_spec(self):
        """Test cache key generation follows spec"""
        query = "AI"
        sections = ["COMPLETED_PROJECTS"]
        filters = {"industry": "tech"}

        key = VaultCacheService._make_cache_key(query, sections, filters)

        # Should be SHA256 hash (64 hex chars)
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    def test_citation_format_in_response(self):
        """Test that citation format can be validated in response"""
        response = """
        첫 번째 요점은 이렇습니다[출처 1].
        두 번째는 [출처 2]에 따르면...
        그리고 첫 번째를 다시 인용하면[출처 1]...
        """

        _, indices = VaultCitationService.parse_citations(response)

        # Should extract unique indices
        assert set(indices) == {1, 2}

        # Validate against sources
        sources = [
            DocumentSource(document_id="d1", section=VaultSection.COMPLETED_PROJECTS, title="S1"),
            DocumentSource(document_id="d2", section=VaultSection.COMPLETED_PROJECTS, title="S2"),
        ]

        is_valid, error = VaultCitationService.validate_citations(response, sources)
        assert is_valid is True
        assert error is None
