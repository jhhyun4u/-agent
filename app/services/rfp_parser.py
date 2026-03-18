import json
from pathlib import Path

import anthropic
from PyPDF2 import PdfReader

from app.config import settings
from app.models.schemas import RFPData

# RFP 파싱 전용 프롬프트 (기존 app/prompts/proposal.py에서 인라인 이동)
SYSTEM_PROMPT = """당신은 전문 용역 제안서 작성 전문가입니다.
공공기관 및 민간 기업의 용역 제안서를 작성하는 데 풍부한 경험이 있습니다.
제안서는 명확하고 설득력 있으며, 발주처의 요구사항을 정확히 반영해야 합니다.
한국어로 작성하며, 공공기관 제안서 형식과 관행을 따릅니다.
수치 데이터는 반드시 확인하여, 근거가 있는 자료만 활용해야 합니다. 출처가 불분명하거나 검증되지 않은 수치는 사용하지 마세요."""

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
    "budget": "예산 (명시된 경우, 없으면 null)",
    "requirements": ["주요 요구사항 목록"],
    "evaluation_criteria": ["평가 기준 목록 (배점 포함 시 함께 기재)"],
    "table_of_contents": ["RFP에 명시된 제안서 목차 항목 (없으면 빈 배열)"]
}}"""


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

async def parse_rfp_bytes(content: bytes, file_type: str = "pdf") -> str:
    """바이트 데이터에서 텍스트 추출.

    Args:
        content: 파일 바이트 데이터
        file_type: 파일 타입 (pdf, hwp, hwpx, docx)

    Returns:
        추출된 텍스트. 실패 시 빈 문자열.
    """
    import tempfile

    if not content:
        return ""

    suffix = f".{file_type}" if not file_type.startswith(".") else file_type
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        from app.utils.file_utils import extract_text_from_file
        return extract_text_from_file(tmp_path)
    except Exception:
        return ""
    finally:
        tmp_path.unlink(missing_ok=True)


async def parse_rfp_from_url(url: str, file_type: str = "pdf") -> str:
    """URL에서 파일을 다운로드하여 텍스트 추출.

    Args:
        url: 첨부파일 다운로드 URL
        file_type: 파일 타입 (pdf, hwp, hwpx, docx)

    Returns:
        추출된 텍스트. 실패 시 빈 문자열.
    """
    import tempfile
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status != 200:
                return ""
            content_bytes = await resp.read()

    if not content_bytes:
        return ""

    suffix = f".{file_type}" if not file_type.startswith(".") else file_type
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content_bytes)
        tmp_path = Path(tmp.name)

    try:
        from app.utils.file_utils import extract_text_from_file
        return extract_text_from_file(tmp_path)
    except Exception:
        return ""
    finally:
        tmp_path.unlink(missing_ok=True)


async def download_file_from_url(url: str, timeout: int = 30) -> tuple[bytes, str]:
    """URL에서 파일 바이트 다운로드.

    Returns:
        (file_bytes, content_type) 튜플. 실패 시 (b"", "").
    """
    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status != 200:
                    return b"", ""
                content_type = resp.headers.get("Content-Type", "application/octet-stream")
                return await resp.read(), content_type
    except Exception:
        return b"", ""


async def parse_rfp_text(content: str) -> RFPData:
    from app.utils import create_anthropic_client, extract_json_from_response
    client = create_anthropic_client(async_client=True)
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": RFP_ANALYSIS_PROMPT.format(rfp_text=content[:10000]),
        }],
    )
    data = extract_json_from_response(response.content[0].text)
    return RFPData(raw_text=content, **data)
