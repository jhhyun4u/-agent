from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

from app.models.schemas import ProposalContent


def build_pptx(content: ProposalContent, project_name: str, output_path: Path) -> Path:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # 표지
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = f"{project_name}"
    slide.placeholders[1].text = "용역 제안서"

    sections = [
        ("사업 개요", content.project_overview),
        ("사업 이해도", content.understanding),
        ("접근 방법론", content.approach),
        ("수행 방법론", content.methodology),
        ("추진 일정", content.schedule),
        ("투입 인력", content.team_composition),
        ("기대 효과", content.expected_outcomes),
    ]

    if content.budget_plan:
        sections.append(("예산 계획", content.budget_plan))

    for title, body in sections:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = title
        tf = slide.placeholders[1].text_frame
        tf.clear()
        # 내용을 줄 단위로 추가 (슬라이드에 맞게 요약)
        lines = [line.strip() for line in body.split("\n") if line.strip()]
        for i, line in enumerate(lines[:10]):  # 슬라이드당 최대 10줄
            if i == 0:
                tf.paragraphs[0].text = line
                tf.paragraphs[0].font.size = Pt(16)
            else:
                p = tf.add_paragraph()
                p.text = line
                p.font.size = Pt(16)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    return output_path
