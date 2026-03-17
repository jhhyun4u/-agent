"""
출처 태깅 서비스 (§16-3-2)

제안서 텍스트에서 출처 태그를 추출하고, 근거 비율·미태깅 주장을 분석.
"""

import re
from dataclasses import dataclass, field
from typing import Literal

from app.prompts.trustworthiness import FORBIDDEN_EXPRESSIONS

# 태그 유형
TagType = Literal[
    "KB", "역량DB", "콘텐츠", "RFP", "G2B",
    "추정", "일반지식", "플레이스홀더", "비RFP용어",
]

# 태그 정규식 패턴 (참조 ID 캡처 지원: [KB-CAP-045], [역량DB-PRJ-012] 등)
TAG_PATTERNS: dict[TagType, re.Pattern] = {
    "KB": re.compile(r"\[KB(?:-[A-Z]+-\d+)?\]"),
    "역량DB": re.compile(r"\[역량DB(?:-[A-Z]+-\d+)?\]"),
    "콘텐츠": re.compile(r"\[콘텐츠(?:-[A-Z]+-\d+)?\]"),
    "RFP": re.compile(r"\[RFP\s*p?\.?\s*\d+\]"),
    "G2B": re.compile(r"\[G2B(?:-[\d-]+)?\]"),
    "추정": re.compile(r"\[추정\s*\([^)]+\)\]"),
    "일반지식": re.compile(r"\[일반지식\]"),
    "플레이스홀더": re.compile(r"\[KB\s*데이터\s*필요[:\s][^\]]*\]"),
    "비RFP용어": re.compile(r"\[비RFP\s*용어\]"),
}

# 수치를 포함하는 문장 패턴 (태깅 필요 대상)
NUMBER_PATTERN = re.compile(
    r"(?:\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:명|건|원|%|개|회|시간|일|억|만)"
)

# 사실 키워드 (KB 태그 필요)
FACT_KEYWORDS = [
    "수행실적", "수행 실적", "인력", "경력", "인증", "특허",
    "매출", "자본금", "금액", "수주", "납품", "구축",
]


@dataclass
class SourceTag:
    """추출된 출처 태그."""
    tag_type: TagType
    reference_id: str  # 태그 전체 텍스트
    text_span: tuple[int, int]  # (start, end) 위치


def extract_source_tags(text: str) -> list[SourceTag]:
    """텍스트에서 모든 출처 태그를 추출."""
    tags: list[SourceTag] = []
    for tag_type, pattern in TAG_PATTERNS.items():
        for match in pattern.finditer(text):
            tags.append(SourceTag(
                tag_type=tag_type,
                reference_id=match.group(),
                text_span=(match.start(), match.end()),
            ))
    tags.sort(key=lambda t: t.text_span[0])
    return tags


def calculate_grounding_ratio(text: str) -> dict:
    """텍스트의 근거 비율 분석.

    Returns:
        {
            "kb_ratio": float,       # KB/역량DB/콘텐츠 비율
            "general_ratio": float,  # 일반지식 비율
            "untagged_ratio": float, # 미태깅 비율
            "level": str,            # KB기반 / 혼합 / 일반지식기반
            "tag_counts": dict,      # 태그 유형별 카운트
            "total_claims": int,     # 전체 주장/수치 문장 수
        }
    """
    tags = extract_source_tags(text)
    sentences = _split_sentences(text)

    # 수치/사실 포함 문장 수 (태깅 필요 대상)
    claim_sentences = [
        s for s in sentences
        if NUMBER_PATTERN.search(s) or any(kw in s for kw in FACT_KEYWORDS)
    ]
    total_claims = max(len(claim_sentences), 1)

    # 태그 카운트
    tag_counts: dict[str, int] = {}
    for tag in tags:
        tag_counts[tag.tag_type] = tag_counts.get(tag.tag_type, 0) + 1

    kb_tags = sum(tag_counts.get(t, 0) for t in ("KB", "역량DB", "콘텐츠", "RFP", "G2B"))
    general_tags = tag_counts.get("일반지식", 0) + tag_counts.get("추정", 0)
    total_tags = kb_tags + general_tags

    kb_ratio = round(kb_tags / total_claims, 2) if total_claims else 0
    general_ratio = round(general_tags / total_claims, 2) if total_claims else 0
    untagged_ratio = round(max(0, 1 - kb_ratio - general_ratio), 2)

    # 수준 판정
    if kb_ratio >= 0.6:
        level = "KB기반"
    elif kb_ratio >= 0.3:
        level = "혼합"
    else:
        level = "일반지식기반"

    return {
        "kb_ratio": kb_ratio,
        "general_ratio": general_ratio,
        "untagged_ratio": untagged_ratio,
        "level": level,
        "tag_counts": tag_counts,
        "total_claims": total_claims,
    }


