"""
비용 기준 자동 선택 — KOSA / KEA / MOEF

RFP 텍스트 키워드 → 도메인 규칙 → 발주기관 과거 기준 순서로 판단.
"""

import logging
import re

from app.services.pricing.models import CostStandardRecommendation

logger = logging.getLogger(__name__)

# 도메인 → 기본 비용 기준 매핑
DOMAIN_RULES: dict[str, str] = {
    "SI/SW개발": "KOSA",
    "소프트웨어": "KOSA",
    "정보시스템": "KOSA",
    "IT": "KOSA",
    "엔지니어링": "KEA",
    "건설": "KEA",
    "설계": "KEA",
    "감리": "KEA",
    "정책연구": "MOEF",
    "학술": "MOEF",
    "컨설팅": "KOSA",
    "용역": "KOSA",
}

# RFP 텍스트 키워드 → 비용 기준
RFP_KEYWORDS: list[tuple[str, str]] = [
    (r"소프트웨어기술자", "KOSA"),
    (r"SW기술자", "KOSA"),
    (r"정보통신기술자", "KOSA"),
    (r"ICT기술자", "KOSA"),
    (r"엔지니어링기술자", "KEA"),
    (r"건설기술인", "KEA"),
    (r"기술사", "KEA"),
    (r"한국과학기술정보연구원", "MOEF"),
    (r"연구원인건비", "MOEF"),
    (r"학술연구용역", "MOEF"),
]


class CostStandardSelector:
    """비용 기준 자동 선택기."""

    async def select(
        self,
        domain: str,
        rfp_text: str | None = None,
        client_name: str | None = None,
    ) -> CostStandardRecommendation:
        # 1. RFP 텍스트에서 명시적 기준 키워드 탐색
        if rfp_text:
            for pattern, standard in RFP_KEYWORDS:
                if re.search(pattern, rfp_text):
                    return CostStandardRecommendation(
                        standard=standard,
                        confidence="high",
                        reason=f"RFP 텍스트에서 '{pattern}' 키워드 발견",
                    )

        # 2. 발주기관의 과거 사용 기준 조회
        if client_name:
            try:
                from app.utils.supabase_client import get_async_client
                client = await get_async_client()
                past = await client.table("market_price_data").select(
                    "evaluation_method, domain"
                ).ilike("client_org", f"%{client_name}%").limit(10).execute()

                if past.data:
                    # 가장 빈번한 도메인 기반 추정
                    domains = [r.get("domain", "") for r in past.data if r.get("domain")]
                    if domains:
                        most_common = max(set(domains), key=domains.count)
                        std = _domain_to_standard(most_common)
                        if std:
                            return CostStandardRecommendation(
                                standard=std,
                                confidence="medium",
                                reason=f"발주기관 '{client_name}'의 과거 주요 도메인: {most_common}",
                            )
            except Exception as e:
                logger.debug(f"발주기관 기준 조회 실패: {e}")

        # 3. 도메인 기반 규칙 매핑
        std = _domain_to_standard(domain)
        if std:
            return CostStandardRecommendation(
                standard=std,
                confidence="medium",
                reason=f"도메인 '{domain}' 기반 기본 규칙",
            )

        # 4. 기본값
        return CostStandardRecommendation(
            standard="KOSA",
            confidence="low",
            reason="기본값 (도메인 매핑 실패)",
        )


def _domain_to_standard(domain: str) -> str | None:
    """도메인 문자열에서 비용 기준 추출."""
    for key, std in DOMAIN_RULES.items():
        if key in domain:
            return std
    return None
