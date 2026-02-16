from pydantic import BaseModel


class ProjectInput(BaseModel):
    """직접 입력 기반 제안서 생성 요청"""

    project_name: str
    client_name: str
    project_scope: str
    duration: str
    budget: str | None = None
    requirements: list[str] = []
    additional_info: str | None = None


class RFPData(BaseModel):
    """RFP 파싱 결과 구조"""

    title: str
    client_name: str
    project_scope: str
    duration: str
    budget: str | None = None
    requirements: list[str] = []
    evaluation_criteria: list[str] = []
    raw_text: str


class ProposalSection(BaseModel):
    """제안서 개별 섹션"""

    title: str
    content: str


class ProposalContent(BaseModel):
    """Claude가 생성한 제안서 전체 내용"""

    project_overview: str
    understanding: str
    approach: str
    methodology: str
    schedule: str
    team_composition: str
    expected_outcomes: str
    budget_plan: str | None = None


class ProposalResponse(BaseModel):
    """제안서 생성 API 응답"""

    proposal_id: str
    message: str
    docx_path: str | None = None
    pptx_path: str | None = None
