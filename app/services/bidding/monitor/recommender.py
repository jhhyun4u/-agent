"""
입찰 AI 분석 서비스 — TENOPA 전용

3단계 파이프라인:
  Stage 0: 자격 판정 (pass / fail / ambiguous) — 배치 20건
  Stage 1: 전처리 (공고문 → BidSummary 핵심 추출) — 건별
  Stage 2: TENOPA 리뷰어 (수주 심의 0~100점 평가) — 배치 10건

Stage 1은 content_text가 있는 공고만 실행.
Stage 2는 전처리 결과가 있으면 요약본 기반, 없으면 원문 기반으로 평가.
"""

__all__ = ["_score_to_grade", "BidRecommender"]

import json
import logging
from datetime import datetime, timezone

from anthropic import AsyncAnthropic

from app.config import settings
from app.models.bid_schemas import (
    BidAnnouncement,
    BidRecommendation,
    BidSummary,
    QualificationResult,
    ReasonAnalysis,
    RecommendationReason,
    RiskFactor,
    TeamBidProfile,
    TenopaBidReview,
)
from app.prompts.bid_review import (
    PREPROCESSOR_SYSTEM,
    PREPROCESSOR_USER,
    REVIEWER_SYSTEM,
    REVIEWER_USER_BATCH,
    VERDICT_TO_ACTION,
    VERDICT_TO_PROBABILITY,
)
from app.services.bidding.monitor.preprocessor import BidPreprocessor

logger = logging.getLogger(__name__)

_MATCH_GRADE_TABLE = [(90, "S"), (80, "A"), (70, "B"), (60, "C"), (0, "D")]


def _score_to_grade(score: int) -> str:
    for threshold, grade in _MATCH_GRADE_TABLE:
        if score >= threshold:
            return grade
    return "D"


