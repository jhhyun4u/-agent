"""
입찰 AI 분석 서비스

Claude API로 2단계 분석:
  1단계: 자격 판정 (pass / fail / ambiguous) — 배치 20건
  2단계: 매칭 점수 산출 (0~100) — 배치 20건
"""

import json
import logging
from datetime import datetime, timezone

from anthropic import AsyncAnthropic

from app.config import settings
from app.models.bid_schemas import (
    BidAnnouncement,
    BidRecommendation,
    QualificationResult,
    RecommendationReason,
    RiskFactor,
    TeamBidProfile,
)

logger = logging.getLogger(__name__)

_MATCH_GRADE_TABLE = [(90, "S"), (80, "A"), (70, "B"), (60, "C"), (0, "D")]


def _score_to_grade(score: int) -> str:
    for threshold, grade in _MATCH_GRADE_TABLE:
        if score >= threshold:
            return grade
    return "D"


class BidRecommender:
    """Claude 기반 2단계 입찰 분석 엔진"""

    BATCH_SIZE = 20
    CLAUDE_TIMEOUT = 30.0

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-5-20250929"

    # ── 공개 API ────────────────────────────────────────────

    async def analyze_bids(
        self,
        team_profile: TeamBidProfile,
        bids: list[BidAnnouncement],
        top_n: int = 20,
    ) -> tuple[list[BidRecommendation], list[QualificationResult]]:
        """
        1단계 + 2단계 통합 실행.

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

        # 1단계: 자격 판정
        if to_check:
            checked = await self.check_qualifications(team_profile, to_check)
            qual_results.extend(checked)

        qual_map = {r.bid_no: r for r in qual_results}

        # 2단계: pass + ambiguous만 매칭 분석
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
        """1단계: 배치 자격 판정 (BATCH_SIZE건/호출)"""
        results: list[QualificationResult] = []

        for i in range(0, len(bids), self.BATCH_SIZE):
            batch = bids[i : i + self.BATCH_SIZE]
            try:
                batch_results = await self._call_qualification(team_profile, batch)
                results.extend(batch_results)
            except Exception as e:
                logger.error(f"자격 판정 배치 {i//self.BATCH_SIZE+1} 실패: {e}")
                # 실패한 배치는 ambiguous로 처리
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
        """2단계: 배치 매칭 점수 산출 (BATCH_SIZE건/호출)"""
        results: list[BidRecommendation] = []

        for i in range(0, len(bids), self.BATCH_SIZE):
            batch = bids[i : i + self.BATCH_SIZE]
            try:
                batch_results = await self._call_scoring(team_profile, batch)
                results.extend(batch_results)
            except Exception as e:
                logger.error(f"매칭 점수 배치 {i//self.BATCH_SIZE+1} 실패: {e}")
                # 실패한 배치 건너뜀

        return results

    # ── Claude 호출 ──────────────────────────────────────────

    async def _call_qualification(
        self, team_profile: TeamBidProfile, bids: list[BidAnnouncement]
    ) -> list[QualificationResult]:
        """Claude 1단계 프롬프트 실행"""
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

    async def _call_scoring(
        self, team_profile: TeamBidProfile, bids: list[BidAnnouncement]
    ) -> list[BidRecommendation]:
        """Claude 2단계 프롬프트 실행"""
        profile_text = self._format_profile(team_profile)
        bids_text = self._format_bids_for_scoring(bids)

        system = f"""당신은 공공입찰 매칭 분석 전문가입니다.
팀 역량과 공고를 비교하여 매칭 점수와 추천 사유를 생성합니다.

중요: recommendation_reasons는 반드시 1개 이상 포함해야 합니다.
category는 "전문성"|"실적"|"규모"|"기술"|"지역"|"기타" 중 하나.
strength는 "high"|"medium"|"low" 중 하나.

[팀 프로필]
{profile_text}"""

        user = f"""다음 {len(bids)}개 공고에 대해 매칭 분석을 수행하세요.

{bids_text}

반드시 JSON 배열만 반환하세요. 다른 텍스트 없이:
[
  {{
    "bid_no": "공고번호",
    "match_score": 85,
    "match_grade": "A",
    "recommendation_summary": "한 줄 추천 요약",
    "recommendation_reasons": [
      {{"category": "전문성", "reason": "사유", "strength": "high"}}
    ],
    "risk_factors": [
      {{"risk": "리스크", "level": "medium"}}
    ],
    "win_probability_hint": "중상",
    "recommended_action": "적극 검토"
  }}
]"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            timeout=self.CLAUDE_TIMEOUT,
            messages=[{"role": "user", "content": user}],
            system=system,
        )

        return self._parse_scoring_response(response.content[0].text, bids)

    # ── 파싱 헬퍼 ────────────────────────────────────────────

    def _parse_qualification_response(
        self, text: str, bids: list[BidAnnouncement]
    ) -> list[QualificationResult]:
        bid_nos = {b.bid_no for b in bids}
        try:
            # JSON 블록 추출
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

            # 파싱 누락된 공고는 ambiguous 처리
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

    def _parse_scoring_response(
        self, text: str, bids: list[BidAnnouncement]
    ) -> list[BidRecommendation]:
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

                score = max(0, min(100, int(item.get("match_score", 0))))
                grade = item.get("match_grade") or _score_to_grade(score)

                reasons_raw = item.get("recommendation_reasons") or []
                reasons = [
                    RecommendationReason(
                        category=r.get("category", "기타"),
                        reason=r.get("reason", ""),
                        strength=r.get("strength", "medium"),
                    )
                    for r in reasons_raw
                    if r.get("reason")
                ]
                if not reasons:
                    reasons = [RecommendationReason(
                        category="기타", reason="팀 역량과 부합", strength="medium"
                    )]

                risks_raw = item.get("risk_factors") or []
                risks = [
                    RiskFactor(
                        risk=r.get("risk", ""),
                        level=r.get("level", "low"),
                    )
                    for r in risks_raw
                    if r.get("risk")
                ]

                results.append(BidRecommendation(
                    bid_no=bid_no,
                    match_score=score,
                    match_grade=grade,
                    recommendation_summary=item.get("recommendation_summary", ""),
                    recommendation_reasons=reasons,
                    risk_factors=risks,
                    win_probability_hint=item.get("win_probability_hint", "중"),
                    recommended_action=item.get("recommended_action", "검토"),
                ))
            return results

        except Exception as e:
            logger.error(f"매칭 점수 응답 파싱 실패: {e}\n응답: {text[:300]}")
            return []

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

    def _format_bids_for_scoring(self, bids: list[BidAnnouncement]) -> str:
        parts = []
        for b in bids:
            budget = f"{b.budget_amount:,}원" if b.budget_amount else "미기재"
            days = f"D-{b.days_remaining}" if b.days_remaining is not None else "마감일 미상"
            content_preview = (b.content_text or "내용 없음")[:800]
            parts.append(
                f"bid_no: {b.bid_no}\n"
                f"공고명: {b.bid_title}\n"
                f"발주기관: {b.agency}\n"
                f"사업금액: {budget}\n"
                f"마감: {days}\n"
                f"공고내용: {content_preview}\n"
            )
        return "\n---\n".join(parts)
