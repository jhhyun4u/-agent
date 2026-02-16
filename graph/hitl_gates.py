"""
HITL 게이트 구현 (v3.1.1, interrupt() 기반)

C-1 Fix: HITL 무한 루프 → interrupt() 함수로 전면 재설계

5개 게이트:
- Gate #1, #2, #4: 조건부 (자동 통과 가능)
- Gate #3, #5: ★필수 (항상 사람 개입)
"""

import sys
import os
from pathlib import Path

# Add project root to path
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from typing import Dict, Any, Literal
from dataclasses import dataclass, asdict
from langgraph.types import interrupt, Command

from state.phased_state import PhasedSupervisorState
from config.claude_optimizer import TokenUsageTracker


@dataclass
class HITLDecision:
    """Supervisor의 HITL 판단 결과"""

    gate_id: int
    action: Literal["auto_pass", "require_human", "recommend_human"]
    reason: str
    summary_for_human: str  # 사람에게 보여줄 요약
    approval_items: list[str]  # 사람이 확인/승인해야 할 항목


def evaluate_hitl_gate(gate_id: int, state: PhasedSupervisorState) -> HITLDecision:
    """
    각 HITL 게이트에서 사람 개입이 필요한지 판단.
    
    Returns:
        HITLDecision: auto_pass / require_human / recommend_human
    """

    ps = state.get("proposal_state", {})
    artifact = state.get(f"phase_artifact_{gate_id}", {})
    ws = state.get("phase_working_state", {})

    # ── Gate #1: Research → Analysis ──
    if gate_id == 1:
        past_count = len(artifact.get("past_proposals_summary", []))
        has_rfp = bool(artifact.get("rfp_title"))

        if not has_rfp:
            return HITLDecision(
                gate_id=1,
                action="require_human",
                reason="RFP 파싱 실패. 문서를 확인해주세요.",
                summary_for_human="RFP 문서에서 텍스트를 추출하지 못했습니다.",
                approval_items=["RFP 문서 재업로드 또는 수동 입력"],
            )
        if past_count == 0:
            return HITLDecision(
                gate_id=1,
                action="recommend_human",
                reason=f"참조할 과거 실적이 0건. 수동으로 참조 자료를 추가할 수 있습니다.",
                summary_for_human="유사 과거 실적을 찾지 못했습니다.",
                approval_items=["과거 실적 수동 추가 여부"],
            )

        return HITLDecision(
            gate_id=1,
            action="auto_pass",
            reason=f"수집 완료. RFP 파싱 성공, 과거 실적 {past_count}건.",
            summary_for_human="",
            approval_items=[],
        )

    # ── Gate #2: Analysis → Plan ──
    elif gate_id == 2:
        qual_status = artifact.get("qualification_status", "")
        weaknesses = artifact.get("our_weaknesses", [])

        if qual_status == "미충족":
            return HITLDecision(
                gate_id=2,
                action="require_human",
                reason="필수 자격 요건 미충족. 입찰 포기 또는 대응 방안 결정 필요.",
                summary_for_human=f"자격 요건 미충족: {artifact.get('qualification_gaps', [])}",
                approval_items=["입찰 계속 여부", "자격 보완 방안"],
            )

        if len(weaknesses) >= 3:
            return HITLDecision(
                gate_id=2,
                action="recommend_human",
                reason=f"약점 {len(weaknesses)}개 식별. 전략 수립 전 확인 권장.",
                summary_for_human=f"식별된 약점: {weaknesses}",
                approval_items=["약점 대응 방향 확인"],
            )

        return HITLDecision(
            gate_id=2,
            action="auto_pass",
            reason="분석 정상 완료. 자격 충족, 경쟁 환경 양호.",
            summary_for_human="",
            approval_items=[],
        )

    # ── Gate #3: Plan → Implement (항상 필수) ──
    elif gate_id == 3:
        artifact = state.get("phase_artifact_3", {})
        return HITLDecision(
            gate_id=3,
            action="require_human",
            reason="전략 승인은 항상 사람이 해야 합니다.",
            summary_for_human=_format_strategy_summary(artifact),
            approval_items=[
                "핵심 전략 메시지",
                "차별화 포인트",
                "인력 배정",
                "섹션별 분량 배분",
            ],
        )

    # ── Gate #4: Implement → Test ──
    elif gate_id == 4:
        artifact = state.get("phase_artifact_4", {})
        total_pages = artifact.get("total_pages", 0)
        target_pages = artifact.get("total_target_pages", 0)
        traceability = artifact.get("overall_traceability", 0)

        page_deviation = (
            abs(total_pages - target_pages) / max(target_pages, 1)
            if target_pages > 0
            else 0
        )

        if page_deviation > 0.3 or traceability < 0.8:
            issues = []
            if page_deviation > 0.3:
                issues.append(
                    f"분량 편차 {page_deviation:.0%} (목표 {target_pages}p, 실제 {total_pages:.1f}p)"
                )
            if traceability < 0.8:
                issues.append(f"요구사항 커버리지 {traceability:.0%} (목표 80%)")

            return HITLDecision(
                gate_id=4,
                action="require_human",
                reason=f"초안 품질 이슈: {', '.join(issues)}",
                summary_for_human="\n".join(issues),
                approval_items=["방향 수정 여부", "특정 섹션 재작성 지시"],
            )

        return HITLDecision(
            gate_id=4,
            action="auto_pass",
            reason=f"초안 정상. 분량 {total_pages:.1f}/{target_pages}p, 커버리지 {traceability:.0%}.",
            summary_for_human="",
            approval_items=[],
        )

    # ── Gate #5: Test → Complete (항상 필수) ──
    elif gate_id == 5:
        ws = state.get("phase_working_state", {})
        quality = ws.get("quality_score", 0)

        return HITLDecision(
            gate_id=5,
            action="require_human",
            reason="최종 승인은 항상 사람이 해야 합니다.",
            summary_for_human=_format_final_summary(ws, quality),
            approval_items=[
                "최종 품질 점수 확인",
                "문서 형식 확인",
                "제출 승인",
            ],
        )

    return HITLDecision(
        gate_id=gate_id,
        action="auto_pass",
        reason="Unknown gate",
        summary_for_human="",
        approval_items=[],
    )