class BidRecommender:
    """TENOPA 전용 Claude 기반 3단계 입찰 분석 엔진"""

    QUAL_BATCH_SIZE = 20
    REVIEW_BATCH_SIZE = 10
    CLAUDE_TIMEOUT = 30.0

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-5-20250929"
        self.preprocessor = BidPreprocessor()

    # ── 공개 API ────────────────────────────────────────────

    async def analyze_bids(
        self,
        team_profile: TeamBidProfile,
        bids: list[BidAnnouncement],
        top_n: int = 20,
    ) -> tuple[list[BidRecommendation], list[QualificationResult]]:
        """
        3단계 통합 실행.

        Returns:
            (recommendations, all_qual_results)
            - recommendations: match_score 내림차순, pass/ambiguous만 포함
            - all_qual_results: fail 포함 전체 자격 판정 결과
        """
        if not bids:
            return [], []

        # qualification_available=False인 공고는 자동 ambiguous 처리
        auto_ambiguous = [b for b in bids if not b.qualification_available]
        to_check = [b for b in bids if b.qualification_available]

        qual_results: list[QualificationResult] = [
            QualificationResult(
                bid_no=b.bid_no,
                qualification_status="ambiguous",
                qualification_notes="공고 원문 직접 확인 필요 (자격요건 텍스트 미제공)",
            )
            for b in auto_ambiguous
        ]

        # Stage 0: 자격 판정
        if to_check:
            checked = await self.check_qualifications(team_profile, to_check)
            qual_results.extend(checked)

        qual_map = {r.bid_no: r for r in qual_results}

        # Stage 1+2: pass + ambiguous만 전처리 + 리뷰
        eligible = [
            b for b in bids
            if qual_map.get(b.bid_no) and qual_map[b.bid_no].qualification_status != "fail"
        ][:top_n]

        recommendations: list[BidRecommendation] = []
        if eligible:
            recommendations = await self.score_bids(team_profile, eligible)

        # match_score 내림차순 정렬
        recommendations.sort(key=lambda r: r.match_score, reverse=True)
        return recommendations, qual_results

    async def check_qualifications(
        self,
        team_profile: TeamBidProfile,
        bids: list[BidAnnouncement],
    ) -> list[QualificationResult]:
        """Stage 0: 배치 자격 판정 (QUAL_BATCH_SIZE건/호출)"""
        results: list[QualificationResult] = []

        for i in range(0, len(bids), self.QUAL_BATCH_SIZE):
            batch = bids[i : i + self.QUAL_BATCH_SIZE]
            try:
                batch_results = await self._call_qualification(team_profile, batch)
                results.extend(batch_results)
            except Exception as e:
                logger.error(f"자격 판정 배치 {i//self.QUAL_BATCH_SIZE+1} 실패: {e}")
                for b in batch:
                    results.append(QualificationResult(
                        bid_no=b.bid_no,
                        qualification_status="ambiguous",
                        qualification_notes="AI 분석 일시 오류 — 직접 확인 필요",
                    ))

        return results

    async def score_bids(
        self,
        team_profile: TeamBidProfile,
        bids: list[BidAnnouncement],
    ) -> list[BidRecommendation]:
        """Stage 1(전처리) + Stage 2(TENOPA 리뷰) 통합."""
        # Stage 1: 전처리 (content_text 있는 건만)
        to_preprocess = [b for b in bids if b.content_text]
        summaries: dict[str, BidSummary] = {}
        if to_preprocess:
            try:
                summaries = await self.preprocessor.preprocess_batch(to_preprocess)
                logger.info(f"전처리 완료: {len(summaries)}/{len(to_preprocess)}건")
            except Exception as e:
                logger.warning(f"전처리 배치 실패 (원문 기반 진행): {e}")

        # Stage 2: TENOPA 리뷰어 평가
        results: list[BidRecommendation] = []
        for i in range(0, len(bids), self.REVIEW_BATCH_SIZE):
            batch = bids[i : i + self.REVIEW_BATCH_SIZE]
            try:
                reviews = await self._call_tenopa_review(batch, summaries)
                converted = [self._review_to_recommendation(r) for r in reviews]
                results.extend(converted)
            except Exception as e:
                logger.error(f"TENOPA 리뷰 배치 {i//self.REVIEW_BATCH_SIZE+1} 실패: {e}")

        return results

    async def review_single(self, bid: BidAnnouncement) -> TenopaBidReview | None:
        """단일 공고 TENOPA 리뷰 (전처리 포함). API/테스트용."""
        summary = await self.preprocessor.preprocess(bid) if bid.content_text else None
        summaries = {bid.bid_no: summary} if summary else {}
        reviews = await self._call_tenopa_review([bid], summaries)
        return reviews[0] if reviews else None

    # ── Stage 0: 자격 판정 호출 ────────────────────────────────

    async def _call_qualification(
        self, team_profile: TeamBidProfile, bids: list[BidAnnouncement]
    ) -> list[QualificationResult]:
        """Claude 자격 판정 프롬프트 실행"""
        profile_text = self._format_profile(team_profile)
        bids_text = self._format_bids_for_qualification(bids)

        system = f"""당신은 공공입찰 자격 판정 전문가입니다.
팀 프로필과 공고 자격요건을 비교하여 참여 자격 여부를 판정합니다.

[팀 프로필]
{profile_text}

판정 기준:
- pass: 자격요건을 명확히 충족
- fail: 자격요건 불충족이 명확 (예: 특정 인증 미보유, 기업 규모 미달)
- ambiguous: 자격요건 불명확하거나 추가 확인 필요"""

        user = f"""다음 {len(bids)}개 공고에 대해 자격 판정을 수행하세요.

{bids_text}

반드시 JSON 배열만 반환하세요. 다른 텍스트 없이:
[
  {{
    "bid_no": "공고번호",
    "qualification_status": "pass|fail|ambiguous",
    "disqualification_reason": "fail일 때만 작성",
    "qualification_notes": "ambiguous일 때만 작성"
  }}
]"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            timeout=self.CLAUDE_TIMEOUT,
            messages=[{"role": "user", "content": user}],
            system=system,
        )

        return self._parse_qualification_response(response.content[0].text, bids)

    # ── Stage 2: TENOPA 리뷰어 호출 ───────────────────────────

    async def _call_tenopa_review(
        self,
        bids: list[BidAnnouncement],
        summaries: dict[str, BidSummary],
    ) -> list[TenopaBidReview]:
        """TENOPA 수주 심의위원 프롬프트 배치 실행"""
        bids_parts = []
        for b in bids:
            budget = f"{b.budget_amount:,}원" if b.budget_amount else "미기재"
            days = f"D-{b.days_remaining}" if b.days_remaining is not None else "마감일 미상"

            # 전처리 요약이 있으면 사용, 없으면 원문 축약
            summary = summaries.get(b.bid_no)
            if summary:
                summary_text = summary.to_text()
            else:
                summary_text = (b.content_text or "내용 없음")[:800]

            bids_parts.append(
                f"[공고번호] {b.bid_no}\n"
                f"[공고명] {b.bid_title}\n"
                f"[발주기관] {b.agency}\n"
                f"[예산] {budget}\n"
                f"[마감] {days}\n"
                f"[요약]\n{summary_text}"
            )

        bids_text = "\n\n---\n\n".join(bids_parts)
        user_msg = REVIEWER_USER_BATCH.format(
            count=len(bids),
            bids_text=bids_text,
        )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            timeout=self.CLAUDE_TIMEOUT,
            messages=[{"role": "user", "content": user_msg}],
            system=REVIEWER_SYSTEM,
        )

        return self._parse_review_response(response.content[0].text, bids)

    # ── 파싱 헬퍼 ────────────────────────────────────────────

    def _parse_qualification_response(
        self, text: str, bids: list[BidAnnouncement]
    ) -> list[QualificationResult]:
        bid_nos = {b.bid_no for b in bids}
        try:
            start = text.find("[")
            end = text.rfind("]") + 1
            data = json.loads(text[start:end])

            results = []
            parsed_nos = set()
            for item in data:
                bid_no = str(item.get("bid_no", "")).strip()
                if bid_no not in bid_nos:
                    continue
                status = item.get("qualification_status", "ambiguous")
                if status not in ("pass", "fail", "ambiguous"):
                    status = "ambiguous"
                results.append(QualificationResult(
                    bid_no=bid_no,
                    qualification_status=status,
                    disqualification_reason=item.get("disqualification_reason"),
                    qualification_notes=item.get("qualification_notes"),
                ))
                parsed_nos.add(bid_no)

            for b in bids:
                if b.bid_no not in parsed_nos:
                    results.append(QualificationResult(
                        bid_no=b.bid_no,
                        qualification_status="ambiguous",
                        qualification_notes="AI 응답 파싱 실패 — 직접 확인 필요",
                    ))
            return results

        except Exception as e:
            logger.error(f"자격 판정 응답 파싱 실패: {e}\n응답: {text[:300]}")
            return [
                QualificationResult(
                    bid_no=b.bid_no,
                    qualification_status="ambiguous",
                    qualification_notes="AI 응답 파싱 오류",
                )
                for b in bids
            ]

    def _parse_review_response(
        self, text: str, bids: list[BidAnnouncement]
    ) -> list[TenopaBidReview]:
        """TENOPA 리뷰어 응답 파싱 → TenopaBidReview 목록"""
        bid_nos = {b.bid_no for b in bids}
        try:
            start = text.find("[")
            end = text.rfind("]") + 1
            data = json.loads(text[start:end])

            results = []
            for item in data:
                bid_no = str(item.get("bid_no", "")).strip()
                if bid_no not in bid_nos:
                    continue

                score = max(0, min(100, int(item.get("suitability_score", 0))))
                verdict = item.get("verdict", "제외")
                if verdict not in ("추천", "검토 필요", "제외"):
                    verdict = "검토 필요" if score >= 40 else "제외"

                analysis = item.get("reason_analysis", {})
                strengths = analysis.get("strengths", []) if isinstance(analysis, dict) else []
                risks = analysis.get("risks", []) if isinstance(analysis, dict) else []

                results.append(TenopaBidReview(
                    bid_no=bid_no,
                    bid_title=item.get("bid_title", ""),
                    suitability_score=score,
                    verdict=verdict,
                    reason_analysis=ReasonAnalysis(
                        strengths=strengths,
                        risks=risks,
                    ),
                    action_plan=item.get("action_plan", ""),
                ))
            return results

        except Exception as e:
            logger.error(f"TENOPA 리뷰 응답 파싱 실패: {e}\n응답: {text[:300]}")
            return []

    # ── 변환 헬퍼: TenopaBidReview → BidRecommendation ───────

    def _review_to_recommendation(self, review: TenopaBidReview) -> BidRecommendation:
        """기존 BidRecommendation 스키마 호환 변환."""
        # strengths → RecommendationReason
        reasons = [
            RecommendationReason(
                category="전문성",
                reason=s,
                strength="high" if review.suitability_score >= 70 else "medium",
            )
            for s in review.reason_analysis.strengths
        ]
        if not reasons:
            reasons = [RecommendationReason(
                category="기타",
                reason=review.action_plan or "평가 완료",
                strength="medium",
            )]

        # risks → RiskFactor
        risks = [
            RiskFactor(
                risk=r,
                level="high" if review.suitability_score < 40 else "medium",
            )
            for r in review.reason_analysis.risks
        ]

        return BidRecommendation(
            bid_no=review.bid_no,
            match_score=review.suitability_score,
            match_grade=_score_to_grade(review.suitability_score),
            recommendation_summary=f"[{review.verdict}] {review.action_plan}",
            recommendation_reasons=reasons,
            risk_factors=risks,
            win_probability_hint=VERDICT_TO_PROBABILITY.get(review.verdict, "중"),
            recommended_action=VERDICT_TO_ACTION.get(review.verdict, "검토"),
        )

    # ── 포맷 헬퍼 ────────────────────────────────────────────

    def _format_profile(self, p: TeamBidProfile) -> str:
        lines = [
            f"전문분야: {', '.join(p.expertise_areas) or '미지정'}",
            f"보유기술: {', '.join(p.tech_keywords) or '미지정'}",
            f"수행실적: {p.past_projects or '미입력'}",
            f"기업규모: {p.company_size or '미지정'}",
            f"보유인증: {', '.join(p.certifications) or '없음'}",
            f"사업자유형: {p.business_registration_type or '미지정'}",
        ]
        if p.employee_count is not None:
            lines.append(f"임직원수: {p.employee_count}명")
        if p.founded_year:
            lines.append(f"설립연도: {p.founded_year}년")
        return "\n".join(lines)

    def _format_bids_for_qualification(self, bids: list[BidAnnouncement]) -> str:
        parts = []
        for b in bids:
            content_preview = (b.content_text or "내용 없음")[:500]
            parts.append(
                f"bid_no: {b.bid_no}\n"
                f"공고명: {b.bid_title}\n"
                f"발주기관: {b.agency}\n"
                f"공고내용(요약): {content_preview}\n"
            )
        return "\n---\n".join(parts)
