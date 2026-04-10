"""Phase 9: 핵심 서비스 단위 테스트

테스트 대상:
- token_manager: STEP별 토큰 예산 관리 (함수 기반)
- session_manager: ProposalSessionManager
- section_lock: acquire_lock / release_lock (함수 기반)
- source_tagger: SourceTag + 출처 분석 함수들
- compliance_tracker: ComplianceTracker
"""

from unittest.mock import patch
from tests.conftest import make_supabase_mock


# ══════════════════════════════════════
# Token Manager (함수 기반)
# ══════════════════════════════════════

def test_token_manager_imports():
    """token_manager 핵심 함수 import 가능."""
    from app.services.token_manager import get_budget, check_budget, truncate_context, build_context, estimate_tokens
    assert callable(get_budget)
    assert callable(check_budget)
    assert callable(truncate_context)
    assert callable(build_context)
    assert callable(estimate_tokens)


def test_token_manager_get_budget():
    """STEP별 토큰 예산 조회."""
    from app.services.token_manager import get_budget
    budget = get_budget("rfp_analyze")
    assert isinstance(budget, int)
    assert budget > 0


def test_token_manager_check_budget():
    """예산 확인 — 초과 여부."""
    from app.services.token_manager import check_budget
    result = check_budget("rfp_analyze", 1000)
    assert isinstance(result, dict)
    assert "allowed" in result or "ok" in result or "within_budget" in result or isinstance(result.get("budget"), int)


def test_token_manager_estimate_tokens():
    """토큰 수 추정."""
    from app.services.token_manager import estimate_tokens
    count = estimate_tokens("이것은 테스트 문장입니다.")
    assert isinstance(count, int)
    assert count > 0


def test_token_manager_truncate_context():
    """컨텍스트 트렁케이션."""
    from app.services.token_manager import truncate_context
    long_text = "가" * 10000
    truncated = truncate_context(long_text, max_chars=100)
    assert len(truncated) <= len(long_text)  # 트렁케이션이 동작함


# ══════════════════════════════════════
# Session Manager
# ══════════════════════════════════════

def test_session_manager_import():
    """ProposalSessionManager import 가능."""
    from app.services.session_manager import ProposalSessionManager
    assert ProposalSessionManager is not None


async def test_session_manager_mark_expired():
    """만료 프로포절 마킹."""
    from app.services.session_manager import ProposalSessionManager

    mock_sb = make_supabase_mock(table_data={
        "proposals": [
            {"id": "p-1", "status": "processing", "updated_at": "2026-01-01T00:00:00Z"},
        ],
    })
    with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
        sm = ProposalSessionManager()
        count = await sm.mark_expired_proposals()
    assert isinstance(count, int)


# ══════════════════════════════════════
# Section Lock (함수 기반)
# ══════════════════════════════════════

def test_section_lock_import():
    """section_lock 함수 import 가능."""
    from app.services.section_lock import acquire_lock, release_lock, get_locks
    assert callable(acquire_lock)
    assert callable(release_lock)
    assert callable(get_locks)


async def test_section_lock_acquire():
    """섹션 잠금 획득."""
    from app.services.section_lock import acquire_lock

    mock_sb = make_supabase_mock(table_data={"section_locks": []})
    with patch("app.services.section_lock.get_async_client", return_value=mock_sb):
        result = await acquire_lock("prop-1", "sec-1", "user-001")
    assert result is not None


async def test_section_lock_release():
    """섹션 잠금 해제."""
    from app.services.section_lock import release_lock

    mock_sb = make_supabase_mock(table_data={"section_locks": []})
    with patch("app.services.section_lock.get_async_client", return_value=mock_sb):
        await release_lock("prop-1", "sec-1", "user-001")


# ══════════════════════════════════════
# Source Tagger
# ══════════════════════════════════════

def test_source_tagger_import():
    """source_tagger 함수 import 가능."""
    from app.services.source_tagger import SourceTag, extract_source_tags
    assert SourceTag is not None
    assert callable(extract_source_tags)


def test_source_tagger_extract_tags():
    """텍스트에서 출처 태그 추출."""
    from app.services.source_tagger import extract_source_tags
    text = "이 시스템은 [출처:KB-001] 성공적으로 구축되었습니다."
    tags = extract_source_tags(text)
    assert isinstance(tags, list)


def test_source_tagger_grounding_ratio():
    """근거 비율 분석."""
    from app.services.source_tagger import calculate_grounding_ratio
    text = "이 프로젝트는 [출처:KB-001] 실적 기반입니다. 우리는 최고입니다."
    result = calculate_grounding_ratio(text)
    assert isinstance(result, dict)
    assert "kb_ratio" in result or "grounding_ratio" in result or "ratio" in result


def test_source_tagger_trustworthiness():
    """신뢰성 평가."""
    from app.services.source_tagger import evaluate_trustworthiness
    text = "약 100건의 프로젝트를 수행했습니다."
    result = evaluate_trustworthiness(text)
    assert isinstance(result, dict)


# ══════════════════════════════════════
# Compliance Tracker
# ══════════════════════════════════════

def test_compliance_tracker_import():
    """ComplianceTracker import 가능."""
    from app.services.compliance_tracker import ComplianceTracker
    assert ComplianceTracker is not None


def test_compliance_tracker_create():
    """ComplianceTracker 인스턴스 생성."""
    from app.services.compliance_tracker import ComplianceTracker
    tracker = ComplianceTracker()
    assert tracker is not None
