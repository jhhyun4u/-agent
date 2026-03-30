"""문서 유형별 지능형 청킹 서비스.

제안서/보고서 → 제목 기반 섹션 분할
발표자료(PPTX) → 슬라이드 그룹
계약서 → 조항(제N조) 단위
기타 → 고정 윈도우 + 오버랩
"""

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    """청킹 결과 단위."""

    index: int
    chunk_type: str  # section | slide | article | window
    section_title: str | None
    content: str
    char_count: int


def chunk_document(
    text: str,
    doc_type: str,
    doc_subtype: str = "",
    max_chunk_chars: int = 3000,
    window_chars: int = 2000,
    overlap_chars: int = 200,
) -> list[Chunk]:
    """문서 유형에 따라 적절한 청킹 전략 선택."""
    if not text or len(text.strip()) < 50:
        return []

    if doc_type == "presentation":
        return _chunk_slides(text)
    elif doc_type == "contract":
        return _chunk_articles(text, window_chars, overlap_chars)
    elif doc_type in ("proposal", "report"):
        return _chunk_by_headings(text, max_chunk_chars, overlap_chars)
    else:
        return _chunk_by_window(text, window_chars, overlap_chars)


# ── 제목 패턴 기반 섹션 분할 ──

_HEADING_PATTERNS = [
    r"^제\s*\d+\s*[장절항]",
    r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]\.\s",
    r"^\d+\.\s+[가-힣]",
    r"^\d+\.\d+\s+[가-힣]",
    r"^[가나다라마바사아자차카타파하]\.\s",
]
_HEADING_RE = re.compile("|".join(f"(?:{p})" for p in _HEADING_PATTERNS), re.MULTILINE)


def _chunk_by_headings(
    text: str,
    max_chars: int = 3000,
    overlap: int = 200,
    min_chars: int = 200,
) -> list[Chunk]:
    """제목 패턴 기반 섹션 분할. 감지 실패 시 윈도우 폴백."""
    matches = list(_HEADING_RE.finditer(text))

    if len(matches) < 2:
        return _chunk_by_window(text)

    chunks: list[Chunk] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[start:end].strip()

        if not section:
            continue

        title = section.split("\n", 1)[0].strip()[:100]

        if len(section) > max_chars:
            sub_chunks = _chunk_by_window(section, max_chars, overlap)
            for j, sc in enumerate(sub_chunks):
                sc.section_title = f"{title} (part {j + 1})" if title else None
                sc.index = len(chunks)
                chunks.append(sc)
        elif len(section) >= min_chars:
            chunks.append(Chunk(
                index=len(chunks),
                chunk_type="section",
                section_title=title,
                content=section,
                char_count=len(section),
            ))

    # 첫 매치 이전 텍스트 (서론 등)
    preamble = text[: matches[0].start()].strip()
    if preamble and len(preamble) >= min_chars:
        chunks.insert(0, Chunk(
            index=0,
            chunk_type="section",
            section_title="서론",
            content=preamble,
            char_count=len(preamble),
        ))
        for c in chunks[1:]:
            c.index += 1

    return chunks if chunks else _chunk_by_window(text)


# ── 슬라이드 기반 분할 (PPTX) ──

_SLIDE_RE = re.compile(r"\[슬라이드\s+\d+\]")


def _chunk_slides(text: str, max_slides_per_chunk: int = 3) -> list[Chunk]:
    """[슬라이드 N] 마커 기반 분할, 최대 3장씩 그룹."""
    parts = _SLIDE_RE.split(text)
    slides = [s.strip() for s in parts if s.strip()]

    if not slides:
        return _chunk_by_window(text)

    chunks: list[Chunk] = []
    for i in range(0, len(slides), max_slides_per_chunk):
        group = slides[i : i + max_slides_per_chunk]
        content = "\n\n".join(group)
        end_idx = min(i + max_slides_per_chunk, len(slides))
        chunks.append(Chunk(
            index=len(chunks),
            chunk_type="slide",
            section_title=f"슬라이드 {i + 1}~{end_idx}",
            content=content,
            char_count=len(content),
        ))
    return chunks


# ── 계약서 조항 분할 ──

_ARTICLE_RE = re.compile(r"(?=제\s*\d+\s*조)")


def _chunk_articles(
    text: str,
    window: int = 2000,
    overlap: int = 200,
) -> list[Chunk]:
    """'제N조' 패턴 기반 분할."""
    splits = _ARTICLE_RE.split(text)
    splits = [s.strip() for s in splits if s.strip()]

    if len(splits) <= 1:
        return _chunk_by_window(text, window, overlap)

    chunks: list[Chunk] = []
    for s in splits:
        title_match = re.match(r"(제\s*\d+\s*조[^\n]*)", s)
        title = title_match.group(1)[:100] if title_match else None
        chunks.append(Chunk(
            index=len(chunks),
            chunk_type="article",
            section_title=title,
            content=s,
            char_count=len(s),
        ))
    return chunks


# ── 윈도우 청킹 (폴백) ──


def _chunk_by_window(
    text: str,
    window: int = 2000,
    overlap: int = 200,
) -> list[Chunk]:
    """고정 윈도우 + 오버랩 분할."""
    chunks: list[Chunk] = []
    start = 0
    while start < len(text):
        end = start + window
        content = text[start:end].strip()
        if content:
            chunks.append(Chunk(
                index=len(chunks),
                chunk_type="window",
                section_title=None,
                content=content,
                char_count=len(content),
            ))
        start += window - overlap
        if start + overlap >= len(text):
            break
    return chunks
