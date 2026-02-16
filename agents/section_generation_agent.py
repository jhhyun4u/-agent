"""
섹션 생성 에이전트 (Sub-agent 3/5)

역할:
- 제안서 섹션별 콘텐츠 생성
- 섹션 간 의존성 관리
- Phase 기반 병렬 생성

노드 구성:
1. plan_phases - 섹션 의존성 분석 및 Phase 계획
2. generate_sections - 섹션 콘텐츠 생성 (LLM)
"""

from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from state.agent_states import SectionGenerationState
from config.claude_optimizer import ModelTier


def plan_phases_node(state: SectionGenerationState) -> dict:
    """섹션 생성 Phase 계획 - 규칙 기반"""
    allocations = state.get("allocations", [])

    # 간단한 Phase 계획: 중요도 기반으로 순서 결정
    phases = []
    high_priority = [a for a in allocations if a.get("importance") == "high"]
    medium_priority = [a for a in allocations if a.get("importance") == "medium"]
    low_priority = [a for a in allocations if a.get("importance") == "low"]

    if high_priority:
        phases.append([a["section"] for a in high_priority])
    if medium_priority:
        phases.append([a["section"] for a in medium_priority])
    if low_priority:
        phases.append([a["section"] for a in low_priority])

    return {
        "generation_phases": phases,
        "current_phase_index": 0,
        "remaining_phases": phases,
    }


async def generate_sections_node(state: SectionGenerationState) -> dict:
    """섹션 콘텐츠 생성 - LLM 사용"""
    rfp_analysis = state.get("rfp_analysis", {})
    strategy = state.get("strategy", {})
    allocations = state.get("allocations", [])

    llm = ChatAnthropic(model=ModelTier.SONNET.value, temperature=0.7)

    generated_sections = {}

    for allocation in allocations[:3]:  # 처음 3개 섹션만 생성 (데모)
        section_name = allocation.get("section", "")
        pages = allocation.get("allocated_pages", 2)

        prompt = f"""다음 섹션의 제안서 콘텐츠를 작성하세요.

# 섹션 정보
섹션명: {section_name}
목표 페이지: {pages}페이지

# 프로젝트 정보
사업명: {rfp_analysis.get('rfp_title', '')}
발주처: {rfp_analysis.get('client_name', '')}
핵심 메시지: {strategy.get('core_message', '')}

# 요구사항
- 전문적이고 설득력 있는 내용
- 구체적인 방법론과 사례 포함
- {pages}페이지 분량 (약 {pages * 500}자)

마크다운 형식으로 작성하세요."""

        response = await llm.ainvoke([
            SystemMessage(content="당신은 제안서 작성 전문가입니다."),
            HumanMessage(content=prompt)
        ])

        content = response.content

        generated_sections[section_name] = {
            "content": content,
            "pages": pages,
            "status": "generated",
            "word_count": len(content)
        }

    return {"generated_sections": generated_sections}


def finalize_sections_node(state: SectionGenerationState) -> dict:
    """최종 섹션 결과 생성"""
    sections_result = {
        "sections": state.get("generated_sections", {}),
        "total_sections": len(state.get("generated_sections", {})),
        "status": "completed"
    }

    return {"sections_result": sections_result}


def build_section_generation_graph():
    """섹션 생성 Sub-agent 그래프 구축"""

    builder = StateGraph(SectionGenerationState)

    # 노드 추가
    builder.add_node("plan_phases", plan_phases_node)
    builder.add_node("generate_sections", generate_sections_node)
    builder.add_node("finalize", finalize_sections_node)

    # 엣지 정의
    builder.add_edge(START, "plan_phases")
    builder.add_edge("plan_phases", "generate_sections")
    builder.add_edge("generate_sections", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()
