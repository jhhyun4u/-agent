"""
테크노베이션파트너스 수행실적 Excel → 로컬 역량 JSON 변환

소스: TENOPA Project History (HYUN).xlsx (766건)
출력: data/company_profile.json
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import openpyxl

# ── 경로 설정 ──────────────────────────────────────
EXCEL_PATH = Path(
    r"c:\Users\현재호\OneDrive - 테크노베이션파트너스"
    r"\바탕 화면\TENOPA Project History (HYUN).xlsx"
)
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "company_profile.json"

# ── 불용어 (키워드 추출 시 제거) ────────────────────
STOPWORDS = {
    # 일반 조사·접속
    "및", "등", "의", "을", "를", "이", "가", "은", "는", "에", "에서",
    "으로", "로", "과", "와", "대한", "위한", "관한", "따른", "통한",
    # 일반 동사·명사 (과제명에 흔하지만 도메인 특이성 낮음)
    "기술", "개발", "사업", "연구", "용역", "수립", "조사", "분석",
    "구축", "운영", "지원", "관리", "서비스", "시스템", "평가",
    "추진", "활용", "방안", "계획", "기반", "강화", "확대",
    "고도화", "개선", "도입", "설계", "제도", "정책", "전략",
    "체계", "플랫폼", "실태", "현황", "보고서", "마련", "수행",
    "과제", "프로젝트", "산업", "기관", "센터", "재단", "진흥원",
    "협회", "학회", "위원회", "연구원", "본부", "부문",
    "년도", "차년도", "단계", "후속",
    # 범용어 (공고 제목에 너무 흔해 매칭 노이즈 유발)
    "관련", "분야", "국가", "국내", "국내외", "종합", "대형",
    "사업의", "육성을", "추진을", "지원을", "극복을", "수립을",
    "성과", "확보", "신규",
}

# ── 홈페이지 사업영역 (고정) ─────────────────────────
SERVICES = ["R&D Nexus", "AI Transformation", "T2B & Regional Innovation", "Future Workforce"]

TECH_DOMAINS = [
    "AI·로봇", "바이오·헬스케어", "우주·해양", "양자기술",
    "에너지·환경", "반도체·소재", "자동차·모빌리티", "국방·안보",
    "ICT·SW", "문화·콘텐츠", "농식품", "건설·인프라",
]


def parse_excel() -> list[dict]:
    """Excel 파싱 → track_records 리스트."""
    wb = openpyxl.load_workbook(str(EXCEL_PATH), read_only=True, data_only=True)
    ws = wb.active

    records = []
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        # 컬럼: 번호, 과제명, 발주처, 관련부처, 총개발기간, 과제개월수, 계약금액(천원), 연구책임자, 키워드, 요약, 비고
        title = str(row[1] or "").strip()
        if not title:
            continue

        client = str(row[2] or "").strip()
        department = str(row[3] or "").strip()
        period = str(row[4] or "").strip()

        # 계약금액: 천원 단위 → 원 단위
        budget_raw = row[6]
        try:
            budget_krw = int(float(budget_raw or 0)) * 1000
        except (ValueError, TypeError):
            budget_krw = 0

        # 키워드: Excel에 있으면 사용, 없으면 자동 추출
        manual_kw = str(row[8] or "").strip() if len(row) > 8 else ""
        if manual_kw:
            keywords = [k.strip() for k in re.split(r"[,;/·]", manual_kw) if k.strip()]
        else:
            keywords = extract_keywords(title)

        records.append({
            "title": title,
            "client": client,
            "department": department,
            "budget_krw": budget_krw,
            "period": period,
            "keywords": keywords,
        })

    wb.close()
    return records


def extract_keywords(title: str) -> list[str]:
    """과제명에서 도메인 키워드 추출."""
    # 한글 2글자 이상, 영문 2글자 이상
    tokens = re.findall(r"[가-힣]{2,}|[A-Za-z]{2,}", title)
    return [t for t in tokens if t.lower() not in {s.lower() for s in STOPWORDS} and len(t) >= 2]


def build_keyword_index(records: list[dict]) -> dict:
    """키워드 빈도 인덱스 생성."""
    domain_counter = Counter()
    client_counter = Counter()
    dept_counter = Counter()

    for r in records:
        for kw in r["keywords"]:
            domain_counter[kw] += 1
        if r["client"]:
            client_counter[r["client"]] += 1
        if r["department"]:
            dept_counter[r["department"]] += 1

    return {
        "domain_keywords": dict(domain_counter.most_common()),
        "client_frequency": dict(client_counter.most_common()),
        "department_frequency": dict(dept_counter.most_common()),
    }


def build_search_keywords(keyword_index: dict, min_freq: int = 5) -> list[str]:
    """검색용 키워드: 빈도 min_freq 이상."""
    return [kw for kw, cnt in keyword_index["domain_keywords"].items() if cnt >= min_freq]


def build_profile(records: list[dict]) -> dict:
    """전체 프로필 JSON 생성."""
    budgets = [r["budget_krw"] for r in records if r["budget_krw"] > 0]
    keyword_index = build_keyword_index(records)
    search_keywords = build_search_keywords(keyword_index)

    profile = {
        "company": {
            "name": "테크노베이션파트너스",
            "services": SERVICES,
            "tech_domains": TECH_DOMAINS,
            "stats": {
                "total_projects": len(records),
                "avg_budget_krw": int(sum(budgets) / len(budgets)) if budgets else 0,
                "min_budget_krw": min(budgets) if budgets else 0,
                "max_budget_krw": max(budgets) if budgets else 0,
                "total_budget_krw": sum(budgets),
            },
        },
        "track_records": records,
        "keyword_index": keyword_index,
        "search_keywords": search_keywords,
    }
    return profile


def main():
    if not EXCEL_PATH.exists():
        print(f"[ERROR] Excel 파일 없음: {EXCEL_PATH}")
        sys.exit(1)

    print(f"[1/3] Excel 파싱: {EXCEL_PATH.name}")
    records = parse_excel()
    print(f"      → {len(records)}건 파싱 완료")

    print("[2/3] 프로필 생성")
    profile = build_profile(records)
    stats = profile["company"]["stats"]
    print(f"      → 평균 예산: {stats['avg_budget_krw']:,.0f}원")
    print(f"      → 검색 키워드: {len(profile['search_keywords'])}개")

    print(f"[3/3] 저장: {OUTPUT_PATH}")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    # 요약
    ki = profile["keyword_index"]
    print("\n━━━ 요약 ━━━")
    print(f"총 수행실적: {stats['total_projects']}건")
    print(f"상위 발주처: {', '.join(list(ki['client_frequency'].keys())[:5])}")
    print(f"상위 부처: {', '.join(list(ki['department_frequency'].keys())[:5])}")
    print(f"상위 도메인 키워드: {', '.join(profile['search_keywords'][:15])}")


if __name__ == "__main__":
    main()
