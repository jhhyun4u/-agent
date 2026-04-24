"""공공입찰 제안서 HWPX 생성 모듈 (python-hwpx v2.5 기반)

샘플 기반 표준 서식:
  - 페이지: A4 (210×297mm), 여백 좌우 20mm / 상하 15mm
  - 본문: 10pt 맑은 고딕
  - 내용 기호(□ ◦ -): 11pt 휴먼명조
  - 소제목(1. 2.): 12pt 맑은 고딕 bold
  - 장제목(Ⅰ. Ⅱ.): 14pt 맑은 고딕 bold
  - 표지 제목: 22pt HY헤드라인M
"""

import asyncio
import logging
import xml.etree.ElementTree as _ET_orig
from copy import deepcopy
from pathlib import Path

from hwpx import HwpxDocument
from lxml import etree as _LET  # type: ignore
from lxml.etree import _Element as _LxmlElement  # type: ignore

logger = logging.getLogger(__name__)

_HH_NS = "http://www.hancom.co.kr/hwpml/2011/head"
_HH = f"{{{_HH_NS}}}"

# 공공입찰 제안서 표준 폰트 (추가 주입)
# 기본 fontface: 0=함초롬돋움, 1=함초롬바탕
# 주입 후:       2=맑은 고딕, 3=휴먼명조, 4=HY헤드라인M
_INJECT_FONTS = [
    ("맑은 고딕",     "TTF"),  # idx 2
    ("휴먼명조",      "TTF"),  # idx 3
    ("HY헤드라인M",  "TTF"),  # idx 4
]
_FONT_MALGUN  = 2  # 맑은 고딕 index
_FONT_HUMAN   = 3  # 휴먼명조 index
_FONT_HEADLINE = 4  # HY헤드라인M index

# charPr 스타일 정의 (height = 1/10pt 단위)
_STYLE_DEFS = {
    "body":         {"height": "1200", "font_idx": _FONT_MALGUN,   "bold": False},  # 12pt 맑은 고딕
    "content":      {"height": "1200", "font_idx": _FONT_HUMAN,    "bold": False},  # 12pt 휴먼명조
    "table":        {"height": "1000", "font_idx": _FONT_MALGUN,   "bold": False},  # 10pt 맑은 고딕
    "section":      {"height": "1200", "font_idx": _FONT_MALGUN,   "bold": True},   # 12pt 맑은 고딕 bold
    "chapter":      {"height": "1400", "font_idx": _FONT_MALGUN,   "bold": True},   # 14pt 맑은 고딕 bold
    "cover_title":  {"height": "2200", "font_idx": _FONT_HEADLINE, "bold": False},  # 22pt HY헤드라인M
    "cover_name":   {"height": "1400", "font_idx": _FONT_MALGUN,   "bold": True},   # 14pt 맑은 고딕 bold
}
_STYLE_ORDER = ["body", "content", "table", "section", "chapter", "cover_title", "cover_name"]

# 빌드 중 활성 스타일 ID (build_hwpx 내에서 설정)
_S: dict[str, str] = {}


# ---------------------------------------------------------------------------
# 라이브러리 패치
# ---------------------------------------------------------------------------

def _patch_hwpx_library() -> None:
    """python-hwpx v2.5 lxml 호환성 패치.

    ensure_run_style 내 modifier 클로저가 lxml._Element에 stdlib ET.SubElement를
    호출해 TypeError 발생하는 문제를 수정한다.
    """
    import hwpx.oxml.document as _doc

    class _ETProxy:
        """xml.etree.ElementTree proxy — lxml element에 SubElement 호출 시 LET로 위임"""

        def __getattr__(self, name: str):
            return getattr(_ET_orig, name)

        @staticmethod
        def SubElement(parent, tag, attrib=None, **extra):
            if isinstance(parent, _LxmlElement):
                attrs = dict(attrib or {})
                attrs.update(extra)
                return _LET.SubElement(parent, tag, attrs)
            return _ET_orig.SubElement(parent, tag, attrib or {}, **extra)

    _doc.ET = _ETProxy()


