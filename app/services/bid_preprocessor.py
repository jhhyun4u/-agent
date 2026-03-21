"""
공고문 전처리 에이전트

공고문 원문에서 4개 핵심 섹션만 타겟팅 추출:
  - 사업 개요 (사업명, 예산, 기간, 추진 배경)
  - 주요 과업 내용 (범위, 산출물, 기술 요구사항)
  - 입찰 참가 자격 (제한 사항, 필수 실적)
  - 평가 방법 (기술/가격 배점)

토큰 절감: 원문 전체 대신 구조화된 JSON 요약만 리뷰어에 전달.
"""

import json
import logging
from typing import Optional

from anthropic import AsyncAnthropic

from app.config import settings
from app.models.bid_schemas import BidAnnouncement, BidSummary
from app.prompts.bid_review import PREPROCESSOR_SYSTEM, PREPROCESSOR_USER

logger = logging.getLogger(__name__)


class BidPreprocessor:
    """Claude 기반 공고문 전처리 에이전트"""

    CLAUDE_TIMEOUT = 40.0
    MAX_CONTENT_CHARS = 8000  # 원문 최대 길이 (첨부파일 텍스트 대응)

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-5-20250929"

    async def preprocess(self, bid: BidAnnouncement) -> Optional[BidSummary]:
        """단일 공고 전처리 → BidSummary 반환. 실패 시 None."""
        content = (bid.content_text or "")[:self.MAX_CONTENT_CHARS]
        if not content.strip():
            return None

        user_msg = PREPROCESSOR_USER.format(
            bid_no=bid.bid_no,
            bid_title=bid.bid_title,
            agency=bid.agency,
            content_text=content,
        )

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                timeout=self.CLAUDE_TIMEOUT,
                system=PREPROCESSOR_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
            )
            text = response.content[0].text
            return self._parse_summary(text, bid)
        except Exception as e:
            logger.warning(f"전처리 실패 bid_no={bid.bid_no}: {e}")
            return None

    async def preprocess_batch(
        self, bids: list[BidAnnouncement]
    ) -> dict[str, BidSummary]:
        """배치 전처리 (순차 호출). {bid_no: BidSummary} 반환."""
        results: dict[str, BidSummary] = {}
        for bid in bids:
            summary = await self.preprocess(bid)
            if summary:
                results[bid.bid_no] = summary
        return results

    def _parse_summary(self, text: str, bid: BidAnnouncement) -> Optional[BidSummary]:
        """Claude 응답 → BidSummary 파싱."""
        try:
            # JSON 블록 추출
            start = text.find("{")
            end = text.rfind("}") + 1
            if start < 0 or end <= start:
                logger.warning(f"전처리 JSON 미발견: {text[:200]}")
                return None
            data = json.loads(text[start:end])

            meta = data.get("summary_metadata", {})
            quals = data.get("qualifications", {})

            return BidSummary(
                bid_no=bid.bid_no,
                organization=meta.get("organization", bid.agency),
                budget_detail=meta.get("budget_detail", ""),
                period=meta.get("period", ""),
                core_tasks=data.get("core_tasks", []),
                required_license=quals.get("required_license", ""),
                experience_needed=quals.get("experience_needed", ""),
                restriction=quals.get("restriction", ""),
                evaluation_points=data.get("evaluation_points", ""),
            )
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"전처리 파싱 실패 bid_no={bid.bid_no}: {e}")
            return None
