# LangGraph 노드 아키텍처 분석 & 3-레이어 모델 적용 방안
## (기존 16개 상태 혼입 → 10개 비즈니스상태 + 40개 워크플로우상태 분리)

> **분석일**: 2026-03-29
> **현황**: 40개 노드, 부분적 상태관리 (current_step 기반)
> **문제**: 상태가 분산되어 있고, 현재 DB 제약과 충돌
> **목표**: 3-레이어 구조를 LangGraph 노드 설계에 명시적으로 반영

---

## 📊 현황 분석

### 1. 현재 LangGraph 구조

```
StateGraph: ProposalState (TypedDict)
    │
    ├─ 기본 정보 (title, client_name, deadline, bid_amount)
    ├─ 14개 서브 모델 (RFPAnalysis, Strategy, GoNoGoResult, ...)
    ├─ 상태 필드:
    │   ├─ current_step (str) ← 현재 LangGraph 노드 이름 추적
    │   └─ metadata (dict) ← 혼합된 상태값 저장 (문제!)
    └─ 기타 (feedback_history, approval, kb_references, ...)

40개 노드:
    HEAD (1→2): rfp_analyze, research_gather, go_no_go, strategy_generate
    PATH A (3A→6A): plan_* → proposal_write_next → ppt_* → mock_evaluation
    PATH B (3B→6B): submission_plan → bid_plan → cost_sheet → submission_checklist
    TAIL (7→8): eval_result → project_closing
    GATES: fork_gate, convergence_gate, review_* (16개)

라우팅:
    edges.py: 15개 라우팅 함수
    - _approval_router 팩토리로 단순 approved/rejected 생성
    - 복잡한 다방향은 개별 함수 (route_after_gng_review, etc.)
```

### 2. 상태 추적 현황

**문제점**:
```
① current_step 사용 (현재):
   - state["current_step"] = "rfp_analyze"
   - state["current_step"] = "go_no_go_go" / "go_no_go_no_go"
   - 각 노드가 임의로 설정 → 혼란

② 노드별 위치 정보 불명확:
   - "review_rfp" 노드에 있는지, rfp_analyze 노드에 있는지 불분명
   - current_step이 최종 위치인지, intermediate인지 불명확

③ 상태 전환 로직 산재:
   - routes_workflow.py (lines 148, 298): status = "running" / "cancelled" (❌ DB 제약 위반)
   - state.get("current_step") 기반 분기 (edges.py)
   - 일관된 상태 전환 패턴 부재

④ Layer 1 (비즈니스상태) 추적 안됨:
   - proposals.status에만 저장되고, 노드에서 업데이트 안 함
   - in_progress 상태가 얼마나 진행되었는지 알 수 없음
```

**현재 상태 필드 정의** (state.py):
```python
class ProposalState(TypedDict):
    # ... 기본 정보
    current_step: str              # ← 현재 노드 (문제: 정의 불명확)
    # ... 14개 서브모델
    # ... feedback_history, approval, etc.
    # ❌ 없음: 명시적 status, win_result, workflow_phase, ai_runtime_status
```

### 3. 기존 노드의 상태 관리 패턴

**Pattern A: Review 게이트 (16개)**
```python
def review_node(step_name):
    def _review(state: ProposalState) -> dict:
        artifact = _get_artifact(state, step_name)  # ← 현재 산출물 조회
        human_input = interrupt(interrupt_data)      # ← 사용자 입력 대기

        # 승인/거부에 따라 current_step 설정
        if approved:
            return {"current_step": "approved", ...}
        else:
            return {"current_step": "rejected", ...}
    return _review

# 라우팅: route_after_rfp_review, route_after_strategy_review, ...
# 문제: current_step 값이 다양하고, 다음 노드 이름과 불일치
```

