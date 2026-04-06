# LangGraph 3-레이어 모델 구현 로드맵
## (단계별 코드 변경 & 테스트 가이드)

> **작성일**: 2026-03-29
> **적용 대상**: state.py, graph.py, nodes/*.py, edges.py, routes_workflow.py
> **총 작업량**: ~20-25시간 (병렬 처리 가능)
> **리스크**: 낮음 (기존 구조 유지하며 점진 확장)

---

## 🚀 Phase A: 기초 준비 (Day 1, ~4시간)

### Step A-1: Enum 타입 정의

**파일**: `app/graph/state.py` 상단에 추가

```python
# ── 3-레이어 Enum 정의 (신규) ──

from enum import Enum

class ProposalStatus(str, Enum):
    """Layer 1: Business Status (사용자/PM이 보는 단계)"""
    WAITING       = "waiting"
    IN_PROGRESS   = "in_progress"
    COMPLETED     = "completed"
    SUBMITTED     = "submitted"
    PRESENTATION  = "presentation"
    CLOSED        = "closed"
    ARCHIVED      = "archived"
    ON_HOLD       = "on_hold"
    EXPIRED       = "expired"

class WinResult(str, Enum):
    """closed 상태의 세부값"""
    WON        = "won"
    LOST       = "lost"
    NO_GO      = "no_go"
    ABANDONED  = "abandoned"
    CANCELLED  = "cancelled"

class AIRuntimeStatus(str, Enum):
    """Layer 3: AI 실행 임시 상태"""
    RUNNING     = "running"
    PAUSED      = "paused"
    ERROR       = "error"
    NO_RESPONSE = "no_response"
    COMPLETE    = "complete"
```

### Step A-2: ProposalState 확장

**파일**: `app/graph/state.py` ProposalState 정의 부분

```python
class ProposalState(TypedDict):
    # ═══ 기존 필드 (유지) ═══
    project_id: str
    team_id: str
    owner_id: str
    title: str
    # ... (기존 필드 모두 유지)

    # ═══ 신규: Layer 1 (Business Status) ═══
    business_status: str  # ProposalStatus enum 값
    win_result: Optional[str]  # WinResult enum 값 (closed일 때만)

    # ═══ 신규: Layer 2 (Workflow Phase) ═══
    current_phase: Optional[str]  # LangGraph 노드명
                                  # "rfp_analyze", "strategy_generate", "proposal_write_next", etc.

    # ═══ 신규: Layer 3 (AI Runtime Status) ═══
    ai_runtime_status: str  # AIRuntimeStatus enum 값
    ai_task_id: Optional[str]  # LangGraph session_id
    ai_error: Optional[str]  # 에러 메시지

    # ═══ 신규: 타임스탬프 (Layer 1 이벤트 추적) ═══
    started_at: Optional[str]             # ISO 8601 timestamp
    completed_at: Optional[str]
    submitted_at: Optional[str]
    presentation_started_at: Optional[str]
    closed_at: Optional[str]
    archived_at: Optional[str]
    expired_at: Optional[str]

    # ═══ 하위호환: 기존 필드 (deprecated, 점진 제거) ═══
    current_step: Optional[str]  # 기존 호환성용 (v5.1에서 제거)

    # ... (14개 서브모델, feedback_history, approval 등 기존 필드)
```

**Reducer 정의** (현재 상태 반영용):

```python
from typing import Annotated

def _override_business_status(a, b):
    """비즈니스상태는 명시적 업데이트만 반영"""
    return b if b else a

def _override_workflow_phase(a, b):
    """워크플로우상태는 각 노드가 업데이트"""
    return b if b else a

# TypedDict에 Annotated 적용
class ProposalState(TypedDict):
    business_status: Annotated[str, _override_business_status]
    current_phase: Annotated[str, _override_workflow_phase]
    # ... 기존 Annotated reducers 유지
```

### Step A-3: 상태 전환 유틸 함수

**파일**: `app/graph/nodes/state_utils.py` (신규)

```python
"""상태 전환 헬퍼 함수 (Layer 1 관리)"""

from datetime import datetime, timezone
from typing import Optional
from app.graph.state import (
    ProposalStatus, WinResult, AIRuntimeStatus
)

# ── 전환 규칙 테이블 ──

VALID_TRANSITIONS = {
    ProposalStatus.WAITING: [
        ProposalStatus.IN_PROGRESS,
        ProposalStatus.ON_HOLD,
    ],
    ProposalStatus.IN_PROGRESS: [
        ProposalStatus.COMPLETED,
        ProposalStatus.CLOSED,  # No-Go
        ProposalStatus.ON_HOLD,
        ProposalStatus.EXPIRED,
    ],
    ProposalStatus.COMPLETED: [
        ProposalStatus.SUBMITTED,
        ProposalStatus.IN_PROGRESS,  # 재작업
        ProposalStatus.ON_HOLD,
    ],
    ProposalStatus.SUBMITTED: [
        ProposalStatus.PRESENTATION,
        ProposalStatus.CLOSED,  # 서류탈락
        ProposalStatus.ON_HOLD,
    ],
    ProposalStatus.PRESENTATION: [
        ProposalStatus.CLOSED,  # 평가결과
        ProposalStatus.ON_HOLD,
    ],
    ProposalStatus.CLOSED: [
        ProposalStatus.ARCHIVED,  # 30일 후
    ],
    # 모든 활성 상태에서 on_hold 가능
    ProposalStatus.ON_HOLD: [
        ProposalStatus.WAITING,
        ProposalStatus.IN_PROGRESS,
        ProposalStatus.COMPLETED,
        ProposalStatus.SUBMITTED,
        ProposalStatus.PRESENTATION,
    ],
    ProposalStatus.EXPIRED: [
        ProposalStatus.CLOSED,  # 자동 또는 수동 진입
    ],
}

def is_valid_transition(
    from_status: ProposalStatus,
    to_status: ProposalStatus,
) -> bool:
    """전환 가능성 검증"""
    return to_status in VALID_TRANSITIONS.get(from_status, [])

def get_timestamp_field_for_status(status: ProposalStatus) -> Optional[str]:
    """상태에 해당하는 타임스탬프 필드명 반환"""
    timestamp_map = {
        ProposalStatus.IN_PROGRESS: "started_at",
        ProposalStatus.COMPLETED: "completed_at",
        ProposalStatus.SUBMITTED: "submitted_at",
        ProposalStatus.PRESENTATION: "presentation_started_at",
        ProposalStatus.CLOSED: "closed_at",
        ProposalStatus.ARCHIVED: "archived_at",
        ProposalStatus.EXPIRED: "expired_at",
    }
    return timestamp_map.get(status)

def build_status_transition_update(
    from_status: ProposalStatus,
    to_status: ProposalStatus,
    win_result: Optional[WinResult] = None,
) -> dict:
    """상태 전환 업데이트 딕셔너리 생성"""

    if not is_valid_transition(from_status, to_status):
        return {"error": f"Invalid transition: {from_status} → {to_status}"}

    now = datetime.now(timezone.utc).isoformat()
    update = {
        "business_status": to_status.value,
    }

    # 타임스탬프 설정
    ts_field = get_timestamp_field_for_status(to_status)
    if ts_field:
        update[ts_field] = now

    # win_result 설정 (closed일 때만)
    if to_status == ProposalStatus.CLOSED and win_result:
        update["win_result"] = win_result.value

    return update
```

**테스트**:
```bash
cd app && python -m pytest tests/graph/test_state_utils.py -v
```

---

## 🔧 Phase B: 핵심 노드 개선 (Day 2, ~6시간)

### Step B-1: go_no_go 노드 개선

**파일**: `app/graph/nodes/go_no_go.py` (수정)

```python
# ── 헤더 추가 ──
from app.graph.state import (
    GoNoGoResult, ProposalState, ProposalStatus, WinResult, AIRuntimeStatus
)
from app.graph.nodes.state_utils import (
    build_status_transition_update, ProposalStatus, WinResult
)

# ── 함수 수정 (마지막 return 부분) ──

async def go_no_go(state: ProposalState) -> dict:
    """STEP 1-②: Go/No-Go (3-레이어 모델 적용)"""

    # ... (기존 로직: gng 계산 부분은 동일)

    gng = GoNoGoResult(
        # ... (기존 필드)
    )

    # ═══ 신규: 3-레이어 상태 업데이트 ═══

    updates = {
        "go_no_go_result": gng,

        # Layer 3: AI 실행 상태
        "ai_runtime_status": AIRuntimeStatus.COMPLETE.value,
        "ai_task_id": state.get("ai_task_id"),  # 세션 유지

        # Layer 2: 워크플로우 위상
        "current_phase": "go_no_go",

        # 기존 호환성
        "current_step": (
            "go_no_go_go"
            if gng.recommendation == "go"
            else "go_no_go_no_go"
        ),
    }

    # Layer 1: 비즈니스상태 (no_go 결정 시 즉시 closed)
    if gng.recommendation == "no_go":
        status_update = build_status_transition_update(
            from_status=ProposalStatus.IN_PROGRESS,
            to_status=ProposalStatus.CLOSED,
            win_result=WinResult.NO_GO,
        )
        updates.update(status_update)
        updates["current_phase"] = "end"  # 조기 종료

    return updates
```

**테스트**:
```python
# tests/graph/test_nodes/test_go_no_go.py 추가/수정

async def test_go_no_go_no_go_updates_business_status():
    state = {
        "business_status": "in_progress",
        "rfp_analysis": {...},  # mock
        ...
    }
    result = await go_no_go(state)

    assert result["business_status"] == "closed"
    assert result["win_result"] == "no_go"
    assert result["current_phase"] == "end"
    assert result["closed_at"] is not None
```

### Step B-2: proposal_complete 시점 추가

**파일**: `app/graph/nodes/proposal_nodes.py` (수정)

이미 proposal_write_next에서 마지막 섹션 완료를 감지하고 있음.
상태 전환 로직만 추가:

```python
async def proposal_write_next(state: ProposalState) -> dict:
    # ... (기존: 섹션 작성 로직)

    current_index = state.get("current_section_index", 0)
    total_sections = len(state.get("dynamic_sections", []))

    # ── 신규: 마지막 섹션 완료 시 상태 전환 ──
    if current_index + 1 >= total_sections:
        status_update = build_status_transition_update(
            from_status=ProposalStatus.IN_PROGRESS,
            to_status=ProposalStatus.COMPLETED,
        )

        return {
            **status_update,  # Layer 1 타임스탬프 포함

            # Layer 2/3
            "current_phase": "proposal_complete",
            "ai_runtime_status": AIRuntimeStatus.COMPLETE.value,

            # 기존 필드
            "proposal_sections": [...],
            "current_section_index": total_sections,
            "current_step": "proposal_complete",  # 호환성
        }
    else:
        return {
            "current_phase": f"proposal_write[{current_index + 1}/{total_sections}]",
            "ai_runtime_status": AIRuntimeStatus.RUNNING.value,
            "current_section_index": current_index + 1,
            "current_step": "proposal_next_section",
        }
```

### Step B-3: 평가 완료 시점 개선

**파일**: `app/graph/nodes/evaluation_nodes.py` (수정)

```python
async def eval_result_node(state: ProposalState) -> dict:
    # ... (기존: 평가 결과 처리)

    eval_result = EvaluationResult(...)

    # ── 신규: 최종 결과에 따른 상태 전환 ──

    win_result = None
    if eval_result.decision == "won":
        win_result = WinResult.WON
    elif eval_result.decision == "lost":
        win_result = WinResult.LOST
    # (archived/cancelled은 프론트엔드/user 액션)

    status_update = build_status_transition_update(
        from_status=ProposalStatus.PRESENTATION,
        to_status=ProposalStatus.CLOSED,
        win_result=win_result,
    )

    return {
        **status_update,  # Layer 1

        # Layer 2/3
        "current_phase": "eval_complete",
        "ai_runtime_status": AIRuntimeStatus.COMPLETE.value,

        # 기존
        "eval_result": eval_result,
        "current_step": f"eval_{eval_result.decision}",
    }
```

---

## 🎛️ Phase C: Review 게이트 일괄 개선 (Day 2-3, ~5시간)

### Step C-1: review_node 개선

**파일**: `app/graph/nodes/review_node.py` (수정)

현재 review_node 함수 내부에 다음 추가:

```python
def review_node(step_name: str):
    """공통 리뷰 게이트 (3-레이어 상태 추적)"""

    def _review(state: ProposalState) -> dict:
        # ── 기존 로직 ──
        artifact = _get_artifact(state, step_name)
        perspective = REVIEW_PERSPECTIVES.get(step_name, {})

        # ── 신규: Layer 3 상태 설정 (일시중지) ──
        interrupt_data = {
            # ... 기존 필드
            "business_status": state.get("business_status"),  # 정보 전달용
            "current_phase": step_name,  # 리뷰 단계
        }

        # interrupt: 사용자 입력 대기
        human_input = interrupt(interrupt_data)

        # ── 신규: interrupt 재개 시 상태 처리 ──

        # 특수: Go/No-Go 리뷰 → 상태 전환
        if step_name == "go_no_go":
            return _handle_gng_review(state, human_input, step_name)

        # 특수: 제출 리뷰 → 상태 전환 (submitted로)
        if step_name == "submission_checklist":
            if human_input.get("quick_approve") or human_input.get("approved"):
                status_update = build_status_transition_update(
                    ProposalStatus.COMPLETED,
                    ProposalStatus.SUBMITTED,
                )
                return {
                    **status_update,
                    "current_phase": "submitted",
                    "ai_runtime_status": AIRuntimeStatus.COMPLETE.value,
                    "approval": {step_name: {"status": "approved", ...}},
                    "current_step": f"review_{step_name}_approved",
                }

        # 기본: 승인/거부만 (상태 유지)
        return {
            "ai_runtime_status": AIRuntimeStatus.COMPLETE.value,
            "current_phase": step_name,
            "approval": {
                step_name: {
                    "status": (
                        "approved"
                        if human_input.get("quick_approve") or human_input.get("approved")
                        else "rejected"
                    ),
                    "feedback": human_input.get("feedback", ""),
                    "timestamp": human_input.get("timestamp", ""),
                }
            },
            "current_step": (
                f"review_{step_name}_approved"
                if human_input.get("approved")
                else f"review_{step_name}_rejected"
            ),
        }

    return _review
```

---

## 🎯 Phase D: 라우팅 개선 (Day 3, ~4시간)

### Step D-1: Layer 기반 라우팅 함수

**파일**: `app/graph/edges.py` (수정 - 점진적 전환)

**기존 패턴 유지** (호환성):
```python
# 기존 코드 보존

route_after_rfp_review = _approval_router("rfp")
route_after_gng_review = _approval_router_with_layer1("go_no_go")  # ← 개선
```

**신규 Layer 기반 라우팅 함수**:
```python
def route_after_proposal_complete(state: ProposalState) -> str:
    """섹션 작성 완료 후 라우팅 (Layer 1 기반)"""

    business_status = state.get("business_status", "")

    # Layer 1: completed 상태 확인
    if business_status == ProposalStatus.COMPLETED.value:
        return "self_review"

    # 중간 섹션 (Layer 2: current_phase 확인)
    current_phase = state.get("current_phase", "")
    if "proposal_write" in current_phase:
        return "next_section"

    return "error"


def route_after_eval_complete(state: ProposalState) -> str:
    """평가 완료 후 라우팅"""

    business_status = state.get("business_status", "")
    win_result = state.get("win_result")

    # Layer 1: closed 상태 확인
    if business_status != ProposalStatus.CLOSED.value:
        return "error"

    # Layer 1: win_result 확인
    if win_result == WinResult.WON.value:
        return "won"
    elif win_result == WinResult.LOST.value:
        return "lost"

    return "end"
```

### Step D-2: 조건부 엣지 추가

**파일**: `app/graph/graph.py` (수정)

```python
# ── 신규: Layer 기반 조건부 엣지 ──

def build_graph(checkpointer=None):
    g = StateGraph(ProposalState)

    # ... (기존 노드 정의)

    # [신규] 제안서 작성 완료 후 분기
    g.add_conditional_edges("proposal_complete", route_after_proposal_complete, {
        "self_review": "self_review",
        "next_section": "proposal_write_next",
        "error": "error_handler",
    })

    # [신규] 평가 완료 후 분기
    g.add_conditional_edges("eval_complete", route_after_eval_complete, {
        "won": "project_closing",
        "lost": "project_closing",
        "end": END,
    })

    # ... (기존 엣지)

    return g.compile(checkpointer=checkpointer)
```

---

## 🔌 Phase E: API 레이어 수정 (Day 3, ~3시간)

### Step E-1: routes_workflow.py 수정

**파일**: `app/api/routes_workflow.py` (수정)

현재 라인 148, 298 문제 해결:

```python
# ── 기존 (문제) ──
if proposal.data["status"] == "running":
    raise WFAlreadyRunningError(proposal_id)

# ── 신규 ──
# DB 확인 대신 ai_task_status 테이블 확인
from app.services.ai_status_manager import AIStatusManager
ai_manager = AIStatusManager()
active = await ai_manager.get_active_task(proposal_id)
if active:
    raise WFAlreadyRunningError(proposal_id)
```

**workflow 시작 시**:
```python
@router.post("/{proposal_id}/start")
async def start_workflow(...):
    # ... 기존 검증

    # ── 신규: AI 상태 초기화 ──
    state = {
        "business_status": ProposalStatus.IN_PROGRESS.value,  # 자동 전환
        "ai_runtime_status": AIRuntimeStatus.RUNNING.value,
        "ai_task_id": session_id,
        # ...
    }

    # ... workflow invoke
```

---

## ✅ Phase F: 통합 테스트 (Day 4, ~3시간)

### Step F-1: 상태 전환 경로 테스트

**파일**: `tests/graph/test_state_lifecycle.py` (신규)

```python
@pytest.mark.asyncio
async def test_proposal_lifecycle():
    """전체 워크플로우 상태 전환 경로 검증"""

    state = {
        "business_status": ProposalStatus.WAITING.value,
        "ai_runtime_status": AIRuntimeStatus.COMPLETE.value,
        # ...
    }

    # 1. waiting → in_progress
    state_1 = await workflow.invoke(state, {"task": "start"})
    assert state_1["business_status"] == ProposalStatus.IN_PROGRESS.value
    assert state_1["started_at"] is not None

    # 2. in_progress (no_go) → closed
    state_2 = await workflow.invoke(state_1, {"task": "go_no_go", "decision": "no_go"})
    assert state_2["business_status"] == ProposalStatus.CLOSED.value
    assert state_2["win_result"] == WinResult.NO_GO.value

    # 3. in_progress → completed
    state_1b = await workflow.invoke(state, {"task": "complete_sections"})
    assert state_1b["business_status"] == ProposalStatus.COMPLETED.value

    # 4. completed → submitted
    state_3 = await workflow.invoke(state_1b, {"task": "submit"})
    assert state_3["business_status"] == ProposalStatus.SUBMITTED.value
    assert state_3["submitted_at"] is not None

    # 5. submitted → presentation
    state_4 = await workflow.invoke(state_3, {"task": "present"})
    assert state_4["business_status"] == ProposalStatus.PRESENTATION.value

    # 6. presentation → closed (won)
    state_5 = await workflow.invoke(state_4, {"task": "eval_result", "decision": "won"})
    assert state_5["business_status"] == ProposalStatus.CLOSED.value
    assert state_5["win_result"] == WinResult.WON.value
```

### Step F-2: No-Go 조기 종료 테스트

```python
@pytest.mark.asyncio
async def test_no_go_shortcut_workflow():
    """No-Go 결정 시 in_progress → closed 단축"""

    state = {
        "business_status": ProposalStatus.IN_PROGRESS.value,
        "rfp_analysis": {...},  # mock
        ...
    }

    # go_no_go 노드 실행
    result = await go_no_go(state)

    assert result["business_status"] == ProposalStatus.CLOSED.value
    assert result["win_result"] == WinResult.NO_GO.value
    assert result["current_phase"] == "end"  # 조기 종료
```

### Step F-3: 라우팅 호환성 테스트

```python
@pytest.mark.asyncio
async def test_routing_layer_compatibility():
    """기존 라우팅이 새 상태와 호환되는지 검증"""

    # 기존 route_after_gng_review 호환성
    state_go = {
        "business_status": ProposalStatus.IN_PROGRESS.value,
        "current_step": "go_no_go_go",
        "go_no_go_result": GoNoGoResult(recommendation="go", ...),
    }
    assert route_after_gng_review(state_go) == "go"

    # 신규 Layer 기반
    state_no_go = {
        "business_status": ProposalStatus.CLOSED.value,
        "win_result": WinResult.NO_GO.value,
    }
    # route_after_gng_review_v2(state_no_go) == "no_go" 검증
```

---

## 📅 일정 & 리소스

| Phase | 작업 | 일정 | 시간 | 담당 |
|-------|------|------|------|------|
| A | 기초 (Enum, state, utils) | Day 1 | 4h | 1명 |
| B | 핵심 노드 (go_no_go, proposal_complete, eval) | Day 2 | 6h | 1명 |
| C | Review 게이트 (16개) | Day 2-3 | 5h | 1명 |
| D | 라우팅 개선 (edges.py, graph.py) | Day 3 | 4h | 1명 |
| E | API 수정 (routes_workflow) | Day 3 | 3h | 1명 |
| F | 테스트 & 통합 | Day 4 | 3h | 1명 |
| - | **합계** | 4일 | **25h** | 1명 |

**병렬화 가능**:
- Phase A + B 병렬 (A-1 완료 후 B 시작)
- Phase C + D 병렬 (독립적)
- Phase E는 Phase B 완료 후

---

## 🚦 진행 체크리스트

### 선행 조건
- [ ] langgraph-node-architecture-analysis.md 검토 완료
- [ ] unified-state-system.plan.md (DB 마이그레이션) 검토 완료
- [ ] 팀 내 동의: Layer 구조 적용

### Phase A
- [ ] state.py Enum 추가
- [ ] ProposalState 신규 필드 추가
- [ ] state_utils.py 생성 & 테스트

### Phase B
- [ ] go_no_go.py 수정 & 테스트
- [ ] proposal_nodes.py 수정 & 테스트
- [ ] evaluation_nodes.py 수정 & 테스트

### Phase C
- [ ] review_node.py 수정 & 테스트
- [ ] 16개 review 게이트 동작 검증

### Phase D
- [ ] edges.py 라우팅 함수 개선
- [ ] graph.py 조건부 엣지 추가
- [ ] 라우팅 호환성 테스트

### Phase E
- [ ] routes_workflow.py 수정
- [ ] API 엔드포인트 테스트

### Phase F
- [ ] 상태 전환 경로 E2E 테스트
- [ ] 조기 종료 (no_go) 시나리오
- [ ] 병렬 노드 상태 병합 검증

---

## ⚠️ 위험 관리

| 위험 | 영향도 | 완화 방안 |
|------|--------|----------|
| current_step 필드 일관성 손상 | 중간 | 기존 필드 유지, 점진 제거 |
| 라우팅 로직 버그 | 높음 | 각 라우팅 경로별 단위 테스트 |
| 병렬 노드 상태 충돌 | 중간 | Annotated reducer로 합병 규칙 명확화 |
| DB 마이그레이션과 동기화 불일치 | 높음 | 동시 테스트 (dev 환경) |

---

## 📌 다음 액션

1. **설계 승인** → 위 로드맵 타당성 확인
2. **Branch 생성** → `feature/langgraph-3layer` 브랜치에서 작업
3. **Phase A 시작** → state.py Enum 정의부터
4. **Daily sync** → 진행 상황 추적
5. **PR 단위 통합** → 각 Phase별 PR 생성 & 검토