_patch_hwpx_library()


# ---------------------------------------------------------------------------
# 폰트 & 스타일 주입
# ---------------------------------------------------------------------------

def _inject_fonts(header_root: _LxmlElement) -> None:
    """모든 fontface 언어 그룹에 표준 폰트 추가"""
    for ff_el in header_root.iter(f"{_HH}fontface"):
        existing_faces = {f.get("face", "") for f in ff_el}
        existing_ids = {int(f.get("id", 0)) for f in ff_el if f.get("id", "").isdigit()}
        max_id = max(existing_ids, default=-1)

        for font_name, font_type in _INJECT_FONTS:
            if font_name not in existing_faces:
                max_id += 1
                f_el = _LET.SubElement(ff_el, f"{_HH}font")
                f_el.set("id", str(max_id))
                f_el.set("face", font_name)
                f_el.set("type", font_type)
                f_el.set("isEmbedded", "0")

        ff_el.set("fontCnt", str(len(ff_el)))


def _inject_char_styles(header_root: _LxmlElement) -> dict[str, str]:
    """커스텀 charPr를 header에 주입하고 style_name → id 매핑 반환"""
    char_props = header_root.find(f".//{_HH}charProperties")
    if char_props is None:
        raise RuntimeError("charProperties를 header에서 찾을 수 없음")

    # 기존 id=0 을 base로 복사
    base_cp = next(
        (cp for cp in char_props if cp.get("id") == "0"),
        next(iter(char_props), None),
    )
    if base_cp is None:
        raise RuntimeError("base charPr를 찾을 수 없음")

    existing_ids = {
        int(cp.get("id", 0))
        for cp in char_props
        if cp.get("id", "").lstrip("-").isdigit()
    }
    next_id = max(existing_ids, default=-1) + 1

    style_ids: dict[str, str] = {}
    for style_name in _STYLE_ORDER:
        defn = _STYLE_DEFS[style_name]

        new_cp = deepcopy(base_cp)
        new_cp.set("id", str(next_id))
        new_cp.set("height", defn["height"])
        new_cp.set("textColor", "#000000")

        # fontRef 모든 언어를 동일 폰트로 설정
        fontref = new_cp.find(f"{_HH}fontRef")
        if fontref is not None:
            idx = str(defn["font_idx"])
            for attr in ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user"):
                fontref.set(attr, idx)

        # bold 처리
        bold_el = new_cp.find(f"{_HH}bold")
        if defn["bold"]:
            if bold_el is None:
                _LET.SubElement(new_cp, f"{_HH}bold")
        else:
            if bold_el is not None:
                new_cp.remove(bold_el)

        char_props.append(new_cp)
        style_ids[style_name] = str(next_id)
        next_id += 1

    all_cp_count = len(list(char_props.findall(f"{_HH}charPr")))
    char_props.set("itemCnt", str(all_cp_count))
    return style_ids


def _setup_styles(doc: HwpxDocument) -> dict[str, str]:
    """문서 header에 폰트·스타일 주입 후 style_name → charPrID 반환"""
    header = doc.headers[0]
    root = header._element
    _inject_fonts(root)
    style_ids = _inject_char_styles(root)
    header.mark_dirty()
    return style_ids


# ---------------------------------------------------------------------------
# 섹션 구조 매핑
# ---------------------------------------------------------------------------

_CHAPTER_MAP = {
    "Ⅰ. 제안개요":    ["project_overview", "understanding", "approach"],
    "Ⅱ. 제안업체 일반": ["team_composition"],
    "Ⅲ. 사업 수행부문": ["methodology"],
    "Ⅳ. 사업관리방안": ["schedule", "expected_outcomes"],
}

_SECTION_TITLES = {
    "project_overview": "1. 제안목적 및 배경",
    "understanding":    "2. 제안범위",
    "approach":         "3. 추진전략",
    "team_composition": "1. 일반현황 및 조직",
    "methodology":      "1. 사업수행 세부계획",
    "schedule":         "1. 추진일정",
    "expected_outcomes":"2. 기대효과",
}


