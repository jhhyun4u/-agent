"""제안서 템플릿 서비스 — output/output template/ 폴더에서 목차를 추출합니다."""

import json
import logging
import zipfile
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

# 기본 목차 (템플릿 파싱 실패 시 폴백)
DEFAULT_TOC = [
    "사업 개요",
    "사업 이해도",
    "접근 방법론",
    "수행 방법론",
    "추진 일정",
    "투입 인력 및 조직 구성",
    "기대 효과",
    "예산 계획",
]

# 메모리 캐시 (프로세스 생존 기간 동안 유지)
_toc_cache: dict[str, list[str]] = {}


def _read_pdf_text(path: Path) -> str:
    """PDF에서 텍스트를 추출합니다."""
    try:
        import PyPDF2
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pages = []
            for i, page in enumerate(reader.pages):
                if i >= 10:  # 목차는 앞부분에 있으므로 10페이지까지만
                    break
                text = page.extract_text() or ""
                pages.append(text)
        return "\n".join(pages)
    except Exception as e:
        logger.warning(f"PDF 읽기 실패 {path.name}: {e}")
        return ""


def _read_hwpx_text(path: Path) -> str:
    """HWPX(ZIP+XML)에서 텍스트를 추출합니다."""
    try:
        with zipfile.ZipFile(path, "r") as z:
            # HWPX 구조: Contents/section0.xml, Contents/section1.xml, ...
            section_names = sorted([n for n in z.namelist() if "section" in n.lower() and n.endswith(".xml")])
            texts = []
            for name in section_names[:3]:  # 앞부분 3개 섹션만
                with z.open(name) as xmlf:
                    raw = xmlf.read().decode("utf-8", errors="ignore")
                    # XML 태그 제거하고 텍스트만 추출
                    try:
                        root = ET.fromstring(raw)
                        text = " ".join(root.itertext())
                    except ET.ParseError:
                        # 파싱 실패 시 단순 태그 제거
                        import re
                        text = re.sub(r"<[^>]+>", " ", raw)
                    texts.append(text[:5000])
        return "\n".join(texts)
    except Exception as e:
        logger.warning(f"HWPX 읽기 실패 {path.name}: {e}")
        return ""


def _get_template_files() -> list[Path]:
    """템플릿 디렉토리에서 지원 파일 목록을 반환합니다."""
    template_dir = Path(settings.template_dir)
    if not template_dir.exists():
        return []
    files = []
    for ext in (".pdf", ".hwpx", ".hwp"):
        files.extend(template_dir.glob(f"*{ext}"))
    return sorted(files)


async def _extract_toc_with_claude(text: str, filename: str) -> list[str]:
    """Claude를 사용해 문서 텍스트에서 목차를 추출합니다."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    prompt = f"""다음은 용역 제안서 템플릿/샘플 문서의 텍스트입니다.
이 문서의 목차(섹션 제목) 구조를 추출해주세요.

문서명: {filename}

문서 내용 (앞부분):
{text[:4000]}

반드시 아래 JSON 형식으로 응답하세요:
{{
    "toc": ["섹션1 제목", "섹션2 제목", "섹션3 제목", "..."]
}}

- 최상위 섹션 제목만 추출하세요 (하위 섹션 제외)
- 숫자 번호 없이 순수 제목명만 반환하세요 (예: "1. 사업 개요" → "사업 개요")
- 목차를 찾을 수 없으면 빈 배열 반환
"""
    try:
        r = await client.messages.create(
            model=settings.claude_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = r.content[0].text
        # JSON 추출
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            d = json.loads(m.group())
            toc = d.get("toc", [])
            if isinstance(toc, list) and toc:
                return [str(item).strip() for item in toc if item]
    except Exception as e:
        logger.warning(f"Claude TOC 추출 실패: {e}")
    return []


async def get_template_toc(prefer_filename: Optional[str] = None) -> list[str]:
    """
    템플릿 폴더에서 기본 목차를 추출합니다.

    우선순위:
    1. prefer_filename 매칭 파일
    2. PDF 파일 (파싱 용이)
    3. HWPX 파일
    4. 하드코딩 기본값

    캐시된 결과가 있으면 재사용합니다.
    """
    cache_key = prefer_filename or "__default__"
    if cache_key in _toc_cache:
        logger.info(f"템플릿 TOC 캐시 사용: {cache_key}")
        return _toc_cache[cache_key]

    files = _get_template_files()
    if not files:
        logger.info("템플릿 파일 없음 — 기본 목차 사용")
        return DEFAULT_TOC

    # 파일 선택 우선순위
    selected = None
    if prefer_filename:
        for f in files:
            if prefer_filename in f.name:
                selected = f
                break
    if not selected:
        # PDF 우선
        pdfs = [f for f in files if f.suffix == ".pdf"]
        selected = pdfs[0] if pdfs else files[0]

    logger.info(f"템플릿 파일 선택: {selected.name}")

    # 텍스트 추출
    if selected.suffix == ".pdf":
        text = _read_pdf_text(selected)
    else:
        text = _read_hwpx_text(selected)

    if not text.strip():
        logger.warning("텍스트 추출 실패 — 기본 목차 사용")
        return DEFAULT_TOC

    # Claude로 TOC 추출
    toc = await _extract_toc_with_claude(text, selected.name)
    if not toc:
        logger.info("TOC 추출 실패 — 기본 목차 사용")
        toc = DEFAULT_TOC

    _toc_cache[cache_key] = toc
    logger.info(f"템플릿 TOC 추출 완료: {len(toc)}개 섹션")
    return toc


def get_available_templates() -> list[dict]:
    """사용 가능한 템플릿 파일 목록을 반환합니다."""
    files = _get_template_files()
    return [
        {"filename": f.name, "type": f.suffix.lstrip(".").upper(), "path": str(f)}
        for f in files
    ]


def clear_toc_cache():
    """TOC 캐시를 초기화합니다."""
    _toc_cache.clear()
