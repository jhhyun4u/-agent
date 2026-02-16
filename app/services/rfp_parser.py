import json
from pathlib import Path

import anthropic
from PyPDF2 import PdfReader

from app.config import settings
from app.models.schemas import RFPData
from app.prompts.proposal import RFP_ANALYSIS_PROMPT, SYSTEM_PROMPT


def extract_text_from_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n".join(text_parts)


def extract_text_from_docx(file_path: Path) -> str:
    from docx import Document

    doc = Document(str(file_path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix == ".docx":
        return extract_text_from_docx(file_path)
    elif suffix == ".hwp":
        raise NotImplementedError("HWP 파싱은 추후 지원 예정입니다.")
    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {suffix}")


async def parse_rfp(file_path: Path) -> RFPData:
    raw_text = extract_text(file_path)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": RFP_ANALYSIS_PROMPT.format(rfp_text=raw_text[:10000]),
            }
        ],
    )

    result_text = response.content[0].text
    # JSON 블록 추출
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0]
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0]

    data = json.loads(result_text.strip())
    return RFPData(raw_text=raw_text, **data)