def find_ungrounded_claims(text: str) -> list[dict]:
    """미태깅 주장 및 문제 문장 검출.

    Returns:
        [{"sentence_index": int, "sentence": str, "issue": str, "severity": str}]
    """
    sentences = _split_sentences(text)
    tags = extract_source_tags(text)
    issues: list[dict] = []

    # 태그 위치 집합
    tagged_ranges: list[tuple[int, int]] = [t.text_span for t in tags]

    pos = 0
    for i, sentence in enumerate(sentences):
        sent_start = text.find(sentence, pos)
        sent_end = sent_start + len(sentence) if sent_start >= 0 else pos + len(sentence)
        pos = max(pos, sent_end)

        # 수치 포함 문장에 태그 없으면 경고
        if NUMBER_PATTERN.search(sentence):
            has_tag = any(
                s <= sent_end and e >= sent_start
                for s, e in tagged_ranges
            )
            if not has_tag:
                issues.append({
                    "sentence_index": i,
                    "sentence": sentence.strip()[:200],
                    "issue": "수치에 출처 태그 누락",
                    "severity": "high",
                })

        # 사실 키워드 + KB 태그 없음
        fact_found = [kw for kw in FACT_KEYWORDS if kw in sentence]
        if fact_found:
            has_kb_tag = any(
                tag.tag_type in ("KB", "역량DB", "콘텐츠")
                and tag.text_span[0] >= sent_start
                and tag.text_span[1] <= sent_end + 50  # 태그가 문장 직후에 올 수 있음
                for tag in tags
            )
            if not has_kb_tag:
                issues.append({
                    "sentence_index": i,
                    "sentence": sentence.strip()[:200],
                    "issue": f"사실 키워드 '{fact_found[0]}'에 KB 태그 누락",
                    "severity": "high",
                })

        # 금지 표현 검출
        for expr in FORBIDDEN_EXPRESSIONS:
            if expr in sentence:
                issues.append({
                    "sentence_index": i,
                    "sentence": sentence.strip()[:200],
                    "issue": f"금지 표현: '{expr}'",
                    "severity": "medium",
                })

    return issues


