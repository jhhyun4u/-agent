"""HWPX 문서 구조 심층 분석 — 고객 양식 스타일/구조 추출.

원본: Canine89/hwpxskill/scripts/analyze_template.py
서비스 모듈로 래핑 — CLI argparse 제거, 함수 API만 노출.

고객이 제공한 HWPX 양식을 분석하여:
- 폰트 정의 (fontface)
- 글자 스타일 (charPr) — 크기, 폰트, 볼드, 밑줄 등
- 문단 스타일 (paraPr) — 정렬, 행간, 여백 등
- 테두리/배경 (borderFill)
- 페이지 설정 (여백, 크기)
- 표 구조 (행×열, 셀 병합, 너비)
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree  # type: ignore

NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
}


@dataclass
class FontInfo:
    id: str
    face: str
    lang: str


@dataclass
class CharStyle:
    id: str
    height_pt: float
    font_name: str
    font_id: str
    text_color: str
    bold: bool
    italic: bool
    underline: str | None
    spacing: int
    border_fill_id: str


@dataclass
class ParaStyle:
    id: str
    h_align: str
    line_spacing_value: str
    line_spacing_type: str
    heading_type: str
    heading_level: str
    margins: dict[str, str]
    border_fill_id: str


@dataclass
class PageSetup:
    width: str
    height: str
    landscape: str
    margin_left: str
    margin_right: str
    margin_top: str
    margin_bottom: str
    margin_header: str
    margin_footer: str
    body_width: int


@dataclass
class TableInfo:
    id: str
    rows: int
    cols: int
    width: str
    height: str
    col_widths: list[str]
    repeat_header: str
    cells: list[dict]


@dataclass
class TemplateAnalysis:
    """양식 분석 결과."""
    fonts: list[FontInfo] = field(default_factory=list)
    char_styles: list[CharStyle] = field(default_factory=list)
    para_styles: list[ParaStyle] = field(default_factory=list)
    page_setup: PageSetup | None = None
    tables: list[TableInfo] = field(default_factory=list)
    paragraph_count: int = 0
    header_xml_path: str | None = None
    section_xml_path: str | None = None


def _get_text(el) -> str:
    texts = []
    for t in el.findall(".//hp:t", NS):
        if t.text:
            texts.append(t.text)
    return "".join(texts)


def _analyze_fonts(header_root) -> tuple[list[FontInfo], dict]:
    """폰트 정의 분석."""
    fonts: list[FontInfo] = []
    font_map: dict[tuple[str, str], str] = {}

    for fontface in header_root.findall(".//hh:fontface", NS):
        lang = fontface.get("lang", "?")
        for font in fontface.findall("hh:font", NS):
            fid = font.get("id", "")
            face = font.get("face", "")
            font_map[(lang, fid)] = face
            if lang == "HANGUL":
                fonts.append(FontInfo(id=fid, face=face, lang=lang))

    return fonts, font_map


def _analyze_char_styles(header_root, font_map: dict) -> list[CharStyle]:
    """글자 스타일 분석."""
    styles: list[CharStyle] = []

    for cp in header_root.findall(".//hh:charPr", NS):
        cid = cp.get("id", "")
        height = int(cp.get("height", "0"))
        pt = height / 100
        color = cp.get("textColor", "#000000")
        bfref = cp.get("borderFillIDRef", "0")

        fontref = cp.find("hh:fontRef", NS)
        font_id = fontref.get("hangul", "0") if fontref is not None else "0"
        font_name = font_map.get(("HANGUL", font_id), f"font{font_id}")

        spacing_el = cp.find("hh:spacing", NS)
        spacing = int(spacing_el.get("hangul", "0")) if spacing_el is not None else 0

        bold = cp.find("hh:bold", NS) is not None
        italic = cp.find("hh:italic", NS) is not None
        ul = cp.find("hh:underline", NS)
        underline = None
        if ul is not None and ul.get("type", "NONE") != "NONE":
            underline = ul.get("shape", "SOLID")

        styles.append(CharStyle(
            id=cid,
            height_pt=pt,
            font_name=font_name,
            font_id=font_id,
            text_color=color,
            bold=bold,
            italic=italic,
            underline=underline,
            spacing=spacing,
            border_fill_id=bfref,
        ))

    return styles


def _analyze_para_styles(header_root) -> list[ParaStyle]:
    """문단 스타일 분석."""
    styles: list[ParaStyle] = []

    for pp in header_root.findall(".//hh:paraPr", NS):
        pid = pp.get("id", "")

        align = pp.find("hh:align", NS)
        h_align = align.get("horizontal", "?") if align is not None else "?"

        heading = pp.find("hh:heading", NS)
        h_type = heading.get("type", "NONE") if heading is not None else "NONE"
        h_level = heading.get("level", "0") if heading is not None else "0"

        ls = pp.find(".//hh:lineSpacing", NS)
        ls_val = ls.get("value", "?") if ls is not None else "?"
        ls_type = ls.get("type", "PERCENT") if ls is not None else "?"

        margins: dict[str, str] = {}
        for m_name in ["intent", "left", "right", "prev", "next"]:
            m = pp.find(f".//hc:{m_name}", NS)
            if m is not None:
                val = m.get("value", "0")
                if val != "0":
                    margins[m_name] = val

        border = pp.find("hh:border", NS)
        bf_ref = border.get("borderFillIDRef", "2") if border is not None else "2"

        styles.append(ParaStyle(
            id=pid,
            h_align=h_align,
            line_spacing_value=ls_val,
            line_spacing_type=ls_type,
            heading_type=h_type,
            heading_level=h_level,
            margins=margins,
            border_fill_id=bf_ref,
        ))

    return styles


def _analyze_page_setup(section_root) -> PageSetup | None:
    """페이지 설정 분석."""
    secpr = section_root.find(".//hp:secPr", NS)
    if secpr is None:
        return None

    pagepr = secpr.find("hp:pagePr", NS)
    if pagepr is None:
        return None

    w = pagepr.get("width", "0")
    h = pagepr.get("height", "0")
    landscape = pagepr.get("landscape", "0")

    margin = pagepr.find("hp:margin", NS)
    if margin is None:
        return PageSetup(w, h, landscape, "0", "0", "0", "0", "0", "0", int(w))

    ml = margin.get("left", "0")
    mr = margin.get("right", "0")
    mt = margin.get("top", "0")
    mb = margin.get("bottom", "0")
    mh = margin.get("header", "0")
    mf = margin.get("footer", "0")
    body_width = int(w) - int(ml) - int(mr)

    return PageSetup(
        width=w, height=h, landscape=landscape,
        margin_left=ml, margin_right=mr,
        margin_top=mt, margin_bottom=mb,
        margin_header=mh, margin_footer=mf,
        body_width=body_width,
    )


def _analyze_tables(section_root) -> list[TableInfo]:
    """표 구조 분석."""
    tables: list[TableInfo] = []

    for tbl in section_root.xpath(".//hp:tbl", namespaces=NS):
        tbl_id = tbl.get("id", "?")
        rows = int(tbl.get("rowCnt", "0"))
        cols = int(tbl.get("colCnt", "0"))
        repeat_header = tbl.get("repeatHeader", "0")

        sz = tbl.find("hp:sz", NS)
        width = sz.get("width", "?") if sz is not None else "?"
        height = sz.get("height", "?") if sz is not None else "?"

        col_widths: dict[int, str] = {}
        cells: list[dict] = []

        for tr in tbl.findall("hp:tr", NS):
            for tc in tr.findall("hp:tc", NS):
                addr = tc.find("hp:cellAddr", NS)
                col_idx = int(addr.get("colAddr", "0")) if addr is not None else 0
                row_idx = int(addr.get("rowAddr", "0")) if addr is not None else 0

                span_el = tc.find("hp:cellSpan", NS)
                cs = int(span_el.get("colSpan", "1")) if span_el is not None else 1
                rs = int(span_el.get("rowSpan", "1")) if span_el is not None else 1

                csz = tc.find("hp:cellSz", NS)
                cw = csz.get("width", "?") if csz is not None else "?"

                if cs == 1 and col_idx not in col_widths:
                    col_widths[col_idx] = cw

                # 셀 텍스트 수집
                sublist = tc.find("hp:subList", NS)
                text = ""
                if sublist is not None:
                    for p in sublist.findall("hp:p", NS):
                        text += _get_text(p)

                cells.append({
                    "col": col_idx, "row": row_idx,
                    "col_span": cs, "row_span": rs,
                    "width": cw, "text": text[:100],
                })

        sorted_widths = [col_widths.get(i, "?") for i in range(cols)]
        tables.append(TableInfo(
            id=tbl_id, rows=rows, cols=cols,
            width=width, height=height,
            col_widths=sorted_widths,
            repeat_header=repeat_header,
            cells=cells,
        ))

    return tables


def analyze_template(hwpx_path: str | Path) -> TemplateAnalysis:
    """HWPX 양식 파일을 분석하여 구조 정보 반환.

    Args:
        hwpx_path: 분석할 HWPX 파일 경로

    Returns:
        TemplateAnalysis: 폰트, 스타일, 페이지 설정, 표 구조 등
    """
    path = Path(hwpx_path)
    tmpdir = tempfile.mkdtemp()

    try:
        with zipfile.ZipFile(path, "r") as z:
            z.extractall(tmpdir)

        header_path = Path(tmpdir) / "Contents" / "header.xml"
        section_path = Path(tmpdir) / "Contents" / "section0.xml"

        if not header_path.exists() or not section_path.exists():
            raise FileNotFoundError(
                "Contents/header.xml 또는 Contents/section0.xml 없음"
            )

        header_root = etree.parse(str(header_path)).getroot()
        section_root = etree.parse(str(section_path)).getroot()

        fonts, font_map = _analyze_fonts(header_root)
        char_styles = _analyze_char_styles(header_root, font_map)
        para_styles = _analyze_para_styles(header_root)
        page_setup = _analyze_page_setup(section_root)
        tables = _analyze_tables(section_root)

        # 문단 수 카운트
        paragraphs = section_root.xpath(".//hp:p", namespaces=NS)
        paragraph_count = len(paragraphs)

        return TemplateAnalysis(
            fonts=fonts,
            char_styles=char_styles,
            para_styles=para_styles,
            page_setup=page_setup,
            tables=tables,
            paragraph_count=paragraph_count,
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def extract_header_xml(hwpx_path: str | Path, output_path: str | Path) -> Path:
    """HWPX에서 header.xml 추출."""
    path = Path(hwpx_path)
    out = Path(output_path)
    with zipfile.ZipFile(path, "r") as z:
        data = z.read("Contents/header.xml")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return out


def extract_section_xml(hwpx_path: str | Path, output_path: str | Path) -> Path:
    """HWPX에서 section0.xml 추출."""
    path = Path(hwpx_path)
    out = Path(output_path)
    with zipfile.ZipFile(path, "r") as z:
        data = z.read("Contents/section0.xml")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return out