**Pattern B: 주요 노드 (go_no_go, strategy_generate, proposal_write_next)**
```python
async def go_no_go(state: ProposalState) -> dict:
    gng = GoNoGoResult(...)  # 계산

    return {
        "current_step": "go_no_go_go" or "go_no_go_no_go",  # ← 라우팅 신호
        "go_no_go_result": gng,  # 결과만 저장
        # ❌ 상태를 업데이트하지 않음 (proposals 테이블의 status)
    }

# 라우팅: route_after_gng_review
# 분기: "go" → strategy_generate, "no_go" → END
```

**Pattern C: 병렬 노드 (plan_team, plan_assign, plan_price, etc.)**
```python
async def plan_team(state: ProposalState) -> dict:
    team_plan = PlanTeam(...)

    return {
        "current_step": "plan_team_done",  # ← 신호용
        "plan": {"team": team_plan, ...},
    }

# Convergence gate에서 병합: plan_merge
# 문제: 각 노드가 current_step을 설정하면 마지막 것만 유지됨
#      (병렬 노드의 current_step 덮어쓰기 문제)
```

---

## 🎯 3-레이어 모델 적용 설계

### 1. 확장된 ProposalState 정의

**신규 필드 추가** (state.py):

```python
from enum import Enum

class ProposalStatus(str, Enum):
    """Layer 1: 비즈니스상태 (사용자/PM이 보는 단계)"""
    WAITING       = "waiting"       # 초기 상태
    IN_PROGRESS   = "in_progress"   # 작성 진행 중
    COMPLETED     = "completed"     # 작성 완료
    SUBMITTED     = "submitted"     # 제출 완료
    PRESENTATION  = "presentation"  # 발표 진행
    CLOSED        = "closed"        # 종료
    ARCHIVED      = "archived"      # 보관
    ON_HOLD       = "on_hold"       # 보류
    EXPIRED       = "expired"       # 만료

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

class ProposalState(TypedDict):
    # [기존 필드]
    project_id: str
    team_id: str
    owner_id: str
    # ...

    # [Layer 1: Business Status]
    business_status: ProposalStatus          # ← 신규 (10개 값)
    win_result: Optional[WinResult]          # ← 신규 (closed일 때만)

    # [Layer 2: Workflow Phase]
    current_phase: str                       # ← 신규 (LangGraph 노드명)
                                             # 값: rfp_analyze, strategy_generate,
                                             #     proposal_write_next, etc.

    # [Layer 3: AI Runtime Status]
    ai_runtime_status: AIRuntimeStatus       # ← 신규 (임시, 세션용)
    ai_task_id: str                          # ← 신규 (LangGraph session_id)
    ai_error: Optional[str]                  # ← 신규 (에러 메시지)

    # [타임스탬프]
    started_at: Optional[str]                # ← waiting → in_progress
    completed_at: Optional[str]              # ← in_progress → completed
    submitted_at: Optional[str]              # ← completed → submitted
    presentation_started_at: Optional[str]   # ← submitted → presentation
    closed_at: Optional[str]                 # ← * → closed
    archived_at: Optional[str]               # ← closed → archived
    expired_at: Optional[str]                # ← expired 진입

    # [기존 필드 유지]
    current_step: str                        # ← 호환성 유지 (deprecated)
    # ... 14개 서브모델
    # ... feedback_history, approval, etc.
```

### 2. 상태 전환 명시화

**새로운 게이트 노드: state_transition_gate**

