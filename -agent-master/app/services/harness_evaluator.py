"""
하네스 Evaluator - 섹션 품질 자동 평가

평가 항목:
1. 신뢰성 (Hallucination 체크) - 35%
2. 설득력 (논리성 + 구조) - 25%
3. 완전성 (필요 요소 포함) - 25%
4. 명확성 (이해도) - 15%

사용 사례:
- 제안서 섹션 자동 검증
- 다양한 프롬프트 버전 비교
- 품질 기준 만족 여부 판단
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import asyncio
import logging

from app.services.claude_client import claude_generate

logger = logging.getLogger(__name__)


@dataclass
class EvaluationScore:
    """평가 결과"""
    overall: float           # 0~1 종합 점수
    hallucination: float     # 0~1 사실성
    persuasiveness: float    # 0~1 설득력
    completeness: float      # 0~1 완전성
    clarity: float          # 0~1 명확성
    threshold: float = 0.75  # 통과 기준
    feedback: str = ""       # 개선 피드백
    passed: bool = field(init=False)

    def __post_init__(self):
        self.passed = self.overall >= self.threshold


class SectionEvaluator:
    """섹션 작성 품질 평가기"""

    # 섹션별 필수 요소
    REQUIRED_ELEMENTS = {
        "executive_summary": [
            "핵심 가치제안",
            "차별화 요소",
            "기대 효과",
        ],
        "technical_approach": [
            "기술 개요",
            "구현 방식",
            "위험 관리",
        ],
        "team": [
            "주요 인력",
            "경험/실적",
            "조직도",
        ],
        "project_plan": [
            "일정표",
            "마일스톤",
            "리스크",
        ],
        "pricing": [
            "가격 책정 근거",
            "비용 구조",
            "결제 조건",
        ],
    }

    def __init__(self):
        pass  # 자체 검증 로직 사용

    async def evaluate(
        self,
        section_content: str,
        section_type: str,
        reference_materials: Optional[List[str]] = None
    ) -> EvaluationScore:
        """
        섹션 콘텐츠 평가

        Args:
            section_content: 평가할 섹션 텍스트
            section_type: 섹션 타입
            reference_materials: 검증용 참고 자료

        Returns:
            EvaluationScore 객체
        """

        logger.info(f"📊 섹션 '{section_type}' 평가 시작...")

        # 병렬 평가 실행
        try:
            scores = await asyncio.gather(
                self._check_hallucination(section_content, reference_materials),
                self._check_persuasiveness(section_content, section_type),
                self._check_completeness(section_content, section_type),
                self._check_clarity(section_content),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"평가 중 오류: {e}")
            # 오류 발생 시 기본값 반환
            return EvaluationScore(
                overall=0.5,
                hallucination=0.5,
                persuasiveness=0.5,
                completeness=0.5,
                clarity=0.5,
                feedback="평가 중 오류 발생"
            )

        # 결과 처리 (예외 처리)
        hallucination_score = scores[0] if not isinstance(scores[0], Exception) else 0.5
        persuasiveness_score = scores[1] if not isinstance(scores[1], Exception) else 0.5
        completeness_score = scores[2] if not isinstance(scores[2], Exception) else 0.5
        clarity_score = scores[3] if not isinstance(scores[3], Exception) else 0.5

        # 가중치 기반 종합 점수 계산
        weights = {
            "hallucination": 0.35,      # 사실성 우선
            "persuasiveness": 0.25,
            "completeness": 0.25,
            "clarity": 0.15,
        }

        overall = (
            hallucination_score * weights["hallucination"] +
            persuasiveness_score * weights["persuasiveness"] +
            completeness_score * weights["completeness"] +
            clarity_score * weights["clarity"]
        )

        # 피드백 생성
        feedback = self._generate_feedback({
            "hallucination": hallucination_score,
            "persuasiveness": persuasiveness_score,
            "completeness": completeness_score,
            "clarity": clarity_score,
        })

        result = EvaluationScore(
            overall=overall,
            hallucination=hallucination_score,
            persuasiveness=persuasiveness_score,
            completeness=completeness_score,
            clarity=clarity_score,
            feedback=feedback,
        )

        status = "✅ 통과" if result.passed else "❌ 미흡"
        logger.info(
            f"평가 완료 {status}: "
            f"종합 {result.overall:.1%} | "
            f"신뢰성 {result.hallucination:.1%} | "
            f"설득력 {result.persuasiveness:.1%}"
        )

        return result

    async def _check_hallucination(
        self,
        content: str,
        reference_materials: Optional[List[str]] = None
    ) -> float:
        """
        신뢰성 체크 (0~1)

        참고 자료와의 연관성 기반 신뢰도 평가
        """
        try:
            # 참고 자료가 있으면 연관성 체크
            if reference_materials:
                match_count = 0
                for material in reference_materials:
                    if material and material.lower() in content.lower():
                        match_count += 1

                # 참고 자료와의 일치도 기반 점수
                confidence = match_count / len(reference_materials) if reference_materials else 0.5
                return min(confidence + 0.3, 1.0)  # 기본값 0.3 + 매칭도
            else:
                # 참고 자료 없을 때: 콘텐츠 품질 기반 휴리스틱
                # - 문장 수, 단락 수, 구체적 수치 등
                sentences = [s.strip() for s in content.split('.') if s.strip()]
                has_numbers = any(char.isdigit() for char in content)
                has_structure = '\n' in content or '-' in content

                score = 0.6  # 기본값
                if len(sentences) > 3:
                    score += 0.1
                if has_numbers:
                    score += 0.15
                if has_structure:
                    score += 0.15

                return min(score, 1.0)
        except Exception as e:
            logger.warning(f"Hallucination check error: {e}")
            return 0.65  # 기본값

    async def _check_persuasiveness(self, content: str, section_type: str) -> float:
        """
        설득력 체크 (0~1)

        논리성, 구조, 근거 제시 등 평가
        """
        prompt = f"""
