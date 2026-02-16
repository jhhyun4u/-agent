"""
Supervisor 오케스트레이터 구현.

v3.0: Multi-Agent 아키텍처의 핵심
- supervisor_plan_node: 동적 워크플로우 계획
- supervisor_route_node: 다음 에이전트 결정
- 에러 복구 로직
"""

from typing import Literal
import json
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

from state import SupervisorState, WorkflowPlan, initialize_supervisor_state
from prompts.supervisor import (
    SUPERVISOR_PLANNING_PROMPT,
    SUPERVISOR_ROUTING_PROMPT,
    SUPERVISOR_ERROR_RECOVERY_PROMPT,
)


class SupervisorNode:
    """Supervisor의 핵심 노드들"""

    def __init__(self, model: str = "claude-sonnet-4-5-20250929", temperature: float = 0):
        self.llm = ChatAnthropic(model=model, temperature=temperature)

    async def plan_workflow(self, state: SupervisorState) -> dict:
        """
        RFP 특성 분석 및 워크플로우 동적 결정.
        
        설계: Part II.4.1 - Supervisor Planning 노드
        """

        phase = state.get("current_phase", "initialization")
        proposal = state.get("proposal_state", {})
        rfp = proposal.get("rfp_analysis", {})

        # 프롬프트 구성
        prompt = f"""{SUPERVISOR_PLANNING_PROMPT}

## 현재 상태
- Phase: {phase}
- 완료된 단계: {state.get("agent_status", {})}
- 에러 이력: {len(state.get("errors", []))}건

## RFP 정보
- 제목: {rfp.get('rfp_title', 'N/A')}
- 발주처: {rfp.get('client_name', 'N/A')}
- 평가 방식: {rfp.get('evaluation_method', 'N/A')}
- 배점: {rfp.get('evaluation_criteria', [])}
- 페이지 제한: {proposal.get('page_limit', 'N/A')}

## 과제 요구사항
- 필수 인력: {bool(rfp.get('mandatory_qualifications'))}
- 예산 배점: {next((c.get('score', 0) for c in rfp.get('evaluation_criteria', []) if '예산' in c.get('name', '')), '정보없음')}%
- 재입찰 여부: {proposal.get('is_resubmission', False)}

최적의 실행 계획을 수립해주세요.
"""

        try:
            # LLM 호출
            response = await self.llm.agenerate([prompt])
            generated = response.generations[0][0].text

            # 응답 파싱
            plan_data = self._parse_plan_response(generated)

            return {
                "workflow_plan": plan_data.get("steps", []),
                "dynamic_decisions": state.get("dynamic_decisions", []) + [{
                    "decision": "workflow_plan",
                    "rationale": plan_data.get("rationale", ""),
                    "estimated_duration": plan_data.get("estimated_duration_minutes", 0),
                    "timestamp": datetime.now().isoformat(),
                }],
                "skipped_steps": plan_data.get("skip_reasons", {}),
            }

        except Exception as e:
            # 기본 계획으로 폴백 (RFP 분석 → 전략 → 섹션 → 품질 → 문서)
            return {
                "workflow_plan": ["rfp_analysis", "strategy", "section_gen", "quality", "document"],
                "dynamic_decisions": state.get("dynamic_decisions", []) + [{
                    "decision": "workflow_plan_fallback",
                    "rationale": f"계획 LLM 호출 실패: {str(e)[:100]}. 기본 계획 사용.",
                    "timestamp": datetime.now().isoformat(),
                }],
                "skipped_steps": {},
                "errors": state.get("errors", []) + [{
                    "node": "supervisor_plan",
                    "error_type": type(e).__name__,
                    "message": str(e)[:300],
                    "timestamp": datetime.now().isoformat(),
                    "fatal": False,
                }],
            }

    async def route_next_agent(self, state: SupervisorState) -> dict:
        """
        현재 phase와 workflow_plan에 따라 다음 에이전트를 동적으로 결정.
        
        설계: Part II.5.2 - 동적 라우팅 함수
        """

        phase = state.get("current_phase", "initialization")
        plan = state.get("workflow_plan", [])
        status = state.get("agent_status", {})
        errors = state.get("errors", [])

        # 에러 상태 처리
        if errors and errors[-1].get("fatal"):
            return {"current_phase": "error", "next_action": "error"}

        # Phase별 라우팅
        routing_map = {
            "initialization":       ("rfp_analysis", "RFP 분석 시작"),
            "rfp_analysis":         self._route_after_rfp(state),
            "strategy_development": ("hitl_strategy", "전략 HITL 게이트"),
            "hitl_strategy":        self._route_after_strategy_hitl(state),
            "section_generation":   ("quality", "품질 검토"),
            "quality_review":       self._route_after_quality(state),
            "hitl_final":           ("document", "문서 최종화"),
            "document_finalization":("completed", "제안서 완료"),
            "completed":            ("completed", "완료"),
        }

        next_action, description = routing_map.get(phase, ("error", "알 수 없는 상태"))

        return {
            "current_phase": next_action if next_action == "completed" or next_action == "error" else phase,
            "next_action": next_action,
            "description": description,
            "dynamic_decisions": state.get("dynamic_decisions", []) + [{
                "decision": f"route_from_{phase}",
                "rationale": description,
                "timestamp": datetime.now().isoformat(),
            }],
        }

    def _route_after_rfp(self, state: SupervisorState) -> tuple[str, str]:
        """RFP 분석 후 라우팅"""
        rfp = state.get("proposal_state", {}).get("rfp_analysis", {})

        # 수의계약이거나 경쟁 분석이 불필요하면 → 바로 전략으로
        if rfp.get("evaluation_method") == "수의계약":
            if "skipped_steps" not in state:
                state["skipped_steps"] = []
            state["skipped_steps"].append({
                "step": "competitive_analysis",
                "reason": "수의계약이므로 경쟁 분석 불필요"
            })

        return ("strategy_development", "전략 수립 시작")

    def _route_after_strategy_hitl(self, state: SupervisorState) -> tuple[str, str]:
        """전략 HITL 후 라우팅"""
        rfp = state.get("proposal_state", {}).get("rfp_analysis", {})

        # 인력 요건이 없으면 → 바로 섹션 생성
        if not rfp.get("mandatory_qualifications"):
            if "skipped_steps" not in state:
                state["skipped_steps"] = []
            state["skipped_steps"].append({
                "step": "personnel_assignment",
                "reason": "RFP에 필수 인력 요건 없음"
            })
            state["current_phase"] = "section_generation"
            return ("section_gen", "섹션 생성 시작")

        return ("section_generation", "인력 배정 → 섹션 생성")

    def _route_after_quality(self, state: SupervisorState) -> tuple[str, str]:
        """품질 검토 후 라우팅"""
        ps = state.get("proposal_state", {})
        quality = ps.get("quality_score", 0)
        rounds = ps.get("revision_round", 0)

        if quality >= 0.75:
            state["current_phase"] = "hitl_final"
            return ("hitl_final", "최종 HITL 게이트")

        if rounds >= 3:
            state["current_phase"] = "hitl_final"
            dynamic = state.get("dynamic_decisions", [])
            dynamic.append({
                "decision": "force_hitl_after_max_revisions",
                "rationale": f"품질 {quality:.2f}, 3회 수정 후에도 미달. 사람 판단 필요.",
                "timestamp": datetime.now().isoformat(),
            })
            return ("hitl_final", "3회 수정 후 최종 HITL")

        # 재수정
        return ("quality_review", "섹션 재수정")

    @staticmethod
    def _parse_plan_response(response: str) -> dict:
        """LLM 응답에서 계획 정보 추출"""
        try:
            # JSON 블록 찾기
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "{" in response:
                json_str = response[response.index("{"):response.rindex("}") + 1]
            else:
                return {"steps": [], "rationale": response, "skip_reasons": {}}

            return json.loads(json_str)
        except Exception:
            # 파싱 실패 시 기본값
            return {
                "steps": ["rfp_analysis", "strategy", "section_gen", "quality", "document"],
                "rationale": response[:300],
                "skip_reasons": {},
            }