```python
# app/graph/nodes/state_transition_gate.py (신규)

from datetime import datetime, timezone
from app.graph.state import (
    ProposalState, ProposalStatus, WinResult, AIRuntimeStatus
)

async def state_transition_gate(state: ProposalState, new_status: ProposalStatus, win_result: Optional[WinResult] = None) -> dict:
    """명시적 상태 전환 처리."""

    now = datetime.now(timezone.utc).isoformat()
    current = state.get("business_status", ProposalStatus.WAITING)

    # 유효한 전환인지 검증 (전환 규칙 테이블 적용)
    if not _is_valid_transition(current, new_status):
        return {
            "ai_runtime_status": AIRuntimeStatus.ERROR,
            "ai_error": f"Invalid transition: {current} → {new_status}",
        }

    # 타임스탬프 업데이트
    updates = {"business_status": new_status}
    if new_status == ProposalStatus.IN_PROGRESS:
        updates["started_at"] = now
    elif new_status == ProposalStatus.COMPLETED:
        updates["completed_at"] = now
    elif new_status == ProposalStatus.SUBMITTED:
        updates["submitted_at"] = now
    elif new_status == ProposalStatus.PRESENTATION:
        updates["presentation_started_at"] = now
    elif new_status == ProposalStatus.CLOSED:
        updates["closed_at"] = now
        updates["win_result"] = win_result
    elif new_status == ProposalStatus.ARCHIVED:
        updates["archived_at"] = now
    elif new_status == ProposalStatus.EXPIRED:
        updates["expired_at"] = now

    # 이벤트 로깅 (proposal_timelines)
    await _record_timeline_event(
        state.get("project_id"),
        from_status=current,
        to_status=new_status,
        win_result=win_result,
        triggered_by="system",
    )

    return updates

def _is_valid_transition(from_status: ProposalStatus, to_status: ProposalStatus) -> bool:
    """전환 규칙 검증"""
    VALID_TRANSITIONS = {
        ProposalStatus.WAITING: [ProposalStatus.IN_PROGRESS, ProposalStatus.ON_HOLD],
        ProposalStatus.IN_PROGRESS: [
            ProposalStatus.COMPLETED,
            ProposalStatus.CLOSED,  # No-Go
            ProposalStatus.ON_HOLD,
            ProposalStatus.EXPIRED,
        ],
        # ... (전환 규칙 테이블 참조)
    }
    return to_status in VALID_TRANSITIONS.get(from_status, [])
```

### 3. 노드별 상태 업데이트 책임 명확화

**기존**: 상태 업데이트 없음
**신규**: 각 노드가 명시적으로 업데이트

#### 예1: go_no_go 노드 개선

```python
# 기존 (문제: 상태 업데이트 없음)
async def go_no_go(state: ProposalState) -> dict:
    gng = GoNoGoResult(...)
    return {
        "current_step": "go_no_go_go",  # 라우팅용
        "go_no_go_result": gng,
    }

# 신규 (3-레이어 명시화)
async def go_no_go(state: ProposalState) -> dict:
    # Layer 3: AI 실행 시작
    updates = {
        "ai_runtime_status": AIRuntimeStatus.RUNNING,
        "current_phase": "go_no_go",  # Layer 2
    }

    gng = GoNoGoResult(...)
    updates["go_no_go_result"] = gng

    # Layer 1: 비즈니스상태 (no_go인 경우만 즉시 closed)
    if gng.recommendation == "no-go":
        state_updates = await state_transition_gate(
            state,
            new_status=ProposalStatus.CLOSED,
            win_result=WinResult.NO_GO,
        )
        updates.update(state_updates)
        updates["current_phase"] = "end"  # 조기 종료
    else:
        # go인 경우: in_progress 유지 (다음 노드로)
        updates["current_step"] = "go_no_go_proceed"  # 호환성

    # Layer 3: AI 실행 완료
    updates["ai_runtime_status"] = AIRuntimeStatus.COMPLETE

    return updates
```

#### 예2: 제안서 작성 완료 노드

```python
# app/graph/nodes/proposal_nodes.py (개선)

async def proposal_write_next(state: ProposalState) -> dict:
    # ... 섹션 작성

    current_index = state.get("current_section_index", 0)
    total_sections = len(state.get("dynamic_sections", []))

    if current_index + 1 >= total_sections:
        # 마지막 섹션 완료 → in_progress → completed 전환
        state_updates = await state_transition_gate(
            state,
            new_status=ProposalStatus.COMPLETED,
        )
        return {
            **state_updates,
            "current_phase": "proposal_complete",  # Layer 2
            "current_section_index": total_sections,
            "current_step": "proposal_complete",  # 호환성
        }
    else:
        return {
            "current_phase": f"proposal_write[{current_index + 1}/{total_sections}]",
            "current_section_index": current_index + 1,
            "current_step": f"proposal_next_section",
        }
```

