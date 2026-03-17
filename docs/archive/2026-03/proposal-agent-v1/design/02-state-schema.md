# LangGraph State 스키마

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [03-graph-definition.md](03-graph-definition.md), [07-routing-edges.md](07-routing-edges.md)
> **원본 섹션**: §3 (+ §32-3 merged)

---

## 3. LangGraph State 스키마

> **v1.3 변경**: STEP 0을 RFP 공고 검색/추천으로 변경. Go/No-Go를 STEP 1 RFP 분석 이후로 이동. `RfpRecommendation` 모델 추가, `search_results` 필드 추가.
> **v1.4 변경**: `BidDetail` 모델 추가 (G2B 공고 상세), `search_query` / `bid_detail` 필드 추가. STEP 0 pick-up 후 하이브리드 RFP 획득 지원.
> **v2.0 변경**: 결재선(`ApprovalChainEntry`), 사용자 컨텍스트(`user_id`, `team_id`) 추가. `ApprovalStatus`에 결재선 이력 포함.
> **v3.0 변경**: KB 참조 필드(`kb_references`, `client_intel_ref`, `competitor_refs`), AI 상태 추적(`ai_task_id`), 토큰 사용 추적(`token_usage`), 피드백 윈도우(`feedback_window_size`) 추가.

```python
# app/graph/state.py
from typing import Annotated, TypedDict, Optional, Literal
from pydantic import BaseModel

# ── 서브 모델 ──

class ApprovalChainEntry(BaseModel):
    """결재선 단일 항목 — 예산 기준에 따라 1~3단계."""
    role: Literal["lead", "director", "executive"]
    user_id: str
    user_name: str
    status: Literal["pending", "approved", "rejected"] = "pending"
    decided_at: str = ""
    feedback: str = ""

class ApprovalStatus(BaseModel):
    status: str           # "pending" | "approved" | "rejected"
    approved_by: str = ""
    approved_at: str = ""
    feedback: str = ""
    # ★ v2.0: 결재선 (Go/No-Go, 제안서 최종 승인 시 사용)
    chain: list[ApprovalChainEntry] = []   # 비어 있으면 팀장 단독 승인

class RfpRecommendation(BaseModel):
    """STEP 0: 공고 검색 추천 결과 항목 (최대 5건)."""
    bid_no: str
    project_name: str
    client: str
    budget: str
    deadline: str
    # ── 공고 요약 정보 (관심과제 선정 판단 근거) ──
    project_summary: str            # 사업 개요 요약 (2~3문장)
    key_requirements: list[str]     # 주요 요구사항 (3~5개)
    eval_method: str                # 평가 방식 요약 (기술:가격 비율, 적격심사 등)
    competition_level: str          # 경쟁 강도 예측 (높음/보통/낮음 + 근거)
    # ── AI 적합도 평가 ──
    fit_score: int                  # 적합도 점수 (100점 만점)
    fit_rationale: str              # 적합도 판단 근거
    expected_positioning: Literal["defensive", "offensive", "adjacent"]
    brief_analysis: str             # 종합 한줄 분석

class BidDetail(BaseModel):
    """STEP 0→1 전환: G2B 공고 상세 정보 (자동 수집)."""
    bid_no: str
    project_name: str
    client: str
    budget: str
    deadline: str
    description: str               # 공고 상세 설명
    requirements_summary: str      # 주요 요구사항 요약
    attachments: list[dict]        # G2B 첨부파일 목록 [{ name, url, type }]
    rfp_auto_text: str = ""        # G2B에서 자동 추출한 RFP 텍스트 (첨부 PDF 등)

class GoNoGoResult(BaseModel):
    """STEP 1-②: RFP 분석 이후 Go/No-Go 의사결정 결과."""
    rfp_analysis_ref: str = ""      # RFP분석서 참조 (분석 완료 후 생성)
    positioning: Literal["defensive", "offensive", "adjacent"]
    positioning_rationale: str
    feasibility_score: int
    score_breakdown: dict
    pros: list[str]
    risks: list[str]
    recommendation: Literal["go", "no-go"]
    decision: str = "pending"

class RFPAnalysis(BaseModel):
    project_name: str
    client: str
    deadline: str
    case_type: Literal["A", "B"]
    eval_items: list[dict]
    tech_price_ratio: dict
    hot_buttons: list[str]
    mandatory_reqs: list[str]
    format_template: dict           # { exists: bool, structure: dict|null }
    volume_spec: dict
    special_conditions: list[str]

class StrategyAlternative(BaseModel):
    """전략 대안 — 최소 2가지, Human이 하나를 선택하거나 조합."""
    alt_id: str                     # "A", "B", ...
    ghost_theme: str
    win_theme: str
    action_forcing_event: str
    key_messages: list[str]
    price_strategy: dict
    risk_assessment: dict

class Strategy(BaseModel):
    positioning: Literal["defensive", "offensive", "adjacent"]
    positioning_rationale: str
    alternatives: list[StrategyAlternative]
    selected_alt_id: str = ""       # Human이 선택한 대안 ID
    # 아래는 선택된 대안에서 복사 + Human 수정 반영
    ghost_theme: str = ""
    win_theme: str = ""
    action_forcing_event: str = ""
    key_messages: list[str] = []
    focus_areas: list[dict] = []
    price_strategy: dict = {}
    competitor_analysis: dict = {}
    risks: list[dict] = []

class ComplianceItem(BaseModel):
    req_id: str
    content: str
    source_step: str                # 어느 단계에서 추가되었는지
    status: Literal["미확인", "충족", "미충족", "해당없음"] = "미확인"
    proposal_section: str = ""      # 대응하는 제안서 섹션

class ProposalSection(BaseModel):
    section_id: str
    title: str
    content: str
    version: int
    case_type: Literal["A", "B"]    # 케이스 A: 자유양식, B: 서식 채우기
    template_structure: Optional[dict] = None  # 케이스 B: 원본 서식 구조
    self_review_score: Optional[dict] = None

class ProposalPlan(BaseModel):
    team: list[dict]
    deliverables: list[dict]
    schedule: dict
    storylines: dict
    bid_price: dict

class PPTSlide(BaseModel):
    slide_id: str
    title: str
    content: str
    notes: str
    version: int


# ── Annotated Reducers ──

def _merge_dict(existing: dict, new: dict) -> dict:
    return {**existing, **new}

def _append_list(existing: list, new: list) -> list:
    return existing + new

def _replace(existing, new):
    return new


# ── 핵심 State 정의 ──

class ProposalState(TypedDict):
    # 프로젝트 메타
    project_id: str
    project_name: str

    # ★ v2.0: 소유·조직 컨텍스트
    team_id: str                    # 소속 팀 ID (프로젝트 생성 시 자동 귀속)
    division_id: str                # 소속 본부 ID
    created_by: str                 # 생성자 user_id
    participants: list[str]         # 참여 팀원 user_id 목록

    # ★ 실행 모드 (간이 / 정규)
    mode: Literal["lite", "full"]   # lite: 역량DB 없이 시작 가능

    # ★ 입찰 포지셔닝 (STEP 1-② Go/No-Go에서 확정, STEP 2에서도 변경 가능)
    positioning: Literal["defensive", "offensive", "adjacent"]

    # 단계별 산출물
    search_query: dict                       # STEP 0: 초기 검색 조건 { keywords, budget_min, region, ... }
    search_results: Annotated[list[RfpRecommendation], _replace]  # STEP 0: 공고 검색 추천 결과
    picked_bid_no: str                       # STEP 0: 사용자가 pick-up한 공고번호
    bid_detail: Optional[BidDetail]          # STEP 0→1: G2B 공고 상세 (자동 수집)
    go_no_go: Optional[GoNoGoResult]         # STEP 1-②: Go/No-Go 결과
    rfp_raw: str
    rfp_analysis: Optional[RFPAnalysis]
    strategy: Optional[Strategy]
    plan: Optional[ProposalPlan]
    proposal_sections: Annotated[list[ProposalSection], _replace]
    ppt_slides: Annotated[list[PPTSlide], _replace]

    # Compliance Matrix (전 단계에 걸쳐 진화)
    compliance_matrix: Annotated[list[ComplianceItem], _replace]

    # 단계별 승인 상태
    approval: Annotated[dict[str, ApprovalStatus], _merge_dict]

    # 현재 실행 중인 단계
    current_step: str

    # 피드백 이력
    feedback_history: Annotated[list[dict], _append_list]

    # ★ 부분 재작업 대상 (빈 리스트 = 전체 실행)
    rework_targets: list[str]

    # 동적 섹션 목록
    dynamic_sections: list[str]

    # 병렬 작업 중간 결과
    parallel_results: Annotated[dict, _merge_dict]

    # ★ v3.0: KB 참조 정보
    kb_references: Annotated[list[dict], _append_list]
    # 형식: [{ "source": "content_library"|"client_intel"|"competitor"|"lesson",
    #          "id": str, "title": str, "relevance_score": float, "used_in_step": str }]
    client_intel_ref: Optional[dict]       # 발주기관 DB 매칭 결과 (Go/No-Go에서 참조)
    competitor_refs: list[dict]            # 경쟁사 DB 매칭 결과 (전략 수립에서 참조)

    # ★ v3.0: AI 상태 추적
    ai_task_id: str                        # 현재 AI 작업 ID (ai_status_manager 연동)

    # ★ v3.0: 토큰 사용 추적
    token_usage: Annotated[dict, _merge_dict]
    # 형식: { "step_name": { "input_tokens": int, "output_tokens": int, "cached_tokens": int } }

    # ★ v3.0: 피드백 윈도우 (최근 N회만 프롬프트에 포함)
    feedback_window_size: int              # 기본값 3 (token_manager에서 관리)

    # ★ v3.2: ProposalForge 통합 — 신규 필드
    research_brief: Optional[dict]           # research_gather 노드 출력 (7차원 리서치 결과)
    presentation_strategy: Optional[dict]    # presentation_strategy 노드 출력 (발표전략)
    budget_detail: Optional[dict]            # plan_price 확장 출력 (상세 원가 — 노임단가·직접경비·간접경비·기술료)
    evaluation_simulation: Optional[dict]    # self_review 확장 출력 (3인 페르소나 시뮬레이션 + 예상 질문·모범답변)

    # ★ v3.5 추가
    current_section_index: Annotated[int, lambda a, b: b]  # 순차 작성 인덱스 (0-based)
```

### v3.5 추가 필드

| 필드 | 타입 | 용도 | Reducer |
|---|---|---|---|
| `current_section_index` | `int` | 현재 작성 중인 섹션 인덱스 (0-based). `proposal_start_gate`에서 0으로 초기화, `route_after_section_review`에서 +1 | `lambda a, b: b` (최신값 우선) |

---
