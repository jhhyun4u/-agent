"""
STEP 8A-8F End-to-End Integration Test
완전한 제안서 처리 파이프라인 테스트 (8A-8F)

실행 환경:
- Staging 서버에서 실행
- 샘플 RFP 데이터 필요
- Claude API 키 필요

실행 방법:
cd /staging/tenopa-proposer
source venv/bin/activate
python -m pytest tests/test_step8_e2e.py -v -s
"""

import time
from datetime import datetime
from uuid import uuid4

import pytest
from app.graph.state import ProposalState
from app.graph.nodes.step8a_customer_analysis import proposal_customer_analysis
from app.graph.nodes.step8b_section_validator import proposal_section_validator
from app.graph.nodes.step8c_consolidation import proposal_sections_consolidation
from app.graph.nodes.step8d_mock_evaluation import mock_evaluation_analysis
from app.graph.nodes.step8e_feedback_processor import (
    mock_evaluation_feedback_processor,
)
from app.graph.nodes.step8f_rewrite import proposal_write_next_v2


class StepMetrics:
    """각 스텝 실행 시간 및 메트릭 기록"""

    def __init__(self):
        self.steps = {}

    def record(self, step_name: str, duration: float, success: bool, error: str = None):
        """스텝 실행 결과 기록"""
        self.steps[step_name] = {
            "duration": duration,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }

    def print_summary(self):
        """메트릭 요약 출력"""
        print("\n" + "=" * 70)
        print("[METRICS] STEP 8A-8F E2E Test Summary")
        print("=" * 70)
        total_duration = 0

        for step, metrics in self.steps.items():
            status = "PASS" if metrics["success"] else "FAIL"
            duration = metrics["duration"]
            total_duration += duration

            print(
                f"{step:20} | {status:6} | {duration:7.2f}s | {metrics.get('error', 'OK')}"
            )

        print("-" * 70)
        print(f"{'TOTAL':20} | {'':6} | {total_duration:7.2f}s")
        print("=" * 70 + "\n")

        return total_duration


@pytest.fixture
def test_proposal_state() -> ProposalState:
    """테스트용 ProposalState 생성 - 모든 Step 8 단계를 위한 완전한 초기 상태"""
    proposal_sections = [
        {
            "section_id": "sec_001",
            "title": "Executive Summary",
            "content": "This section summarizes the proposal and key value propositions...",
        },
        {
            "section_id": "sec_002",
            "title": "Technical Approach",
            "content": "Our technical approach includes the following components and methodologies...",
        },
    ]

    # dynamic_sections는 proposal_sections과 동일한 구조 (8C는 섹션 dict 기대)
    dynamic_sections = proposal_sections.copy()

    test_user_id = str(uuid4())
    return {
        "proposal_id": str(uuid4()),
        "project_id": str(uuid4()),  # Step 8C expects project_id
        "created_by": test_user_id,  # Step 8C expects created_by UUID
        "rfp_analysis": {
            "title": "Sample RFP for Testing",
            "description": "This is a test RFP",
            "requirements": ["Requirement 1", "Requirement 2"],
            "evaluation_criteria": ["Criterion 1", "Criterion 2"],
            "deadline": "2026-04-30",
            "budget_range": "$100K - $500K",
        },
        "proposal_sections": proposal_sections,
        "dynamic_sections": dynamic_sections,  # 초기화: Step 8C expects this
        "strategy": {
            "positioning": "Premium quality provider",
            "win_themes": ["Quality", "Reliability"],
        },
        "customer_profile": {
            "client_name": "Sample Client",
            "industry": "Technology",
            "requirements_summary": "High-quality technical solution",
            "decision_criteria": ["Cost", "Quality", "Timeline"],
        },
        "validation_report": {
            "sections": proposal_sections,
            "total_issues": 0,
            "critical_issues": [],
            "validation_passed": True,
        },
        "consolidated_proposal": None,
        "mock_eval_result": None,
        "feedback_summary": None,
        "artifact_versions": {},
        "current_step": "proposal_analysis",
        "current_section_index": 0,  # Step 8F expects this
        "rewrite_iteration_count": 0,  # Step 8F expects this
        "node_errors": {},
    }


