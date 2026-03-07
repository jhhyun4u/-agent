"""공공입찰 제안서 HWPX 생성 모듈 (python-hwpx v2.5 기반)"""

import asyncio
import logging
from pathlib import Path

from hwpx import HwpxDocument

logger = logging.getLogger(__name__)

# 섹션 키 → 본문 장(章) 매핑
_CHAPTER_MAP = {
    "Ⅰ. 제안개요": ["project_overview", "understanding", "approach"],
    "Ⅱ. 제안업체 일반": ["team_composition"],
    "Ⅲ. 사업 수행부문": ["methodology"],
    "Ⅳ. 사업관리방안": ["schedule", "expected_outcomes"],
}

# 섹션 키 → 소제목 매핑
_SECTION_TITLES = {
    "project_overview": "1. 제안목적 및 배경",
    "understanding": "2. 제안범위",
    "approach": "3. 추진전략",
    "team_composition": "1. 일반현황 및 조직",
    "methodology": "1. 사업수행 세부계획",
    "schedule": "1. 추진일정",
    "expected_outcomes": "2. 기대효과",
}


def _add_empty(doc: HwpxDocument, count: int = 1) -> None:
    """빈 단락 추가 (여백용)"""
    for _ in range(count):
        doc.add_paragraph("")


def _add_cover(doc: HwpxDocument, project_name: str, metadata: dict) -> None:
    """표지 페이지 생성"""
    _add_empty(doc, 6)

    # 제목
    title_para = doc.add_paragraph()
    title_para.add_run("제   안   서", bold=True)

    _add_empty(doc, 3)

    # 사업명
    name_para = doc.add_paragraph()
    name_para.add_run(project_name, bold=True)

    _add_empty(doc, 1)

    # 입찰공고번호 (있을 경우)
    bid_number = metadata.get("bid_notice_number", "")
    if bid_number:
        doc.add_paragraph(bid_number)

    _add_empty(doc, 4)

    # 제출일
    submit_date = metadata.get("submit_date", "")
    if submit_date:
        doc.add_paragraph(submit_date)

    _add_empty(doc, 1)

    # 발주처
    client_name = metadata.get("client_name", "")
    if client_name:
        doc.add_paragraph(client_name)

    _add_empty(doc, 1)

    # 제안업체
    proposer = metadata.get("proposer_name", "")
    if proposer:
        proposer_para = doc.add_paragraph()
        proposer_para.add_run(proposer, bold=True)

    _add_empty(doc, 4)


def _add_evaluation_table(doc: HwpxDocument, metadata: dict) -> None:
    """평가항목 참조표 섹션 추가"""
    # 섹션 제목
    header_para = doc.add_paragraph()
    header_para.add_run("[ 평가항목 참조표 ]", bold=True)

    _add_empty(doc)

    # 평가 가중치 데이터 (있을 경우 활용)
    evaluation_weights = metadata.get("evaluation_weights", {})

    try:
        # 헤더 행 포함 테이블 생성
        # 행 수: 헤더 1 + 항목 수 + 가격평가 1 + 합계 1
        item_count = max(len(evaluation_weights), 3)
        rows = item_count + 3
        table = doc.add_table(rows=rows, cols=5)

        # 헤더 텍스트를 첫 번째 행에 순서대로 추가
        headers = ["구분", "평가항목", "심사항목", "배점", "해당 페이지"]
        for col_idx, header_text in enumerate(headers):
            # 테이블 셀 접근: table.rows[row_idx].cells[col_idx]
            cell = table.rows[0].cells[col_idx]
            cell_para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
            cell_para.add_run(header_text, bold=True)

        # 평가 항목 행 채우기
        row_idx = 1
        total_score = 0
        for weight_name, weight_val in list(evaluation_weights.items())[:item_count]:
            score = int(weight_val) if str(weight_val).isdigit() else 0
            total_score += score
            for col_idx, text in enumerate(["정성평가", weight_name, "", str(score), ""]):
                cell = table.rows[row_idx].cells[col_idx]
                cell_para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
                cell_para.add_run(text)
            row_idx += 1

        # 남은 행 비우기
        while row_idx < rows - 2:
            row_idx += 1

        # 가격평가 행
        price_row = rows - 2
        price_score = 100 - total_score if total_score < 100 else 20
        for col_idx, text in enumerate(["가격평가", "입찰가격", "평점산식에 의한 평가", str(price_score), ""]):
            cell = table.rows[price_row].cells[col_idx]
            cell_para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
            cell_para.add_run(text)

        # 합계 행
        total_row = rows - 1
        for col_idx, text in enumerate(["합계", "", "", "100", ""]):
            cell = table.rows[total_row].cells[col_idx]
            cell_para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
            cell_para.add_run(text, bold=(col_idx == 3))

    except Exception as e:
        logger.warning(f"평가항목 참조표 테이블 생성 실패, 텍스트 대체: {e}")
        doc.add_paragraph("구분 | 평가항목 | 심사항목 | 배점 | 해당 페이지")
        doc.add_paragraph("정성평가 | 사업수행계획서 | — | 80 | —")
        doc.add_paragraph("가격평가 | 입찰가격 | 평점산식 | 20 | —")
        doc.add_paragraph("합계 | | | 100 | ")

    _add_empty(doc, 2)


