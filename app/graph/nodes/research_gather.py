"""
v3.5: RFP 내용 기반 선행 리서치 노드

RFP 분석 결과(사업명, 핫버튼, 평가항목, 필수요건, 기술 키워드)에서
리서치 주제를 동적으로 도출하여 관련 자료를 선행 조사.
review 없이 자동 통과 → go_no_go로 직행.
"""

import logging

from app.graph.state import ProposalState
from app.services.claude_client import claude_generate
from app.services import prompt_tracker

logger = logging.getLogger(__name__)


async def research_gather(state: ProposalState) -> dict:
    """RFP 내용 기반 선행 리서치: RFP에서 조사 주제를 동적 도출."""

    rfp = state.get("rfp_analysis")
    if not rfp:
        return {"current_step": "research_gather_complete"}

    if hasattr(rfp, "model_dump"):
        rfp_dict = rfp.model_dump()
    elif isinstance(rfp, dict):
        rfp_dict = rfp
    else:
        rfp_dict = {}

    # RFP 핵심 정보 추출
    project_name = rfp_dict.get("project_name", "")
    client = rfp_dict.get("client", "")
    hot_buttons = rfp_dict.get("hot_buttons", [])
    eval_items = rfp_dict.get("eval_items", [])
    mandatory_reqs = rfp_dict.get("mandatory_reqs", [])
    tech_keywords = rfp_dict.get("tech_keywords", [])
    scope = rfp_dict.get("scope", "")

    eval_item_names = [item.get("item", "") for item in eval_items if isinstance(item, dict)]

    rfp_context = f"""사업명: {project_name}
발주기관: {client}
사업범위: {scope}
핫버튼(발주기관 관심사항): {hot_buttons}
평가항목: {eval_item_names}
필수요건: {mandatory_reqs}
기술 키워드: {tech_keywords}"""

    prompt = f"""당신은 용역 제안 전문 리서처입니다.
아래 RFP를 분석하여, 제안서 작성에 필요한 선행 리서치를 수행하세요.

## RFP 핵심 정보
{rfp_context}

## 지시사항

### 1단계: 리서치 주제 도출
RFP의 사업명, 핫버튼, 평가항목, 필수요건, 기술 키워드를 분석하여
이 사업에 특화된 리서치 주제를 5~8개 도출하세요.
(고정된 차원이 아니라, 이 RFP에 실제로 필요한 조사 주제를 선정)

### 2단계: 주제별 리서치 + 데이터 품질 태깅
각 주제에 대해:
- 핵심 발견(finding) 3~5개
- 제안서 작성에 활용할 수 있는 구체적 근거/데이터/사례
- 발주기관이 중요시할 포인트

data_points의 각 항목은 반드시 아래 4축 품질 기준을 자가 평가하세요:
- Alignment: RFP 과업·핫버튼과 직접 연관되는 데이터인가?
- Credibility: 출처가 공신력 있는 기관(정부·국제기구·학술)인가?
- Depth: 구체적 수치(%, 원, 달러 등)나 명확한 팩트를 포함하는가?
- Utility: 제안서에서 차별화 근거로 직접 활용 가능한가?

4축 중 2개 이상 미달 시 해당 데이터는 출력하지 마세요.

### 3단계: 제안 전략 시사점
- Go/No-Go 판단에 영향을 줄 핵심 요소
- 제안서에서 강조해야 할 차별화 포인트
- 주의해야 할 리스크/약점

## 출처 태그 규칙
모든 data_points에 출처를 명시하세요:
- 정부·국제기구 보고서: 기관명 + 발행연도 + 보고서명
- 업계 리서치: 조사기관명 + 발행연도
- 3년 이상 된 데이터는 "N년 기준" 병기
- 출처를 특정할 수 없는 경우 source를 "일반지식"으로 표기

## 출력 형식 (JSON)
{{
  "research_topics": [
    {{
      "topic": "리서치 주제명",
      "relevance": "이 주제가 필요한 이유 (RFP 어떤 항목과 연관)",
      "findings": ["구체적 발견1", "발견2", "발견3"],
      "data_points": [
        {{
          "content": "데이터 내용 (구체적 수치 포함)",
          "credibility": "high | medium | low",
          "source": "출처 기관명, 발행연도, 보고서명"
        }}
      ],
      "rfp_alignment": "연관된 RFP 항목(핫버튼/평가항목/필수요건)",
      "proposal_implication": "제안서 작성 시 활용 방안"
    }}
  ],
  "summary": "종합 리서치 요약 (3~5문장)",
  "go_no_go_implications": ["Go/No-Go에 영향을 줄 핵심 요소"],
  "differentiation_points": ["차별화 포인트"],
  "risk_factors": ["주의해야 할 리스크"]
}}
"""

    result = await claude_generate(prompt)

    # 프롬프트 사용 기록 (인라인 프롬프트)
    proposal_id = state.get("project_id", "")
    if proposal_id:
        try:
            import hashlib
            await prompt_tracker.record_usage(
                proposal_id=proposal_id,
                artifact_step="research_gather",
                section_id=None,
                prompt_id="_inline.research_gather",
                prompt_version=0,
                prompt_hash=hashlib.sha256(prompt[:500].encode()).hexdigest(),
            )
        except Exception:
            pass

    return {
        "research_brief": result if not result.get("_parse_error") else {"summary": result.get("text", "")},
        "current_step": "research_gather_complete",
    }
