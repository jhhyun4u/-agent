"""
RFP 분석 에이전트 (Sub-agent 1/5)

역할:
- RFP 문서에서 텍스트 추출 및 정제
- 구조적 분석 (섹션, 평가 기준, 배점)
- 숨은 의도 및 발주처 심리 분석
- 자격 요건 검증
- 발주처 언어 프로필 생성

노드 구성:
1. extract_document - 문서에서 텍스트 추출
2. clean_text - 텍스트 정제 및 정규화
3. structural_analysis - 구조 분석 (LLM)
4. implicit_analysis - 숨은 의도 분석 (LLM)
5. client_language - 발주처 언어 프로필 (LLM)
6. qualification_check - 자격 요건 검증 (LLM)
"""

from typing import Any
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from state.agent_states import RFPAnalysisState, RFPAnalysisOutput
from config.claude_optimizer import ModelTier
from app.utils import extract_text_from_file
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════
# 노드 구현
# ═══════════════════════════════════════════════════════════════════════════

def extract_document_node(state: RFPAnalysisState) -> dict:
    """문서에서 텍스트 추출"""
    raw_doc = state.get("raw_document", "")

    # 이미 텍스트인 경우
    if isinstance(raw_doc, str) and not raw_doc.startswith("/"):
        return {"cleaned_text": raw_doc}

    # 파일 경로인 경우
    try:
        file_path = Path(raw_doc)
        if file_path.exists():
            text = extract_text_from_file(file_path)
            return {"cleaned_text": text}
    except:
        pass

    return {"cleaned_text": raw_doc}


def clean_text_node(state: RFPAnalysisState) -> dict:
    """텍스트 정제 및 정규화 (규칙 기반)"""
    text = state.get("cleaned_text", "")

    # 기본 정제
    cleaned = text.strip()

    # 연속된 공백 제거
    import re
    cleaned = re.sub(r'\s+', ' ', cleaned)

    # 특수 문자 정리 (선택적)
    # cleaned = re.sub(r'[^\w\s\.,;:!?()-]', '', cleaned)

    return {"cleaned_text": cleaned}


async def structural_analysis_node(state: RFPAnalysisState) -> dict:
    """구조 분석 - LLM 사용"""
    text = state.get("cleaned_text", "")

    llm = ChatAnthropic(
        model=ModelTier.SONNET.value,
        temperature=0
    )

    prompt = f"""다음 RFP 문서를 분석하여 구조적 정보를 추출하세요.

# RFP 문서
{text[:15000]}

# 추출할 정보
1. 제안요청서 제목
2. 발주처 명칭
3. 사업 개요
4. 사업 범위
5. 평가 기준 및 배점
6. 제출 마감일
7. 예산 규모

JSON 형식으로 응답하세요:
{{
    "title": "제안요청서 제목",
    "client_name": "발주처",
    "project_scope": "사업 범위",
    "evaluation_criteria": [
        {{"criterion": "기술 능력", "weight": 40}},
        {{"criterion": "가격", "weight": 30}}
    ],
    "deadline": "YYYY-MM-DD",
    "budget": "예산 규모"
}}"""

    response = await llm.ainvoke([
        SystemMessage(content="당신은 RFP 분석 전문가입니다."),
        HumanMessage(content=prompt)
    ])

    import json
    result_text = response.content

    # JSON 추출
    try:
        if "```json" in result_text:
            json_str = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            json_str = result_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = result_text

        result = json.loads(json_str)
    except:
        result = {
            "title": "분석 실패",
            "client_name": "알 수 없음",
            "project_scope": text[:500],
            "evaluation_criteria": [],
            "deadline": "",
            "budget": ""
        }

    return {"structural_result": result}


async def implicit_analysis_node(state: RFPAnalysisState) -> dict:
    """숨은 의도 및 발주처 심리 분석 - LLM 사용"""
    text = state.get("cleaned_text", "")
    structural = state.get("structural_result", {})

    llm = ChatAnthropic(
        model=ModelTier.SONNET.value,
        temperature=0.3
    )

    prompt = f"""RFP 문서에서 발주처의 숨은 의도와 심리를 분석하세요.

# RFP 정보
제목: {structural.get('title', 'N/A')}
발주처: {structural.get('client_name', 'N/A')}

# RFP 내용 (발췌)
{text[:10000]}

# 분석 항목
1. 발주처가 진짜 원하는 것은 무엇인가?
2. 어떤 문제를 해결하려고 하는가?
3. 발주처의 우선순위는 무엇인가?
4. 어떤 제안이 유리할까?

JSON 형식으로 응답하세요:
{{
    "hidden_intent": "발주처의 숨은 의도",
    "pain_points": ["문제점1", "문제점2"],
    "priorities": ["우선순위1", "우선순위2"],
    "winning_strategy": "승리 전략 제안"
}}"""

    response = await llm.ainvoke([
        SystemMessage(content="당신은 비즈니스 심리 분석 전문가입니다."),
        HumanMessage(content=prompt)
    ])

    import json
    result_text = response.content

    try:
        if "```json" in result_text:
            json_str = result_text.split("```json")[1].split("```")[0].strip()
        else:
            json_str = result_text
        result = json.loads(json_str)
    except:
        result = {
            "hidden_intent": "분석 중",
            "pain_points": [],
            "priorities": [],
            "winning_strategy": ""
        }

    return {"implicit_analysis": result}


