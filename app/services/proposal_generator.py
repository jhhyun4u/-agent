from typing import Union

from app.config import settings
from app.models.schemas import ProjectInput, ProposalContent, RFPData
from app.prompts.proposal import PROPOSAL_GENERATION_PROMPT, SYSTEM_PROMPT
from app.utils import create_anthropic_client, extract_json_from_response


def _format_requirements(requirements: list[str]) -> str:
    """요구사항 리스트를 문자열로 포맷팅"""
    return "\n".join(f"- {r}" for r in requirements) if requirements else "없음"


def _prepare_prompt_data(source: Union[ProjectInput, RFPData]) -> dict:
    """
    프롬프트 데이터 준비 (공통 로직)

    Args:
        source: ProjectInput 또는 RFPData

    Returns:
        프롬프트 포맷팅에 필요한 데이터 딕셔너리
    """
    if isinstance(source, ProjectInput):
        return {
            "project_name": source.project_name,
            "client_name": source.client_name,
            "project_scope": source.project_scope,
            "duration": source.duration,
            "budget": source.budget or "미정",
            "requirements": _format_requirements(source.requirements),
            "additional_info": source.additional_info or "없음",
        }
    else:  # RFPData
        additional_info = (
            f"평가기준: {', '.join(source.evaluation_criteria)}"
            if source.evaluation_criteria
            else "없음"
        )
        return {
            "project_name": source.title,
            "client_name": source.client_name,
            "project_scope": source.project_scope,
            "duration": source.duration,
            "budget": source.budget or "미정",
            "requirements": _format_requirements(source.requirements),
            "additional_info": additional_info,
        }


async def generate_proposal_from_input(project: ProjectInput) -> ProposalContent:
    """직접 입력 기반 제안서 생성"""
    prompt_data = _prepare_prompt_data(project)
    prompt = PROPOSAL_GENERATION_PROMPT.format(**prompt_data)
    return await _call_claude(prompt)


async def generate_proposal_from_rfp(rfp: RFPData) -> ProposalContent:
    """RFP 분석 결과 기반 제안서 생성"""
    prompt_data = _prepare_prompt_data(rfp)
    prompt = PROPOSAL_GENERATION_PROMPT.format(**prompt_data)
    return await _call_claude(prompt)


async def _call_claude(prompt: str) -> ProposalContent:
    """Claude API 호출 및 응답 파싱 (비동기)"""
    client = create_anthropic_client(async_client=True)
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    result_text = response.content[0].text
    data = extract_json_from_response(result_text)
    return ProposalContent(**data)
