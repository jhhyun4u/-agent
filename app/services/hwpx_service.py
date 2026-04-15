"""HWPX 서비스 래퍼 — hwpxskill 기반 통합 API.

고수준 인터페이스:
- analyze_reference: 고객 양식 분석 (스타일/구조 추출)
- build_proposal_hwpx: 제안서 HWPX 생성 (템플릿 기반 + 섹션 XML 생성)
- validate: HWPX 무결성 검증
- check_page_drift: 레퍼런스 대비 쪽수 드리프트 검사
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from lxml import etree  # type: ignore

logger = logging.getLogger(__name__)

# OWPML 네임스페이스
_HP_NS = "http://www.hancom.co.kr/hwpml/2011/paragraph"
_HS_NS = "http://www.hancom.co.kr/hwpml/2011/section"
_HP = f"{{{_HP_NS}}}"
_HS = f"{{{_HS_NS}}}"

# 공공입찰 제안서 표준 폰트 (1/100pt 단위)
_STYLE_DEFS = {
    "chapter":  {"height": "1400", "bold": True},    # 14pt bold — Ⅰ. 제안개요
    "section":  {"height": "1200", "bold": True},     # 12pt bold — 1. 제안목적
    "body":     {"height": "1100", "bold": False},    # 11pt normal — 본문
    "table":    {"height": "1000", "bold": False},    # 10pt normal — 표
    "cover":    {"height": "2200", "bold": True},     # 22pt bold — 표지 제목
}


def analyze_reference(hwpx_path: str | Path) -> dict:
    """고객 양식 HWPX 분석 → 스타일/구조 정보 dict 반환.

    Returns:
        dict with keys: fonts, char_styles, para_styles, page_setup, tables, paragraph_count
    """
    from app.services.hwpx.analyze_template import analyze_template

    analysis = analyze_template(hwpx_path)
    return {
        "fonts": [{"id": f.id, "face": f.face, "lang": f.lang} for f in analysis.fonts],
        "char_styles": [
            {
                "id": s.id, "height_pt": s.height_pt, "font_name": s.font_name,
                "bold": s.bold, "italic": s.italic, "underline": s.underline,
                "text_color": s.text_color,
            }
            for s in analysis.char_styles
        ],
        "para_styles": [
            {
                "id": s.id, "h_align": s.h_align,
                "line_spacing": f"{s.line_spacing_value}{s.line_spacing_type}",
                "heading_type": s.heading_type,
                "margins": s.margins,
            }
            for s in analysis.para_styles
        ],
        "page_setup": {
            "width": analysis.page_setup.width,
            "height": analysis.page_setup.height,
            "body_width": analysis.page_setup.body_width,
            "margins": {
                "left": analysis.page_setup.margin_left,
                "right": analysis.page_setup.margin_right,
                "top": analysis.page_setup.margin_top,
                "bottom": analysis.page_setup.margin_bottom,
            },
        } if analysis.page_setup else None,
        "tables": [
            {
                "id": t.id, "rows": t.rows, "cols": t.cols,
                "width": t.width, "col_widths": t.col_widths,
                "cell_count": len(t.cells),
            }
            for t in analysis.tables
        ],
        "paragraph_count": analysis.paragraph_count,
    }


def _generate_section_xml(sections: list, metadata: dict) -> str:
    """제안서 섹션 데이터를 section0.xml 내용으로 변환.

    OWPML 최소 구조로 XML 생성. charPrIDRef 0(기본 스타일) 사용.
    """
    # OWPML section XML 뼈대
    root = etree.Element(
        f"{_HS}sec",
        nsmap={"hp": _HP_NS, "hs": _HS_NS},
    )

    def _add_paragraph(parent, text: str, char_pr_id: str = "0", para_pr_id: str = "0"):
        """section에 문단 하나 추가."""
        p = etree.SubElement(parent, f"{_HP}p")
        p.set("paraPrIDRef", para_pr_id)
        p.set("styleIDRef", "0")
        run = etree.SubElement(p, f"{_HP}run")
        run.set("charPrIDRef", char_pr_id)
        t = etree.SubElement(run, f"{_HP}t")
        t.text = text
        return p

    def _add_empty(parent, count: int = 1):
        for _ in range(count):
            _add_paragraph(parent, "")

    # ── 표지 ──
    project_name = metadata.get("project_name", "용역 제안서")
    _add_empty(root, 6)
    _add_paragraph(root, "제   안   서")
    _add_empty(root, 3)
    _add_paragraph(root, project_name)
    _add_empty(root, 2)

    bid_number = metadata.get("bid_notice_number", "")
    if bid_number:
        _add_paragraph(root, bid_number)

    submit_date = metadata.get("submit_date", "")
    if submit_date:
        _add_paragraph(root, submit_date)
    _add_empty(root, 2)

    client_name = metadata.get("client_name", "")
    if client_name:
        _add_paragraph(root, client_name)

    proposer = metadata.get("proposer_name", "")
    if proposer:
        _add_paragraph(root, proposer)
    _add_empty(root, 4)

    # ── 목차 ──
    _add_paragraph(root, "목   차")
    _add_empty(root)

    for i, s in enumerate(sections, 1):
        s_dict = s.model_dump() if hasattr(s, "model_dump") else (s if isinstance(s, dict) else {})
        title = s_dict.get("title", s_dict.get("section_id", f"섹션 {i}"))
        _add_paragraph(root, f"  {i}. {title}")

    _add_empty(root, 2)

    # ── 본문 ──
    for i, s in enumerate(sections, 1):
        s_dict = s.model_dump() if hasattr(s, "model_dump") else (s if isinstance(s, dict) else {})
        title = s_dict.get("title", s_dict.get("section_id", f"섹션 {i}"))
        content = s_dict.get("content", "")

        _add_empty(root)
        _add_paragraph(root, f"{i}. {title}")
        _add_empty(root)

        if content:
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped:
                    _add_paragraph(root, stripped)
                else:
                    _add_empty(root)

        _add_empty(root)

    # secPr (페이지 설정 — A4 기본)
    first_p = root.find(f".//{_HP}p")
    secpr_parent = first_p if first_p is not None else root
    secpr = etree.SubElement(secpr_parent, f"{_HP}secPr")
    pagepr = etree.SubElement(secpr, f"{_HP}pagePr")
    pagepr.set("width", "59528")   # A4 210mm
    pagepr.set("height", "84188")  # A4 297mm
    pagepr.set("landscape", "0")
    margin = etree.SubElement(pagepr, f"{_HP}margin")
    margin.set("left", "5669")    # 20mm
    margin.set("right", "5669")   # 20mm
    margin.set("top", "4252")     # 15mm
    margin.set("bottom", "4252")  # 15mm
    margin.set("header", "4252")
    margin.set("footer", "4252")

    etree.indent(root, space="  ")
    return etree.tostring(root, encoding="unicode", xml_declaration=False)


def build_proposal_hwpx(
    sections: list,
    output_path: str | Path,
    metadata: dict | None = None,
    reference_hwpx: str | Path | None = None,
) -> Path:
    """제안서 HWPX 생성 (동기).

    Args:
        sections: ProposalSection 리스트 (title, content, section_id)
        output_path: 출력 .hwpx 파일 경로
        metadata: 부가 정보 (project_name, client_name, proposer_name, submit_date, bid_notice_number)
        reference_hwpx: 고객 양식 HWPX (있으면 header를 그대로 사용)

    Returns:
        생성된 HWPX 파일 경로
    """
    from app.services.hwpx.build_hwpx import build_from_template

    metadata = metadata or {}
    output = Path(output_path)

    # section0.xml 동적 생성 → 임시 파일
    section_xml_content = _generate_section_xml(sections, metadata)
    tmp_section = Path(tempfile.gettempdir()) / "tenopa_hwpx_section0.xml"
    tmp_section.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n{section_xml_content}',
        encoding="utf-8",
    )

    header_override = None
    if reference_hwpx:
        # 고객 양식의 header.xml 추출하여 오버라이드 (서식 보존)
        from app.services.hwpx.analyze_template import extract_header_xml
        tmp_header = Path(tempfile.gettempdir()) / "tenopa_hwpx_header.xml"
        extract_header_xml(reference_hwpx, tmp_header)
        header_override = tmp_header

    result = build_from_template(
        output_path=output,
        template="proposal",
        header_override=header_override,
        section_override=tmp_section,
        title=metadata.get("project_name", "용역 제안서"),
        creator=metadata.get("proposer_name", "tenopa"),
    )

    # 생성 후 검증
    errors = validate(result)
    if errors:
        logger.warning(f"HWPX 검증 경고: {errors}")

    # 쪽수 가드 (레퍼런스가 있을 때)
    if reference_hwpx:
        drift_warnings = check_page_drift(reference_hwpx, result)
        if drift_warnings:
            logger.warning(f"쪽수 드리프트 경고: {drift_warnings}")

    logger.info(f"HWPX 생성 완료: {result}")
    return result


async def build_proposal_hwpx_async(
    sections: list,
    output_path: str | Path,
    metadata: dict | None = None,
    reference_hwpx: str | Path | None = None,
) -> Path:
    """build_proposal_hwpx의 비동기 래퍼."""
    return await asyncio.to_thread(
        build_proposal_hwpx, sections, output_path, metadata, reference_hwpx,
    )


def validate(hwpx_path: str | Path) -> list[str]:
    """HWPX 무결성 검증. 빈 리스트면 유효."""
    from app.services.hwpx.validate import validate_hwpx
    return validate_hwpx(hwpx_path)


def check_page_drift(
    reference_path: str | Path,
    output_path: str | Path,
    max_text_delta: float = 0.15,
    max_paragraph_delta: float = 0.25,
) -> list[str]:
    """레퍼런스 대비 쪽수 드리프트 검사. 빈 리스트면 통과."""
    from app.services.hwpx.page_guard import check_page_drift as _check
    return _check(reference_path, output_path, max_text_delta, max_paragraph_delta)
