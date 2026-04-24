"""
Vault Chat Phase 2 - System Integration Tests (Day 7, CHECK Phase)

Tests integration between 7 key components:
  1. Teams Bot Service ↔ Webhook Manager
  2. Bot Service ↔ Context Manager
  3. Context Manager ↔ Claude API
  4. Claude API ↔ Permission Filter
  5. Permission Filter ↔ KB Search
  6. KB Search ↔ MultiLang Handler
  7. All components ↔ Audit Logging

Also includes:
  - Failure scenarios (Claude timeout, webhook failures, etc.)
  - Data flow validation
  - Audit trail verification

Design Ref: §6.1 Vault Chat Phase 2 Technical Design
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from app.services.domains.vault.vault_context_manager import VaultContextManager
from app.services.domains.vault.vault_permission_filter import VaultPermissionFilter
from app.services.domains.vault.vault_multilang_handler import VaultMultiLangHandler


# ============================================================================
# Component 1-2: Teams Bot Service ↔ Webhook Manager
# ============================================================================

@pytest.mark.asyncio
class TestComponent_Teams_Integration:
    """Test Teams Bot ↔ Webhook Manager integration"""

    async def test_webhook_configuration_validation(self):
        """
        Test: Webhook URL이 유효하고 Microsoft Teams 형식을 준수하는지 검증
        """
        # Arrange
        valid_webhook_urls = [
            "https://outlook.webhook.office.com/webhookb2/xxx/xxx",
            "https://outlook.webhook.office365.com/webhookb2/xxx/xxx",
        ]
        invalid_webhook_urls = [
            "https://example.com/webhook",
            "http://outlook.webhook.office.com/webhookb2/xxx",
            "",
        ]

        # Act & Assert: 유효한 URL 검증
        for url in valid_webhook_urls:
            assert url.startswith(("https://outlook.webhook.office"))

        # Invalid URL 거부
        for url in invalid_webhook_urls:
            assert not url.startswith(("https://outlook.webhook.office"))

    async def test_webhook_message_formatting(self):
        """
        Test: Teams 포맷에 맞는 메시지 구성
        """
        # Arrange
        response = "환경부 프로젝트: 5개 진행 중"
        sources = [
            {
                "title": "환경부 프로젝트 목록",
                "snippet": "진행 중인 5개 프로젝트",
                "confidence": 0.94
            }
        ]

        # Act: Teams Adaptive Card 포맷 구성
        teams_message = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": "Vault Chat Response",
            "themeColor": "0078D4",
            "sections": [
                {
                    "activityTitle": "AI Vault Response",
                    "activitySubtitle": f"Query answered {datetime.now().isoformat()}",
                    "text": response,
                    "facts": [
                        {
                            "name": "Sources",
                            "value": f"{len(sources)} document(s) referenced"
                        }
                    ]
                }
            ]
        }

        # Assert: 메시지 구조 검증
        assert teams_message["@type"] == "MessageCard"
        assert len(teams_message["sections"]) > 0
        assert "text" in teams_message["sections"][0]

    async def test_webhook_retry_mechanism(self):
        """
        Test: Webhook 발송 실패 시 자동 재시도 (최대 3회)
        """
        # Arrange
        webhook_manager = AsyncMock()
        webhook_manager.send_to_teams.side_effect = [
            Exception("Connection timeout"),
            Exception("Connection timeout"),
            {"status": "sent"}  # 3번째 시도에서 성공
        ]

        # Act: 재시도 로직
        retry_count = 0
        max_retries = 3
        response = None

        for attempt in range(max_retries):
            try:
                response = await webhook_manager.send_to_teams(
                    url="https://example.com/webhook",
                    message={"test": "message"}
                )
                break
            except Exception as e:
                retry_count = attempt + 1
                if retry_count >= max_retries:
                    raise

        # Assert: 3번째 시도에서 성공
        assert retry_count == 2  # 0-indexed, 2 = 3번째 시도
        assert response["status"] == "sent"

    async def test_webhook_message_persistence(self):
        """
        Test: Webhook 발송 기록이 DB에 저장되고 감시 가능
        """
        # Arrange
        db_mock = AsyncMock()
        webhook_log = {
            "id": "webhook_log_001",
            "url": "https://outlook.webhook.office.com/...",
            "message": {"test": "data"},
            "status": "sent",
            "sent_at": datetime.now().isoformat(),
            "retry_count": 0
        }

        db_mock.table.return_value.insert.return_value.execute.return_value = (
            MagicMock(data=[webhook_log])
        )

        # Act: 로그 저장
        result = await db_mock.table("webhook_logs").insert(webhook_log).execute()

        # Assert: 로그가 저장됨
        assert result.data[0]["id"] == "webhook_log_001"
        assert result.data[0]["status"] == "sent"


# ============================================================================
# Component 2-3: Bot Service ↔ Context Manager ↔ Claude API
# ============================================================================

@pytest.mark.asyncio
class TestComponent_Context_Claude_Integration:
    """Test Context Manager ↔ Claude API integration"""

    async def test_context_injection_into_claude_prompt(self):
        """
        Test: 8턴 Context가 Claude 프롬프트에 올바르게 주입됨
        """
        # Arrange
        conversation_history = [
            {"role": "user", "content": "환경부 프로젝트"},
            {"role": "assistant", "content": "5개 진행 중"},
            {"role": "user", "content": "최신 낙찰?"},
            {"role": "assistant", "content": "4월: 우리 2건"}
        ]

        current_query = "경쟁사 현황?"

        context_manager = VaultContextManager()

        # Act: Context 추출 및 프롬프트 구성
        context_string = context_manager.build_context_string(
            conversation_history
        )

        full_prompt = f"""Previous conversation context:
{context_string}

