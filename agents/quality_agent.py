"""
품질 관리 에이전트 (Sub-agent 4/5)

역할:
- 제안서 품질 검토
- 일관성 및 추적성 검증
- 개선 제안

노드 구성:
1. critique_sections - 섹션별 비평 (LLM)
2. check_consistency - 일관성 검증 (Tool/LLM)
3. calculate_quality_score - 품질 점수 산출
4. decide_action - 통과/수정/에스컬레이션 결정
"""

from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from state.agent_states import QualityState
from config.claude_optimizer import ModelTier


async def critique_sections_node(state: QualityState) -> dict:
    """섹션별 비평 - LLM 사용"""
    sections = state.get("sections", {})
    rfp_analysis = state.get("rfp_analysis", {})

    llm = ChatAnthropic(model=ModelTier.SONNET.value, temperature=0)

    # 처음 2개 섹션만 검토 (데모)
    section_items = list(sections.items())[:2]

    critique_result = {}
    for section_name, section_data in section_items:
        content = section_data.get("content", "")[:3000]  # 처음 3000자만

        prompt = f"""다음 제안서 섹션을 검토하고 품질을 평가하세요.

# 섹션: {section_name}
{content}

# 평가 항목
1. 논리적 흐름 (1-5점)
2. 구체성 (1-5점)
3. 설득력 (1-5점)
4. 개선 제안

JSON 형식으로 응답하세요:
{{
    "logic_score": 4,
    "specificity_score": 3,
    "persuasiveness_score": 4,
    "suggestions": ["개선사항1", "개선사항2"]
}}"""

        response = await llm.ainvoke([
            SystemMessage(content="당신은 제안서 품질 평가 전문가입니다."),
            HumanMessage(content=prompt)
        ])

        import json
        try:
            result_text = response.content
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = result_text
            result = json.loads(json_str)
        except:
            result = {
                "logic_score": 3,
                "specificity_score": 3,
                "persuasiveness_score": 3,
                "suggestions": []
            }

        critique_result[section_name] = result

    return {"critique_result": critique_result}


def check_consistency_node(state: QualityState) -> dict:
    """일관성 검증 - 규칙 기반"""
    sections = state.get("sections", {})

    # 간단한 일관성 검사
    issues = []

    # 섹션 수 검증
    if len(sections) < 3:
        issues.append({
            "severity": "medium",
            "type": "completeness",
            "description": f"섹션 수 부족 (현재 {len(sections)}개)"
        })

    # 내용 길이 검증
    for section_name, section_data in sections.items():
        content = section_data.get("content", "")
        target_pages = section_data.get("pages", 2)
        min_words = target_pages * 400

        if len(content) < min_words:
            issues.append({
                "severity": "low",
                "type": "length",
                "location": section_name,
                "description": f"분량 부족 (목표: {target_pages}페이지)"
            })

    return {"integration_issues": issues}


def calculate_quality_score_node(state: QualityState) -> dict:
    """품질 점수 산출"""
    critique = state.get("critique_result", {})
    issues = state.get("integration_issues", [])

    # 평균 점수 계산
    total_score = 0
    count = 0

    for section_critique in critique.values():
        total_score += section_critique.get("logic_score", 3)
        total_score += section_critique.get("specificity_score", 3)
        total_score += section_critique.get("persuasiveness_score", 3)
        count += 3

    avg_score = (total_score / count) if count > 0 else 3.0
    normalized_score = avg_score / 5.0

    # 이슈로 감점
    critical_issues = len([i for i in issues if i.get("severity") == "high"])
    normalized_score -= (critical_issues * 0.1)

    quality_score = max(0.0, min(1.0, normalized_score))

    return {
        "quality_score": quality_score,
        "revision_round": state.get("revision_round", 0)
    }


def decide_action_node(state: QualityState) -> dict:
    """통과/수정/에스컬레이션 결정"""
    quality_score = state.get("quality_score", 0.0)
    revision_round = state.get("revision_round", 0)
    issues = state.get("integration_issues", [])

    # 결정 로직
    if quality_score >= 0.8:
        action = "pass"
        reason = None
    elif revision_round >= 3:
        action = "escalate"
        reason = "수정 횟수 초과"
    elif len([i for i in issues if i.get("severity") == "high"]) > 0:
        action = "revise"
        reason = "중대 이슈 발견"
    elif quality_score < 0.6:
        action = "revise"
        reason = "품질 기준 미달"
    else:
        action = "pass"
        reason = None

    return {
        "quality_action": action,
        "escalation_reason": reason
    }


def finalize_quality_node(state: QualityState) -> dict:
    """최종 품질 결과 생성"""
    quality_result = {
        "quality_score": state.get("quality_score", 0.0),
        "action": state.get("quality_action", "pass"),
        "issues": state.get("integration_issues", []),
        "critique": state.get("critique_result", {}),
    }

    return {"quality_result": quality_result}


def build_quality_graph():
    """품질 관리 Sub-agent 그래프 구축"""

    builder = StateGraph(QualityState)

    # 노드 추가
    builder.add_node("critique_sections", critique_sections_node)
    builder.add_node("check_consistency", check_consistency_node)
    builder.add_node("calculate_score", calculate_quality_score_node)
    builder.add_node("decide_action", decide_action_node)
    builder.add_node("finalize", finalize_quality_node)

    # 엣지 정의
    builder.add_edge(START, "critique_sections")
    builder.add_edge("critique_sections", "check_consistency")
    builder.add_edge("check_consistency", "calculate_score")
    builder.add_edge("calculate_score", "decide_action")
    builder.add_edge("decide_action", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()
