"""
전략 수립 에이전트 (Sub-agent 2/5)

역할:
- 경쟁 환경 분석
- 배점별 섹션 배분 전략
- 핵심 메시지 및 차별화 전략 수립
- 인력 배정 계획

노드 구성:
1. analyze_competition - 경쟁 분석 (LLM)
2. allocate_resources - 배점 배분 전략 (Tool)
3. develop_strategy - 전략 수립 (LLM)
4. assign_personnel - 인력 배정 (Tool/LLM)
"""

from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from state.agent_states import StrategyState
from config.claude_optimizer import ModelTier


async def analyze_competition_node(state: StrategyState) -> dict:
    """경쟁 환경 분석 - LLM 사용"""
    rfp_analysis = state.get("rfp_analysis", {})

    llm = ChatAnthropic(model=ModelTier.SONNET.value, temperature=0.3)

    prompt = f"""RFP 정보를 바탕으로 경쟁 환경을 분석하세요.

# RFP 정보
사업명: {rfp_analysis.get('rfp_title', '')}
발주처: {rfp_analysis.get('client_name', '')}
평가 기준: {rfp_analysis.get('evaluation_criteria', [])}

# 분석 항목
1. 예상 경쟁사 및 강점/약점
2. 경쟁 우위 확보 방안
3. 차별화 포인트

JSON 형식으로 응답하세요:
{{
    "competitors": ["경쟁사1", "경쟁사2"],
    "threats": ["위협1", "위협2"],
    "opportunities": ["기회1", "기회2"],
    "differentiation": ["차별화1", "차별화2"]
}}"""

    response = await llm.ainvoke([
        SystemMessage(content="당신은 비즈니스 전략 전문가입니다."),
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
            "competitors": [],
            "threats": [],
            "opportunities": [],
            "differentiation": []
        }

    return {"competitive_analysis": result}


def allocate_resources_node(state: StrategyState) -> dict:
    """배점별 섹션 배분 전략 - Tool 기반"""
    rfp_analysis = state.get("rfp_analysis", {})
    criteria = rfp_analysis.get("evaluation_criteria", [])

    # 배점 기반 페이지 할당
    allocations = []
    for criterion in criteria:
        weight = criterion.get("weight", 0)
        pages = max(2, int(weight / 5))  # 기본 2페이지, 10점당 2페이지

        allocations.append({
            "section": criterion.get("criterion", ""),
            "weight": weight,
            "allocated_pages": pages,
            "importance": "high" if weight >= 30 else "medium" if weight >= 15 else "low"
        })

    return {"score_allocations": allocations}


async def develop_strategy_node(state: StrategyState) -> dict:
    """전략 수립 - LLM 사용"""
    rfp_analysis = state.get("rfp_analysis", {})
    competitive = state.get("competitive_analysis", {})

    llm = ChatAnthropic(model=ModelTier.SONNET.value, temperature=0.5)

    prompt = f"""제안서 전략을 수립하세요.

# 발주처 정보
{rfp_analysis.get('client_name', '')}, {rfp_analysis.get('rfp_title', '')}
숨은 의도: {rfp_analysis.get('hidden_intent', '')}

# 경쟁 환경
차별화 포인트: {competitive.get('differentiation', [])}

# 전략 수립
1. 핵심 메시지 (한 문장)
2. 3가지 차별화 요소
3. 경쟁 대응 전략

JSON 형식으로 응답하세요:
{{
    "core_message": "우리의 핵심 메시지",
    "differentiators": ["차별화1", "차별화2", "차별화3"],
    "attack_strategy": "경쟁 대응 전략"
}}"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])

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
            "core_message": "혁신적인 솔루션 제공",
            "differentiators": ["경험", "기술력", "가격 경쟁력"],
            "attack_strategy": "기술 우위 강조"
        }

    return {"strategy_draft": result}


def assign_personnel_node(state: StrategyState) -> dict:
    """인력 배정 계획 - 규칙 기반"""
    allocations = state.get("score_allocations", [])

    # 기본 인력 구성
    personnel = [
        {"role": "PM", "level": "senior", "allocation": 100},
        {"role": "아키텍트", "level": "senior", "allocation": 80},
        {"role": "개발자", "level": "senior", "allocation": 100},
        {"role": "개발자", "level": "junior", "allocation": 100},
        {"role": "QA", "level": "mid", "allocation": 80},
    ]

    return {"personnel_assignments": personnel}


def finalize_strategy_node(state: StrategyState) -> dict:
    """최종 전략 결과 생성"""
    strategy_result = {
        "competitive_analysis": state.get("competitive_analysis", {}),
        "score_allocations": state.get("score_allocations", []),
        "strategy": state.get("strategy_draft", {}),
        "personnel": state.get("personnel_assignments", []),
    }

    return {"strategy_result": strategy_result}


def build_strategy_graph():
    """전략 수립 Sub-agent 그래프 구축"""

    builder = StateGraph(StrategyState)

    # 노드 추가
    builder.add_node("analyze_competition", analyze_competition_node)
    builder.add_node("allocate_resources", allocate_resources_node)
    builder.add_node("develop_strategy", develop_strategy_node)
    builder.add_node("assign_personnel", assign_personnel_node)
    builder.add_node("finalize", finalize_strategy_node)

    # 엣지 정의
    builder.add_edge(START, "analyze_competition")
    builder.add_edge("analyze_competition", "allocate_resources")
    builder.add_edge("allocate_resources", "develop_strategy")
    builder.add_edge("develop_strategy", "assign_personnel")
    builder.add_edge("assign_personnel", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()
