# LangGraph 그래프 정의

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [02-state-schema.md](02-state-schema.md), [04-review-nodes.md](04-review-nodes.md), [07-routing-edges.md](07-routing-edges.md)
> **원본 섹션**: §4 (+ §32-2 STEP 4 교체, §32-9 merged)

---

## 4. LangGraph 그래프 정의

> **v1.3~v1.4 핵심 변경**:
> - STEP 0: RFP 공고 검색/추천 → 관심과제 선정 (interrupt) → **rfp_fetch** (G2B 상세 수집 + RFP 업로드) → STEP 1 진입. 관심과제 없으면 END
> - STEP 1: RFP 분석 → 분석 확인(interrupt) → Go/No-Go + 포지셔닝 확정(interrupt) → STEP 2
> - 부분 재작업: fan-out 함수가 `rework_targets` 확인 → 해당 항목만 Send
> - 포지셔닝 중간 변경: STEP 2 review에서도 `positioning_override` 허용
> - 자가진단 자동 개선 루프: `self_review` → 80점 미만 시 자동 재작성 → 재진단 (최대 2회)

```python
# app/graph/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver  # ★ v2.0: SQLite → PostgreSQL
from langgraph.types import Send

from app.graph.state import ProposalState

def build_graph(checkpointer):
    g = StateGraph(ProposalState)

    # ── 노드 등록 (생략: import 구문) ──

    # STEP 0: 공고 검색/추천
    g.add_node("rfp_search",                rfp_search)
    g.add_node("review_search",             review_node("search"))  # pick-up 선택
    g.add_node("rfp_fetch",                 rfp_fetch)              # G2B 상세 수집 + RFP 업로드 게이트

    # STEP 1-①: RFP 분석
    g.add_node("rfp_analyze",               rfp_analyze)
    g.add_node("review_rfp",                review_node("rfp"))

    # ★ v3.2: STEP 1-①→②: RFP-적응형 사전조사 (review 없이 자동 통과)
    g.add_node("research_gather",           research_gather)

    # STEP 1-②: Go/No-Go + 포지셔닝 확정
    g.add_node("go_no_go",                  go_no_go)
    g.add_node("review_gng",                review_node("go_no_go"))

    # STEP 2
    g.add_node("strategy_generate",         strategy_generate)
    g.add_node("review_strategy",            review_node("strategy"))

    # STEP 3 (병렬, 선택적 재실행)
    g.add_node("plan_fan_out_gate",          _passthrough)
    g.add_node("plan_team",                  plan_team)
    g.add_node("plan_assign",                plan_assign)
    g.add_node("plan_schedule",              plan_schedule)
    g.add_node("plan_story",                 plan_story)
    g.add_node("plan_price",                 plan_price)
    g.add_node("plan_merge",                 plan_merge)
    g.add_node("review_plan",                review_node("plan"))

    # STEP 4 (v3.5: 순차 작성 + 섹션별 리뷰)
    g.add_node("proposal_start_gate",    _proposal_start_gate)   # index 초기화
    g.add_node("proposal_write_next",    proposal_write_next)    # 1개 섹션 순차 작성
    g.add_node("review_section",         review_section_node)    # 섹션별 human 리뷰
    g.add_node("self_review",            self_review_with_auto_improve)
    g.add_node("review_proposal",        review_node("proposal"))

    # ★ v3.2: STEP 4→5: 발표전략 수립 (서류심사 시 건너뛰기)
    g.add_node("presentation_strategy",     presentation_strategy)

    # STEP 5
    g.add_node("ppt_fan_out_gate",           _passthrough)
    g.add_node("ppt_slide",                  ppt_slide)
    g.add_node("ppt_merge",                  ppt_merge)
    g.add_node("review_ppt",                 review_node("ppt"))


    # ── 엣지 정의 ──

    # ★ B-1 + U-1: START → 3가지 진입 경로 분기
    g.add_conditional_edges(START, route_start, {
        "search":        "rfp_search",    # 일반: STEP 0 공고 검색부터
        "direct_fetch":  "rfp_fetch",     # from-search: 공고번호 → rfp_fetch부터
        "direct_rfp":    "rfp_analyze",   # from-rfp: STEP 1 RFP 분석부터
    })

    # STEP 0: 공고 검색 → 관심과제 선정 → RFP 획득
    g.add_edge("rfp_search",       "review_search")
    g.add_conditional_edges("review_search", route_after_search_review, {
        "picked_up":    "rfp_fetch",    # 관심과제 선정 → G2B 상세 수집 + RFP 업로드
        "re_search":    "rfp_search",   # 검색 조건 변경 → 재검색
        "no_interest":  END,            # 관심과제 없음 → 워크플로 종료
    })
    g.add_edge("rfp_fetch",        "rfp_analyze")  # RFP 획득 완료 → STEP 1 진입

    # STEP 1-①: RFP 분석 → 분석 확인
    g.add_edge("rfp_analyze",       "review_rfp")
    g.add_conditional_edges("review_rfp", route_after_rfp_review, {
        "approved":  "research_gather",  # ★ v3.2: 분석 확인 → 리서치 조사 (기존: go_no_go 직행)
        "rejected":  "rfp_analyze",      # 재분석
    })

    # ★ v3.2: 리서치 → Go/No-Go (별도 review 없이 자동 통과)
    g.add_edge("research_gather",  "go_no_go")

    # STEP 1-②: Go/No-Go + 포지셔닝 확정
    g.add_edge("go_no_go",         "review_gng")
    g.add_conditional_edges("review_gng", route_after_gng_review, {
        "go":       "strategy_generate",  # Go → STEP 2
        "no_go":    END,
        "rejected": "go_no_go",
    })

    # STEP 2 (★ 포지셔닝 변경 가능)
    g.add_edge("strategy_generate",  "review_strategy")
    g.add_conditional_edges("review_strategy", route_after_strategy_review, {
        "approved":           "plan_fan_out_gate",
        "rejected":           "strategy_generate",
        "positioning_changed": "strategy_generate",  # 포지셔닝 변경 → 재생성
    })

    # STEP 3: 선택적 병렬 (★ 부분 재작업)
    g.add_conditional_edges("plan_fan_out_gate", plan_selective_fan_out)
    for node in ["plan_team","plan_assign","plan_schedule","plan_story","plan_price"]:
        g.add_edge(node, "plan_merge")
    g.add_edge("plan_merge",         "review_plan")

    # STEP 3 → STEP 4 진입
    # ★ v3.3: 전략-예산 상호조정 루프 (ProposalForge strategy_budget_sync 반영)
    g.add_conditional_edges("review_plan", route_after_plan_review, {
        "approved":             "proposal_start_gate",      # ★ v3.5: proposal_fan_out_gate → proposal_start_gate
        "rework":               "plan_fan_out_gate",        # 부분 재작업
        "rework_with_strategy": "strategy_generate",        # ★ 신규: 예산-전략 부정합 → 전략부터 재수립
    })

    # STEP 4: 순차 작성 루프
    g.add_edge("proposal_start_gate",   "proposal_write_next")
    g.add_edge("proposal_write_next",   "review_section")
    g.add_conditional_edges("review_section", route_after_section_review, {
        "next_section":   "proposal_write_next",    # 승인 → index++ → 다음 섹션
        "rewrite":        "proposal_write_next",    # 반려 → 같은 index 재작성
        "all_done":       "self_review",            # 전체 완료 → 자가진단
    })

    # self_review 이후 (v3.3 5방향 유지, 목적지만 변경)
    g.add_conditional_edges("self_review", route_after_self_review, {
        "pass":            "review_proposal",
        "retry_research":  "research_gather",
        "retry_strategy":  "strategy_generate",
        "retry_sections":  "proposal_start_gate",   # ★ v3.5: proposal_fan_out_gate → proposal_start_gate
        "force_review":    "review_proposal",
    })
    g.add_conditional_edges("review_proposal", route_after_proposal_review, {
        "approved":  "presentation_strategy",
        "rework":    "proposal_start_gate",          # ★ v3.5: proposal_fan_out_gate → proposal_start_gate
    })

    # ★ v3.2: 발표전략 → PPT (서류심사 시 건너뛰기)
    g.add_conditional_edges("presentation_strategy", route_after_presentation_strategy, {
        "proceed":       "ppt_fan_out_gate",     # 발표전략 수립 완료 → PPT 생성
        "document_only": "ppt_fan_out_gate",     # 서류심사 → 발표전략 건너뛰기, PPT는 생성
    })

    # STEP 5
    g.add_conditional_edges("ppt_fan_out_gate", ppt_fan_out)
    g.add_edge("ppt_slide",          "ppt_merge")
    g.add_edge("ppt_merge",          "review_ppt")
    g.add_conditional_edges("review_ppt", route_after_ppt_review, {
        "approved":  END,
        "rework":    "ppt_fan_out_gate",
    })

    return g.compile(checkpointer=checkpointer)


def _passthrough(state: ProposalState) -> dict:
    return {}
```

