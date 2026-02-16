import json
from pathlib import Path

import anthropic
from PyPDF2 import PdfReader

from app.config import settings
from app.models.schemas import RFPData
from app.prompts.proposal import RFP_ANALYSIS_PROMPT, SYSTEM_PROMPT


def extract_text_from_pdf(file_path: Path) -> str:
    """레거시 래퍼 함수 - utils.file_utils 사용 권장"""
    from app.utils import extract_text_from_file
    return extract_text_from_file(file_path)


def extract_text_from_docx(file_path: Path) -> str:
    """레거시 래퍼 함수 - utils.file_utils 사용 권장"""
    from app.utils import extract_text_from_file
    return extract_text_from_file(file_path)


def extract_text(file_path: Path) -> str:
    """파일에서 텍스트 추출"""
    from app.utils import extract_text_from_file
    return extract_text_from_file(file_path)


async def parse_rfp(file_path: Path) -> RFPData:
    """RFP 파일 파싱 및 분석 (비동기)"""
    from app.utils import create_anthropic_client, extract_json_from_response

    raw_text = extract_text(file_path)

    client = create_anthropic_client(async_client=True)
    response = await client.messages.create(
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
    data = extract_json_from_response(result_text)
    return RFPData(raw_text=raw_text, **data)
