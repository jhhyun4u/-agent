from pathlib import Path

from docx import Document
from docx.shared import Pt

from app.models.schemas import ProposalContent


def build_docx(content: ProposalContent, project_name: str, output_path: Path) -> Path:
    doc = Document()

    # 제목
    title = doc.add_heading(f"{project_name} 제안서", level=0)
    title.runs[0].font.size = Pt(24)

    sections = [
        ("1. 사업 개요", content.project_overview),
        ("2. 사업 이해도", content.understanding),
        ("3. 접근 방법론", content.approach),
        ("4. 수행 방법론", content.methodology),
        ("5. 추진 일정", content.schedule),
        ("6. 투입 인력 및 조직 구성", content.team_composition),
        ("7. 기대 효과", content.expected_outcomes),
    ]

    if content.budget_plan:
        sections.append(("8. 예산 계획", content.budget_plan))

    for heading, body in sections:
        doc.add_heading(heading, level=1)
        for paragraph in body.split("\n"):
            if paragraph.strip():
                doc.add_paragraph(paragraph.strip())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    return output_path