def evaluate_trustworthiness(text: str) -> dict:
    """신뢰성 25점 만점 평가 (self_review 4번째 축).

    Returns:
        {
            "score": int (0-25),
            "source_tag_score": int (0-10),
            "kb_ratio_score": int (0-5),
            "exaggeration_score": int (0-5),
            "consistency_score": int (0-5),
            "details": dict,
        }
    """
    grounding = calculate_grounding_ratio(text)
    issues = find_ungrounded_claims(text)

    # 1. 출처 태그 충실도 (10점)
    tagged_ratio = 1 - grounding["untagged_ratio"]
    if tagged_ratio >= 0.8:
        source_tag_score = 10
    elif tagged_ratio >= 0.6:
        source_tag_score = 7
    elif tagged_ratio >= 0.4:
        source_tag_score = 4
    else:
        source_tag_score = 2

    # 2. KB 활용률 (5점)
    if grounding["kb_ratio"] >= 0.5:
        kb_ratio_score = 5
    elif grounding["kb_ratio"] >= 0.3:
        kb_ratio_score = 3
    else:
        kb_ratio_score = 1

    # 3. 과장 표현 부재 (5점)
    exaggeration_count = sum(
        1 for iss in issues if iss["issue"].startswith("금지 표현")
    )
    if exaggeration_count == 0:
        exaggeration_score = 5
    elif exaggeration_count == 1:
        exaggeration_score = 3
    else:
        exaggeration_score = 0

    # 4. 일관성 (5점) — 비RFP 용어
    non_rfp_count = grounding["tag_counts"].get("비RFP용어", 0)
    if non_rfp_count == 0:
        consistency_score = 5
    elif non_rfp_count <= 2:
        consistency_score = 3
    else:
        consistency_score = 1

    total = source_tag_score + kb_ratio_score + exaggeration_score + consistency_score

    return {
        "score": total,
        "source_tag_score": source_tag_score,
        "kb_ratio_score": kb_ratio_score,
        "exaggeration_score": exaggeration_score,
        "consistency_score": consistency_score,
        "details": {
            "grounding": grounding,
            "issue_count": len(issues),
            "exaggeration_count": exaggeration_count,
            "non_rfp_term_count": non_rfp_count,
        },
    }


def check_number_consistency(sections: dict[str, str]) -> list[dict]:
    """섹션 간 동일 수치의 일관성 검증 (S6).

    동일한 수치(예: 금액, 인원)가 여러 섹션에 등장할 때 불일치를 탐지.

    Args:
        sections: {섹션명: 본문 텍스트} 매핑

    Returns:
        [{"number": str, "sections": [{"name": str, "value": str, "context": str}], "issue": str}]
    """
    # 주요 수치 패턴 (금액, 인원, 기간)
    amount_pattern = re.compile(
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(억|만|원|명|건|개월|일)"
    )

    # 섹션별 수치 수집
    number_map: dict[str, list[dict]] = {}  # "단위" -> [{section, value, context}]
    for sec_name, text in sections.items():
        for match in amount_pattern.finditer(text):
            raw_value = match.group(1)
            unit = match.group(2)
            # 문맥: 매칭 앞뒤 30자
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            context = text[start:end].replace("\n", " ").strip()

            key = f"{unit}"
            if key not in number_map:
                number_map[key] = []
            number_map[key].append({
                "section": sec_name,
                "value": raw_value,
                "full": match.group(),
                "context": context,
            })

    # 불일치 탐지: 같은 문맥 키워드 + 다른 수치
    issues: list[dict] = []
    context_keywords = ["총", "합계", "전체", "예산", "사업비", "투입 인력", "총인원"]

    for unit, entries in number_map.items():
        if len(entries) < 2:
            continue
        # 동일 문맥 키워드를 공유하는 항목끼리 비교
        for kw in context_keywords:
            matching = [e for e in entries if kw in e["context"]]
            if len(matching) < 2:
                continue
            values = {e["value"] for e in matching}
            if len(values) > 1:
                issues.append({
                    "number": f"{kw} ({unit})",
                    "sections": [
                        {"name": e["section"], "value": e["full"], "context": e["context"]}
                        for e in matching
                    ],
                    "issue": f"'{kw}' 관련 수치 불일치: {', '.join(values)} {unit}",
                })

    return issues


def _split_sentences(text: str) -> list[str]:
    """텍스트를 문장 단위로 분리."""
    # 한국어 문장 종결 패턴
    sentences = re.split(r"(?<=[.!?。])\s+", text)
    # 줄바꿈 기반 추가 분리
    result: list[str] = []
    for s in sentences:
        result.extend(line.strip() for line in s.split("\n") if line.strip())
    return result