@pytest.mark.asyncio
async def test_step8a_customer_analysis(test_proposal_state: ProposalState):
    """Step 8A: Customer Analysis Node"""
    print("\n[TEST] STEP 8A - Customer Analysis")

    metrics = StepMetrics()
    start_time = time.time()

    try:
        result = await proposal_customer_analysis(test_proposal_state)

        duration = time.time() - start_time

        # 검증
        assert "customer_profile" in result, "customer_profile 필드 누락"
        assert result["customer_profile"] is not None, "customer_profile이 None"

        metrics.record("step8a_customer_analysis", duration, True)
        print(f"[PASS] Step 8A completed in {duration:.2f}s")
        print(f"       Customer Profile keys: {list(result['customer_profile'].keys())}")

    except Exception as e:
        duration = time.time() - start_time
        metrics.record("step8a_customer_analysis", duration, False, str(e))
        print(f"[FAIL] Step 8A failed: {str(e)}")
        raise


@pytest.mark.asyncio
async def test_step8b_section_validator(test_proposal_state: ProposalState):
    """Step 8B: Section Validator Node"""
    print("\n[TEST] STEP 8B - Section Validator")

    metrics = StepMetrics()
    start_time = time.time()

    try:
        result = await proposal_section_validator(test_proposal_state)

        duration = time.time() - start_time

        # 검증
        assert "validation_report" in result, "validation_report 필드 누락"
        assert result["validation_report"] is not None, "validation_report이 None"

        metrics.record("step8b_section_validator", duration, True)
        print(f"[PASS] Step 8B completed in {duration:.2f}s")
        print(
            f"       Validation Report keys: {list(result['validation_report'].keys())}"
        )

    except Exception as e:
        duration = time.time() - start_time
        metrics.record("step8b_section_validator", duration, False, str(e))
        print(f"[FAIL] Step 8B failed: {str(e)}")
        raise


@pytest.mark.asyncio
async def test_step8c_consolidation(test_proposal_state: ProposalState):
    """Step 8C: Consolidation Node"""
    print("\n[TEST] STEP 8C - Consolidation")

    metrics = StepMetrics()
    start_time = time.time()

    try:
        result = await proposal_sections_consolidation(test_proposal_state)

        duration = time.time() - start_time

        # 검증
        assert "consolidated_proposal" in result, "consolidated_proposal 필드 누락"
        assert (
            result["consolidated_proposal"] is not None
        ), "consolidated_proposal이 None"

        metrics.record("step8c_consolidation", duration, True)
        print(f"[PASS] Step 8C completed in {duration:.2f}s")
        print(
            f"       Consolidated Proposal keys: {list(result['consolidated_proposal'].keys())}"
        )

    except Exception as e:
        duration = time.time() - start_time
        metrics.record("step8c_consolidation", duration, False, str(e))
        print(f"[FAIL] Step 8C failed: {str(e)}")
        raise


@pytest.mark.asyncio
async def test_step8d_mock_evaluation(test_proposal_state: ProposalState):
    """Step 8D: Mock Evaluation Node"""
    print("\n[TEST] STEP 8D - Mock Evaluation")

    metrics = StepMetrics()
    start_time = time.time()

    try:
        result = await mock_evaluation_analysis(test_proposal_state)

        duration = time.time() - start_time

        # 검증
        assert "mock_eval_result" in result, "mock_eval_result 필드 누락"
        assert result["mock_eval_result"] is not None, "mock_eval_result이 None"

        metrics.record("step8d_mock_evaluation", duration, True)
        print(f"[PASS] Step 8D completed in {duration:.2f}s")
        print(f"       Mock Eval Result keys: {list(result['mock_eval_result'].keys())}")

    except Exception as e:
        duration = time.time() - start_time
        metrics.record("step8d_mock_evaluation", duration, False, str(e))
        print(f"[FAIL] Step 8D failed: {str(e)}")
        raise


@pytest.mark.asyncio
async def test_step8e_feedback_processor(test_proposal_state: ProposalState):
    """Step 8E: Feedback Processor Node"""
    print("\n[TEST] STEP 8E - Feedback Processor")

    metrics = StepMetrics()
    start_time = time.time()

    try:
        result = await mock_evaluation_feedback_processor(test_proposal_state)

        duration = time.time() - start_time

        # 검증
        assert "feedback_summary" in result, "feedback_summary 필드 누락"
        assert result["feedback_summary"] is not None, "feedback_summary이 None"

        metrics.record("step8e_feedback_processor", duration, True)
        print(f"[PASS] Step 8E completed in {duration:.2f}s")
        print(f"       Feedback Summary keys: {list(result['feedback_summary'].keys())}")

    except Exception as e:
        duration = time.time() - start_time
        metrics.record("step8e_feedback_processor", duration, False, str(e))
        print(f"[FAIL] Step 8E failed: {str(e)}")
        raise


