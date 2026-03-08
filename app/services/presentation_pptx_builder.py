"""발표 자료 전용 PPTX 빌더 — 평가항목 배지(eval_badge) 지원 레이아웃 7종"""

import logging
from pathlib import Path
from typing import Optional

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

logger = logging.getLogger(__name__)

# ── 색상 상수 ────────────────────────────────────────────────────────────────
COLOR_DARK_BLUE  = RGBColor(0x1F, 0x49, 0x7D)   # eval_badge, 강조
COLOR_ACCENT     = RGBColor(0x2E, 0x75, 0xB6)   # 소제목
COLOR_LIGHT_GRAY = RGBColor(0xF2, 0xF2, 0xF2)   # 표 배경
COLOR_DARK_TEXT  = RGBColor(0x26, 0x26, 0x26)   # 본문


# ── 유틸 ─────────────────────────────────────────────────────────────────────

def _add_textbox(slide, left, top, width, height, text="", font_size=18,
                 bold=False, color=None, align=PP_ALIGN.LEFT, wrap=True):
    """텍스트박스 추가 헬퍼"""
    txb = slide.shapes.add_textbox(left, top, width, height)
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    run = p.runs[0] if p.runs else p.add_run()
    run.font.size = Pt(font_size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    return txb


def _add_eval_badge(slide, badge_text: str):
    """슬라이드 우측 상단에 [평가항목명 | XX점] 배지 표시"""
    if not badge_text:
        return
    txb = slide.shapes.add_textbox(Inches(9.5), Inches(0.15), Inches(3.6), Inches(0.45))
    tf = txb.text_frame
    p = tf.paragraphs[0]
    p.text = badge_text
    p.alignment = PP_ALIGN.RIGHT
    run = p.runs[0] if p.runs else p.add_run()
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = COLOR_DARK_BLUE


def _add_speaker_notes(slide, notes_text: str):
    """발표자 노트 추가"""
    if not notes_text:
        return
    slide.notes_slide.notes_text_frame.text = notes_text


def _add_slide_number(slide, num: int):
    """슬라이드 우측 하단에 페이지 번호 표시 (표지 제외)"""
    _add_textbox(
        slide,
        Inches(12.5), Inches(6.9), Inches(0.6), Inches(0.35),
        text=str(num),
        font_size=14,
        color=COLOR_DARK_TEXT,
        align=PP_ALIGN.RIGHT,
    )


def _add_slide_title(slide, title: str, top=Inches(0.7)):
    """슬라이드 제목 텍스트박스"""
    _add_textbox(
        slide, Inches(0.6), top, Inches(12.1), Inches(0.7),
        text=title, font_size=24, bold=True, color=COLOR_DARK_BLUE,
    )


def _add_bullets(slide, bullets: list, top=Inches(1.8), font_size=18):
    """bullet 목록 텍스트박스"""
    if not bullets:
        return
    txb = slide.shapes.add_textbox(Inches(0.8), top, Inches(11.9), Inches(5.0))
    tf = txb.text_frame
    tf.word_wrap = True
    for i, bullet in enumerate(bullets[:5]):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = f"• {bullet}"
        p.space_before = Pt(6)
        run = p.runs[0] if p.runs else p.add_run()
        run.font.size = Pt(font_size)
        run.font.color.rgb = COLOR_DARK_TEXT


# ── 레이아웃별 렌더링 함수 ───────────────────────────────────────────────────

def _render_cover(slide, data: dict) -> None:
    """표지: 사업명 + Win Theme 부제목"""
    _add_textbox(
        slide, Inches(1.2), Inches(2.0), Inches(11.0), Inches(1.2),
        text=data.get("title", ""),
        font_size=36, bold=True, color=COLOR_DARK_BLUE, align=PP_ALIGN.CENTER,
    )
    subtitle = data.get("subtitle", "")
    if subtitle:
        _add_textbox(
            slide, Inches(1.2), Inches(3.5), Inches(11.0), Inches(0.8),
            text=subtitle,
            font_size=20, bold=False, color=COLOR_ACCENT, align=PP_ALIGN.CENTER,
        )
    # 구분선
    line = slide.shapes.add_connector(
        1,  # MSO_CONNECTOR_TYPE.STRAIGHT
        Inches(1.5), Inches(3.3), Inches(11.8), Inches(3.3),
    )
    line.line.color.rgb = COLOR_ACCENT
    line.line.width = Pt(2)
    _add_speaker_notes(slide, data.get("speaker_notes", ""))


def _render_key_message(slide, data: dict) -> None:
    """이기는 전략: Win Theme 헤드라인 + evidence bullets"""
    _add_slide_title(slide, data.get("title", "이기는 전략"))
    headline = data.get("headline", "")
    if headline:
        _add_textbox(
            slide, Inches(0.6), Inches(1.6), Inches(12.1), Inches(0.7),
            text=headline,
            font_size=20, bold=True, color=COLOR_ACCENT,
        )
    _add_bullets(slide, data.get("bullets", []), top=Inches(2.5))
    _add_speaker_notes(slide, data.get("speaker_notes", ""))


def _render_eval_section(slide, data: dict) -> None:
    """평가항목 섹션: eval_badge + bullets (evaluator_check_points 커버)"""
    _add_eval_badge(slide, data.get("eval_badge", ""))
    _add_slide_title(slide, data.get("title", ""))
    _add_bullets(slide, data.get("bullets", []), top=Inches(1.8))
    _add_speaker_notes(slide, data.get("speaker_notes", ""))


def _render_comparison(slide, data: dict) -> None:
    """차별화 비교: 경쟁사 vs 우리 2컬럼 표"""
    _add_eval_badge(slide, data.get("eval_badge", ""))
    _add_slide_title(slide, data.get("title", "차별화 포인트"))

    table_data = data.get("table", [])
    if not table_data:
        # table 없으면 bullets fallback
        _add_bullets(slide, data.get("bullets", []), top=Inches(1.8))
        _add_speaker_notes(slide, data.get("speaker_notes", ""))
        return

    rows = len(table_data) + 1  # 헤더 포함
    cols = 3  # dimension / 경쟁사 / 우리
    tbl = slide.shapes.add_table(rows, cols, Inches(0.6), Inches(1.7), Inches(12.1), Inches(rows * 0.6)).table

    # 헤더
    for ci, header in enumerate(["구분", "경쟁사", "우리"]):
        cell = tbl.cell(0, ci)
        cell.text = header
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.runs[0] if p.runs else p.add_run()
        run.font.bold = True
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_DARK_BLUE

    # 데이터 행
    for ri, row in enumerate(table_data[:6], start=1):
        for ci, (key, text) in enumerate([
            ("dimension", row.get("dimension", "")),
            ("competitor", row.get("competitor", "")),
            ("ours", row.get("ours", "")),
        ]):
            cell = tbl.cell(ri, ci)
            cell.text = text
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.CENTER
            run = p.runs[0] if p.runs else p.add_run()
            run.font.size = Pt(13)
            if ri % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = COLOR_LIGHT_GRAY

    _add_speaker_notes(slide, data.get("speaker_notes", ""))


def _render_timeline(slide, data: dict) -> None:
    """추진 계획 타임라인: 단계별 가로 배치"""
    _add_eval_badge(slide, data.get("eval_badge", ""))
    _add_slide_title(slide, data.get("title", "추진 계획"))

    phases = data.get("phases", [])
    if not phases:
        # phases 없으면 implementation_checklist 구조도 수용
        phases = data.get("implementation_checklist", [])
    if not phases:
        _add_speaker_notes(slide, data.get("speaker_notes", ""))
        return

    n = len(phases)
    total_w = Inches(11.8)
    col_w = total_w / max(n, 1)
    start_left = Inches(0.7)
    top = Inches(1.8)
    height = Inches(4.2)

    phase_colors = [
        RGBColor(0x1F, 0x49, 0x7D),
        RGBColor(0x2E, 0x75, 0xB6),
        RGBColor(0x5B, 0x9B, 0xD5),
        RGBColor(0x9D, 0xC3, 0xE6),
        RGBColor(0xBD, 0xD7, 0xEE),
    ]

    for i, phase in enumerate(phases[:5]):
        left = start_left + col_w * i
        shape = slide.shapes.add_shape(
            1,  # MSO_SHAPE_TYPE.RECTANGLE
            left, top, col_w - Inches(0.08), height,
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = phase_colors[i % len(phase_colors)]
        shape.line.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shape.line.width = Pt(1.5)

        tf = shape.text_frame
        tf.word_wrap = True
        # 단계명
        p = tf.paragraphs[0]
        p.text = phase.get("name", phase.get("phase", f"{i+1}단계"))
        p.alignment = PP_ALIGN.CENTER
        run = p.runs[0] if p.runs else p.add_run()
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        # 기간
        if phase.get("duration"):
            p2 = tf.add_paragraph()
            p2.text = phase["duration"]
            p2.alignment = PP_ALIGN.CENTER
            r2 = p2.runs[0] if p2.runs else p2.add_run()
            r2.font.size = Pt(11)
            r2.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        # 산출물
        for d in phase.get("deliverables", [])[:3]:
            pd = tf.add_paragraph()
            pd.text = f"• {d}"
            pd.alignment = PP_ALIGN.LEFT
            rd = pd.runs[0] if pd.runs else pd.add_run()
            rd.font.size = Pt(10)
            rd.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    _add_speaker_notes(slide, data.get("speaker_notes", ""))


def _render_team(slide, data: dict) -> None:
    """투입 인력 구성 표"""
    _add_eval_badge(slide, data.get("eval_badge", ""))
    _add_slide_title(slide, data.get("title", "투입 인력 & 역량"))

    team_rows = data.get("team_rows", [])
    if not team_rows:
        # bullets fallback
        _add_bullets(slide, data.get("bullets", []), top=Inches(1.8))
        _add_speaker_notes(slide, data.get("speaker_notes", ""))
        return

    rows = len(team_rows) + 1
    tbl = slide.shapes.add_table(
        rows, 4, Inches(0.8), Inches(1.7), Inches(11.7), Inches(rows * 0.55),
    ).table

    for ci, header in enumerate(["역할", "등급", "투입 기간", "담당 업무"]):
        cell = tbl.cell(0, ci)
        cell.text = header
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.runs[0] if p.runs else p.add_run()
        run.font.bold = True
        run.font.size = Pt(13)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_DARK_BLUE

    for ri, row in enumerate(team_rows, start=1):
        vals = [
            row.get("role", ""),
            row.get("grade", ""),
            str(row.get("person_months", "")) + "개월" if row.get("person_months") else row.get("duration", ""),
            row.get("task", ""),
        ]
        for ci, val in enumerate(vals):
            cell = tbl.cell(ri, ci)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            run = p.runs[0] if p.runs else p.add_run()
            run.font.size = Pt(12)
            if ri % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = COLOR_LIGHT_GRAY

    _add_speaker_notes(slide, data.get("speaker_notes", ""))


def _render_closing(slide, data: dict) -> None:
    """마무리: Win Theme 재강조 + 차별화 포인트 CTA"""
    _add_slide_title(slide, data.get("title", "왜 우리인가"))
    headline = data.get("headline", "")
    if headline:
        _add_textbox(
            slide, Inches(0.6), Inches(1.6), Inches(12.1), Inches(0.7),
            text=headline,
            font_size=22, bold=True, color=COLOR_ACCENT, align=PP_ALIGN.CENTER,
        )
    _add_bullets(slide, data.get("bullets", []), top=Inches(2.6), font_size=19)
    _add_speaker_notes(slide, data.get("speaker_notes", ""))


# ── 슬라이드 디스패처 ────────────────────────────────────────────────────────

_LAYOUT_MAP = {
    "cover":        _render_cover,
    "key_message":  _render_key_message,
    "eval_section": _render_eval_section,
    "comparison":   _render_comparison,
    "timeline":     _render_timeline,
    "team":         _render_team,
    "closing":      _render_closing,
}


def _render_slide(prs: Presentation, data: dict) -> None:
    """레이아웃 타입별 슬라이드 렌더링 (실패 시 텍스트 fallback)"""
    layout = data.get("layout", "eval_section")
    renderer = _LAYOUT_MAP.get(layout, _render_eval_section)
    try:
        # slide_layouts[6] = blank layout (인덱스 6이 없으면 마지막 레이아웃)
        layout_idx = min(6, len(prs.slide_layouts) - 1)
        slide = prs.slides.add_slide(prs.slide_layouts[layout_idx])
        renderer(slide, data)
        # 표지(cover)를 제외한 모든 슬라이드에 번호 표시
        if layout != "cover":
            _add_slide_number(slide, data.get("slide_num", 0))
    except Exception as e:
        logger.warning(f"슬라이드 렌더링 실패 ({layout}), fallback 적용: {e}")
        try:
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            slide.shapes.title.text = data.get("title", "")
            bullets = data.get("bullets", [])
            if bullets and len(slide.placeholders) > 1:
                slide.placeholders[1].text = "\n".join(bullets)
        except Exception as e2:
            logger.error(f"fallback 슬라이드도 실패: {e2}")


# ── 템플릿 초기화 ─────────────────────────────────────────────────────────────

def _init_presentation(template_path: Optional[Path]) -> Presentation:
    """템플릿 파일 로드 또는 빈 프레젠테이션 생성"""
    if template_path and template_path.exists():
        try:
            prs = Presentation(str(template_path))
            # 기존 슬라이드 전부 제거 (Slide Master/디자인 유지)
            while len(prs.slides._sldIdLst) > 0:
                rId = prs.slides._sldIdLst[0].rId
                prs.part.drop_rel(rId)
                del prs.slides._sldIdLst[0]
            logger.info(f"템플릿 로드 완료: {template_path}")
            return prs
        except Exception as e:
            logger.warning(f"템플릿 로드 실패, scratch로 fallback: {e}")

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


# ── 공개 인터페이스 ───────────────────────────────────────────────────────────

def build_presentation_pptx(
    slides_json: dict,
    output_path: Path,
    project_name: str = "",
    template_path: Optional[Path] = None,
) -> Path:
    """
    슬라이드 JSON → 발표용 PPTX 파일 생성

    Args:
        slides_json: presentation_generator.py가 반환한 슬라이드 JSON
        output_path: 저장 경로
        project_name: 표지 fallback 제목
        template_path: PPTX 템플릿 파일 경로 (None이면 scratch)

    Returns:
        저장된 PPTX 파일 경로
    """
    prs = _init_presentation(template_path)

    slides = slides_json.get("slides", [])
    if not slides:
        logger.warning("슬라이드 데이터 없음 — 빈 표지만 생성")
        slides = [{"slide_num": 1, "layout": "cover", "title": project_name}]

    for slide_data in sorted(slides, key=lambda s: s.get("slide_num", 99)):
        _render_slide(prs, slide_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    logger.info(f"PPTX 저장 완료: {output_path} ({len(slides)}장)")
    return output_path
