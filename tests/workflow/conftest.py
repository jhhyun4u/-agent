"""워크플로 테스트 전용 fixtures.

Claude API, Supabase, prompt_registry/tracker, PricingEngine을 mock하여
LangGraph 그래프를 실제 실행할 수 있는 환경을 제공한다.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """fixtures/ 디렉토리에서 JSON 로드."""
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


# ── Claude API Mock ──

def _make_claude_mock(fixture_override: str | None = None):
    """claude_generate를 프롬프트 키워드 기반으로 디스패치하는 mock 생성."""

    rfp_fixture = fixture_override or "rfp_analyze.json"

    async def mock_claude_generate(prompt, **kwargs):
        text = prompt if isinstance(prompt, str) else str(prompt)

        # 노드별 프롬프트 키워드 매칭 (순서 중요: 더 구체적인 것 먼저)
        # claude_generate는 dict를 반환 (JSON 파싱 완료 상태)
        if "목차 확정" in text or "스토리라인 설계" in text:
            return load_fixture("plan_story.json")
        if "예산산정" in text or "Budget Narrative" in text or "원가 구조" in text:
            return load_fixture("plan_price.json")
        if "제안 팀을 구성" in text:
            return load_fixture("plan_team.json")
        if "산출물과 역할 배분" in text or ("산출물" in text and "배분" in text):
            return load_fixture("plan_assign.json")
        if "추진 일정" in text:
            return load_fixture("plan_schedule.json")
        if "RFP 문서를 분석" in text or "케이스 A" in text:
            return load_fixture(rfp_fixture)
        if "선행 리서치" in text or "리서치 주제" in text:
            return load_fixture("research_gather.json")
        if "Go/No-Go" in text:
            return load_fixture("go_no_go.json")
        if "제안 전략을 수립" in text or "포지셔닝 매트릭스" in text:
            return load_fixture("strategy.json")
        if "발표전략" in text and "수립" in text:
            return load_fixture("presentation_strategy.json")
        if "TOC" in text or "발표 자료 목차" in text:
            ppt = load_fixture("ppt_slide.json")
            return {"toc": ppt["toc"], "total_slides": ppt["total_slides"]}
        if "Visual Brief" in text or "F-Pattern" in text:
            ppt = load_fixture("ppt_slide.json")
            return {"visual_briefs": ppt["visual_briefs"]}
        if "Storyboard" in text or "슬라이드 본문" in text:
            ppt = load_fixture("ppt_slide.json")
            return {"slides": ppt["slides"], "total_slides": ppt["total_slides"], "eval_coverage": ppt["eval_coverage"]}
        if "4축 평가" in text or "자가진단" in text:
            return load_fixture("self_review_pass.json")
        if "섹션을 작성" in text or "SECTION_PROMPT" in text:
            return load_fixture("proposal_section.json")

        # Path B: 제출서류 계획
        if "제출서류 준비 계획" in text or "제출서류" in text:
            return {
                "documents": [{"doc_id": "D-01", "name": "제안서", "type": "proposal",
                               "required": True, "format": "DOCX", "status": "pending"}],
                "timeline": {"preparation_start": "즉시", "milestones": []},
                "risks": [], "notes": ""
            }

        # Path B: 산출내역서
        if "산출내역서" in text or "cost_sheet" in text:
            return {
                "items": [{"category": "인건비", "amount": 300_000_000}],
                "total": 450_000_000, "notes": ""
            }

        # Path B: 제출 체크리스트
        if "체크리스트" in text:
            return {"checklist": [{"item": "제안서", "ready": True}], "all_ready": True}

        # 6A: 모의 평가
        if "모의 평가" in text or "평가위원" in text:
            return {
                "evaluators": [{"role": "기술 전문가", "total_score": 85, "scores": [],
                                "overall_comment": "양호"}],
                "aggregate": {"average_score": 85, "min_score": 80, "max_score": 90,
                              "win_probability": "보통", "strengths": [], "weaknesses": [],
                              "improvement_suggestions": []},
                "risk_assessment": "수주 가능성 보통"
            }

        # Fallback — 기본 dict 반환
        return {"status": "ok", "content": "test response"}

    return mock_claude_generate


# ── prompt_registry / prompt_tracker Mock ──

async def _mock_get_prompt_for_experiment(prompt_id, proposal_id=None, **kwargs):
    """prompt_registry.get_prompt_for_experiment mock — fallback 프롬프트 반환."""
    return ("", 0, "test-hash")


async def _mock_get_active_prompt(prompt_id, **kwargs):
    return ("", 0, "test-hash")


async def _mock_record_usage(*args, **kwargs):
    pass


# ── PricingEngine Mock ──

def _make_pricing_mock():
    """PricingEngine mock — quick_estimate와 simulate 반환."""
    engine = MagicMock()

    estimate_result = MagicMock()
    estimate_result.estimated_cost = 400_000_000
    estimate_result.labor_mm = 15.0
    estimate_result.cost_breakdown = {"labor": 320_000_000, "overhead": 80_000_000}
    engine.quick_estimate = AsyncMock(return_value=estimate_result)

    sim_result = MagicMock()
    sim_result.recommended_bid = 450_000_000
    sim_result.recommended_ratio = 0.75
    sim_result.scenarios = []
    sim_result.selected_scenario = "balanced"
    sim_result.cost_breakdown = {"labor_cost": 350_000_000}
    sim_result.sensitivity_curve = []
    sim_result.win_probability = 0.6
    sim_result.market_context = {}
    sim_result.data_quality = "hybrid"
    sim_result.model_dump = MagicMock(return_value=load_fixture("bid_plan.json"))
    engine.simulate = AsyncMock(return_value=sim_result)

    return engine


# ── 테스트용 Supabase Mock (기존 conftest 확장) ──

def _make_workflow_supabase_mock():
    """워크플로 실행에 필요한 Supabase mock."""
    from tests.conftest import make_supabase_mock

    mock_client = make_supabase_mock(table_data={
        "capabilities": [],
        "content_library": [],
        "knowledge_base": [],
        "labor_rates": [],
        "market_price_data": [],
        "proposals": [{"id": "test-proposal-001", "status": "initialized"}],
        "feedbacks": [],
        "prompt_registry": [],
        "prompt_experiments": [],
    })
    return mock_client


# ── Fixtures ──

@pytest.fixture
def initial_state():
    """테스트용 최소 ProposalState."""
    return {
        "proposal_id": "test-proposal-001",
        "rfp_raw": """제안요청서