async def client_language_node(state: RFPAnalysisState) -> dict:
    """발주처 언어 프로필 생성 - LLM 사용 (Haiku)"""
    text = state.get("cleaned_text", "")

    llm = ChatAnthropic(
        model=ModelTier.HAIKU.value,
        temperature=0
    )

    prompt = f"""RFP 문서의 언어 스타일을 분석하세요.

# RFP 내용
{text[:8000]}

# 분석 항목
1. 핵심 용어 (자주 사용되는 단어)
2. 문체 (격식체/비격식체, 기술적/비즈니스적)
3. 격식 수준 (매우 격식/보통/캐주얼)

JSON 형식으로 응답하세요:
{{
    "key_terms": ["용어1", "용어2", "용어3"],
    "writing_style": "격식있는 기술 문서체",
    "formality_level": "high"
}}"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    import json
    result_text = response.content

    try:
        if "```json" in result_text:
            json_str = result_text.split("```json")[1].split("```")[0].strip()
        else:
            json_str = result_text
        result = json.loads(json_str)
    except:
        result = {
            "key_terms": [],
            "writing_style": "일반",
            "formality_level": "medium"
        }

    return {"language_profile": result}


async def qualification_check_node(state: RFPAnalysisState) -> dict:
    """자격 요건 검증 - LLM 사용 (Haiku)"""
    structural = state.get("structural_result", {})
    text = state.get("cleaned_text", "")

    llm = ChatAnthropic(
        model=ModelTier.HAIKU.value,
        temperature=0
    )

    prompt = f"""RFP에서 자격 요건을 추출하세요.

# RFP 내용
{text[:8000]}

# 추출 항목
1. 필수 자격 요건
2. 선택 자격 요건
3. 우대 사항

JSON 형식으로 응답하세요:
{{
    "mandatory": ["필수1", "필수2"],
    "optional": ["선택1", "선택2"],
    "preferred": ["우대1", "우대2"]
}}"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    import json
    result_text = response.content

    try:
        if "```json" in result_text:
            json_str = result_text.split("```json")[1].split("```")[0].strip()
        else:
            json_str = result_text
        result = json.loads(json_str)
    except:
        result = {
            "mandatory": [],
            "optional": [],
            "preferred": []
        }

    return {"qualifications": result}


def finalize_rfp_analysis_node(state: RFPAnalysisState) -> dict:
    """최종 RFP 분석 결과 생성"""
    structural = state.get("structural_result", {})
    implicit = state.get("implicit_analysis", {})
    language = state.get("language_profile", {})
    quals = state.get("qualifications", {})

    # 최종 결과 조합
    rfp_analysis_result = {
        "rfp_title": structural.get("title", ""),
        "client_name": structural.get("client_name", ""),
        "project_scope": structural.get("project_scope", ""),
        "evaluation_criteria": structural.get("evaluation_criteria", []),
        "deadline": structural.get("deadline", ""),
        "budget": structural.get("budget", ""),
        "hidden_intent": implicit.get("hidden_intent", ""),
        "pain_points": implicit.get("pain_points", []),
        "priorities": implicit.get("priorities", []),
        "winning_strategy": implicit.get("winning_strategy", ""),
        "language_profile": language,
        "qualifications": quals,
        "completeness_score": 0.85,  # 임시 점수
    }

    return {"rfp_analysis_result": rfp_analysis_result}


# ═══════════════════════════════════════════════════════════════════════════
# 그래프 구축
# ═══════════════════════════════════════════════════════════════════════════

def build_rfp_analysis_graph():
    """RFP 분석 Sub-agent 그래프 구축"""

    builder = StateGraph(RFPAnalysisState)

    # 노드 추가
    builder.add_node("extract_document", extract_document_node)
    builder.add_node("clean_text", clean_text_node)
    builder.add_node("structural_analysis", structural_analysis_node)
    builder.add_node("implicit_analysis", implicit_analysis_node)
    builder.add_node("client_language", client_language_node)
    builder.add_node("qualification_check", qualification_check_node)
    builder.add_node("finalize", finalize_rfp_analysis_node)

    # 엣지 정의 (직선 구조)
    builder.add_edge(START, "extract_document")
    builder.add_edge("extract_document", "clean_text")
    builder.add_edge("clean_text", "structural_analysis")
    builder.add_edge("structural_analysis", "implicit_analysis")
    builder.add_edge("implicit_analysis", "client_language")
    builder.add_edge("client_language", "qualification_check")
    builder.add_edge("qualification_check", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()