#### 예3: Review 게이트 개선

```python
# app/graph/nodes/review_node.py (개선)

def review_node(step_name: str):
    def _review(state: ProposalState) -> dict:
        artifact = _get_artifact(state, step_name)
        perspective = REVIEW_PERSPECTIVES.get(step_name, {})

        # Layer 3: AI 일시중지 (사용자 입력 대기)
        updates = {
            "ai_runtime_status": AIRuntimeStatus.PAUSED,  # ← 신규
        }

        interrupt_data = {
            "step": step_name,
            "artifact": artifact,
            "review_perspective": perspective,
            "message": f"[{perspective.get('perspective')}] {step_name} 검토하세요.",
        }

        human_input = interrupt(interrupt_data)

        # 인터럽트 재개: human_input 처리
        if human_input.get("quick_approve"):
            # 빠른 승인
            return {
                **updates,
                "ai_runtime_status": AIRuntimeStatus.COMPLETE,  # ← Layer 3 재개
                "approval": {
                    step_name: {
                        "status": "approved",
                        "feedback": human_input.get("feedback", ""),
                        "timestamp": human_input.get("timestamp"),
                    }
                },
                "current_step": f"review_{step_name}_approved",  # 호환성
                "current_phase": step_name,  # Layer 2
            }
        else:
            # 거부/재작업
            return {
                **updates,
                "ai_runtime_status": AIRuntimeStatus.COMPLETE,
                "approval": {step_name: {"status": "rejected", ...}},
                "current_step": f"review_{step_name}_rejected",
                "current_phase": step_name,
            }

    return _review
```

---

## 🔄 라우팅 로직 개선

### 1. 기존 라우팅 (문제)

```python
# edges.py (현재)
def route_after_gng_review(state: ProposalState) -> str:
    step = state.get("current_step", "")
    if step == "go_no_go_go":
        return "go"
    elif step == "go_no_go_no_go":
        return "no_go"
    return "rejected"

# 문제:
# ① current_step이 명확하지 않음 (라우팅용? 상태용?)
# ② 레이어 개념 없음
```

### 2. 신규 라우팅 (Layer 기반)

```python
# edges.py (신규 패턴)

def route_after_gng_review(state: ProposalState) -> str:
    """Layer 1 (business_status) + Layer 2 (current_phase) 기반 라우팅."""

    business_status = state.get("business_status", ProposalStatus.IN_PROGRESS)
    current_phase = state.get("current_phase", "")

    # Layer 1: 현재 비즈니스상태 확인
    if business_status == ProposalStatus.CLOSED:
        # No-Go 결정됨 → workflow 조기 종료
        return "no_go"

    # Layer 2: 현재 워크플로우상태 확인
    if current_phase == "go_no_go":
        gng_result = state.get("go_no_go_result")
        if gng_result and gng_result.recommendation == "go":
            return "go"
        return "no_go"

    return "rejected"


def route_after_proposal_complete(state: ProposalState) -> str:
    """섹션 작성 완료 → 자가진단 또는 검토."""

    business_status = state.get("business_status")

    if business_status == ProposalStatus.COMPLETED:
        # 모든 섹션 완료, business_status 전환됨
        return "self_review"

    # 중간 섹션 작성 중
    return "next_section"
```

### 3. 상태 기반 조건 엣지