당신은 제안서 평가 전문가입니다. 다음 섹션의 설득력을 평가하세요.

평가 기준:
- 명확한 주장과 근거
- 논리적 구조
- 수치/사례를 통한 입증
- 대상 고객의 니즈 반영

섹션 타입: {section_type}

[섹션 내용]
{content}

0~10점 중 점수를 숫자로만 답변하세요 (예: 8):
"""

        try:
            response = await claude_generate(prompt)
            # 첫 번째 숫자만 추출
            score_str = ''.join(c for c in response.strip() if c.isdigit())
            if score_str:
                score = int(score_str[0]) / 10
                return min(max(score, 0), 1.0)
            return 0.5
        except Exception as e:
            logger.warning(f"Persuasiveness check error: {e}")
            return 0.5

    async def _check_completeness(self, content: str, section_type: str) -> float:
        """
        완전성 체크 (0~1)

        필수 요소 포함 여부
        """
        elements = self.REQUIRED_ELEMENTS.get(section_type, [])

        if not elements:
            logger.warning(f"Unknown section type: {section_type}")
            return 0.8  # 알 수 없는 타입은 기본값

        # 간단한 키워드 매칭
        found = 0
        for elem in elements:
            if elem in content or elem.replace(" ", "") in content.replace(" ", ""):
                found += 1

        completeness = found / len(elements)
        return completeness

    async def _check_clarity(self, content: str) -> float:
        """
        명확성 체크 (0~1)

        문장 길이, 문법, 가독성 등
        """
        # 간단한 휴리스틱
        sentences = [s.strip() for s in content.split('.') if s.strip()]

        if not sentences:
            return 0.5

        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)

        # 이상적: 15~25 단어/문장
        if 15 <= avg_length <= 25:
            clarity = 0.9
        elif 10 <= avg_length <= 30:
            clarity = 0.7
        elif 5 <= avg_length <= 40:
            clarity = 0.5
        else:
            clarity = 0.3

        # 불릿 포인트 사용 여부 (가독성 개선)
        if '-' in content or '•' in content or '·' in content:
            clarity = min(clarity + 0.1, 1.0)

        # 문단 분리 여부
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) > 1:
            clarity = min(clarity + 0.05, 1.0)

        return clarity

    def _generate_feedback(self, scores: Dict[str, float]) -> str:
        """평가 결과를 바탕으로 개선 피드백 생성"""
        feedback_items = []

        # 각 영역별 피드백
        if scores["hallucination"] < 0.7:
            feedback_items.append("신뢰성 부족 - 출처/근거 명시")

        if scores["persuasiveness"] < 0.7:
            feedback_items.append("설득력 부족 - 논리 구조 강화")

        if scores["completeness"] < 0.7:
            feedback_items.append("내용 부족 - 필수 요소 추가")

        if scores["clarity"] < 0.7:
            feedback_items.append("명확성 낮음 - 문장 단순화")

        if not feedback_items:
            return "✅ 양호"

        return " | ".join(feedback_items)


# 테스트용 함수
async def test_evaluator():
    """Evaluator 테스트"""
    evaluator = SectionEvaluator()

    test_content = """
    우리 회사는 10년 이상의 제안서 작성 경험을 보유하고 있습니다.

    주요 성과:
    - 500+ 프로젝트 수행
    - 80% 이상의 수주율 달성
    - 고객 만족도 95% 이상

    우리의 차별화 요소:
    1. AI 기반 자동화 시스템
    2. 전문 컨설턴트 팀
    3. 품질 보증 프로세스
    """

    score = await evaluator.evaluate(
        section_content=test_content,
        section_type="executive_summary",
        reference_materials=["회사 소개", "성과"],
    )

    print(f"\n테스트 결과:")
    print(f"종합: {score.overall:.1%}")
    print(f"신뢰성: {score.hallucination:.1%}")
    print(f"설득력: {score.persuasiveness:.1%}")
    print(f"완전성: {score.completeness:.1%}")
    print(f"명확성: {score.clarity:.1%}")
    print(f"통과: {'✅' if score.passed else '❌'}")
    print(f"피드백: {score.feedback}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_evaluator())