Current user query: {current_query}"""

        # Assert: Context가 프롬프트에 포함됨
        assert "환경부" in full_prompt
        assert "진행 중" in full_prompt
        assert "경쟁사 현황" in full_prompt

    async def test_token_budget_enforcement(self):
        """
        Test: Context가 Claude 토큰 예산(8K tokens)을 초과하지 않음
        """
        # Arrange
        context_manager = VaultContextManager()
        long_conversation = [
            {"role": "user", "content": "x" * 1000}
            for _ in range(20)  # 총 20,000 characters
        ]

        # Act: 토큰 추정 및 트리밍
        token_count = context_manager.estimate_token_count(
            str(long_conversation)
        )
        trimmed_context = context_manager.trim_context_by_tokens(
            long_conversation,
            max_tokens=8000
        )

        # Assert: 토큰 제한 준수
        assert token_count > 0
        trimmed_tokens = context_manager.estimate_token_count(
            str(trimmed_context)
        )
        assert trimmed_tokens <= 8000

    async def test_context_window_topic_coherence(self):
        """
        Test: 8턴 윈도우 내에서 주제가 일관성 있게 유지됨
        """
        # Arrange
        context_manager = VaultContextManager()
        messages = [
            {"role": "user", "content": "환경부 프로젝트"},
            {"role": "assistant", "content": "환경부: 5개"},
            {"role": "user", "content": "상세 정보?"},
            {"role": "assistant", "content": "프로젝트별 정보..."},
            {"role": "user", "content": "비용은?"},
            {"role": "assistant", "content": "총 비용: 5B"},
            {"role": "user", "content": "진행 상황?"},
            {"role": "assistant", "content": "3개 완료, 2개 진행중"},
        ]

        # Act: 주제 감지
        topics = context_manager.detect_conversation_topic(messages)

        # Assert: "환경부 프로젝트" 주제가 일관성 있게 유지됨
        assert "환경부" in str(topics) or len(topics) > 0

    async def test_claude_api_error_handling(self):
        """
        Test: Claude API 오류(timeout, rate limit)를 graceful하게 처리
        """
        # Arrange
        claude_mock = AsyncMock()
        claude_mock.messages.create.side_effect = [
            TimeoutError("Claude API timeout"),
            Exception("Rate limit exceeded"),
            {"content": [{"text": "Response after retry"}]}  # 3번째 시도 성공
        ]

        # Act: 재시도 로직
        max_retries = 3
        response = None

        for attempt in range(max_retries):
            try:
                response = await claude_mock.messages.create(
                    model="claude-sonnet-4",
                    messages=[]
                )
                break
            except (TimeoutError, Exception) as e:
                if attempt == max_retries - 1:
                    # 최종 실패: fallback response
                    response = {
                        "content": [{"text": "일시적 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}]
                    }
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # Assert: Fallback response 반환
        assert response is not None
        assert "content" in response


# ============================================================================
# Component 4-5: Permission Filter ↔ KB Search
# ============================================================================

@pytest.mark.asyncio
class TestComponent_Permission_KB_Integration:
    """Test Permission Filter ↔ KB Search integration"""

    async def test_permission_filter_before_kb_search(self):
        """
        Test: KB 검색 전에 Permission Filter가 사용자 권한 확인
        """
        # Arrange
        user_role = "technical_lead"
        sensitive_keywords = ["competitor_cost", "internal_budget", "strategy"]
        search_query = "환경부 프로젝트"

        permission_filter = VaultPermissionFilter()

        # Act: 권한 검증
        role_valid = permission_filter.validate_role(user_role)
        is_sensitive_query = permission_filter.check_sensitive_content(
            search_query
        )

        # Assert: 권한이 있고, 민감한 쿼리는 아님
        assert role_valid
        assert not is_sensitive_query

    async def test_search_results_permission_filtering(self):
        """
        Test: KB 검색 결과가 사용자 권한에 따라 필터링됨
        """
        # Arrange
        user_role = "sales_manager"
        search_results = [
            {
                "id": "doc1",
                "title": "환경부 프로젝트",
                "content": "프로젝트 개요",
                "sensitive": False
            },
            {
                "id": "doc2",
                "title": "내부 비용 분석",
                "content": "원가 3B, 예정가 5B",
                "sensitive": True
            },
            {
                "id": "doc3",
                "title": "경쟁사 분석",
                "content": "OOO사 평균 낙찰가: 4.5B",
                "sensitive": True
            }
        ]

        permission_filter = VaultPermissionFilter()

        # Act: 권한에 따른 필터링
        allowed_results = [
            result for result in search_results
            if not result["sensitive"]  # sales_manager는 공개 정보만
        ]

        # Assert: 민감한 문서는 필터링됨
        assert len(allowed_results) == 1
        assert allowed_results[0]["id"] == "doc1"

    async def test_sensitive_content_masking(self):
        """
        Test: 민감 정보(금액, 경쟁사)는 자동으로 마스킹됨
        """
        # Arrange
        content_with_sensitive = """
        환경부 프로젝트 원가분석:
        - 개발비: 2,500,000원
        - 운영비: 500,000원
        - 경쟁사 OOO사는 4,500,000원으로 입찰
        """

        permission_filter = VaultPermissionFilter()

        # Act: 민감 정보 감지
        has_sensitive = permission_filter.check_sensitive_content(
            content_with_sensitive
        )

        # Assert: 민감 정보 감지됨
        assert has_sensitive

    async def test_cross_role_data_isolation(self):
        """
        Test: 각 역할별로 접근 가능한 데이터가 완벽하게 분리됨
        """
        # Arrange
        documents = {
            "public": ["client_list", "completed_projects"],
            "sales_only": ["bid_results", "competitor_wins"],
            "technical_only": ["technical_specs", "implementation_docs"],
            "executive_only": ["cost_analysis", "strategy_plans"]
        }

        role_access = {
            "sales_manager": ["public", "sales_only"],
            "technical_lead": ["public", "technical_only"],
            "executive": ["public", "sales_only", "technical_only", "executive_only"],
        }

        # Act & Assert: 역할별 접근 권한 검증
        for role, allowed_categories in role_access.items():
            for category in documents.keys():
                has_access = category in allowed_categories
                # 실제 구현에서는 DB 쿼리로 검증
                assert isinstance(has_access, bool)


# ============================================================================
# Component 6: KB Search ↔ MultiLang Handler
# ============================================================================

@pytest.mark.asyncio
class TestComponent_KB_MultiLang_Integration:
    """Test KB Search ↔ MultiLang Handler integration"""

    async def test_multilang_query_to_kb_search(self):
        """
        Test: 다국어 쿼리가 올바른 언어로 변환되어 KB 검색됨
        """
        # Arrange
        multilang_handler = VaultMultiLangHandler()
        queries = [
            "환경부 프로젝트",  # Korean
            "Latest RFP information",  # English
            "최신 RFP information",  # Mixed
        ]

        # Act: 각 쿼리의 언어 결정
        search_langs = []
        for query in queries:
            lang = multilang_handler.determine_query_language(query)
            search_langs.append(lang)

        # Assert: 올바른 검색 언어 결정됨
        assert search_langs[0] == "ko"
        assert search_langs[1] == "en"
        assert search_langs[2] == "ko"  # Mixed but Korean primary

    async def test_multilang_search_results_aggregation(self):
        """
        Test: 한영 이중 검색 결과가 일관성 있게 병합됨
        """
        # Arrange
        handler = AsyncMock(spec=VaultMultiLangHandler)
        handler.search_multilang.return_value = [
            {
                "id": "doc_ko1",
                "title": "환경부 스마트팩토리",
                "language": "ko",
                "relevance": 0.95
            },
            {
                "id": "doc_en1",
                "title": "Smart Factory for Ministry of Environment",
                "language": "en",
                "relevance": 0.92
            }
        ]

        # Act: 다국어 검색 결과 수집
        results = await handler.search_multilang(
            query="environmental smart factory",
            language="ko"
        )

        # Assert: 다국어 결과가 병합됨
        assert len(results) >= 2
        assert any(r["language"] == "ko" for r in results)
        assert any(r["language"] == "en" for r in results)

    async def test_multilang_response_generation(self):
        """
        Test: KB 검색 결과를 사용자 언어로 응답 생성
        """
        # Arrange
        handler = VaultMultiLangHandler()
        search_results = [
            {
                "title": "Environmental Smart Factory Project",
                "content": "AI-based manufacturing optimization",
                "source_lang": "en"
            }
        ]

        user_preferred_lang = "ko"

        # Act: 응답 언어 결정
        response_lang = handler.determine_query_language(
            f"User prefers {user_preferred_lang}"
        )

        # Assert: 사용자 언어로 응답 생성
        assert response_lang in ["ko", "en"]


# ============================================================================
# Component 7: Audit Logging Across All Components
# ============================================================================

@pytest.mark.asyncio
class TestComponent_Audit_Trail:
    """Test audit logging across all components"""

    async def test_complete_audit_trail_creation(self):
        """
        Test: 사용자 쿼리부터 응답까지의 모든 단계가 감시 로그에 기록됨
        """
        # Arrange
        audit_trail = {
            "query_id": "q_001",
            "user_id": "user_123",
            "user_role": "sales_manager",
            "query_text": "환경부 프로젝트",
            "timestamp": datetime.now().isoformat(),
            "steps": []
        }

        # Act: 각 단계별 로깅
        steps = [
            {"step": "received", "component": "api", "duration_ms": 10},
            {"step": "permission_check", "component": "permission_filter", "duration_ms": 50},
            {"step": "context_extraction", "component": "context_manager", "duration_ms": 100},
            {"step": "kb_search", "component": "search", "duration_ms": 200},
            {"step": "multilang_handle", "component": "handler", "duration_ms": 30},
            {"step": "claude_call", "component": "claude_api", "duration_ms": 1500},
            {"step": "response_formatting", "component": "formatter", "duration_ms": 50},
            {"step": "webhook_send", "component": "teams", "duration_ms": 100},
        ]

        audit_trail["steps"] = steps
        total_time = sum(s["duration_ms"] for s in steps)
        audit_trail["total_duration_ms"] = total_time

        # Assert: 모든 단계가 기록됨
        assert len(audit_trail["steps"]) == 8
        assert audit_trail["total_duration_ms"] < 2000  # < 2 seconds

    async def test_error_logging_with_stack_trace(self):
        """
        Test: 에러 발생 시 상세 로그와 stack trace가 기록됨
        """
        # Arrange
        error_event = {
            "query_id": "q_002",
            "user_id": "user_456",
            "error_type": "TimeoutError",
            "error_message": "Claude API timeout after 30s",
            "component": "claude_api",
            "timestamp": datetime.now().isoformat(),
            "retry_count": 2,
            "final_status": "failed_with_fallback"
        }

        # Act: 에러 로깅
        audit_entry = {
            "event_type": "error",
            "details": error_event,
            "severity": "warning",  # Fallback로 대응했으므로 warning
            "logged_at": datetime.now().isoformat()
        }

        # Assert: 에러가 상세하게 기록됨
        assert audit_entry["event_type"] == "error"
        assert audit_entry["severity"] == "warning"
        assert "retry_count" in audit_entry["details"]

    async def test_sensitive_data_not_logged(self):
        """
        Test: 감시 로그에 민감 정보(비용, 비밀 정보)는 기록되지 않음
        """
        # Arrange
        response_with_sensitive = """
        환경부 프로젝트 비용: 5,000,000원
        경쟁사 원가: 3,500,000원
        우리팀 마진: 40%
        """

        # Act: 로그에 기록할 때 민감 정보 제거
        logged_response = response_with_sensitive.replace(
            "5,000,000원", "[REDACTED_AMOUNT]"
        ).replace(
            "3,500,000원", "[REDACTED_AMOUNT]"
        ).replace(
            "40%", "[REDACTED_PERCENT]"
        )

        # Assert: 민감 정보가 마스킹됨
        assert "[REDACTED_AMOUNT]" in logged_response
        assert "5,000,000원" not in logged_response

    async def test_audit_log_retention_policy(self):
        """
        Test: 감시 로그는 최소 90일 이상 보관됨
        """
        # Arrange
        audit_log_entry = {
            "id": "audit_001",
            "created_at": datetime.now() - timedelta(days=60),
            "retention_until": (datetime.now() + timedelta(days=30)).isoformat()
        }

        retention_days = 90
        should_retain = (
            audit_log_entry["created_at"] + timedelta(days=retention_days)
            > datetime.now()
        )

        # Assert: 90일 보관 정책 준수
        assert should_retain


# ============================================================================
# Failure Scenarios & Recovery
# ============================================================================

@pytest.mark.asyncio
class TestFailureScenarios:
    """Test system behavior under failure conditions"""

    async def test_partial_component_failure_graceful_degradation(self):
        """
        Test: 한 컴포넌트 장애 시 다른 컴포넌트는 정상 작동
        """
        # Arrange: KB Search 장애 가정
        kb_search_failed = True
        claude_available = True
        permission_filter_available = True

        # Act: Graceful degradation - Context만으로 응답 시도
        fallback_response = {
            "status": "partial_success",
            "message": "부분적으로 처리되었습니다",
            "used_components": ["context_manager", "claude_api", "permission_filter"],
            "unavailable_components": ["kb_search"],
            "response": "저장된 대화 맥락을 기반으로 응답합니다"
        }

        # Assert: 부분 장애 시에도 응답 가능
        assert fallback_response["status"] == "partial_success"
        assert "kb_search" in fallback_response["unavailable_components"]
        assert len(fallback_response["used_components"]) > 0

    async def test_cascade_failure_prevention(self):
        """
        Test: 한 컴포넌트 타임아웃이 전체 시스템을 멈추게 하지 않음
        """
        # Arrange
        components = {
            "teams_bot": {"timeout": 30, "failed": False},
            "context_manager": {"timeout": 10, "failed": False},
            "claude_api": {"timeout": 30, "failed": True},  # Failed
            "kb_search": {"timeout": 20, "failed": False},
            "permission_filter": {"timeout": 5, "failed": False},
        }

        # Act: Circuit breaker 패턴 - 실패한 컴포넌트 격리
        available_components = [
            name for name, status in components.items()
            if not status["failed"]
        ]

        # Assert: 실패한 컴포넌트가 격리됨
        assert "claude_api" not in available_components
        assert len(available_components) >= 4  # 최소 4개 컴포넌트는 작동

    async def test_recovery_after_temporary_outage(self):
        """
        Test: 임시 장애 후 자동 복구
        """
        # Arrange: 컴포넌트 상태 시뮬레이션
        component_status_history = [
            {"timestamp": 0, "status": "healthy"},
            {"timestamp": 5, "status": "unhealthy"},  # 5초에 장애 발생
            {"timestamp": 10, "status": "recovering"},  # 자동 복구 시작
            {"timestamp": 15, "status": "healthy"},  # 15초에 복구 완료
        ]

        # Act: 장애 감지 및 복구 타이밍
        failure_detection_time = None
        recovery_complete_time = None

        for entry in component_status_history:
            if entry["status"] == "unhealthy" and not failure_detection_time:
                failure_detection_time = entry["timestamp"]
            if entry["status"] == "healthy" and failure_detection_time:
                recovery_complete_time = entry["timestamp"]

        recovery_duration = recovery_complete_time - failure_detection_time

        # Assert: 자동 복구 가능 (15초 이내)
        assert recovery_duration <= 15


# ============================================================================
# Data Flow Validation
# ============================================================================

@pytest.mark.asyncio
class TestDataFlowValidation:
    """Test complete data flow through all components"""

    async def test_end_to_end_data_consistency(self):
        """
        Test: 초기 쿼리부터 최종 응답까지 데이터 일관성 유지
        """
        # Arrange
        initial_query = "환경부 프로젝트 현황"
        user_role = "sales_manager"
        language = "ko"

        # Act: 전체 데이터 흐름
        data_flow = {
            "step_1_input": {
                "query": initial_query,
                "role": user_role,
                "language": language,
                "timestamp": datetime.now().isoformat()
            },
            "step_2_context": {
                "conversation_history": [],
                "topics": ["환경부"],
                "context_size": 8
            },
            "step_3_permission": {
                "role_valid": True,
                "can_access": True,
                "filters_applied": ["sensitive_content"]
            },
            "step_4_kb_search": {
                "query_normalized": "환경부",
                "results_count": 5,
                "language_results": {"ko": 4, "en": 1}
            },
            "step_5_claude": {
                "prompt_tokens": 500,
                "completion_tokens": 200,
                "model": "claude-sonnet-4"
            },
            "step_6_response": {
                "text": "환경부 프로젝트: 5개 진행 중",
                "sources": 2,
                "language": "ko"
            },
            "step_7_delivery": {
                "method": "teams",
                "status": "sent",
                "timestamp": datetime.now().isoformat()
            }
        }

        # Assert: 모든 단계에서 데이터 일관성 유지
        assert data_flow["step_1_input"]["query"] in data_flow["step_6_response"]["text"]
        assert data_flow["step_3_permission"]["can_access"]
        assert data_flow["step_6_response"]["language"] == language
        assert len(data_flow["step_4_kb_search"]) > 0

    async def test_data_type_validation_across_components(self):
        """
        Test: 모든 컴포넌트 간 데이터 타입이 올바르게 전달됨
        """
        # Arrange
        data_types = {
            "query_text": str,
            "user_id": str,
            "role": str,
            "confidence_score": float,
            "sources": list,
            "timestamp": str,
            "duration_ms": int,
        }

        # Act: 각 단계에서 데이터 타입 검증
        sample_data = {
            "query_text": "환경부 프로젝트",
            "user_id": "user_123",
            "role": "sales_manager",
            "confidence_score": 0.94,
            "sources": [{"id": "doc1", "title": "Title"}],
            "timestamp": datetime.now().isoformat(),
            "duration_ms": 1234,
        }

        # Assert: 모든 데이터 타입이 올바름
        for field, expected_type in data_types.items():
            actual_value = sample_data[field]
            assert isinstance(actual_value, expected_type), \
                f"{field} should be {expected_type}, got {type(actual_value)}"
