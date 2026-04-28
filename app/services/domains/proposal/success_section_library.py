"""
성공 섹션 라이브러리 서비스 — 학술연구용역 특화

수주 제안서 → 섹션 자동 추출·분류 → 품질 점수 산출 → 유사 섹션 추천
"""

import json
import logging
import re
from datetime import datetime, timezone

from app.services.domains.vault.embedding_service import (
    embedding_text_for_content,
    generate_embedding,
)
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

# ── 학술연구용역 과제 유형 분류 키워드 ─────────────────────────────────────

STUDY_TYPE_PATTERNS: dict[str, list[str]] = {
    "기초조사":   ["기초조사", "현황조사", "기초 조사", "현황 조사"],
    "실태조사":   ["실태조사", "실태 분석", "실태 연구", "실태 파악"],
    "정책연구":   ["정책연구", "제도연구", "법제도", "정책 연구", "법령", "제도 개선", "정책 분석"],
    "타당성분석": ["타당성", "예비타당성", "사전타당성", "타당성 분석", "feasibility"],
    "성과평가":   ["성과평가", "사업평가", "효과성 평가", "성과 분석", "사후 평가", "중간 평가"],
    "계획수립":   ["기본계획", "종합계획", "마스터플랜", "중장기 계획", "발전계획", "추진계획", "기본 계획"],
    "중장기전략": ["중장기전략", "발전전략", "비전", "로드맵", "중장기 전략"],
    "컨설팅":     ["컨설팅", "자문", "컨설팅 용역", "경영 진단"],
}

# ── 섹션 유형 → section_category 매핑 ─────────────────────────────────────
# section_prompts.py의 SECTION_TYPES 기준

SECTION_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "UNDERSTAND":   ["사업의 이해", "과업의 이해", "목적", "배경", "현황", "필요성", "범위", "개요"],
    "STRATEGY":     ["추진 전략", "전략", "방향", "프레임워크", "핵심 성공"],
    "METHODOLOGY":  ["방법론", "수행 방법", "수행 절차", "프로세스", "수행 체계", "수행 방안", "단계별"],
    "MANAGEMENT":   ["사업 관리", "일정", "품질", "리스크", "추진 체계", "조직", "관리 방안"],
    "PERSONNEL":    ["인력", "투입 인력", "인력 구성", "연구진", "연구팀", "약력", "경력", "역할"],
    "TRACK_RECORD": ["수행 실적", "실적", "유사 사업", "수행 경험", "레퍼런스", "회사 소개", "수행경험"],
    "ADDED_VALUE":  ["기대효과", "기대 성과", "활용 방안", "파급효과", "성과 목표"],
}

CLIENT_TYPE_KEYWORDS: dict[str, list[str]] = {
    "중앙부처": ["부", "처", "청", "원", "위원회", "부처", "국가", "정부"],
    "지자체":   ["특별시", "광역시", "도", "시청", "군청", "구청", "지자체", "지방"],
    "공공기관": ["공단", "공사", "진흥원", "연구원", "센터", "재단", "협회", "원"],
    "민간":     ["주식회사", "(주)", "기업", "그룹", "협동조합"],
}


def _detect_study_type(text: str) -> str:
    """RFP 내용에서 과제 유형 자동 감지."""
    text_lower = text.lower()
    for study_type, keywords in STUDY_TYPE_PATTERNS.items():
        if any(kw in text for kw in keywords):
            return study_type
    return "기타"


def _detect_section_category(section_title: str) -> str:
    """섹션 제목에서 섹션 분류 자동 감지."""
    for category, keywords in SECTION_CATEGORY_KEYWORDS.items():
        if any(kw in section_title for kw in keywords):
            return category
    return "기타"


def _detect_client_type(client_name: str) -> str:
    """발주기관명에서 기관 유형 감지."""
    for client_type, keywords in CLIENT_TYPE_KEYWORDS.items():
        if any(kw in client_name for kw in keywords):
            return client_type
    return "기타"


def _compute_quality_score(
    won_count: int,
    lost_count: int,
    reuse_count: int,
    diagnosis_score: float | None,
    updated_at: str | None,
) -> float:
    """
    품질 점수 (0~100):
      수주율 × 40 + 진단점수 × 30 + 재사용률 × 20 + 신선도 × 10
    """
    total = won_count + lost_count
    won_rate = (won_count / total) if total > 0 else 0.5  # 데이터 없으면 중립

    diag_rate = ((diagnosis_score or 70) / 100)

    reuse_rate = min(reuse_count / 10, 1.0)

    freshness = 1.0
    if updated_at:
        try:
            updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            days = (datetime.now(timezone.utc) - updated).days
            freshness = max(0.0, 1.0 - max(0, days - 180) * 0.003)
        except ValueError:
            pass

    return round(
        won_rate * 40 + diag_rate * 30 + reuse_rate * 20 + freshness * 10, 2
    )


