SYSTEM_PROMPT = """당신은 전문 용역 제안서 작성 전문가입니다.
공공기관 및 민간 기업의 용역 제안서를 작성하는 데 풍부한 경험이 있습니다.
제안서는 명확하고 설득력 있으며, 발주처의 요구사항을 정확히 반영해야 합니다.
한국어로 작성하며, 공공기관 제안서 형식과 관행을 따릅니다."""

PROPOSAL_GENERATION_PROMPT = """다음 프로젝트 정보를 바탕으로 용역 제안서 내용을 작성해주세요.

## 프로젝트 정보
- 프로젝트명: {project_name}
- 발주처: {client_name}
- 사업 범위: {project_scope}
- 사업 기간: {duration}
- 예산: {budget}
- 요구사항: {requirements}
- 추가 정보: {additional_info}

## 작성 지침
각 섹션을 상세하고 구체적으로 작성해주세요.

반드시 아래 JSON 형식으로 응답해주세요:
{{
    "project_overview": "사업 개요 (프로젝트의 배경, 목적, 필요성을 포함)",
    "understanding": "사업 이해도 (발주처의 요구사항과 현황에 대한 깊은 이해를 보여주는 내용)",
    "approach": "접근 방법론 (프로젝트를 수행하기 위한 전략적 접근 방식)",
    "methodology": "수행 방법론 (구체적인 수행 절차와 방법, 단계별 활동 포함)",
    "schedule": "추진 일정 (단계별 일정과 마일스톤)",
    "team_composition": "투입 인력 및 조직 구성 (역할별 인력 구성과 자격 요건)",
    "expected_outcomes": "기대 효과 (정량적/정성적 기대 성과)",
    "budget_plan": "예산 계획 (비용 항목별 산출 근거, 예산이 제공된 경우에만 작성)"
}}"""

RFP_ANALYSIS_PROMPT = """다음 RFP(제안요청서) 문서 내용을 분석하여 핵심 정보를 추출해주세요.

## RFP 원문
{rfp_text}

## 추출 지침
아래 JSON 형식으로 핵심 정보를 정리해주세요:
{{
    "title": "사업명",
    "client_name": "발주 기관명",
    "project_scope": "사업 범위 요약",
    "duration": "사업 기간",
    "budget": "예산 (명시된 경우)",
    "requirements": ["주요 요구사항 목록"],
    "evaluation_criteria": ["평가 기준 목록"]
}}"""
