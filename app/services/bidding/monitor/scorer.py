"""
공고 적합도 스코어링 v2 (tenopa upfront research 특화)

4단계 파이프라인:
  1. 역할 키워드 필수 매칭 — 1개 이상 없으면 탈락
  2. 분류(pubPrcrmntClsfcNm) 가중치 — 가산/감산 점수
  3. 도메인 키워드 가산 — tenopa 핵심 업무 영역 매칭
  4. 컨텍스트 감점 — 역할 키워드가 있어도 현장 실행형이면 감점

설계 원칙:
  - 블랙리스트 NO → 점수 기반 랭킹
  - "안전진단 기술기획"처럼 역할 키워드가 있으면 어떤 분류든 통과
  - 분류는 정렬 우선순위에만 영향
  - 중복(재공고) 제거: 제목 유사도 기반

v2 튜닝 (2026-03-21):
  - 건설/토목 현장 실행형 컨텍스트 감점 추가
  - 역할 키워드 "연구"+"전략" 등 복합 매칭 시 추가 가산
  - 중복(재공고) 제거 강화 (제목 정규화 기반)
  - tenopa 핵심 도메인(기술전략, R&D기획, 정보화전략) 강화
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 키워드 정의
# ─────────────────────────────────────────────

# 역할 키워드: 최소 1개 반드시 매칭되어야 통과
# NOTE: "연구", "수립"은 단독으로는 범위가 너무 넓어 제외 (2026-03-24)
ROLE_KEYWORDS = [
    "전략", "기획", "조사", "분석", "평가",
    "로드맵", "마스터플랜", "타당성",
    "ISP", "ISMP", "정책", "컨설팅", "자문",
    "진단",  # 안전진단도 "진단 체계 기획"이면 가능
    "기본계획",
]

# score_bid() 호출 전 제목 필터링에 사용하는 frozenset (소문자 변환 완료)
# score_and_rank_bids()의 루프에서 매번 lower() 변환 없이 O(1) 조회 가능
_ROLE_KW_LOWER: frozenset[str] = frozenset(kw.lower() for kw in ROLE_KEYWORDS)

# 고가치 역할 조합: 이 키워드들이 2개 이상 동시 매칭되면 추가 가산
HIGH_VALUE_ROLE_COMBOS = [
    {"전략", "기획"},
    {"R&D", "기획"}, {"정책", "기획"},
    {"로드맵", "전략"}, {"마스터플랜", "전략"},
    {"ISP", "전략"}, {"ISMP", "전략"},
    {"타당성", "조사"},
    {"분석", "기획"},
    {"컨설팅", "전략"}, {"자문", "전략"},
]

# 도메인 키워드: 역할 키워드와 함께 있으면 가산점
DOMAIN_KEYWORDS = [
    # tenopa 핵심 도메인 (가산 높음)
    "기술", "R&D", "연구개발", "과학기술",
    "정보", "디지털", "데이터", "AI", "인공지능",
    "ICT", "산업", "혁신", "스마트", "정보화",
    # tenopa 관련 도메인
    "플랫폼", "시스템", "인프라", "보안", "클라우드",
    "지능형", "고도화", "표준화", "규제",
    # 분야 키워드 (약한 가산)
    "환경", "에너지", "바이오", "우주", "국방", "교통",
]

# tenopa 핵심 도메인 (추가 가산 대상)
CORE_DOMAIN_KEYWORDS = [
    "기술", "R&D", "연구개발", "과학기술", "정보", "디지털",
    "데이터", "AI", "인공지능", "ICT", "정보화", "혁신",
]

# 분류 가중치 (pubPrcrmntClsfcNm 부분 매칭)
CLASSIFICATION_WEIGHTS: List[tuple[str, int]] = [
    # 높은 적합도 (+20~+30)
    ("전략계획서비스", 30),
    ("정책연구", 30),
    ("컨설팅", 25),
    ("기술동향", 25),
    ("경제산업연구", 20),
    ("경영전략연구", 25),
    ("과학기술연구", 20),
    ("정보화프로젝트관리", 20),
    ("정보통신연구", 15),

    # 중간 적합도 (+10~+20)
    ("연구조사서비스", 15),
    ("시장및여론조사", 15),
    ("통계연구", 15),
    ("인력개발및교육연구", 10),
    ("보건복지연구", 10),
    ("데이터서비스", 10),
    ("기타사업지원서비스", 5),
    ("기타기술용역", 5),
    ("감리서비스", 5),

    # 낮은 적합도 (감점) — 역할 키워드 있으면 여전히 통과하지만 순위 하락
    ("건설및지역개발연구", -5),
    ("발굴조사", -20),
    ("토목설계용역", -15),
    ("상하수도설계용역", -15),
    ("설계용역", -10),
    ("시공감리", -15),
    ("폐기물", -25),
    ("청소", -25),
    ("경비", -25),
    ("운송", -20),
    ("급식", -25),
    ("세탁", -25),
    ("조경", -10),
]

# 컨텍스트 감점: 제목에 이 키워드가 포함되면 현장 실행형으로 판단하여 감점
# 단, 역할 키워드 중 "전략/기획/연구/정책/R&D/ISP/ISMP/컨설팅"이 함께 있으면 감점 면제
CONTEXT_PENALTY_KEYWORDS = [
    ("건립", -15), ("신축", -15), ("증축", -15),
    ("조성사업", -10), ("정비사업", -10), ("개량사업", -10),
    ("보수공사", -20), ("포장공사", -20),
    ("시공", -20), ("준설", -15), ("골재", -15),
    ("매장유산", -15), ("발굴", -15),
    ("취약지역생활여건", -10), ("농어촌취약", -10),
    ("상수관", -15), ("하수관", -15), ("소하천", -10),
]
# 감점 면제 키워드 (이것이 제목에 있으면 컨텍스트 감점 적용 안 함)
PENALTY_EXEMPT_KEYWORDS = ["전략", "기획", "정책", "R&D", "ISP", "ISMP", "컨설팅"]

# 조달방식(bidMethdNm) 제외 키워드: 수의시담은 이미 업체가 정해진 건이므로 제외
EXCLUDED_BID_METHODS = ["수의", "수의시담", "수의계약"]


# ─────────────────────────────────────────────
# 소스별 정규화 어댑터 (사전규격·발주계획 → 입찰공고 형식)
# ─────────────────────────────────────────────

def normalize_pre_spec_for_scoring(raw: dict) -> dict:
    """사전규격 raw → 입찰공고 형식으로 필드 매핑."""
    return {
        "bidNtceNo": f"PRE-{(raw.get('bfSpecRgstNo') or raw.get('prcSpcfNo') or '').strip()}",
        "bidNtceNm": (raw.get("bfSpecRgstNm") or raw.get("prcSpcfNm") or "").strip(),
        "ntceInsttNm": (raw.get("orderInsttNm") or raw.get("rlDminsttNm") or "").strip(),
        "presmptPrce": raw.get("asignBdgtAmt") or raw.get("presmptPrce") or "0",
        "bidClseDt": raw.get("bfSpecRgstClseDt") or raw.get("opninRgstClseDt") or "",
        "pubPrcrmntClsfcNm": "",
        "pubPrcrmntLrgClsfcNm": "",
        "bidMethdNm": "",
        "_bid_stage": "사전규격",
    }


def normalize_plan_for_scoring(raw: dict) -> dict:
    """발주계획 raw → 입찰공고 형식으로 필드 매핑.

    필드명은 API 실제 응답 확인 후 조정 가능 (예상 필드 기반).
    """
    return {
        "bidNtceNo": f"PLN-{(raw.get('orderPlanNo') or raw.get('bidNtceNo') or '').strip()}",
        "bidNtceNm": (raw.get("orderPlanNm") or raw.get("bidNtceNm") or "").strip(),
        "ntceInsttNm": (raw.get("orderInsttNm") or raw.get("dminsttNm") or "").strip(),
        "presmptPrce": raw.get("asignBdgtAmt") or raw.get("presmptPrce") or "0",
        "bidClseDt": raw.get("orderPlanRegDt") or "",
        "pubPrcrmntClsfcNm": "",
        "pubPrcrmntLrgClsfcNm": "",
        "bidMethdNm": raw.get("cntrctMthdNm") or "",
        "_bid_stage": "발주계획",
    }


# ─────────────────────────────────────────────
# 스코어링 결과
# ─────────────────────────────────────────────

@dataclass
class BidScore:
    """공고 적합도 스코어링 결과"""
    bid_no: str
    title: str
    agency: str
    budget: int
    deadline: str
    d_day: Optional[int]
    classification: str       # pubPrcrmntClsfcNm
    classification_large: str  # pubPrcrmntLrgClsfcNm

    score: float = 0.0
    role_keywords_matched: List[str] = field(default_factory=list)
    domain_keywords_matched: List[str] = field(default_factory=list)
    classification_score: int = 0
    context_penalty: int = 0
    is_core_domain: bool = False  # tenopa 핵심 도메인 여부
    bid_stage: str = "입찰공고"   # "입찰공고" | "사전규격" | "발주계획"
    passed: bool = False

    raw: Dict[str, Any] = field(default_factory=dict, repr=False)


# ─────────────────────────────────────────────
# 제목 정규화 (중복 제거용)
# ─────────────────────────────────────────────

_NOISE_PREFIXES = re.compile(
    r"^\s*(\[?긴급\]?|\[?재공고\]?|\(긴급\)|\(재공고\)|\[재공고\]"
    r"|\[정보[,\s]*\d*\]|\[정책[,\s]*\d*\]|\[보안\]"
    r"|\[사전규격\]|\[발주계획\]"
    r")\s*",
)

def _normalize_title(title: str) -> str:
    """재공고/긴급 접두사 제거 + 공백 정규화 → 중복 판별용 키."""
    t = _NOISE_PREFIXES.sub("", title)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:50]  # 앞 50자로 비교


# ─────────────────────────────────────────────
# 스코어링 함수
# ─────────────────────────────────────────────

def score_bid(raw: Dict[str, Any], reference_date: Optional[date] = None) -> BidScore:
    """
    단일 공고에 대해 tenopa 적합도 점수를 산출한다.

    4단계:
      1. 역할 키워드 필수 매칭 (1개 이상)
      2. 분류 가중치
      3. 도메인 키워드 가산 (핵심 도메인 추가 가산)
      4. 컨텍스트 감점 (현장 실행형 패턴)
    """
    ref = reference_date or date.today()

    title = raw.get("bidNtceNm", "")
    title_lower = title.lower()
    agency = raw.get("dminsttNm", "") or raw.get("ntceInsttNm", "")
    cls_detail = (raw.get("pubPrcrmntClsfcNm") or "").strip()
    cls_large = (raw.get("pubPrcrmntLrgClsfcNm") or "").strip()

    # 예산 파싱
    budget_raw = raw.get("presmptPrce") or raw.get("asignBdgtAmt") or "0"
    try:
        budget = int(str(budget_raw).replace(",", "").strip() or "0")
    except (ValueError, TypeError):
        budget = 0

    # 마감일 파싱
    deadline_str = raw.get("bidClseDt", "") or ""
    d_day = None
    if deadline_str:
        for fmt in ("%Y/%m/%d %H:%M:%S", "%Y%m%d%H%M%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                dl = datetime.strptime(str(deadline_str).strip()[:19], fmt)
                d_day = (dl.date() - ref).days
                break
            except ValueError:
                continue

    result = BidScore(
        bid_no=raw.get("bidNtceNo", ""),
        title=title,
        agency=agency,
        budget=budget,
        deadline=deadline_str[:10] if deadline_str else "",
        d_day=d_day,
        classification=cls_detail,
        classification_large=cls_large,
        bid_stage=raw.get("_bid_stage", "입찰공고"),
        raw=raw,
    )

    # ── 1단계: 역할 키워드 필수 매칭 ──────────────────
    for kw in ROLE_KEYWORDS:
        if kw.lower() in title_lower:
            result.role_keywords_matched.append(kw)

    if not result.role_keywords_matched:
        result.passed = False
        result.score = -1
        return result

    result.passed = True

    # ── 2단계: 분류 가중치 ──────────────────────────
    cls_combined = f"{cls_large} {cls_detail}".lower()
    for pattern, weight in CLASSIFICATION_WEIGHTS:
        if pattern.lower() in cls_combined:
            result.classification_score += weight

    # ── 3단계: 도메인 키워드 가산 ────────────────────
    for kw in DOMAIN_KEYWORDS:
        if kw.lower() in title_lower:
            result.domain_keywords_matched.append(kw)

    # 핵심 도메인 체크
    core_matched = [kw for kw in CORE_DOMAIN_KEYWORDS if kw.lower() in title_lower]
    result.is_core_domain = len(core_matched) > 0

    # ── 4단계: 컨텍스트 감점 ─────────────────────────
    has_exempt = any(ek.lower() in title_lower for ek in PENALTY_EXEMPT_KEYWORDS)
    if not has_exempt:
        for pattern, penalty in CONTEXT_PENALTY_KEYWORDS:
            if pattern in title:
                result.context_penalty += penalty

    # ── 최종 점수 산출 ─────────────────────────────
    score = 0.0

    # 역할 키워드 매칭 수 (핵심 가중치)
    score += len(result.role_keywords_matched) * 25

    # 고가치 역할 조합 보너스
    matched_set = set(result.role_keywords_matched)
    combo_bonus = sum(
        15 for combo in HIGH_VALUE_ROLE_COMBOS
        if combo.issubset(matched_set)
    )
    score += min(combo_bonus, 30)  # 최대 30점

    # 분류 가중치
    score += result.classification_score

    # 도메인 키워드 매칭
    score += len(result.domain_keywords_matched) * 10
    # 핵심 도메인 추가 가산
    if result.is_core_domain:
        score += len(core_matched) * 5

    # 컨텍스트 감점
    score += result.context_penalty

    # 예산 규모 가산 (1억당 2점, 최대 30점)
    budget_eok = budget / 100_000_000
    score += min(budget_eok * 2, 30)

    # 마감 임박 가산
    if d_day is not None:
        if 3 <= d_day <= 7:
            score += 10
        elif 7 < d_day <= 14:
            score += 5
        elif d_day < 0:
            score -= 50  # 이미 마감

    result.score = round(score, 1)
    return result


def score_and_rank_bids(
    bids: List[Dict[str, Any]],
    reference_date: Optional[date] = None,
    min_score: float = 0,
    exclude_expired: bool = True,
    max_results: int = 50,
    min_days_remaining: int = 0,
) -> List[BidScore]:
    """
    공고 목록을 스코어링하고 적합도순으로 정렬.

    중복 제거: bid_no 기반 + 제목 유사도 기반 (재공고/긴급 접두사 무시)
    """
    scored = []
    for raw in bids:
        # ── Pre-filter: score_bid() 호출 전 저비용 조건으로 먼저 제거 ──

        # 1) 수의시담 제외: 이미 업체가 정해진 건이므로 모니터링 불필요
        bid_method = (raw.get("bidMethdNm") or raw.get("cntrctMthdNm") or "").strip()
        if any(ex in bid_method for ex in EXCLUDED_BID_METHODS):
            continue

        # 2) 역할 키워드 제목 pre-filter
        #    score_bid() 내부 1단계와 동일한 조건이지만,
        #    BidScore 객체 생성·예산파싱·마감일파싱 없이 문자열 검색만으로 처리.
        #    전수 수집 공고의 ~80%를 여기서 제거해 불필요한 연산을 방지.
        title_lower = raw.get("bidNtceNm", "").lower()
        if not any(kw in title_lower for kw in _ROLE_KW_LOWER):
            continue

        # ── 역할 키워드 통과 → 전체 스코어링 실행 ──
        bs = score_bid(raw, reference_date)
        if not bs.passed:
            continue
        if bs.score < min_score:
            continue
        if exclude_expired and bs.d_day is not None and bs.d_day < 0:
            continue
        if min_days_remaining > 0 and bs.d_day is not None and bs.d_day < min_days_remaining:
            continue
        scored.append(bs)

    scored.sort(key=lambda x: x.score, reverse=True)

    # 중복 제거: bid_no + 제목 정규화
    seen_nos: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[BidScore] = []
    for bs in scored:
        if bs.bid_no in seen_nos:
            continue
        norm_title = _normalize_title(bs.title)
        if norm_title in seen_titles:
            continue
        seen_nos.add(bs.bid_no)
        seen_titles.add(norm_title)
        unique.append(bs)

    return unique[:max_results]