### 4-1. 선택적 Fan-out (부분 재작업) — D-1 해결

```python
# app/graph/graph.py (계속)

ALL_PLAN_NODES = ["plan_team", "plan_assign", "plan_schedule", "plan_story", "plan_price"]

def plan_selective_fan_out(state: ProposalState) -> list[Send]:
    """
    ★ 부분 재작업: rework_targets가 비어 있으면 전체 실행,
    특정 항목이 지정되면 해당 항목만 재실행.
    """
    targets = state.get("rework_targets", [])
    if not targets:
        # 최초 실행 또는 전체 재실행
        nodes_to_run = ALL_PLAN_NODES
    else:
        # 부분 재작업: 지정된 항목만
        nodes_to_run = [n for n in ALL_PLAN_NODES if n in targets]

    return [Send(node, state) for node in nodes_to_run]
```

> **v3.5 변경**: `proposal_selective_fan_out` 함수는 삭제됨 (§32-9 참조). STEP 4는 순차 작성 방식으로 전환되어 더 이상 Send() fan-out을 사용하지 않는다.

### 4-2. plan_merge — 부분 재작업 시 기존 결과 보존

```python
# app/graph/nodes/merge_nodes.py

def plan_merge(state: ProposalState) -> dict:
    """
    병렬 완료 결과 병합.
    부분 재작업 시: 새로 실행된 항목만 갱신, 나머지는 기존 값 유지.
    """
    new_results = state.get("parallel_results", {})
    existing_plan = state.get("plan")

    if existing_plan and state.get("rework_targets"):
        # 부분 재작업: 기존 plan에서 새 결과만 덮어씌움
        merged = existing_plan.model_dump()
        for key, value in new_results.items():
            merged[key] = value
        return {"plan": ProposalPlan(**merged), "rework_targets": []}
    else:
        # 최초 실행: 전체 조합
        return {"plan": ProposalPlan(**new_results), "rework_targets": []}
```

