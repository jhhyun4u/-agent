"""
하네스 엔지니어링 통합 테스트

테스트 범위:
1. Generator: 3변형 병렬 생성
2. Evaluator: 품질 점수 부여
3. Selector: 최고 점수 선택
4. Feedback Loop: 프롬프트 개선
"""

import pytest

from app.graph.nodes.harness_feedback_loop import (
    HarnessFeedbackAnalyzer,
    HarnessFeedbackLoop,
    HarnessPromptRefiner,
)
from app.graph.nodes.harness_proposal_node import HarnessProposalGenerator
from app.services.claude_client import claude_generate_multiple_variants
from app.services.harness_evaluator import SectionEvaluator, EvaluationScore


class TestHarnessGenerator:
    """Generator 테스트: 3변형 병렬 생성"""

    @pytest.mark.asyncio
    async def test_claude_generate_multiple_variants(self):
        """3개 변형 병렬 생성"""
        prompt = """
대한민국 교육부 디지털 기반 교육 현대화 용역과제 제안서의 Executive Summary를 작성하세요.

핵심 제안:
- AI 기반 맞춤형 학습 시스템
- 5년 구현 계획
- 3,000개 학교 참여

변형 지침:
{variant_hint}

Executive Summary (200-250 단어):
"""

        results = await claude_generate_multiple_variants(
            base_prompt=prompt,
            section_type="executive_summary",
            step_name="test_generator",
        )

        # 검증
        assert len(results) == 3
        assert results[0]["variant"] == "conservative"
        assert results[1]["variant"] == "balanced"
        assert results[2]["variant"] == "creative"

        for i, result in enumerate(results):
            assert "content" in result
            assert result["temperature"] in [0.1, 0.3, 0.7]
            assert len(result["content"]) > 0
            print(f"\n변형 {i+1} ({result['variant']}): {len(result['content'])} 문자")

    @pytest.mark.asyncio
    async def test_generator_with_error_handling(self):
        """오류 처리 테스트"""
        invalid_prompt = ""  # 빈 프롬프트

        results = await claude_generate_multiple_variants(
            base_prompt=invalid_prompt,
            section_type="test",
            step_name="test_error",
        )

        # 오류 상황도 처리해야 함
        assert len(results) == 3
        # 결과에 error 필드가 있을 수 있음
        error_count = sum(1 for r in results if "error" in r)
        assert error_count >= 0  # 최대 3개 모두 실패 가능


class TestHarnessEvaluator:
    """Evaluator 테스트: 품질 평가"""

    @pytest.mark.asyncio
    async def test_section_evaluator_initialization(self):
        """평가기 초기화"""
        evaluator = SectionEvaluator()
        assert evaluator is not None
        assert hasattr(evaluator, "REQUIRED_ELEMENTS")
        assert "executive_summary" in evaluator.REQUIRED_ELEMENTS

    @pytest.mark.asyncio
    async def test_evaluation_score_calculation(self):
        """평가 점수 계산"""
        test_content = """
우리 회사는 10년 이상의 제안서 작성 경험을 보유하고 있습니다.

주요 성과:
- 500+ 프로젝트 수행
- 80% 이상의 수주율 달성
- 고객 만족도 95% 이상

차별화 요소:
1. AI 기반 자동화 시스템
2. 전문 컨설턴트 팀
3. 품질 보증 프로세스
"""

        evaluator = SectionEvaluator()
        score = await evaluator.evaluate(
            section_content=test_content,
            section_type="executive_summary",
            reference_materials=["회사 소개", "성과"],
        )

        assert isinstance(score, EvaluationScore)
        assert 0 <= score.overall <= 1
        assert 0 <= score.hallucination <= 1
        assert 0 <= score.persuasiveness <= 1
        assert 0 <= score.completeness <= 1
        assert 0 <= score.clarity <= 1
        assert score.feedback != ""

        print("\n평가 결과:")
        print(f"  종합: {score.overall:.1%}")
        print(f"  신뢰성: {score.hallucination:.1%}")
        print(f"  설득력: {score.persuasiveness:.1%}")
        print(f"  완전성: {score.completeness:.1%}")
        print(f"  명확성: {score.clarity:.1%}")
        print(f"  피드백: {score.feedback}")
        print(f"  통과: {'✅' if score.passed else '❌'}")

    @pytest.mark.asyncio
    async def test_evaluation_with_empty_content(self):
        """빈 콘텐츠 평가"""
        evaluator = SectionEvaluator()
        score = await evaluator.evaluate(
            section_content="",
            section_type="executive_summary",
        )

        assert score.overall < 0.5  # 낮은 점수 예상