# ---------------------------------------------------------------------------
# 문단 헬퍼
# ---------------------------------------------------------------------------

def _add_empty(doc: HwpxDocument, count: int = 1) -> None:
    """빈 단락 추가 (여백용)"""
    for _ in range(count):
        doc.add_paragraph("", char_pr_id_ref=_S.get("body", "0"))


def _add_content_paragraph(doc: HwpxDocument, line: str) -> None:
    """본문 한 줄을 기호 체계에 맞게 단락으로 추가"""
    stripped = line.strip()
    if not stripped:
        _add_empty(doc)
        return

    # 기호별 스타일 분기
    if stripped.startswith("□"):
        # □ 대분류 — 11pt 휴먼명조
        para = doc.add_paragraph("", char_pr_id_ref=_S.get("content", "0"), include_run=False)
        para.add_run("□ ", char_pr_id_ref=_S.get("content", "0"))
        para.add_run(stripped[1:].strip(), char_pr_id_ref=_S.get("content", "0"))

    elif stripped.startswith("❍") or stripped.startswith("○"):
        # ❍ 중분류 — 11pt 휴먼명조
        sym = stripped[0]
        para = doc.add_paragraph("", char_pr_id_ref=_S.get("content", "0"), include_run=False)
        para.add_run(f"  {sym} ", char_pr_id_ref=_S.get("content", "0"))
        para.add_run(stripped[1:].strip(), char_pr_id_ref=_S.get("content", "0"))

    elif stripped.startswith("☞"):
        # ☞ 후속과제 — 11pt 휴먼명조
        para = doc.add_paragraph("", char_pr_id_ref=_S.get("content", "0"), include_run=False)
        para.add_run("  ☞ ", char_pr_id_ref=_S.get("content", "0"))
        para.add_run(stripped[1:].strip(), char_pr_id_ref=_S.get("content", "0"))

    elif stripped.startswith("【") and "】" in stripped:
        # 【 】 핵심 강조 — 12pt 맑은 고딕 bold
        doc.add_paragraph(stripped, char_pr_id_ref=_S.get("section", "0"))

    elif stripped.startswith("(근거:") or stripped.startswith("(출처:"):
        # 법령 출처 — 10pt 맑은 고딕, 들여쓰기
        doc.add_paragraph("    " + stripped, char_pr_id_ref=_S.get("body", "0"))

    elif stripped.startswith("- ") or stripped.startswith("\u00ad"):
        # - 소분류 — 11pt 휴먼명조
        para = doc.add_paragraph("", char_pr_id_ref=_S.get("content", "0"), include_run=False)
        para.add_run("    - ", char_pr_id_ref=_S.get("content", "0"))
        para.add_run(stripped.lstrip("-\u00ad").strip(), char_pr_id_ref=_S.get("content", "0"))

    elif len(stripped) > 2 and stripped[0].isdigit() and stripped[1] == ".":
        # 숫자 목록 (1. 2. 등) — 12pt 맑은 고딕 bold
        doc.add_paragraph(stripped, char_pr_id_ref=_S.get("section", "0"))

    else:
        # 일반 텍스트 — 10pt 맑은 고딕
        doc.add_paragraph(stripped, char_pr_id_ref=_S.get("body", "0"))


# ---------------------------------------------------------------------------
# 표지
# ---------------------------------------------------------------------------

