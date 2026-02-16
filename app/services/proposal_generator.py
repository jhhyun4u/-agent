import json

import anthropic

from app.config import settings
from app.models.schemas import ProjectInput, ProposalContent, RFPData
from app.prompts.proposal import PROPOSAL_GENERATION_PROMPT, SYSTEM_PROMPT


async def generate_proposal_from_input(project: ProjectInput) -> ProposalContent:
    prompt = PROPOSAL_GENERATION_PROMPT.format(
        project_name=project.project_name,
        client_name=project.client_name,
        project_scope=project.project_scope,
        duration=project.duration,
        budget=project.budget or "미정",
        requirements="\n".join(f"- {r}" for r in project.requirements) or "없음",
        additional_info=project.additional_info or "없음",
    )
    return await _call_claude(prompt)


async def generate_proposal_from_rfp(rfp: RFPData) -> ProposalContent:
    prompt = PROPOSAL_GENERATION_PROMPT.format(
        project_name=rfp.title,
        client_name=rfp.client_name,
        project_scope=rfp.project_scope,
        duration=rfp.duration,
        budget=rfp.budget or "미정",
        requirements="\n".join(f"- {r}" for r in rfp.requirements) or "없음",
        additional_info=f"평가기준: {', '.join(rfp.evaluation_criteria)}"
        if rfp.evaluation_criteria
        else "없음",
    )
    return await _call_claude(prompt)


async def _call_claude(prompt: str) -> ProposalContent:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    result_text = response.content[0].text
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0]
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0]

    data = json.loads(result_text.strip())
    return ProposalContent(**data)