사업명: 클라우드 기반 ERP 시스템 구축
발주기관: ABC 주식회사
예산: 5억원
기간: 6개월
평가항목: 기술 이해도(30), 수행 방안(40), 프로젝트 관리(30)
필수요건: ISO 27001 인증, 5년 이상 ERP 구축 경험""",
        "current_step": "",
        "error": None,
    }


@pytest.fixture
def initial_state_doc_only():
    """서류심사 전용 ProposalState (PPT 스킵)."""
    return {
        "proposal_id": "test-proposal-002",
        "rfp_raw": """제안요청서
사업명: 데이터 분석 플랫폼 구축
발주기관: XYZ 공공기관
예산: 3억원
기간: 4개월
심사방법: 서류심사(document_only)""",
        "current_step": "",
        "error": None,
    }


@pytest.fixture
def workflow_patches():
    """워크플로 실행에 필요한 모든 patch를 적용하는 context manager 반환."""

    def _apply(rfp_fixture=None):
        mock_claude = _make_claude_mock(rfp_fixture)
        mock_supabase = _make_workflow_supabase_mock()
        _make_pricing_mock()

        # 노드 모듈이 'from ... import claude_generate'로 직접 import하므로
        # 각 노드 모듈의 참조도 함께 패치해야 한다.
        claude_patches = [
            patch("app.services.claude_client.claude_generate", side_effect=mock_claude),
            patch("app.graph.nodes.rfp_analyze.claude_generate", side_effect=mock_claude),
            patch("app.graph.nodes.research_gather.claude_generate", side_effect=mock_claude),
            patch("app.graph.nodes.go_no_go.claude_generate", side_effect=mock_claude),
            patch("app.graph.nodes.strategy_generate.claude_generate", side_effect=mock_claude),
            patch("app.graph.nodes.plan_nodes.claude_generate", side_effect=mock_claude),
            patch("app.graph.nodes.proposal_nodes.claude_generate", side_effect=mock_claude),
            patch("app.graph.nodes.ppt_nodes.claude_generate", side_effect=mock_claude),
            patch("app.graph.nodes.submission_nodes.claude_generate", side_effect=mock_claude),
            patch("app.graph.nodes.evaluation_nodes.claude_generate", side_effect=mock_claude),
        ]
        other_patches = [
            patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=mock_supabase)),
            patch("app.services.prompt_registry.get_prompt_for_experiment", side_effect=_mock_get_prompt_for_experiment),
            patch("app.services.prompt_registry.get_active_prompt", side_effect=_mock_get_active_prompt),
            patch("app.services.prompt_tracker.record_usage", side_effect=_mock_record_usage),
        ]
        patches = claude_patches + other_patches
        return patches, mock_claude, mock_supabase

    return _apply


@pytest.fixture
async def workflow_graph():
    """MemorySaver 기반 실제 그래프 반환."""
    from langgraph.checkpoint.memory import MemorySaver
    from app.graph.graph import build_graph

    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)
    return graph