# HITL 게이트 노드들
async def hitl_strategy_gate(state: SupervisorState) -> dict:
    """전략 HITL 게이트"""
    return {
        "current_phase": "hitl_strategy",
        "messages": state.get("messages", []) + [{
            "role": "system",
            "content": f"""
## 전략 HITL 게이트

다음 전략을 검토하고 승인/수정해주세요:

**핵심 메시지**: {state.get('proposal_state', {}).get('core_message', 'N/A')}
**차별화 포인트**: {state.get('proposal_state', {}).get('differentiators', [])}
**경쟁 대응 전략**: {state.get('proposal_state', {}).get('attack_strategy', 'N/A')}

---
승인하려면 "승인" 또는 "approve" 입력
수정이 필요하면 구체적인 피드백을 입력해주세요.
"""
        }],
    }


async def hitl_personnel_gate(state: SupervisorState) -> dict:
    """인력 배정 HITL 게이트"""
    assignments = state.get("proposal_state", {}).get("personnel_assignments", [])
    personnel_text = "\n".join([
        f"- {a.get('role', '')}: {a.get('candidate_name', '')} "
        f"({a.get('experience_years', 0)}년 경력)"
        for a in assignments
    ])

    return {
        "current_phase": "hitl_personnel",
        "messages": state.get("messages", []) + [{
            "role": "system",
            "content": f"""
## 인력 배정 HITL 게이트

다음 인력 배정을 검토해주세요:

{personnel_text}

---
승인하려면 "승인"
변경이 필요하면 구체적인 지시를 입력해주세요.
"""
        }],
    }


