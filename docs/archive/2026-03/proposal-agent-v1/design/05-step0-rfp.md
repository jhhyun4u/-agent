# STEP 0: RFP 공고 검색 + Go/No-Go

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [03-graph-definition.md](03-graph-definition.md), [07-routing-edges.md](07-routing-edges.md)
> **원본 섹션**: §6, §7

---

## 6. STEP 0: RFP 공고 검색 노드

```python
# app/graph/nodes/rfp_search.py

MAX_RECOMMENDATIONS = 5  # 관심과제 후보 최대 5건

async def rfp_search(state: ProposalState) -> dict:
    """
    STEP 0: G2B 공고 검색 + AI 적합도 평가 + 추천 리스트 생성 (최대 5건).
    각 공고에 대해 요약정보(사업개요, 주요 요구사항, 평가방식, 경쟁강도)를 제공하여
    사용자가 관심과제를 선정할 수 있도록 한다.
    """
    # ★ A-3 + U-4: 검색 조건 결정 (초기 search_query > 재검색 피드백 > project_name)
    query_params = state.get("search_query", {})  # 초기 검색 조건 (프로젝트 생성 시 전달)

    # 재검색인 경우: feedback_history에서 최신 검색 조건 추출
    feedback_history = state.get("feedback_history", [])
    if feedback_history:
        last = feedback_history[-1]
        if last.get("step") == "search":
            raw_query = last.get("search_query", {})
            if isinstance(raw_query, dict):
                query_params = {**query_params, **raw_query}  # 기존 조건에 덮어씌움
            else:
                query_params["keywords"] = str(raw_query)

    search_keywords = query_params.get("keywords", "") or state.get("project_name", "")
    mode = state.get("mode", "full")

    # G2B 공고 검색
    raw_results = await g2b_client.search_bids(
        keywords=search_keywords,
        budget_min=query_params.get("budget_min"),
        region=query_params.get("region"),
    )

    if mode == "full":
        # 역량 DB + ★ v3.0: 발주기관·경쟁사 DB 기반 적합도 평가
        capabilities = await capability_store.get_all()
        # ★ v3.0: 검색 결과 발주기관에 대한 기존 입찰 이력 조회
        client_names = [r.get("client", "") for r in raw_results]
        client_histories = await client_intelligence.get_bid_histories_by_names(client_names)
        recommendations = await claude_generate(
            RFP_SEARCH_PROMPT.format(
                bids=raw_results,
                capabilities=capabilities,
                client_histories=client_histories,  # ★ v3.0: 발주기관 입찰 이력
                max_results=MAX_RECOMMENDATIONS,
                # 프롬프트 지시: 각 공고에 대해
                # - project_summary: 사업 개요 2~3문장
                # - key_requirements: 주요 요구사항 3~5개
                # - eval_method: 평가 방식 (기술:가격 비율 등)
                # - competition_level: 경쟁 강도 예측 (★ 발주기관 입찰 이력 참고)
                # - fit_score/rationale: 자사 역량 대비 적합도
            ),
        )
    else:
        # lite 모드: 역량 DB 없이 공고 요약만
        recommendations = await claude_generate(
            RFP_SEARCH_LITE_PROMPT.format(
                bids=raw_results,
                max_results=MAX_RECOMMENDATIONS,
            ),
        )

    # 적합도순 정렬, 최대 5건
    sorted_recs = sorted(recommendations, key=lambda r: r.get("fit_score", 0), reverse=True)
    return {
        "search_results": [RfpRecommendation(**r) for r in sorted_recs[:MAX_RECOMMENDATIONS]],
        "current_step": "search_complete",
    }
```

### 6-1. rfp_fetch: G2B 상세 수집 + RFP 업로드 게이트 — U-1 해결

> **하이브리드 방식**: G2B에서 공고 상세·첨부파일을 자동 수집하고, 사용자에게 RFP 원본 파일 업로드 기회를 제공한다.
> G2B 자동 추출 텍스트만으로도 진행 가능하지만, 사용자가 별도 RFP PDF를 업로드하면 더 정확한 분석이 된다.

