"""
Compliance Matrix 생애주기 관리 (§10)

STEP 1: RFP 필수 요건에서 초안 생성
STEP 2: 전략 관점 항목 추가 (Win Theme, AFE, 핵심 메시지)
STEP 4: 자가진단 — 각 항목 충족 여부 AI 체크
"""

import logging

from app.graph.state import ComplianceItem
from app.services.claude_client import claude_generate

logger = logging.getLogger(__name__)

COMPLIANCE_CHECK_PROMPT = """다음 요건의 충족 여부를 판정하세요.

## 요건
{requirement}

## 제안서 내용
{proposal_content}

## 출력 형식 (JSON)
{{
  "status": "충족 또는 미충족 또는 해당없음",
  "matching_section": "해당 요건을 충족하는 섹션 ID (있으면)",
  "evidence": "충족 근거 또는 미충족 사유"
}}
"""


class ComplianceTracker:
    """Compliance Matrix 전 단계 생애주기 관리."""

    @staticmethod
    async def create_initial(rfp_analysis) -> list[ComplianceItem]:
        """STEP 1: RFP 필수 요건에서 초안 생성."""
        if hasattr(rfp_analysis, "model_dump"):
            rfp_dict = rfp_analysis.model_dump()
        elif isinstance(rfp_analysis, dict):
            rfp_dict = rfp_analysis
        else:
            return []

        items = []

        # 필수 요건
        for i, req in enumerate(rfp_dict.get("mandatory_reqs", [])):
            items.append(ComplianceItem(
                req_id=f"REQ-{i+1:03d}",
                content=req,
                source_step="rfp",
                status="미확인",
            ))

        # 평가항목에서 추가 요건
        for item in rfp_dict.get("eval_items", []):
            item_name = item.get("item", item.get("항목명", ""))
            weight = item.get("weight", item.get("배점", 0))
            if item_name:
                items.append(ComplianceItem(
                    req_id=f"EVAL-{item_name[:10]}",
                    content=f"평가항목: {item_name} ({weight}점)",
                    source_step="rfp",
                    status="미확인",
                ))

        return items

    @staticmethod
    async def update_from_strategy(
        matrix: list[ComplianceItem], strategy
    ) -> list[ComplianceItem]:
        """STEP 2: 전략 관점 항목 추가."""
        if hasattr(strategy, "model_dump"):
            s_dict = strategy.model_dump()
        elif isinstance(strategy, dict):
            s_dict = strategy
        else:
            return matrix

        win_theme = s_dict.get("win_theme", "")
        afe = s_dict.get("action_forcing_event", "")
        key_messages = s_dict.get("key_messages", [])

        if win_theme:
            matrix.append(ComplianceItem(
                req_id="STR-WIN",
                content=f"Win Theme 반영 확인: {win_theme}",
                source_step="strategy",
                status="미확인",
            ))

        if afe:
            matrix.append(ComplianceItem(
                req_id="STR-AFE",
                content=f"Action Forcing Event 반영: {afe}",
                source_step="strategy",
                status="미확인",
            ))

        for i, msg in enumerate(key_messages):
            matrix.append(ComplianceItem(
                req_id=f"STR-MSG-{i+1}",
                content=f"핵심 메시지 {i+1} 반영: {msg}",
                source_step="strategy",
                status="미확인",
            ))

        return matrix

    @staticmethod
    async def check_compliance(
        sections: list, matrix: list[ComplianceItem]
    ) -> list[ComplianceItem]:
        """STEP 4 자가진단: 각 항목 충족 여부 AI 체크."""
        all_content = ""
        for s in sections:
            content = s.content if hasattr(s, "content") else s.get("content", "")
            all_content += content + "\n"

        if not all_content.strip():
            return matrix

        # 항목이 많으면 배치 처리 (전체 내용을 한 번에 전달)
        for item in matrix:
            if item.status != "미확인":
                continue
            try:
                result = await claude_generate(
                    COMPLIANCE_CHECK_PROMPT.format(
                        requirement=item.content,
                        proposal_content=all_content[:10000],
                    ),
                    max_tokens=500,
                )
                # 응답 타입 체크 (dict가 아니면 기본값 설정)
                if isinstance(result, dict):
                    item.status = result.get("status", "미확인")
                    item.proposal_section = result.get("matching_section", "")
                else:
                    logger.warning(f"Compliance check 응답 타입 오류: {type(result)}")
                    item.status = "미확인"
            except Exception as e:
                logger.warning(f"Compliance 체크 실패 [{item.req_id}]: {e}")

        return matrix