def _add_cover(doc: HwpxDocument, project_name: str, metadata: dict) -> None:
    """표지 페이지 생성"""
    _add_empty(doc, 6)

    # 제목 "제   안   서"
    doc.add_paragraph("제   안   서", char_pr_id_ref=_S.get("cover_title", "0"))

    _add_empty(doc, 3)

    # 사업명
    doc.add_paragraph(project_name, char_pr_id_ref=_S.get("cover_name", "0"))

    _add_empty(doc, 1)

    # 입찰공고번호
    bid_number = metadata.get("bid_notice_number", "")
    if bid_number:
        doc.add_paragraph(bid_number, char_pr_id_ref=_S.get("body", "0"))

    _add_empty(doc, 4)

    # 제출일
    submit_date = metadata.get("submit_date", "")
    if submit_date:
        doc.add_paragraph(submit_date, char_pr_id_ref=_S.get("body", "0"))

    _add_empty(doc, 1)

    # 발주처
    client_name = metadata.get("client_name", "")
    if client_name:
        doc.add_paragraph(client_name, char_pr_id_ref=_S.get("body", "0"))

    _add_empty(doc, 1)

    # 제안업체
    proposer = metadata.get("proposer_name", "")
    if proposer:
        doc.add_paragraph(proposer, char_pr_id_ref=_S.get("cover_name", "0"))

    _add_empty(doc, 4)


# ---------------------------------------------------------------------------
# 평가항목 참조표
# ---------------------------------------------------------------------------

def _add_evaluation_table(doc: HwpxDocument, metadata: dict) -> None:
    """평가항목 참조표 섹션 추가"""
    doc.add_paragraph("[ 평가항목 참조표 ]", char_pr_id_ref=_S.get("section", "0"))
    _add_empty(doc)

    evaluation_weights = metadata.get("evaluation_weights", {})

    try:
        item_count = max(len(evaluation_weights), 3)
        rows = item_count + 3
        table = doc.add_table(rows=rows, cols=5)

        headers = ["구분", "평가항목", "심사항목", "배점", "해당 페이지"]
        for col_idx, header_text in enumerate(headers):
            cell = table.rows[0].cells[col_idx]
            cell_para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
            cell_para.add_run(header_text, char_pr_id_ref=_S.get("table", "0"))

        row_idx = 1
        total_score = 0
        for weight_name, weight_val in list(evaluation_weights.items())[:item_count]:
            score = int(weight_val) if str(weight_val).isdigit() else 0
            total_score += score
            for col_idx, text in enumerate(["정성평가", weight_name, "", str(score), ""]):
                cell = table.rows[row_idx].cells[col_idx]
                cell_para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
                cell_para.add_run(text, char_pr_id_ref=_S.get("table", "0"))
            row_idx += 1

        while row_idx < rows - 2:
            row_idx += 1

        price_row = rows - 2
        price_score = 100 - total_score if total_score < 100 else 20
        for col_idx, text in enumerate(["가격평가", "입찰가격", "평점산식에 의한 평가", str(price_score), ""]):
            cell = table.rows[price_row].cells[col_idx]
            cell_para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
            cell_para.add_run(text, char_pr_id_ref=_S.get("table", "0"))

        total_row = rows - 1
        for col_idx, text in enumerate(["합계", "", "", "100", ""]):
            cell = table.rows[total_row].cells[col_idx]
            cell_para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
            cp_id = _S.get("section", "0") if col_idx == 3 else _S.get("table", "0")
            cell_para.add_run(text, char_pr_id_ref=cp_id)

    except Exception as e:
        logger.warning(f"평가항목 참조표 테이블 생성 실패, 텍스트 대체: {e}")
        doc.add_paragraph("구분 | 평가항목 | 심사항목 | 배점 | 해당 페이지",
                          char_pr_id_ref=_S.get("body", "0"))
        doc.add_paragraph("정성평가 | 사업수행계획서 | — | 80 | —",
                          char_pr_id_ref=_S.get("body", "0"))
        doc.add_paragraph("가격평가 | 입찰가격 | 평점산식 | 20 | —",
                          char_pr_id_ref=_S.get("body", "0"))
        doc.add_paragraph("합계 | | | 100 | ",
                          char_pr_id_ref=_S.get("body", "0"))

    _add_empty(doc, 2)


# ---------------------------------------------------------------------------
# 목차
# ---------------------------------------------------------------------------