async def hitl_final_gate(state: SupervisorState) -> dict:
    """최종 HITL 게이트"""
    ps = state.get("proposal_state", {})

    return {
        "current_phase": "hitl_final",
        "messages": state.get("messages", []) + [{
            "role": "system",
            "content": f"""
## 최종 HITL 게이트

제안서 완성 전 최종 검토:

**품질 점수**: {ps.get('quality_score', 0):.2f}
**전체 페이지**: {ps.get('total_pages', 0)}p
**섹션 상태**: {sum(1 for s in ps.get('sections', {}).values() if s.get('status') == 'finalized')}/{len(ps.get('sections', {}))}

---
승인 시 "승인"
추가 수정이 필요하면 구체적으로 입력해주세요.
"""
        }],
    }


# Supervisor 그래프 빌더
def build_supervisor_graph(subgraphs: dict | None = None, checkpointer=None) -> any:
    """
    Supervisor 메인 그래프 구축.

    설계: Part II.4.3 - Supervisor 메인 그래프

    Args:
        subgraphs: Sub-agent 그래프 딕셔너리 (optional)
        checkpointer: 메모리 체크포인터 (optional)
    """

    supervisor = SupervisorNode()
    builder = StateGraph(SupervisorState)

    # ── 코어 노드 ──
    builder.add_node("plan_workflow", supervisor.plan_workflow)
    builder.add_node("route_next", supervisor.route_next_agent)

    # HITL 게이트
    builder.add_node("hitl_strategy", hitl_strategy_gate)
    builder.add_node("hitl_personnel", hitl_personnel_gate)
    builder.add_node("hitl_final", hitl_final_gate)

    # 서브그래프 (실제 구현 시 subgraphs에서 주입됨)
    if subgraphs:
        for name, subgraph in subgraphs.items():
            builder.add_node(name, subgraph)

    # ── 엣지 ──
    builder.add_edge(START, "plan_workflow")
    builder.add_edge("plan_workflow", "route_next")

    # 조건부 라우팅
    def route_based_next_action(state: SupervisorState) -> str:
        action = state.get("next_action", "error")
        action_map = {
            "rfp_analysis": "rfp_analysis_agent",
            "strategy": "strategy_agent",
            "section_gen": "section_gen_agent",
            "quality": "quality_agent",
            "document": "document_agent",
            "hitl_strategy": "hitl_strategy",
            "hitl_final": "hitl_final",
            "completed": END,
            "error": END,
        }
        return action_map.get(action, END)

    builder.add_conditional_edges(
        "route_next",
        route_based_next_action,
        {
            "rfp_analysis_agent": "rfp_analysis_agent" if subgraphs else "plan_workflow",
            "strategy_agent": "strategy_agent" if subgraphs else "plan_workflow",
            "section_gen_agent": "section_gen_agent" if subgraphs else "plan_workflow",
            "quality_agent": "quality_agent" if subgraphs else "plan_workflow",
            "document_agent": "document_agent" if subgraphs else "plan_workflow",
            "hitl_strategy": "hitl_strategy",
            "hitl_final": "hitl_final",
            END: END,
        } if subgraphs else {
            "hitl_strategy": "hitl_strategy",
            "hitl_final": "hitl_final",
            END: END,
        }
    )

    # Sub-agent에서 → route_next로 복귀
    if subgraphs:
        for agent_name in ["rfp_analysis_agent", "strategy_agent", "section_gen_agent", "quality_agent", "document_agent"]:
            builder.add_edge(agent_name, "route_next")

    # HITL 게이트에서 → route_next로 복귀
    builder.add_edge("hitl_strategy", "route_next")
    builder.add_edge("hitl_personnel", "route_next")
    builder.add_edge("hitl_final", "route_next")

    # 체크포인터가 제공되면 사용, 아니면 일반 컴파일
    if checkpointer:
        return builder.compile(checkpointer=checkpointer)
    else:
        return builder.compile()