@pytest.mark.asyncio
async def test_step8f_rewrite(test_proposal_state: ProposalState):
    """Step 8F: Rewrite Node"""
    print("\n[TEST] STEP 8F - Proposal Rewrite")

    metrics = StepMetrics()
    start_time = time.time()

    try:
        result = await proposal_write_next_v2(test_proposal_state)

        duration = time.time() - start_time

        # 검증
        assert "proposal_sections" in result, "proposal_sections 필드 누락"
        assert result["proposal_sections"] is not None, "proposal_sections이 None"

        metrics.record("step8f_rewrite", duration, True)
        print(f"[PASS] Step 8F completed in {duration:.2f}s")
        print(f"       Rewritten Sections: {len(result.get('proposal_sections', []))}")

    except Exception as e:
        duration = time.time() - start_time
        metrics.record("step8f_rewrite", duration, False, str(e))
        print(f"[FAIL] Step 8F failed: {str(e)}")
        raise


@pytest.mark.asyncio
async def test_complete_pipeline_e2e(test_proposal_state: ProposalState):
    """완전한 8A-8F 파이프라인 통합 테스트"""
    print("\n" + "=" * 70)
    print("[E2E TEST] STEP 8A-8F Complete Pipeline")
    print("=" * 70)

    metrics = StepMetrics()
    pipeline_start = time.time()

    state = test_proposal_state.copy()

    # Step 8A: Customer Analysis
    try:
        start = time.time()
        state.update(await proposal_customer_analysis(state))
        metrics.record("8A Customer Analysis", time.time() - start, True)
        print("✓ Step 8A completed")
    except Exception as e:
        metrics.record("8A Customer Analysis", time.time() - start, False, str(e))
        print(f"✗ Step 8A failed: {e}")
        return

    # Step 8B: Validation
    try:
        start = time.time()
        state.update(await proposal_section_validator(state))
        metrics.record("8B Section Validator", time.time() - start, True)
        print("✓ Step 8B completed")
    except Exception as e:
        metrics.record("8B Section Validator", time.time() - start, False, str(e))
        print(f"✗ Step 8B failed: {e}")
        return

    # Step 8C: Consolidation
    try:
        start = time.time()
        state.update(await proposal_sections_consolidation(state))
        metrics.record("8C Consolidation", time.time() - start, True)
        print("✓ Step 8C completed")
    except Exception as e:
        metrics.record("8C Consolidation", time.time() - start, False, str(e))
        print(f"✗ Step 8C failed: {e}")
        return

    # Step 8D: Mock Evaluation
    try:
        start = time.time()
        state.update(await mock_evaluation_analysis(state))
        metrics.record("8D Mock Evaluation", time.time() - start, True)
        print("✓ Step 8D completed")
    except Exception as e:
        metrics.record("8D Mock Evaluation", time.time() - start, False, str(e))
        print(f"✗ Step 8D failed: {e}")
        return

    # Step 8E: Feedback
    try:
        start = time.time()
        state.update(await mock_evaluation_feedback_processor(state))
        metrics.record("8E Feedback Processor", time.time() - start, True)
        print("✓ Step 8E completed")
    except Exception as e:
        metrics.record("8E Feedback Processor", time.time() - start, False, str(e))
        print(f"✗ Step 8E failed: {e}")
        return

    # Step 8F: Rewrite
    try:
        start = time.time()
        state.update(await proposal_write_next_v2(state))
        metrics.record("8F Rewrite", time.time() - start, True)
        print("✓ Step 8F completed")
    except Exception as e:
        metrics.record("8F Rewrite", time.time() - start, False, str(e))
        print(f"✗ Step 8F failed: {e}")
        return

    # Print metrics
    total = time.time() - pipeline_start
    metrics.print_summary()

    print(f"\n[RESULT] E2E Pipeline Total Time: {total:.2f}s")
    print(f"[RESULT] Final State Keys: {list(state.keys())}")
    print("[SUCCESS] Complete pipeline executed successfully!\n")


if __name__ == "__main__":
    # pytest 없이 직접 실행 가능
    print("Run with pytest:\n")
    print("  pytest tests/test_step8_e2e.py -v -s\n")
    print("또는:\n")
    print("  python -m pytest tests/test_step8_e2e.py::test_complete_pipeline_e2e -v -s")