def _add_toc(doc: HwpxDocument) -> None:
    """목차 페이지 생성"""
    doc.add_paragraph("목   차", char_pr_id_ref=_S.get("chapter", "0"))
    _add_empty(doc)

    toc_items = [
        ("Ⅰ. 제안개요",           True),
        ("  1. 제안목적 및 배경",  False),
        ("  2. 제안범위",          False),
        ("  3. 추진전략",          False),
        ("Ⅱ. 제안업체 일반",       True),
        ("  1. 일반현황 및 조직",  False),
        ("Ⅲ. 사업 수행부문",       True),
        ("  1. 사업수행 세부계획", False),
        ("Ⅳ. 사업관리방안",        True),
        ("  1. 추진일정",          False),
        ("  2. 기대효과",          False),
    ]

    for item_text, is_chapter in toc_items:
        cp_id = _S.get("chapter", "0") if is_chapter else _S.get("body", "0")
        doc.add_paragraph(item_text, char_pr_id_ref=cp_id)

    _add_empty(doc, 2)


# ---------------------------------------------------------------------------
# 본문
# ---------------------------------------------------------------------------

def _add_body(doc: HwpxDocument, sections: dict) -> None:
    """본문 4개 장(章) 생성"""
    for chapter_title, section_keys in _CHAPTER_MAP.items():
        _add_empty(doc)
        doc.add_paragraph(chapter_title, char_pr_id_ref=_S.get("chapter", "0"))
        _add_empty(doc)

        for key in section_keys:
            content = sections.get(key, "")
            if not content:
                for k, v in sections.items():
                    if key.replace("_", " ").lower() in k.lower() or k.lower() in key.lower():
                        content = v
                        break

            if not content:
                continue

            section_title = _SECTION_TITLES.get(key, key.replace("_", " ").title())
            doc.add_paragraph(section_title, char_pr_id_ref=_S.get("section", "0"))
            _add_empty(doc)

            for line in content.split("\n"):
                _add_content_paragraph(doc, line)

            _add_empty(doc)

    # 매핑 외 추가 섹션 → 부록
    mapped_keys = {k for keys in _CHAPTER_MAP.values() for k in keys}
    extra_sections = {k: v for k, v in sections.items() if k not in mapped_keys}
    if extra_sections:
        _add_empty(doc)
        doc.add_paragraph("부록", char_pr_id_ref=_S.get("chapter", "0"))
        _add_empty(doc)
        for key, content in extra_sections.items():
            if not content:
                continue
            doc.add_paragraph(key.replace("_", " ").title(),
                              char_pr_id_ref=_S.get("section", "0"))
            _add_empty(doc)
            for line in content.split("\n"):
                _add_content_paragraph(doc, line)
            _add_empty(doc)


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def build_hwpx(
    sections: dict,
    output_path: Path,
    project_name: str = "용역 제안서",
    metadata: dict | None = None,
) -> Path:
    """HWPX 제안서 생성 (동기)

    Args:
        sections: Phase4Artifact.sections dict
        output_path: 저장 경로 (.hwpx)
        project_name: 사업명 (표지 제목)
        metadata: 부가 정보 dict
            - client_name: 발주처
            - proposer_name: 제안업체명
            - submit_date: 제출일 (예: "2026. 3.")
            - bid_notice_number: 입찰공고번호
            - evaluation_weights: dict (평가항목 배점)

    Returns:
        생성된 파일 경로
    """
    global _S
    metadata = metadata or {}
    doc = HwpxDocument.new()

    # 폰트·스타일 주입
    _S = _setup_styles(doc)
    logger.debug(f"스타일 ID 할당: {_S}")

    _add_cover(doc, project_name, metadata)
    _add_evaluation_table(doc, metadata)
    _add_toc(doc)
    _add_body(doc, sections)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save_to_path(str(output_path))
    logger.info(f"HWPX 생성 완료: {output_path}")
    return output_path


async def build_hwpx_async(
    sections: dict,
    output_path: Path,
    project_name: str = "용역 제안서",
    metadata: dict | None = None,
) -> Path:
    """build_hwpx의 비동기 래퍼 (asyncio.to_thread 사용)"""
    return await asyncio.to_thread(build_hwpx, sections, output_path, project_name, metadata)