```python
# app/graph/nodes/rfp_fetch.py
from langgraph.types import interrupt

async def rfp_fetch(state: ProposalState) -> dict:
    """
    STEP 0 → STEP 1 전환 노드:
    1) G2B API로 공고 상세 + 첨부파일 자동 수집
    2) 첨부파일 중 RFP PDF가 있으면 자동 파싱
    3) interrupt()로 사용자에게 추가 RFP 파일 업로드 기회 제공
    4) rfp_raw 확보 → rfp_analyze 진입 가능
    """
    bid_no = state.get("picked_bid_no", "")

    # ── 1) G2B 공고 상세 자동 수집 ──
    detail = await g2b_client.get_bid_detail(bid_no)
    bid_detail = BidDetail(
        bid_no=bid_no,
        project_name=detail["project_name"],
        client=detail["client"],
        budget=detail["budget"],
        deadline=detail["deadline"],
        description=detail.get("description", ""),
        requirements_summary=detail.get("requirements_summary", ""),
        attachments=detail.get("attachments", []),
    )

    # ── 2) G2B 첨부파일에서 RFP 자동 추출 시도 ──
    auto_rfp_text = ""
    for att in bid_detail.attachments:
        if att.get("type") in ("pdf", "hwp", "hwpx"):
            try:
                file_bytes = await g2b_client.download_attachment(att["url"])
                auto_rfp_text = await parse_rfp_bytes(file_bytes, att["type"])
                break  # 첫 번째 성공한 파일 사용
            except Exception:
                continue

    bid_detail.rfp_auto_text = auto_rfp_text

    # ── 3) interrupt: 사용자에게 RFP 파일 업로드 기회 ──
    human_input = interrupt({
        "step": "rfp_fetch",
        "bid_detail": bid_detail.model_dump(),
        "has_auto_rfp": bool(auto_rfp_text),
        "message": "공고 상세를 수집했습니다. RFP 원본 파일이 있으면 업로드하세요.",
        "hint": "G2B 첨부파일에서 RFP를 자동 추출했습니다." if auto_rfp_text
                else "G2B 첨부파일에서 RFP를 찾지 못했습니다. 직접 업로드해 주세요.",
    })

    # ── 4) 사용자 응답 처리 ──
    if human_input.get("rfp_file_text"):
        # 사용자가 RFP 파일 업로드 → 파싱된 텍스트 사용
        rfp_raw = human_input["rfp_file_text"]
    elif auto_rfp_text:
        # 사용자 스킵 + G2B 자동 추출 성공 → 자동 텍스트 사용
        rfp_raw = auto_rfp_text
    else:
        # G2B 추출 실패 + 사용자 스킵 → 공고 상세 설명만으로 진행
        rfp_raw = f"[공고 상세 기반]\n{bid_detail.description}\n\n{bid_detail.requirements_summary}"

    return {
        "bid_detail": bid_detail,
        "rfp_raw": rfp_raw,
        "project_name": bid_detail.project_name,  # 프로젝트 기본정보 자동 채움
        "current_step": "rfp_fetch_complete",
    }
```

---

## 7. STEP 1-②: Go/No-Go 노드 — B-2 추가

> **RFP 분석 완료 후**, 분석 결과 + 자사 역량 DB를 기반으로 포지셔닝 판정 및 수주 가능성을 평가한다.
> **★ v3.2**: `research_gather` 리서치 결과를 추가 컨텍스트로 주입. 발주기관 인텔리전스 5단계 분석 프레임워크 추가 (ProposalForge #3). 토큰 예산 15,000 → 18,000.

```python
# app/graph/nodes/go_no_go.py

async def go_no_go(state: ProposalState) -> dict:
    """
    STEP 1-②: RFP 분석 결과를 기반으로 Go/No-Go 평가.
    - Full 모드: 역량 DB + RFP 분석 + 리서치 브리프 → AI 포지셔닝 추천 + 수주 가능성 점수
    - Lite 모드: RFP 분석만으로 간이 평가 (포지셔닝은 사용자 직접 선택)
    ★ v3.2: research_brief 주입 + 발주기관 인텔리전스 5단계 프레임워크
    """
    rfp = state.get("rfp_analysis")
    mode = state.get("mode", "full")
    research_brief = state.get("research_brief", {})  # ★ v3.2

    if mode == "full":
        capabilities = await capability_store.get_all()
        # ★ v3.0: KB 참조 — 발주기관 DB + 경쟁사 DB 조회
        client_name = rfp.client if rfp else ""
        client_intel = await client_intelligence.get_by_name(client_name)
        competitors = await competitor_intelligence.search_by_domain(
            rfp.hot_buttons if rfp else []
        )
        result = await claude_generate(
            GO_NO_GO_FULL_PROMPT.format(
                rfp_analysis=rfp,
                capabilities=capabilities,
                hot_buttons=rfp.hot_buttons,
                eval_items=rfp.eval_items,
                tech_price_ratio=rfp.tech_price_ratio,
                client_intel=client_intel,       # ★ v3.0: 발주기관 성향·이력
                competitors=competitors,          # ★ v3.0: 경쟁사 강약점
                research_brief=research_brief,    # ★ v3.2: 7차원 리서치 결과
            ),
        )
    else:
        # Lite 모드: 역량 DB 없이 RFP 분석만으로 간이 판단
        result = await claude_generate(
            GO_NO_GO_LITE_PROMPT.format(
                rfp_analysis=rfp,
            ),
        )
        # Lite 모드에서는 수주 가능성 점수 생략
        result["feasibility_score"] = 0
        result["score_breakdown"] = {}

    gng = GoNoGoResult(
        rfp_analysis_ref=f"rfp_{state.get('project_id', '')}",
        positioning=result["positioning"],
        positioning_rationale=result["positioning_rationale"],
        feasibility_score=result.get("feasibility_score", 0),
        score_breakdown=result.get("score_breakdown", {}),
        pros=result["pros"],
        risks=result["risks"],
        recommendation=result["recommendation"],
    )

    return {
        "go_no_go": gng,
        "positioning": gng.positioning,  # 잠정 포지셔닝 (Human이 변경 가능)
        "current_step": "go_no_go_complete",
        # ★ v3.0: KB 참조 기록
        "client_intel_ref": client_intel.to_dict() if client_intel else None,
        "competitor_refs": [c.to_dict() for c in competitors] if competitors else [],
        "kb_references": [
            {"source": "client_intel", "id": client_intel.id, "title": client_name,
             "relevance_score": 1.0, "used_in_step": "go_no_go"}
        ] if client_intel else [],
    }
```

---