class TestHarnessProposalGenerator:
    """HarnessProposalGenerator 통합 테스트"""

    @pytest.mark.asyncio
    async def test_generate_section_full_cycle(self):
        """완전한 생성 사이클: 생성 → 평가 → 선택"""
        generator = HarnessProposalGenerator()

        prompt_template = """
제안서 Executive Summary를 다음 지침으로 작성하세요.

공고: 정부 디지털 혁신 과제
포지셔닝: 기술 리더 / 비용 효율

지침:
{variant_hint}

Executive Summary (200 단어):
"""

        result = await generator.generate_section(
            prompt_template=prompt_template,
            section_type="executive_summary",
            state=None,
            reference_materials=["디지털 혁신", "기술"],
        )

        # 검증
        assert result["section_type"] == "executive_summary"
        assert result["selected_variant"] in [
            "conservative",
            "balanced",
            "creative",
        ]
        assert result["score"] >= 0
        assert result["content"] != ""
        assert "conservative" in result["scores"]
        assert "balanced" in result["scores"]
        assert "creative" in result["scores"]

        print("\n생성 결과:")
        print(f"  선택: {result['selected_variant']}")
        print(f"  점수: {result['score']:.1%}")
        print(f"  Conservative: {result['scores']['conservative']:.1%}")
        print(f"  Balanced: {result['scores']['balanced']:.1%}")
        print(f"  Creative: {result['scores']['creative']:.1%}")


class TestHarnessFeedbackLoop:
    """피드백 루프 테스트"""

    @pytest.mark.asyncio
    async def test_feedback_analysis(self):
        """평가 결과 분석"""
        analyzer = HarnessFeedbackAnalyzer()

        evaluation_result = {
            "overall": 0.60,
            "hallucination": 0.5,
            "persuasiveness": 0.7,
            "completeness": 0.5,
            "clarity": 0.7,
            "feedback": "신뢰성 부족 - 출처/근거 명시",
        }

        analysis = await analyzer.analyze_evaluation(
            evaluation_detail=evaluation_result,
            section_type="executive_summary",
            variant_name="balanced",
        )

        assert analysis is not None
        assert len(analysis.weak_areas) > 0
        assert analysis.improvement_priority in ["critical", "high", "medium", "low"]
        assert analysis.suggested_changes != ""

        print("\n분석 결과:")
        print(f"  약점: {analysis.weak_areas}")
        print(f"  우선순위: {analysis.improvement_priority}")
        print(f"  개선안: {analysis.suggested_changes[:100]}...")

    @pytest.mark.asyncio
    async def test_prompt_refiner(self):
        """프롬프트 개선"""
        refiner = HarnessPromptRefiner()
        analyzer = HarnessFeedbackAnalyzer()

        original_prompt = "Executive Summary를 작성하세요."

        evaluation_result = {
            "overall": 0.5,
            "hallucination": 0.4,
            "persuasiveness": 0.6,
            "completeness": 0.5,
            "clarity": 0.5,
        }

        analysis = await analyzer.analyze_evaluation(
            evaluation_detail=evaluation_result,
            section_type="executive_summary",
            variant_name="balanced",
        )

        improved = await refiner.refine_prompt(
            original_prompt=original_prompt,
            analysis=analysis,
            section_type="executive_summary",
        )

        assert improved.original == original_prompt
        assert improved.improved != ""
        assert improved.reasoning != ""
        assert len(improved.focus_areas) > 0

        print("\n프롬프트 개선:")
        print(f"  원본 길이: {len(original_prompt)}")
        print(f"  개선 길이: {len(improved.improved)}")
        print(f"  이유: {improved.reasoning}")

    @pytest.mark.asyncio
    async def test_feedback_loop_iteration(self):
        """완전한 피드백 루프 반복"""
        loop = HarnessFeedbackLoop()

        prompt = "Executive Summary를 작성하세요."
        evaluation_results = {
            "conservative": {
                "overall": 0.65,
                "hallucination": 0.6,
                "persuasiveness": 0.7,
                "completeness": 0.65,
                "clarity": 0.75,
                "feedback": "양호",
            },
            "balanced": {
                "overall": 0.70,
                "hallucination": 0.65,
                "persuasiveness": 0.75,
                "completeness": 0.70,
                "clarity": 0.80,
                "feedback": "양호",
            },
            "creative": {
                "overall": 0.60,
                "hallucination": 0.5,
                "persuasiveness": 0.65,
                "completeness": 0.60,
                "clarity": 0.70,
                "feedback": "신뢰성 부족",
            },
        }

        result = await loop.iterate(
            prompt=prompt,
            evaluation_results=evaluation_results,
            section_type="executive_summary",
            current_iteration=1,
            max_iterations=3,
        )

        assert result["iteration"] == 1
        assert result["best_variant"] == "balanced"
        assert result["best_score"] == 0.70
        assert "should_continue" in result
        assert "analysis" in result

        summary = loop.get_summary()
        assert summary["iterations"] == 1
        assert summary["initial_score"] == 0.70

        print("\n루프 반복 결과:")
        print(f"  반복: {result['iteration']}")
        print(f"  최고: {result['best_variant']} ({result['best_score']:.1%})")
        print(f"  약점: {result['weak_areas']}")
        print(f"  계속: {result['should_continue']}")


