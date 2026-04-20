"""
Unit Tests for Vault Phase 2 Services
Tests: VaultContextManager, VaultPermissionFilter, VaultMultiLangHandler
Design Ref: §5.1
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List
from datetime import datetime

from app.models.vault_schemas import ChatMessage, DocumentSource
from app.services.vault_context_manager import VaultContextManager
from app.services.vault_permission_filter import VaultPermissionFilter
from app.services.vault_multilang_handler import VaultMultiLangHandler


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_messages() -> List[ChatMessage]:
    """Create mock conversation messages"""
    return [
        ChatMessage(
            id="msg1",
            role="user",
            content="우리 팀의 낙찰 현황을 알려줘",
            created_at=datetime(2026, 4, 20, 10, 0, 0)
        ),
        ChatMessage(
            id="msg2",
            role="assistant",
            content="지난 3개월간 5개 프로젝트를 낙찰했습니다.",
            created_at=datetime(2026, 4, 20, 10, 1, 0)
        ),
        ChatMessage(
            id="msg3",
            role="user",
            content="상세 정보를 보고 싶어",
            created_at=datetime(2026, 4, 20, 10, 2, 0)
        ),
        ChatMessage(
            id="msg4",
            role="assistant",
            content="자세한 정보는 다음과 같습니다...",
            created_at=datetime(2026, 4, 20, 10, 3, 0)
        ),
    ]


@pytest.fixture
def mock_document_sources() -> List[DocumentSource]:
    """Create mock document sources"""
    return [
        DocumentSource(
            document_id="doc1",
            section="completed_projects",
            title="환경부 스마트팩토리 프로젝트",
            snippet="2026년 1월 수주",
            confidence=0.95
        ),
        DocumentSource(
            document_id="doc2",
            section="success_cases",
            title="경쟁사 분석 보고서",
            snippet="OOO사의 최근 입찰 전략",
            confidence=0.87
        ),
    ]


@pytest.fixture
def mock_supabase():
    """Create mock Supabase client"""
    client = AsyncMock()
    return client


# ============================================================================
# VaultContextManager Tests
# ============================================================================

class TestVaultContextManager:
    """Tests for VaultContextManager service"""

    def test_extract_context_basic(self, mock_messages):
        """Test basic context extraction (last 8 turns)"""
        context = VaultContextManager.extract_context(mock_messages)

        assert len(context) == 4
        assert context[0].content == "우리 팀의 낙찰 현황을 알려줘"
        assert context[-1].content == "자세한 정보는 다음과 같습니다..."

    def test_extract_context_empty(self):
        """Test context extraction with empty list"""
        context = VaultContextManager.extract_context([])

        assert context == []

    def test_extract_context_window(self):
        """Test context extraction respects window size"""
        # Create 12 messages
        messages = [
            ChatMessage(role="user", content=f"Message {i}")
            for i in range(12)
        ]

        context = VaultContextManager.extract_context(messages)

        # Should return last 8 (CONTEXT_WINDOW)
        assert len(context) == 8
        assert context[0].content == "Message 4"
        assert context[-1].content == "Message 11"

    def test_detect_conversation_topic(self, mock_messages):
        """Test conversation topic detection"""
        topic = VaultContextManager.detect_conversation_topic(mock_messages)

        assert topic is not None
        assert "우리 팀의 낙찰" in topic
        assert "..." in topic

    def test_detect_conversation_topic_empty(self):
        """Test topic detection with empty messages"""
        topic = VaultContextManager.detect_conversation_topic([])

        assert topic is None

    def test_build_context_string(self, mock_messages):
        """Test context string formatting"""
        context = VaultContextManager.extract_context(mock_messages)
        context_str = VaultContextManager.build_context_string(context)

        assert "Turn 1:" in context_str
        assert "사용자" in context_str
        assert "어시스턴트" in context_str
        assert "낙찰" in context_str

    def test_build_context_string_truncates_long_messages(self):
        """Test that context string truncates long messages"""
        long_content = "A" * 1000
        messages = [
            ChatMessage(role="user", content=long_content)
        ]

        context_str = VaultContextManager.build_context_string(messages)

        # Should be truncated to 500 chars + "..."
        assert "..." in context_str
        assert len(context_str) < len(long_content)

    def test_build_user_message_with_context(self, mock_messages):
        """Test enhanced user message building"""
        context = VaultContextManager.extract_context(mock_messages)
        enhanced = VaultContextManager.build_user_message_with_context(
            "더 자세히 설명해줘",
            context
        )

        assert "[이전 대화 맥락]" in enhanced
        assert "[현재 질문]" in enhanced
        assert "더 자세히 설명해줘" in enhanced
        assert "Turn 1:" in enhanced

    def test_should_inject_context_true(self):
        """Test context injection decision - should inject"""
        assert VaultContextManager.should_inject_context(2) is True
        assert VaultContextManager.should_inject_context(5) is True

    def test_should_inject_context_false(self):
        """Test context injection decision - should not inject"""
        assert VaultContextManager.should_inject_context(1) is False
        assert VaultContextManager.should_inject_context(0) is False

    def test_estimate_token_count(self):
        """Test token estimation"""
        # Approximation: 4 chars = 1 token
        text = "A" * 100
        tokens = VaultContextManager.estimate_token_count(text)

        assert tokens == 26  # 100/4 + 1
        assert isinstance(tokens, int)

    def test_trim_context_by_tokens(self):
        """Test context trimming within token budget"""
        # Create context within token budget
        context_str = "Turn 1: 사용자: Hello\nTurn 2: 어시스턴트: World"
        max_tokens = 100

        trimmed = VaultContextManager.trim_context_by_tokens(context_str, max_tokens)

        # Should not trim since within budget
        assert len(trimmed) > 0

    def test_trim_context_by_tokens_exceeds_budget(self):
        """Test context trimming when exceeding token budget"""
        # Create very long context
        context_str = "\n".join([f"Turn {i}: Message {'A' * 50}" for i in range(20)])
        max_tokens = 50

        trimmed = VaultContextManager.trim_context_by_tokens(context_str, max_tokens)

        # Should trim
        tokens = VaultContextManager.estimate_token_count(trimmed)
        assert tokens <= max_tokens

    def test_prepare_context_for_injection(self, mock_messages):
        """Test complete context preparation for injection"""
        context_str, token_count = VaultContextManager.prepare_context_for_injection(
            mock_messages,
            max_tokens=200
        )

        assert len(context_str) > 0
        assert token_count > 0
        assert token_count <= 200
        assert isinstance(context_str, str)


# ============================================================================
# VaultPermissionFilter Tests
# ============================================================================

class TestVaultPermissionFilter:
    """Tests for VaultPermissionFilter service"""

    def test_get_role_level_member(self):
        """Test role level lookup for member"""
        level = VaultPermissionFilter.get_role_level("member")
        assert level == 0

    def test_get_role_level_admin(self):
        """Test role level lookup for admin"""
        level = VaultPermissionFilter.get_role_level("admin")
        assert level == 4

    def test_get_role_level_unknown(self):
        """Test role level lookup for unknown role"""
        level = VaultPermissionFilter.get_role_level("unknown")
        assert level == 0  # Default

    def test_get_role_level_case_insensitive(self):
        """Test role level lookup is case insensitive"""
        assert VaultPermissionFilter.get_role_level("LEAD") == 1
        assert VaultPermissionFilter.get_role_level("LeAdEr") == 0  # Unknown

    @pytest.mark.asyncio
    async def test_filter_response_no_sources(self):
        """Test filtering response with no sources"""
        mock_supabase = AsyncMock()

        response, sources, reasons = await VaultPermissionFilter.filter_response(
            user_role="member",
            response_text="Test response",
            sources=[],
            supabase_client=mock_supabase,
            user_id="user1"
        )

        assert response == "Test response"
        assert sources == []
        assert reasons == []

    def test_validate_role_valid(self):
        """Test role validation for valid roles"""
        assert VaultPermissionFilter.validate_role("member") is True
        assert VaultPermissionFilter.validate_role("admin") is True
        assert VaultPermissionFilter.validate_role("DIRECTOR") is True

    def test_validate_role_invalid(self):
        """Test role validation for invalid roles"""
        assert VaultPermissionFilter.validate_role("unknown") is False
        assert VaultPermissionFilter.validate_role("superuser") is False

    def test_check_sensitive_content_clean(self):
        """Test sensitive content check - clean response"""
        is_clean, detected = VaultPermissionFilter.check_sensitive_content(
            response_text="Here is public information",
            user_role="member",
            restricted_keywords=["salary", "budget"]
        )

        assert is_clean is True
        assert detected == []

    def test_check_sensitive_content_dirty(self):
        """Test sensitive content check - contains restricted keyword"""
        is_clean, detected = VaultPermissionFilter.check_sensitive_content(
            response_text="The salary for this role is $100,000",
            user_role="member",
            restricted_keywords=["salary", "budget"]
        )

        assert is_clean is False
        assert "salary" in detected


# ============================================================================
# VaultMultiLangHandler Tests
# ============================================================================

class TestVaultMultiLangHandler:
    """Tests for VaultMultiLangHandler service"""

    def test_detect_language_korean(self):
        """Test Korean language detection"""
        lang = VaultMultiLangHandler.detect_language("안녕하세요. 우리 팀의 낙찰 현황을 알려줘")
        assert lang == "ko"

    def test_detect_language_english(self):
        """Test English language detection"""
        lang = VaultMultiLangHandler.detect_language("Hello, what is the latest project status?")
        assert lang == "en"

    def test_detect_language_default(self):
        """Test default language when detection uncertain"""
        lang = VaultMultiLangHandler.detect_language("123")
        assert lang == "ko"  # Default

    def test_detect_language_empty(self):
        """Test language detection with empty string"""
        lang = VaultMultiLangHandler.detect_language("")
        assert lang == "ko"  # Default

    def test_get_language_label_valid(self):
        """Test language label conversion"""
        assert VaultMultiLangHandler.get_language_label("ko") == "한국어"
        assert VaultMultiLangHandler.get_language_label("en") == "영어"
        assert VaultMultiLangHandler.get_language_label("zh") == "중국어"

    def test_get_language_label_invalid(self):
        """Test language label for invalid code"""
        assert VaultMultiLangHandler.get_language_label("xx") == "Unknown"

    @pytest.mark.asyncio
    async def test_save_language_preference_invalid(self):
        """Test saving invalid language preference"""
        mock_supabase = AsyncMock()

        result = await VaultMultiLangHandler.save_language_preference(
            mock_supabase,
            "user1",
            "invalid_lang"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_determine_query_language_explicit(self):
        """Test explicit language specification takes priority"""
        mock_supabase = AsyncMock()

        lang = await VaultMultiLangHandler.determine_query_language(
            text="한국어 텍스트",
            supabase_client=mock_supabase,
            user_id="user1",
            explicit_language="en"
        )

        assert lang == "en"  # Explicit overrides detection

    @pytest.mark.asyncio
    async def test_determine_query_language_detected(self):
        """Test language detection fallback"""
        mock_supabase = AsyncMock()

        lang = await VaultMultiLangHandler.determine_query_language(
            text="Hello, this is English",
            supabase_client=mock_supabase,
            user_id=None,
            explicit_language=None
        )

        assert lang == "en"  # Detected

    @pytest.mark.asyncio
    async def test_determine_query_language_default(self):
        """Test default language when no detection"""
        mock_supabase = AsyncMock()

        lang = await VaultMultiLangHandler.determine_query_language(
            text="123",
            supabase_client=mock_supabase,
            user_id=None,
            explicit_language=None
        )

        assert lang == "ko"  # Default

    @pytest.mark.asyncio
    async def test_search_multilang_empty(self):
        """Test multi-language search returns list"""
        mock_supabase = AsyncMock()

        results = await VaultMultiLangHandler.search_multilang(
            mock_supabase,
            "프로젝트",
            language="ko",
            limit=10
        )

        # Should handle gracefully (empty or with error)
        assert isinstance(results, list)

    def test_validate_language_code_valid(self):
        """Test language code validation - valid codes"""
        assert VaultMultiLangHandler.validate_language_code("ko") is True
        assert VaultMultiLangHandler.validate_language_code("en") is True
        assert VaultMultiLangHandler.validate_language_code("zh") is True

    def test_validate_language_code_invalid(self):
        """Test language code validation - invalid codes"""
        assert VaultMultiLangHandler.validate_language_code("xx") is False
        assert VaultMultiLangHandler.validate_language_code("invalid") is False

    def test_get_supported_languages_info(self):
        """Test getting supported languages information"""
        langs = VaultMultiLangHandler.get_supported_languages_info()

        assert "ko" in langs
        assert "en" in langs
        assert "zh" in langs
        assert "ja" in langs
        assert langs["ko"] == "한국어"


# ============================================================================
# Integration Tests
# ============================================================================

class TestVaultPhase2Integration:
    """Integration tests combining multiple services"""

    def test_context_and_permission_flow(self, mock_messages, mock_document_sources):
        """Test context extraction + permission filtering flow"""
        # Step 1: Extract context
        context = VaultContextManager.extract_context(mock_messages)
        context_str = VaultContextManager.build_context_string(context)

        assert len(context) > 0
        assert len(context_str) > 0

        # Step 2: Check permissions (would be async in real flow)
        assert VaultPermissionFilter.validate_role("director") is True
        assert VaultPermissionFilter.get_role_level("director") == 2

    def test_language_detection_in_context(self, mock_messages):
        """Test language detection in context messages"""
        # Simulate non-Korean message
        en_message = ChatMessage(
            role="user",
            content="What is the project status?"
        )

        detected = VaultMultiLangHandler.detect_language(en_message.content)
        assert detected == "en"

        # Korean message
        ko_detected = VaultMultiLangHandler.detect_language(mock_messages[0].content)
        assert ko_detected == "ko"
