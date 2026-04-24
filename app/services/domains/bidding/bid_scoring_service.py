"""DB 기반 공고 적합도 스코어링 (company_profile.json 대체).

v1 (JSON): 키워드빈도40 + 발주처빈도30 + 부처빈도20 + 예산범위10
v2 (DB):   벡터유사도30 + 키워드매칭20 + 발주처경험25 + 부처경험15 + 예산범위10
"""

import logging
import math

from app.services.domains.vault.embedding_service import generate_embedding
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


def _parse_budget(raw) -> int:
    """공고 예산 문자열 → 원 단위 정수."""
    if not raw:
        return 0
    try:
        return int(str(raw).replace(",", "").strip() or "0")
    except (ValueError, TypeError):
        return 0


class BidScoringService:
    """DB(intranet_projects) 기반 공고 스코어링."""

    async def score_bid(self, org_id: str, bid: dict) -> dict:
        """공고 적합도 스코어 (0~100)."""
        title = bid.get("bidNtceNm", "")
        client_name = bid.get("ntceInsttNm", "") or bid.get("dminsttNm", "")
        budget = _parse_budget(bid.get("presmptPrce") or bid.get("asignBdgtAmt"))

        db = await get_async_client()

        # 1. 벡터 유사도 (30점)
        vector_score = 0.0
        similar_projects: list[str] = []
        try:
            embedding = await generate_embedding(title)
            result = await db.rpc("search_projects_by_embedding", {
                "query_embedding": embedding,
                "match_org_id": org_id,
                "match_count": 5,
            }).execute()
            items = result.data or []
            if items:
                avg_sim = sum(r.get("similarity", 0) for r in items) / len(items)
                vector_score = min(avg_sim * 40, 30.0)
                similar_projects = [r["project_name"] for r in items[:3]]
        except Exception as e:
            logger.debug(f"벡터 검색 실패 (폴백 0점): {e}")

        # 2. 키워드 매칭 (20점)
        keyword_stats = await self._get_keyword_stats(db, org_id)
        title_lower = title.lower()
        matched_kw = [kw for kw in keyword_stats if kw.lower() in title_lower]
        weighted_hits = sum(
            1.0 + math.log2(max(keyword_stats.get(kw, 1), 1)) * 0.15
            for kw in matched_kw
        )
        kw_score = min(weighted_hits / 2.0, 1.0) * 20

        # 3. 발주처 경험 (25점)
        client_count = await self._count_client_projects(db, org_id, client_name)
        if client_count > 0:
            client_score = min(15.0 + client_count * 2, 25.0)
        else:
            client_score = 0.0

        # 4. 부처 경험 (15점)
        dept_score, matched_dept = await self._score_department(db, org_id, client_name, title)

        # 5. 예산 범위 (10점)
        budget_score = self._score_budget(budget)

        total = round(vector_score + kw_score + client_score + dept_score + budget_score)

        return {
            "score": total,
            "matched_keywords": matched_kw,
            "similar_projects": similar_projects,
            "client_project_count": client_count,
            "matched_dept": matched_dept,
            "score_detail": {
                "vector_similarity": round(vector_score, 1),
                "keyword": round(kw_score, 1),
                "client": round(client_score, 1),
                "department": round(dept_score, 1),
                "budget": round(budget_score, 1),
            },
        }

    async def _get_keyword_stats(self, db, org_id: str) -> dict[str, int]:
        """키워드 빈도 집계 (keyword_index.domain_keywords 대체)."""
        result = await (
            db.table("intranet_projects")
            .select("keywords")
            .eq("org_id", org_id)
            .execute()
        )

        freq: dict[str, int] = {}
        for row in result.data or []:
            for kw in row.get("keywords") or []:
                if kw and len(kw) >= 2:
                    freq[kw] = freq.get(kw, 0) + 1
        return freq

    async def _count_client_projects(self, db, org_id: str, client_name: str) -> int:
        """발주기관 수행 횟수."""
        if not client_name:
            return 0
        result = await (
            db.table("intranet_projects")
            .select("id", count="exact")
            .eq("org_id", org_id)
            .ilike("client_name", f"%{client_name}%")
            .execute()
        )
        return result.count or 0

    async def _score_department(
        self, db, org_id: str, client_name: str, title: str,
    ) -> tuple[float, str | None]:
        """부처 경험 스코어 (15점 만점)."""
        result = await (
            db.table("intranet_projects")
            .select("department")
            .eq("org_id", org_id)
            .not_.is_("department", "null")
            .execute()
        )

        dept_freq: dict[str, int] = {}
        total = 0
        for row in result.data or []:
            dept = row.get("department")
            if dept:
                dept_freq[dept] = dept_freq.get(dept, 0) + 1
                total += 1

        if not dept_freq:
            return 0.0, None

        text = f"{title} {client_name}"
        for dept, count in sorted(dept_freq.items(), key=lambda x: -x[1]):
            if dept in text:
                score = min((count / max(total, 1)) * 100, 15.0)
                return score, dept

        return 0.0, None

    @staticmethod
    def _score_budget(budget: int) -> float:
        """예산 범위 적합도 (10점 만점)."""
        if budget <= 0:
            return 0.0
        if 10_000_000 <= budget <= 700_000_000:
            return 10.0
        elif budget < 10_000_000:
            return 3.0
        else:
            return 5.0

    async def build_profile_from_db(self, org_id: str) -> dict:
        """
        DB에서 company_profile.json 호환 프로필 생성.

        bid_scoring.py의 load_profile() 폴백에서 사용.
        """
        db = await get_async_client()

        projects = await (
            db.table("intranet_projects")
            .select("project_name, client_name, department, budget_krw, keywords, "
                    "start_date, end_date")
            .eq("org_id", org_id)
            .execute()
        )
        rows = projects.data or []

        if not rows:
            return {"company": {"stats": {"total_projects": 0}}}

        # 통계
        budgets = [r["budget_krw"] for r in rows if r.get("budget_krw") and r["budget_krw"] > 0]

        # 키워드 인덱스
        domain_kw: dict[str, int] = {}
        client_freq: dict[str, int] = {}
        dept_freq: dict[str, int] = {}

        track_records = []
        for r in rows:
            for kw in r.get("keywords") or []:
                if kw and len(kw) >= 2:
                    domain_kw[kw] = domain_kw.get(kw, 0) + 1
            cn = r.get("client_name")
            if cn:
                client_freq[cn] = client_freq.get(cn, 0) + 1
            dept = r.get("department")
            if dept:
                dept_freq[dept] = dept_freq.get(dept, 0) + 1

            track_records.append({
                "title": r.get("project_name", ""),
                "client": cn or "",
                "department": dept or "",
                "budget_krw": r.get("budget_krw") or 0,
                "period": f"{r.get('start_date', '')} ~ {r.get('end_date', '')}",
                "keywords": r.get("keywords") or [],
            })

        search_keywords = [kw for kw, cnt in
                           sorted(domain_kw.items(), key=lambda x: -x[1])
                           if cnt >= 5]

        return {
            "company": {
                "name": "테크노베이션파트너스",
                "stats": {
                    "total_projects": len(rows),
                    "avg_budget_krw": int(sum(budgets) / len(budgets)) if budgets else 0,
                    "min_budget_krw": min(budgets) if budgets else 0,
                    "max_budget_krw": max(budgets) if budgets else 0,
                    "total_budget_krw": sum(budgets),
                },
            },
            "track_records": track_records,
            "keyword_index": {
                "domain_keywords": dict(sorted(domain_kw.items(), key=lambda x: -x[1])),
                "client_frequency": dict(sorted(client_freq.items(), key=lambda x: -x[1])),
                "department_frequency": dict(sorted(dept_freq.items(), key=lambda x: -x[1])),
            },
            "search_keywords": search_keywords,
        }
