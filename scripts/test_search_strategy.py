"""전략 기획 관련 공고 검색 + AI 평가 테스트.

G2B API 장애로 mock 데이터 사용.
실제 G2B 응답 형식과 동일한 구조.
"""
import asyncio
import sys

sys.path.insert(0, ".")

from app.services.core.claude_client import claude_generate
from app.config import settings


# 2026-03-06 ~ 2026-03-13 신규 공고 (전략 기획 관련 mock)
MOCK_RECENT_BIDS = [
    {
        "bid_no": "20260312-101",
        "project_name": "2026년 디지털 전환 중장기 전략 수립 용역",
        "client": "과학기술정보통신부",
        "budget": "1,200,000,000",
        "deadline": "2026-04-18 18:00",
        "announce_date": "2026-03-12",
    },
    {
        "bid_no": "20260311-055",
        "project_name": "공공 데이터 활용 기반 정책분석 체계 고도화 ISP",
        "client": "한국정보화진흥원",
        "budget": "800,000,000",
        "deadline": "2026-04-12 18:00",
        "announce_date": "2026-03-11",
    },
    {
        "bid_no": "20260311-033",
        "project_name": "AI 기반 스마트시티 통합플랫폼 마스터플랜 수립",
        "client": "국토교통부",
        "budget": "1,500,000,000",
        "deadline": "2026-04-22 18:00",
        "announce_date": "2026-03-11",
    },
    {
        "bid_no": "20260310-078",
        "project_name": "차세대 전자정부 아키텍처 전략 기획 및 로드맵 수립",
        "client": "행정안전부",
        "budget": "2,000,000,000",
        "deadline": "2026-04-25 18:00",
        "announce_date": "2026-03-10",
    },
    {
        "bid_no": "20260309-044",
        "project_name": "2026년 국방 정보화 중기 계획 수립 연구용역",
        "client": "국방부",
        "budget": "900,000,000",
        "deadline": "2026-04-08 18:00",
        "announce_date": "2026-03-09",
    },
    {
        "bid_no": "20260308-091",
        "project_name": "공공기관 클라우드 네이티브 전환 전략 컨설팅",
        "client": "한국지능정보사회진흥원(NIA)",
        "budget": "1,100,000,000",
        "deadline": "2026-04-15 18:00",
        "announce_date": "2026-03-08",
    },
    {
        "bid_no": "20260307-022",
        "project_name": "지역 산업 디지털 혁신 전략 수립 및 실행방안 도출",
        "client": "중소벤처기업부",
        "budget": "650,000,000",
        "deadline": "2026-04-10 18:00",
        "announce_date": "2026-03-07",
    },
    {
        "bid_no": "20260307-016",
        "project_name": "금융 분야 AI 도입 전략 및 규제 프레임워크 연구",
        "client": "금융위원회",
        "budget": "700,000,000",
        "deadline": "2026-04-05 18:00",
        "announce_date": "2026-03-07",
    },
]


MOCK_CAPABILITIES = """- [track_record] 클라우드 ERP 시스템 구축: A공공기관 ERP 클라우드 전환 (2024, 10억원, 6개월)
- [track_record] AI 민원분석 시스템: B지자체 민원 자동분류 시스템 구축 (2025, 8억원)
- [track_record] 디지털 전환 ISP: C부처 디지털 전환 정보전략계획 수립 (2024, 5억원)
- [tech] AI/ML 파이프라인: LangGraph 멀티에이전트, RAG, Python/FastAPI
- [tech] 클라우드 아키텍처: AWS/Azure 기반 MSA 설계 및 구축
- [tech] 데이터 분석: 공공데이터 기반 정책 분석, 대시보드 구축
- [personnel] PMP 보유 PM 5명: 공공SI 평균 경력 10년
- [personnel] AI 전문인력 8명: 석사 이상 4명, 관련 자격증 보유
- [personnel] ISP/BPR 컨설턴트 3명: 정보관리기술사 2명"""


def _format_bids(bids: list[dict]) -> str:
    lines = []
    for i, b in enumerate(bids, 1):
        lines.append(
            f"{i}. [{b['bid_no']}] {b['project_name']} | "
            f"{b['client']} | {b['budget']}원 | 마감: {b['deadline']} | 공고일: {b['announce_date']}"
        )
    return "\n".join(lines)


