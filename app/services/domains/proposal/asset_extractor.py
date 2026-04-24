"""회사 자료 → AI 섹션 자동 추출 서비스

PDF/DOCX/TXT 파일에서 텍스트를 추출하고 Claude API를 통해
재사용 가능한 섹션을 자동으로 식별하여 Supabase에 저장합니다.
"""

import json
import logging
from uuid import uuid4

from app.utils import create_anthropic_client
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

# 섹션 추출 시스템 프롬프트
_SYSTEM_PROMPT = "당신은 기업 제안서 전문가입니다. 주어진 문서에서 재사용 가능한 섹션을 추출하세요."

# 섹션 추출 유저 프롬프트 템플릿
_USER_PROMPT_TEMPLATE = """다음 문서에서 제안서에 재사용할 수 있는 섹션들을 추출해주세요.

파일명: {filename}

문서 내용:
{text}

아래 JSON 배열 형식으로만 응답해주세요 (다른 설명 없이):
[
  {{
    "title": "섹션 제목",
    "category": "company_intro|track_record|methodology|organization|schedule|cost|other",
    "content": "마크다운 형식의 섹션 내용"
  }}
]

category는 반드시 다음 중 하나여야 합니다:
- company_intro: 회사 소개, 연혁, 비전
- track_record: 수행 실적, 레퍼런스
- methodology: 방법론, 기술 접근법
- organization: 조직 구성, 인력 계획
- schedule: 일정 계획
- cost: 비용 산출, 가격 제안
- other: 기타

최대 10개 섹션까지만 추출하세요."""

# 허용 카테고리 목록
_VALID_CATEGORIES = frozenset([
    "company_intro", "track_record", "methodology",
    "organization", "schedule", "cost", "other",
])


def _extract_text_from_bytes(file_content: bytes, file_type: str) -> str:
    """파일 바이트에서 텍스트 추출

    Args:
        file_content: 파일 바이트 데이터
        file_type: 파일 유형 ('pdf' | 'docx' | 'txt')

    Returns:
        추출된 텍스트 문자열
    """
    if file_type == "pdf":
        return _extract_text_from_pdf_bytes(file_content)
    elif file_type == "docx":
        return _extract_text_from_docx_bytes(file_content)
    else:
        # txt 및 기타: UTF-8 디코딩
        return file_content.decode("utf-8", errors="ignore")


def _extract_text_from_pdf_bytes(content: bytes) -> str:
    """PDF 바이트에서 텍스트 추출 (PyPDF2 사용)"""
    try:
        import io
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(content))
        pages_text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)
        return "\n".join(pages_text)
    except Exception as exc:
        logger.warning("PDF 텍스트 추출 실패: %s", exc)
        return ""


def _extract_text_from_docx_bytes(content: bytes) -> str:
    """DOCX 바이트에서 텍스트 추출 (python-docx 사용)"""
    try:
        import io
        from docx import Document

        doc = Document(io.BytesIO(content))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception as exc:
        logger.warning("DOCX 텍스트 추출 실패: %s", exc)
        return ""


def _parse_sections_from_response(response_text: str) -> list[dict]:
    """Claude 응답에서 섹션 JSON 파싱

    Args:
        response_text: Claude API 응답 텍스트

    Returns:
        섹션 딕셔너리 목록 (최대 10개)
    """
    try:
        # JSON 코드 블록 추출
        text = response_text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        parsed = json.loads(text.strip())

        if not isinstance(parsed, list):
            logger.warning("Claude 응답이 리스트 형식이 아닙니다.")
            return []

        # 최대 10개 제한 + 유효성 검사
        sections = []
        for item in parsed[:10]:
            if not isinstance(item, dict):
                continue
            title = item.get("title", "").strip()
            category = item.get("category", "other").strip()
            content = item.get("content", "").strip()

            if not title or not content:
                continue

            # 유효하지 않은 카테고리는 other로 대체
            if category not in _VALID_CATEGORIES:
                category = "other"

            sections.append({
                "title": title,
                "category": category,
                "content": content,
            })

        return sections

    except (json.JSONDecodeError, IndexError) as exc:
        logger.warning("섹션 JSON 파싱 실패: %s", exc)
        return []


async def extract_sections_from_asset(
    asset_id: str,
    owner_id: str,
    team_id: str | None,
    file_content: bytes,
    file_type: str,
    filename: str,
) -> list[str]:
    """회사 자료 파일에서 AI를 통해 섹션을 자동 추출하고 Supabase에 저장합니다.

    Args:
        asset_id: 회사 자료 UUID (추출된 섹션의 source_asset_id로 저장)
        owner_id: 소유자 사용자 UUID
        team_id: 팀 UUID (없으면 None)
        file_content: 파일 바이트 데이터
        file_type: 파일 유형 ('pdf' | 'docx' | 'txt')
        filename: 원본 파일명

    Returns:
        생성된 섹션 UUID 목록 (실패 시 빈 리스트)
    """
    # 1. 텍스트 추출
    text = _extract_text_from_bytes(file_content, file_type)
    if not text.strip():
        logger.warning("[asset_extractor] %s: 텍스트 추출 결과가 비어있습니다.", asset_id)
        return []

    # 2. Claude API 호출
    try:
        client = create_anthropic_client(async_client=True)
        user_prompt = _USER_PROMPT_TEMPLATE.format(
            filename=filename,
            text=text[:8000],
        )
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        response_text = response.content[0].text
    except Exception as exc:
        logger.error("[asset_extractor] Claude API 호출 실패 (asset_id=%s): %s", asset_id, exc)
        return []

    # 3. 응답 파싱
    sections = _parse_sections_from_response(response_text)
    if not sections:
        logger.warning("[asset_extractor] %s: 추출된 섹션이 없습니다.", asset_id)
        return []

    # 4. Supabase에 섹션 저장
    section_ids = []
    try:
        supabase = await get_async_client()
        for section in sections:
            section_id = str(uuid4())
            insert_data = {
                "id": section_id,
                "owner_id": owner_id,
                "title": section["title"],
                "category": section["category"],
                "content": section["content"],
                "tags": [],
                "is_public": False,
                "source_asset_id": asset_id,
            }
            if team_id:
                insert_data["team_id"] = team_id

            await supabase.table("sections").insert(insert_data).execute()
            section_ids.append(section_id)

        logger.info(
            "[asset_extractor] %s: %d개 섹션 추출 완료",
            asset_id,
            len(section_ids),
        )
    except Exception as exc:
        logger.error(
            "[asset_extractor] Supabase INSERT 실패 (asset_id=%s): %s",
            asset_id,
            exc,
        )
        # 일부 저장에 성공한 경우 해당 UUID 반환
        # 전체 실패 시 빈 리스트 반환
        if not section_ids:
            return []

    return section_ids