---

### 32-2-4. 순차 작성 흐름도

```
review_plan (approved)
    │
    ▼
proposal_start_gate ── current_section_index = 0
    │                   sections_to_write = _get_sections_to_write(state)
    ▼
proposal_write_next ◄─── (rewrite: 같은 index)
    │  │
    │  │  1. sections_to_write[current_section_index] 가져오기
    │  │  2. classify_section_type() → 유형별 프롬프트 선택
    │  │  3. _build_context(): 스토리라인 + 이전 섹션 + KB + 평가항목
    │  │  4. Claude API 호출 → 섹션 본문 생성
    │  │  5. parallel_results[section_id] 저장
    │  │
    ▼  │
review_section ────────── interrupt() → human 검토
    │  │  │
    │  │  └─ (next_section) → current_section_index++ → proposal_write_next
    │  │
    │  └─── (rewrite) → proposal_write_next (같은 index)
    │
    └───── (all_done) → self_review → review_proposal → ...
```

---

### 32-9. Dead Code 정리 기록

| 항목 | 상태 | 비고 |
|---|---|---|
| `proposal_merge` (merge_nodes.py) | 코드 존재, graph.py 미사용 | 레거시 호환 목적으로 보존. 향후 정리 대상 |
| `proposal_selective_fan_out` (edges.py) | 삭제됨 | v3.5에서 제거 |
| `proposal_fan_out_gate` | 삭제됨 | `proposal_start_gate`로 대체 |

---