```python
# graph.py (신규 edge 타입)

# Layer 1 비즈니스상태에 따른 조건부 엣지
def _should_process_ppt(state: ProposalState) -> bool:
    """발표전략 노드 진입 조건"""
    # Layer 1: 현재 상태가 completed 이상이어야 함
    business_status = state.get("business_status", ProposalStatus.IN_PROGRESS)
    return business_status in [
        ProposalStatus.COMPLETED,
        ProposalStatus.SUBMITTED,
        ProposalStatus.PRESENTATION,
    ]

# Layer 2 워크플로우상태에 따른 조건부 엣지
def _should_submit(state: ProposalState) -> bool:
    """제출 가능 조건"""
    # Layer 2: 현재 위상이 completed 이후여야 함
    current_phase = state.get("current_phase", "")
    completed_phases = ["mock_evaluation", "eval_result", "project_closing"]
    return current_phase in completed_phases
```

---

## 🛠️ 마이그레이션 전략

### Phase 1: ProposalState 확장 (노드 코드 변경 없음)

```python
# state.py 신규 필드 추가
# - business_status, win_result
# - current_phase, ai_runtime_status, ai_task_id, ai_error
# - 8개 타임스탬프 필드
# - current_step 유지 (호환성)
```

### Phase 2: 핵심 노드 개선 (우선순위)

**우선순위**: 상태 전환이 일어나는 노드부터

1. **P1** (상태 게이트 역할)
   - go_no_go (no_go → closed)
   - proposal_complete (→ completed)
   - evaluation_complete (→ closed)
   - project_closing (→ archived)

2. **P2** (리뷰/승인)
   - review_node (16개) ← 일괄 개선

3. **P3** (나머지)
   - rfp_analyze, strategy_generate, plan_*
   - submission_plan, bid_plan, cost_sheet

### Phase 3: 라우팅 개선

1. edges.py: Layer 기반 라우팅으로 점진 전환
2. graph.py: 조건부 엣지 최적화
3. 테스트: 각 라우팅 경로 검증

### Phase 4: 호환성 제거

- current_step 필드 제거
- 구 상태 저장 로직 제거
- routes_workflow.py 정리

---

## 📋 변경 영향도

| 파일 | 현황 | 변경 | 영향 |
|------|------|------|------|
| state.py | 14 서브모델 | +8 필드 추가 | 낮음 (추가만) |
| graph.py | 40 노드 + edge | 라우팅 개선 | 중간 (로직 개선) |
| nodes/*.py | 각 노드 | 상태 업데이트 추가 | 중간 (3-4줄 추가/노드) |
| edges.py | 15 라우팅 함수 | Layer 기반 변환 | 중간 (점진 전환) |
| routes_workflow.py | API | 상태 저장 수정 | 높음 (구조 변경) |
| DB | 기존 schema_v3.4 | 마이그레이션 필요 | 높음 |

---

## ✅ 체크리스트

### 1. 설계 검토
- [ ] 3-레이어 모델이 모든 워크플로우 경로에 적용 가능한가?
- [ ] 기존 40개 노드가 새 state 구조에 호환되는가?
- [ ] 라우팅 로직이 단순해지는가?

### 2. 구현 순서
- [ ] state.py 확장 (backward compatible)
- [ ] 핵심 노드 3개(go_no_go, proposal_complete, evaluation) 개선
- [ ] review_node 일괄 개선
- [ ] 나머지 노드 개선
- [ ] edges.py Layer 기반 리팩토링
- [ ] DB 마이그레이션 동시 진행
- [ ] routes_workflow.py 수정

### 3. 테스트
- [ ] 각 상태 전환 경로 검증
- [ ] 대안 경로 (no_go, cancel, hold) 검증
- [ ] 병렬 노드 (plan_*) 상태 병합 검증
- [ ] 기존 라우팅 호환성 확인

---

## 📌 다음 액션

1. **설계 검토** → 위 분석이 타당한지 확인
2. **우선순위 결정** → P1 노드 3개 먼저 vs 전면 동시 개선
3. **구현 시작** → state.py 확장 후 go_no_go 테스트
4. **DB 마이그레이션** → unified-state-system.plan.md Phase 1 동시 진행