# ── 수주 섹션 추출 ─────────────────────────────────────────────────────────

async def extract_and_register_won_sections(proposal_id: str, org_id: str) -> int:
    """수주 확정 시 제안서 섹션을 성공 섹션 라이브러리에 자동 등록.

    Returns: 등록된 섹션 수
    """
    client = await get_async_client()

    # 제안서 기본 정보
    proposal_res = await (
        client.table("proposals")
        .select("id, title, client_name, rfp_content, bid_amount, org_id")
        .eq("id", proposal_id)
        .single()
        .execute()
    )
    if not proposal_res.data:
        logger.warning(f"제안서를 찾을 수 없음: {proposal_id}")
        return 0

    proposal = proposal_res.data
    rfp_text = proposal.get("rfp_content", "") or ""
    client_name = proposal.get("client_name", "") or ""
    study_type = _detect_study_type(rfp_text)
    client_type = _detect_client_type(client_name)
    contract_amount = proposal.get("bid_amount")

    # 계약 규모 분류
    if contract_amount:
        if contract_amount >= 300_000_000:
            contract_scale = "대형"
        elif contract_amount >= 100_000_000:
            contract_scale = "중형"
        else:
            contract_scale = "소형"
    else:
        contract_scale = None

    # proposal 산출물에서 섹션 목록 가져오기
    artifact_res = await (
        client.table("artifacts")
        .select("data")
        .eq("proposal_id", proposal_id)
        .eq("step", "proposal")
        .order("version", desc=True)
        .limit(1)
        .execute()
    )

    sections_raw: list[dict] = []
    if artifact_res.data:
        data = artifact_res.data[0].get("data") or {}
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                data = {}
        sections_raw = data.get("sections") or data.get("dynamic_sections") or []

    # 섹션 진단 데이터
    diag_res = await (
        client.table("section_diagnostics")
        .select("section_id, overall_score, recommendation")
        .eq("proposal_id", proposal_id)
        .execute()
    )
    diag_map: dict[str, dict] = {}
    for d in (diag_res.data or []):
        diag_map[d["section_id"]] = d

    registered = 0
    for sec in sections_raw:
        sec_id = sec.get("id", "")
        title = sec.get("title", "").strip()
        content = sec.get("content", "").strip()

        if not title or len(content) < 300:
            continue

        diag = diag_map.get(sec_id, {})
        diagnosis_score = diag.get("overall_score")
        recommendation = diag.get("recommendation", "")

        # 진단 점수 낮거나 rework 권고 섹션은 등록 제외
        if diagnosis_score is not None and diagnosis_score < 60:
            continue
        if recommendation == "rework":
            continue

        section_category = _detect_section_category(title)
        tags = [study_type, section_category, client_type, "수주"]
        if contract_scale:
            tags.append(contract_scale)

        embed_text = embedding_text_for_content(title, content, tags)
        embedding = await generate_embedding(embed_text)

        # 기존 항목 확인 (같은 proposal + section)
        existing = await (
            client.table("content_library")
            .select("id, won_count, lost_count, reuse_count, updated_at")
            .eq("source_project_id", proposal_id)
            .eq("title", title)
            .limit(1)
            .execute()
        )

        quality_score = _compute_quality_score(
            won_count=1,
            lost_count=0,
            reuse_count=0,
            diagnosis_score=diagnosis_score,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

        row = {
            "org_id": org_id,
            "title": title,
            "body": content,
            "type": "section_block",
            "source_project_id": proposal_id,
            "industry": client_type,
            "rfp_type": study_type,
            "tags": tags,
            "status": "published",
            "is_winning": True,
            "study_type": study_type,
            "section_category": section_category,
            "client_type": client_type,
            "diagnosis_score": diagnosis_score,
            "quality_score": quality_score,
            "embedding": embedding,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if existing.data:
            rec = existing.data[0]
            row["won_count"] = (rec.get("won_count") or 0) + 1
            row["lost_count"] = rec.get("lost_count") or 0
            row["reuse_count"] = rec.get("reuse_count") or 0
            await (
                client.table("content_library")
                .update(row)
                .eq("id", rec["id"])
                .execute()
            )
        else:
            row["won_count"] = 1
            row["lost_count"] = 0
            row["reuse_count"] = 0
            await client.table("content_library").insert(row).execute()

        registered += 1

    logger.info(
        f"수주 섹션 등록 완료: proposal={proposal_id}, 등록={registered}건, "
        f"study_type={study_type}, client={client_name}"
    )
    return registered


# ── 섹션 추천 ──────────────────────────────────────────────────────────────

async def recommend_winning_sections(
    section_title: str,
    section_category: str | None,
    study_type: str | None,
    org_id: str,
    top_k: int = 5,
) -> list[dict]:
    """섹션 작성 중 유사 수주 섹션 추천.

    우선순위: is_winning=true → 동일 study_type → 동일 section_category → quality_score
    """
    client = await get_async_client()

    embed_text = embedding_text_for_content(
        section_title, "", [section_category or "", study_type or ""]
    )
    embedding = await generate_embedding(embed_text)

    # pgvector 시맨틱 검색
    try:
        rpc_res = await client.rpc(
            "match_content_library",
            {
                "query_embedding": embedding,
                "match_threshold": 0.3,
                "match_count": top_k * 4,
                "p_org_id": org_id,
            },
        ).execute()
        candidates = rpc_res.data or []
    except Exception as e:
        logger.warning(f"시맨틱 검색 실패, 키워드 폴백: {e}")
        # 폴백: 키워드 검색
        res = await (
            client.table("content_library")
            .select("id, title, body, study_type, section_category, client_type, quality_score, is_winning, won_count, tags, source_project_id, diagnosis_score")
            .eq("org_id", org_id)
            .eq("status", "published")
            .ilike("title", f"%{section_title[:10]}%")
            .order("quality_score", desc=True)
            .limit(top_k * 2)
            .execute()
        )
        candidates = res.data or []

    # 스코어링 + 필터링
    def _rank(item: dict) -> float:
        score = item.get("similarity", 0.5)
        if item.get("is_winning"):
            score += 0.3
        if study_type and item.get("study_type") == study_type:
            score += 0.2
        if section_category and item.get("section_category") == section_category:
            score += 0.15
        qs = (item.get("quality_score") or 0) / 100
        score += qs * 0.1
        return score

    ranked = sorted(candidates, key=_rank, reverse=True)[:top_k]

    # 응답 정리 (body 미리보기 200자)
    return [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "preview": (item.get("body") or "")[:200],
            "study_type": item.get("study_type"),
            "section_category": item.get("section_category"),
            "client_type": item.get("client_type"),
            "quality_score": item.get("quality_score"),
            "is_winning": item.get("is_winning", False),
            "won_count": item.get("won_count", 0),
            "tags": item.get("tags", []),
            "diagnosis_score": item.get("diagnosis_score"),
        }
        for item in ranked
    ]


async def get_section_full_content(content_id: str, org_id: str) -> str | None:
    """섹션 전문 반환 + 재사용 카운트 증가."""
    client = await get_async_client()
    res = await (
        client.table("content_library")
        .select("body, reuse_count, won_count, lost_count, updated_at")
        .eq("id", content_id)
        .eq("org_id", org_id)
        .single()
        .execute()
    )
    if not res.data:
        return None

    # reuse_count 증가 + 품질 점수 재계산
    rec = res.data
    new_reuse = (rec.get("reuse_count") or 0) + 1
    new_quality = _compute_quality_score(
        won_count=rec.get("won_count") or 0,
        lost_count=rec.get("lost_count") or 0,
        reuse_count=new_reuse,
        diagnosis_score=None,
        updated_at=rec.get("updated_at"),
    )
    await (
        client.table("content_library")
        .update({"reuse_count": new_reuse, "quality_score": new_quality})
        .eq("id", content_id)
        .execute()
    )
    return rec.get("body", "")


async def get_library_stats(org_id: str) -> dict:
    """라이브러리 현황 통계."""
    client = await get_async_client()

    all_res = await (
        client.table("content_library")
        .select("id, is_winning, study_type, section_category, quality_score, won_count")
        .eq("org_id", org_id)
        .eq("status", "published")
        .execute()
    )
    items = all_res.data or []

    winning = [i for i in items if i.get("is_winning")]
    avg_quality = (
        sum(i.get("quality_score") or 0 for i in winning) / len(winning)
        if winning else 0
    )

    study_type_dist: dict[str, int] = {}
    for i in winning:
        st = i.get("study_type") or "기타"
        study_type_dist[st] = study_type_dist.get(st, 0) + 1

    section_cat_dist: dict[str, int] = {}
    for i in winning:
        cat = i.get("section_category") or "기타"
        section_cat_dist[cat] = section_cat_dist.get(cat, 0) + 1

    return {
        "total_sections": len(items),
        "winning_sections": len(winning),
        "avg_quality_score": round(avg_quality, 1),
        "study_type_distribution": study_type_dist,
        "section_category_distribution": section_cat_dist,
    }
