"""HWPX 레퍼런스 대비 페이지 드리프트 위험 검사.

원본: Canine89/hwpxskill/scripts/page_guard.py
서비스 모듈로 래핑 — CLI argparse 제거, 함수 API만 노출.

검사 항목:
- 문단 수 / 표 수 / 표 구조(rowCnt, colCnt, width, height) 동일성
- 명시적 pageBreak / columnBreak 수 동일성
- 전체 텍스트 길이 편차(기본 15%) 한도
- 문단별 텍스트 길이 급변(기본 25%) 감지
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, asdict
from io import BytesIO
from pathlib import Path

from lxml import etree

NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
}


@dataclass
class PageMetrics:
    paragraph_count: int
    page_break_count: int
    column_break_count: int
    table_count: int
    table_shapes: list[tuple[str, str, str, str, str, str]]
    text_char_total: int
    text_char_total_nospace: int
    paragraph_text_lengths: list[int]

    def to_dict(self) -> dict:
        return asdict(self)


def _read_section_xml_bytes(hwpx_path: Path) -> bytes:
    with zipfile.ZipFile(hwpx_path, "r") as zf:
        return zf.read("Contents/section0.xml")


def _text_of_t_node(t_node: etree._Element) -> str:
    return "".join(t_node.itertext())


def collect_metrics(hwpx_path: str | Path) -> PageMetrics:
    """HWPX 파일에서 페이지 구조 메트릭 수집."""
    section_bytes = _read_section_xml_bytes(Path(hwpx_path))
    root = etree.parse(BytesIO(section_bytes)).getroot()

    paragraphs = root.xpath(".//hs:sec/hp:p", namespaces=NS)
    if not paragraphs:
        paragraphs = root.xpath(".//hp:p", namespaces=NS)

    page_break_count = sum(1 for p in paragraphs if p.get("pageBreak") == "1")
    column_break_count = sum(1 for p in paragraphs if p.get("columnBreak") == "1")

    tables = root.xpath(".//hp:tbl", namespaces=NS)
    table_shapes: list[tuple[str, str, str, str, str, str]] = []
    for t in tables:
        sz = t.find("hp:sz", namespaces=NS)
        width = sz.get("width", "") if sz is not None else ""
        height = sz.get("height", "") if sz is not None else ""
        table_shapes.append((
            t.get("rowCnt", ""),
            t.get("colCnt", ""),
            width,
            height,
            t.get("repeatHeader", ""),
            t.get("pageBreak", ""),
        ))

    t_nodes = root.xpath(".//hp:t", namespaces=NS)
    text_char_total = 0
    text_char_total_nospace = 0
    for t in t_nodes:
        s = _text_of_t_node(t)
        text_char_total += len(s)
        text_char_total_nospace += len("".join(s.split()))

    paragraph_text_lengths: list[int] = []
    for p in paragraphs:
        plen = 0
        for t in p.xpath(".//hp:t", namespaces=NS):
            plen += len(_text_of_t_node(t))
        paragraph_text_lengths.append(plen)

    return PageMetrics(
        paragraph_count=len(paragraphs),
        page_break_count=page_break_count,
        column_break_count=column_break_count,
        table_count=len(tables),
        table_shapes=table_shapes,
        text_char_total=text_char_total,
        text_char_total_nospace=text_char_total_nospace,
        paragraph_text_lengths=paragraph_text_lengths,
    )


def _ratio_delta(a: int, b: int) -> float:
    base = max(a, 1)
    return abs(b - a) / base


def check_page_drift(
    reference_path: str | Path,
    output_path: str | Path,
    max_text_delta_ratio: float = 0.15,
    max_paragraph_delta_ratio: float = 0.25,
) -> list[str]:
    """레퍼런스 HWPX 대비 출력 HWPX의 페이지 드리프트 위험 검사.

    Returns:
        빈 리스트면 통과(PASS), 문자열 리스트면 경고 사항.
    """
    ref = collect_metrics(reference_path)
    out = collect_metrics(output_path)

    errors: list[str] = []

    if ref.paragraph_count != out.paragraph_count:
        errors.append(
            f"문단 수 불일치: ref={ref.paragraph_count}, out={out.paragraph_count}"
        )
    if ref.page_break_count != out.page_break_count:
        errors.append(
            f"명시적 pageBreak 수 불일치: ref={ref.page_break_count}, out={out.page_break_count}"
        )
    if ref.column_break_count != out.column_break_count:
        errors.append(
            f"명시적 columnBreak 수 불일치: ref={ref.column_break_count}, out={out.column_break_count}"
        )
    if ref.table_count != out.table_count:
        errors.append(f"표 수 불일치: ref={ref.table_count}, out={out.table_count}")
    if ref.table_shapes != out.table_shapes:
        errors.append("표 구조(rowCnt/colCnt/width/height/pageBreak) 불일치")

    td = _ratio_delta(ref.text_char_total_nospace, out.text_char_total_nospace)
    if td > max_text_delta_ratio:
        errors.append(
            "전체 텍스트 길이 편차 초과: "
            f"ref={ref.text_char_total_nospace}, out={out.text_char_total_nospace}, "
            f"delta={td:.2%}, limit={max_text_delta_ratio:.2%}"
        )

    if len(ref.paragraph_text_lengths) == len(out.paragraph_text_lengths):
        for idx, (a, b) in enumerate(
            zip(ref.paragraph_text_lengths, out.paragraph_text_lengths), start=1
        ):
            if a == 0 and b == 0:
                continue
            pd = _ratio_delta(a, b)
            if pd > max_paragraph_delta_ratio:
                errors.append(
                    f"{idx}번째 문단 텍스트 길이 편차 초과: "
                    f"ref={a}, out={b}, delta={pd:.2%}, limit={max_paragraph_delta_ratio:.2%}"
                )

    return errors