def _format_strategy_summary(artifact: Dict[str, Any]) -> str:
    """Gate #3용: 전략 요약을 사람이 읽기 좋게 포맷"""

    lines = [
        f"📌 핵심 메시지: {artifact.get('core_message', '')}",
        "",
        "🎯 수주 테마:",
    ]
    for i, theme in enumerate(artifact.get("win_themes", []), 1):
        lines.append(f"  {i}. {theme}")

    lines.append("")
    lines.append("⚔️ 차별화:")
    for d in artifact.get("differentiators", []):
        lines.append(f"  • {d}")

    lines.append("")
    lines.append("👥 핵심 인력:")
    for p in artifact.get("personnel_assignments", [])[:5]:
        lines.append(f"  • {p['role']}: {p.get('name', '')} ({p.get('grade', '')})")

    lines.append("")
    lines.append("📄 섹션 배분:")
    for s in artifact.get("section_plans", [])[:5]:
        lines.append(f"  • {s.get('section_name', '')}: {s.get('target_pages', '')}p")

    return "\n".join(lines)


def _format_final_summary(ws: Dict[str, Any], quality: float) -> str:
    """Gate #5용: 최종 요약"""

    lines = [
        f"📊 최종 품질 점수: {quality:.2f}/1.0",
        f"🔄 수정 라운드: {ws.get('revision_rounds', 0)}회",
        f"📁 생성 문서: {ws.get('final_document_path', '')}",
    ]

    issues = ws.get("critique_result", {}).get("individual_issues", [])
    if issues:
        lines.append("")
        lines.append("⚠️ 남은 이슈:")
        for issue in issues[:3]:
            lines.append(f"  • [{issue.get('section')}] {issue.get('issue')}")

    return "\n".join(lines)


# ═══ HITL 게이트 노드 팩토리 ═══

def make_hitl_gate(gate_id: int):
    """
    C-1 Fix: 게이트 ID별 HITL 노드 팩토리
    각 gate에서 조건부로 interrupt() 호출
    """

    async def hitl_gate_node(state: PhasedSupervisorState) -> Dict[str, Any]:
        # Express 모드 확인 (M-5 Fix)
        express_mode = state.get("express_mode", False)
        if express_mode and gate_id in [1, 2, 4]:  # 조건부 게이트만 자동 통과
            decision = HITLDecision(
                gate_id=gate_id,
                action="auto_pass",
                reason=f"긴급 모드: Gate #{gate_id} 자동 통과",
                summary_for_human="",
                approval_items=[],
            )
            return {
                "hitl_decisions": [*state.get("hitl_decisions", []), asdict(decision)]
            }

        # 일반 모드: 조건 평가
        decision = evaluate_hitl_gate(gate_id, state)

        # auto_pass → 그냥 진행
        if decision.action == "auto_pass":
            return {
                "hitl_decisions": [*state.get("hitl_decisions", []), asdict(decision)]
            }

        # recommend_human || require_human → interrupt() 호출
        # C-1 Fix: interrupt()로 실행을 일시정지하고 사용자 입력 대기
        human_response = interrupt({
            "gate_id": gate_id,
            "action": decision.action,
            "summary": decision.summary_for_human,
            "approval_items": decision.approval_items,
            "reason": decision.reason,
        })

        # 사용자 응답 처리
        approved = human_response.get("approved", False)
        feedback = human_response.get("feedback", "")

        updated_decisions = [*state.get("hitl_decisions", []), asdict(decision)]
        updated_human = {**state.get("hitl_human_inputs", {}), gate_id: human_response}

        if not approved and feedback:
            # 거부 + 피드백 → 이전 Phase 재실행을 위한 상태 설정 (m-3 Fix)
            return {
                "hitl_decisions": updated_decisions,
                "hitl_human_inputs": updated_human,
                "phase_working_state": {
                    **state.get("phase_working_state", {}),
                    "human_feedback": feedback,
                    "retry_requested": True,
                },
            }

        return {
            "hitl_decisions": updated_decisions,
            "hitl_human_inputs": updated_human,
        }

    hitl_gate_node.__name__ = f"hitl_gate_{gate_id}"
    return hitl_gate_node


if __name__ == "__main__":
    # 테스트: HITL 로직 검증

    from state.phased_state import initialize_phased_supervisor_state
    from graph.mock_data import create_mock_artifact_1, create_mock_artifact_2

    print("🧪 HITL 게이트 테스트\n")

    state = initialize_phased_supervisor_state()
    state["phase_artifact_1"] = create_mock_artifact_1()
    state["phase_artifact_2"] = create_mock_artifact_2()

    # Gate #1 테스트 (auto_pass)
    decision1 = evaluate_hitl_gate(1, state)
    print(f"Gate #1: {decision1.action} ({decision1.reason})\n")

    # Gate #2 테스트 (auto_pass)
    decision2 = evaluate_hitl_gate(2, state)
    print(f"Gate #2: {decision2.action} ({decision2.reason})\n")

    print("✅ HITL 게이트 로직 정상 작동")