class TestHarnessIntegration:
    """통합 테스트: 전체 하네스 파이프라인"""

    @pytest.mark.asyncio
    async def test_full_harness_pipeline(self):
        """완전한 하네스 파이프라인"""
        generator = HarnessProposalGenerator()

        prompt = """
정부 용역 제안서의 Executive Summary를 작성하세요.

지침:
{variant_hint}

Executive Summary:
"""

        # 생성
        result = await generator.generate_section(
            prompt_template=prompt,
            section_type="executive_summary",
            state=None,
        )

        assert result["selected_variant"] is not None
        assert result["score"] > 0
        assert len(result["content"]) > 0

        # 피드백 루프
        loop = HarnessFeedbackLoop()

        feedback_result = await loop.iterate(
            prompt=prompt,
            evaluation_results=result["details"],
            section_type="executive_summary",
            current_iteration=1,
            max_iterations=1,
        )

        assert feedback_result is not None
        assert "analysis" in feedback_result

        print("\n통합 테스트 완료:")
        print(f"  초기 선택: {result['selected_variant']} ({result['score']:.1%})")
        print(f"  피드백 분석: {feedback_result['best_variant']} ({feedback_result['best_score']:.1%})")


# 벤치마크 테스트
class TestHarnessBenchmark:
    """성능 벤치마크"""

    @pytest.mark.asyncio
    async def test_variant_generation_performance(self):
        """변형 생성 성능"""
        import time

        prompt = "Executive Summary를 작성하세요."

        start = time.time()
        results = await claude_generate_multiple_variants(
            base_prompt=prompt,
            section_type="executive_summary",
        )
        elapsed = time.time() - start

        print(f"\n벤치마크: 3변형 생성 {elapsed:.2f}초")
        assert elapsed < 60  # 1분 이내
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_evaluation_performance(self):
        """평가 성능"""
        import time

        evaluator = SectionEvaluator()
        content = "Executive Summary를 작성하세요." * 10

        start = time.time()
        score = await evaluator.evaluate(
            section_content=content,
            section_type="executive_summary",
        )
        elapsed = time.time() - start

        print(f"\n벤치마크: 1개 평가 {elapsed:.2f}초")
        assert elapsed < 20  # 20초 이내
        assert score.overall > 0