def _add_toc(doc: HwpxDocument) -> None:
    """목차 페이지 생성"""
    toc_header = doc.add_paragraph()
    toc_header.add_run("목   차", bold=True)

    _add_empty(doc)

    toc_items = [
        "Ⅰ. 제안개요",
        "  1. 제안목적 및 배경",
        "  2. 제안범위",
        "  3. 추진전략",
        "Ⅱ. 제안업체 일반",
        "  1. 일반현황 및 조직",
        "Ⅲ. 사업 수행부문",
        "  1. 사업수행 세부계획",
        "Ⅳ. 사업관리방안",
        "  1. 추진일정",
        "  2. 기대효과",
    ]

    for item in toc_items:
        is_chapter = item.startswith("Ⅰ") or item.startswith("Ⅱ") or item.startswith("Ⅲ") or item.startswith("Ⅳ")
        para = doc.add_paragraph()
        para.add_run(item, bold=is_chapter)

    _add_empty(doc, 2)


def _add_content_paragraph(doc: HwpxDocument, line: str) -> None:
    """본문 한 줄을 기호 체계에 맞게 단락으로 추가"""
    stripped = line.strip()
    if not stripped:
        _add_empty(doc)
        return

    para = doc.add_paragraph()

    # □ 대분류
    if stripped.startswith("□"):
        para.add_run("□ ", bold=True)
        para.add_run(stripped[1:].strip())
    # ❍ 중분류
    elif stripped.startswith("❍"):
        para.add_run("  ❍ ")
        para.add_run(stripped[1:].strip())
    # ☞ 후속과제
    elif stripped.startswith("☞"):
        para.add_run("  ☞ ")
        para.add_run(stripped[1:].strip())
    # 【 】 핵심 강조
    elif stripped.startswith("【") and "】" in stripped:
        para.add_run(stripped, bold=True)
    # (근거: ...) 법령 출처
    elif stripped.startswith("(근거:") or stripped.startswith("(출처:"):
        para.add_run("    " + stripped)
    # - 소분류 (하이픈)
    elif stripped.startswith("- ") or stripped.startswith("­"):
        para.add_run("    - ")
        para.add_run(stripped.lstrip("-­").strip())
    # 숫자 목록 (1. 2. 등)
    elif len(stripped) > 2 and stripped[0].isdigit() and stripped[1] == ".":
        para.add_run(stripped, bold=True)
    # 일반 텍스트
    else:
        para.add_run(stripped)


def _add_body(doc: HwpxDocument, sections: dict) -> None:
    """본문 4개 장(章) 생성"""
    for chapter_title, section_keys in _CHAPTER_MAP.items():
        # 장 제목 (대목차)
        _add_empty(doc)
        chapter_para = doc.add_paragraph()
        chapter_para.add_run(chapter_title, bold=True)
        _add_empty(doc)

        for key in section_keys:
            # 섹션이 sections dict에 없으면 건너뜀
            content = sections.get(key, "")
            if not content:
                # key가 정확히 없으면 유사 키 탐색
                for k, v in sections.items():
                    if key.replace("_", " ").lower() in k.lower() or k.lower() in key.lower():
                        content = v
                        break

            if not content:
                continue

            # 소제목
            section_title = _SECTION_TITLES.get(key, key.replace("_", " ").title())
            sub_para = doc.add_paragraph()
            sub_para.add_run(section_title, bold=True)
            _add_empty(doc)

            # 본문 내용 — 줄 단위 처리
            for line in content.split("\n"):
                _add_content_paragraph(doc, line)

            _add_empty(doc)

    # sections dict에 매핑되지 않은 추가 섹션 처리
    mapped_keys = {k for keys in _CHAPTER_MAP.values() for k in keys}
    extra_sections = {k: v for k, v in sections.items() if k not in mapped_keys}
    if extra_sections:
        _add_empty(doc)
        extra_header = doc.add_paragraph()
        extra_header.add_run("부록", bold=True)
        _add_empty(doc)
        for key, content in extra_sections.items():
            if not content:
                continue
            extra_title = doc.add_paragraph()
            extra_title.add_run(key.replace("_", " ").title(), bold=True)
            _add_empty(doc)
            for line in content.split("\n"):
                _add_content_paragraph(doc, line)
            _add_empty(doc)


def build_hwpx(
    sections: dict,
    output_path: Path,
    project_name: str = "용역 제안서",
    metadata: dict | None = None,
) -> Path:
    """
    HWPX 제안서 생성 (동기)

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
    metadata = metadata or {}
    doc = HwpxDocument.new()

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