async def main():
    print("=" * 70)
    print("  G2B 공고 검색 테스트: 전략 기획 관련 (2026-03-06 ~ 03-13)")
    print("  * G2B API 장애로 mock 데이터 사용")
    print("=" * 70)

    print(f"\n--- 최근 1주 공고 목록 ({len(MOCK_RECENT_BIDS)}건) ---\n")
    for i, b in enumerate(MOCK_RECENT_BIDS, 1):
        budget_bil = int(b['budget'].replace(',', '')) / 100_000_000
        print(f"  {i}. [{b['announce_date']}] {b['project_name']}")
        print(f"     {b['client']} | {budget_bil:.0f}억원 | 마감 {b['deadline'][:10]}")

    if not settings.anthropic_api_key:
        print("\n[SKIP] ANTHROPIC_API_KEY 미설정")
        return

    prompt = f"""당신은 IT 용역 전문 기업의 전략기획팀 AI 어시스턴트입니다.
다음 나라장터(G2B) 공고 목록에서 '전략 기획' 관련 과제를 자사 역량 기준으로 평가하세요.

## 검색 조건
- 기간: 2026-03-06 ~ 2026-03-13 (최근 1주)
- 분야: 전략 기획 (ISP, 마스터플랜, 로드맵, 전략 수립, 컨설팅)

## 공고 목록
{_format_bids(MOCK_RECENT_BIDS)}

## 자사 역량
{MOCK_CAPABILITIES}

## 평가 기준
1. fit_score (0~100): 자사 역량 대비 적합도
2. expected_positioning: defensive(수성) / offensive(공격) / adjacent(인접 확장)
3. 전략 기획/컨설팅 성격이 강한 과제 우선

## 출력 형식 (JSON 배열, 적합도 상위 5건)
[
  {{
    "rank": 1,
    "bid_no": "공고번호",
    "project_name": "사업명",
    "client": "발주기관",
    "budget": "예산",
    "deadline": "마감일",
    "fit_score": 85,
    "fit_rationale": "적합도 판단 근거 (3문장)",
    "expected_positioning": "offensive",
    "key_strengths": ["우리의 강점 1", "강점 2"],
    "risks": ["리스크 1"],
    "recommended_action": "참여 적극 추천 / 참여 검토 / 선별 참여"
  }}
]

반드시 JSON 배열만 출력하세요.
"""

    print("\n[AI] Claude 전략 기획 과제 평가 중...\n")
    result = await claude_generate(prompt, max_tokens=4000)

    if isinstance(result, list):
        recs = result
    elif isinstance(result, dict) and not result.get("_parse_error"):
        recs = result.get("recommendations", [result])
    else:
        print(f"  응답 파싱 실패: {str(result)[:200]}")
        return

    print("=" * 70)
    print(f"  AI 추천 결과 ({len(recs)}건)")
    print("=" * 70)

    for rec in recs:
        score = rec.get("fit_score", 0)
        grade = "S" if score >= 90 else "A" if score >= 80 else "B" if score >= 70 else "C" if score >= 60 else "D"
        pos = rec.get("expected_positioning", "?")
        pos_map = {"defensive": "수성", "offensive": "공격", "adjacent": "인접확장"}
        pos_label = pos_map.get(pos, pos)
        action = rec.get("recommended_action", "")

        print(f"\n  #{rec.get('rank', '?')}  [{grade}] 적합도 {score}점 | {pos_label} | {action}")
        print(f"  {'='*60}")
        print(f"  사업명:   {rec.get('project_name', '')}")
        print(f"  발주기관: {rec.get('client', '')}")
        print(f"  예산:     {rec.get('budget', '')}원")
        print(f"  마감:     {rec.get('deadline', '')}")
        print("  ---")
        print(f"  판단근거: {rec.get('fit_rationale', '')}")

        strengths = rec.get("key_strengths", [])
        if strengths:
            print(f"  강점:     {' / '.join(strengths)}")

        risks = rec.get("risks", [])
        if risks:
            print(f"  리스크:   {' / '.join(risks)}")

    print(f"\n{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
