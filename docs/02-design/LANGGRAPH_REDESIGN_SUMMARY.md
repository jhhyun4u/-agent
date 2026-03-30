# LangGraph 3-레이어 모델 적용 종합 요약
## "원점에서 다시 검토한 노드 아키텍처 개선 방안"

> **분석 완료**: 2026-03-29
> **검토 대상**: 40개 노드, 15개 라우팅, 현재 상태관리 방식
> **결론**: 3-레이어 모델을 명시적으로 적용하면 복잡도 ↓, 명확성 ↑

---

## 🔍 검토 결과: 3가지 핵심 발견

### 1️⃣ 현재 문제: 상태가 3곳에 산재되어 있음

```
❌ 현황:
┌─────────────────────────────────────────────┐
│ proposals 테이블 (DB)                        │
│  status: 16개 혼합된 값                      │
│  ("processing", "submitted", "won", ...)    │
│  ➜ 뭘 의미하는지 불명확                      │
│                                            │
│ ProposalState (LangGraph 메모리)             │
│  current_step: 임의로 설정되는 값             │
│  ("go_no_go_go", "proposal_next_section", )│
│  ➜ 최종 위치인지, 중간인지 모호              │
│                                            │
│ metadata (dict) — 흩어진 추적 정보            │
│  feedback_history, approval, ...            │
│  ➜ 일관된 상태 기록 체계 없음                 │
└─────────────────────────────────────────────┘

✅ 개선 후:
┌─────────────────────────────────────────────┐
│ Layer 1: Business Status (사용자 관점)       │
│  "waiting", "in_progress", "completed",     │
│  "submitted", "presentation", "closed"      │
│  + win_result 세부값 ("won", "lost", ...)   │
│  ➜ PM이 이해하는 6단계                       │
│                                            │
│ Layer 2: Workflow Phase (개발자 관점)       │
│  "rfp_analyze", "strategy_generate",        │
│  "proposal_write_next", "mock_evaluation"   │
│  ➜ LangGraph 40개 노드 이름 정확히 추적     │
│                                            │
│ Layer 3: AI Runtime Status (임시)           │
│  "running", "paused", "error", "complete"   │
│  ➜ 세션 중 AI 실행 상태 추적                │
│                                            │
│ 타임스탬프 (이벤트 추적)                     │
│  started_at, completed_at, submitted_at,   │
│  closed_at, archived_at, ...                │
│  ➜ 각 단계 진입 시점 기록                   │
└─────────────────────────────────────────────┘
```

**영향**:
- DB: 기존 16개 혼재값 → 10개 정의값으로 단순화
- 노드: 상태 업데이트를 명시적으로 수행
- 라우팅: Layer 기반으로 명확한 분기 로직

---

### 2️⃣ 현재 문제: 노드가 상태를 업데이트하지 않음

```
❌ 현황:

go_no_go 노드:
  input: business_status = "in_progress"
  output: {
    "go_no_go_result": GoNoGoResult(...),  ← 결과만
    "current_step": "go_no_go_go"           ← 라우팅 신호
  }
  ➜ business_status는 여전히 "in_progress" (오류!)

proposal_write_next 노드:
  input: business_status = "in_progress"
  output: {
    "proposal_sections": [...],             ← 섹션만
    "current_section_index": 1
  }
  ➜ 마지막 섹션 완료해도 상태 안 바뀜

✅ 개선 후:

go_no_go 노드 (no_go 경우):
  input: business_status = "in_progress"
  output: {
    "business_status": "closed",            ← ★ 명시적 업데이트
    "win_result": "no_go",                  ← ★ 세부값
    "closed_at": "2026-03-29T10:00:00Z",   ← ★ 타임스탬프
    "current_phase": "end",                 ← Layer 2
    "ai_runtime_status": "complete"         ← Layer 3
  }

proposal_write_next 노드 (마지막 섹션):
  input: business_status = "in_progress"
  output: {
    "business_status": "completed",         ← ★ 자동 전환
    "completed_at": "2026-03-29T10:00:00Z", ← ★ 기록
    "current_phase": "proposal_complete",   ← Layer 2
    ...
  }
```

**효과**:
- 각 노드가 명확한 책임을 짐 (상태 업데이트)
- 상태 전환이 추적 가능해짐
- 조기 종료 (no_go) 시 즉각 반영

---

### 3️⃣ 현재 문제: 라우팅이 current_step의 임의값에 의존

```
❌ 현황:

route_after_gng_review:
  if state.get("current_step") == "go_no_go_go":
      return "go"
  elif state.get("current_step") == "go_no_go_no_go":
      return "no_go"

문제:
- 어떤 값이 올까? go_no_go 노드가 임의로 설정
- 만약 노드가 깜빡하면?
- 다른 노드에서도 같은 값 설정하면?

✅ 개선 후:

route_after_gng_review (v2):
  business_status = state.get("business_status")

  # Layer 1: 현재 상태 확인
  if business_status == "closed":
      win_result = state.get("win_result")
      if win_result == "no_go":
          return "no_go"

  # Layer 2: 현재 위상 확인 (backup)
  current_phase = state.get("current_phase")
  if current_phase == "go_no_go":
      gng = state.get("go_no_go_result")
      return "go" if gng.recommendation == "go" else "no_go"

장점:
- Layer 1 (비즈니스상태)을 신뢰할 수 있음
- Layer 2 (워크플로우위상)로 이중 검증
- 일관된 분기 로직
```

---

## 🎯 3-레이어 설계의 핵심 원칙

### Layer 1: Business Status (사용자 관점)
**목적**: PM이 보는 높은 수준의 제안 단계
**값**: 10개 (waiting, in_progress, completed, submitted, presentation, closed, archived, on_hold, expired)
**업데이트**: 명시적 상태 전환 시만 (상태_transition_gate)
**추적**: 8개 타임스탬프로 각 단계 진입 시점 기록
**DB**: proposals.status + proposals.win_result (closed일 때만)

### Layer 2: Workflow Phase (개발자 관점)
**목적**: LangGraph의 현재 실행 위치 추적
**값**: 40개 (노드명: rfp_analyze, strategy_generate, proposal_write_next, ...)
**업데이트**: 각 노드 진입 시 자동
**역할**: 라우팅 검증, 복구 지점, 진행도 표시
**DB**: proposals.current_phase (LangGraph 디버깅용)

### Layer 3: AI Runtime Status (기술 관점)
**목적**: 현재 AI 실행 상태 (세션 단위)
**값**: 5개 (running, paused, error, no_response, complete)
**업데이트**: AI 작업 시작/중단/완료 시
**역할**: interrupt 관리, 에러 추적
**DB**: ai_task_status 테이블 (임시, 세션 종료 시 정리)

### 타임스탬프 (이벤트 추적)
**목적**: 제안서 생명주기 기록
**필드**: started_at, completed_at, submitted_at, presentation_started_at, closed_at, archived_at, expired_at
**역할**: 제안 기간 계산, 마감일 추적, 성과 분석
**DB**: proposals 테이블 (구조화된 이벤트 로그)

---

## 🔄 실제 적용 예시

### 시나리오 1: 정상 제안서 완성

```
초기 상태:
  business_status = "waiting"
  current_phase = null
  ai_runtime_status = "complete"

[1] PM이 "착수" 클릭
  ✓ business_status = "in_progress"  (Layer 1)
  ✓ started_at = NOW()               (타임스탐프)

[2] rfp_analyze 노드 실행
  ✓ current_phase = "rfp_analyze"    (Layer 2)
  ✓ ai_runtime_status = "running"    (Layer 3)

[3] ... (전략 수립, 제안서 작성)

[4] proposal_write_next: 마지막 섹션 완료
  ✓ business_status = "completed"    (Layer 1 자동 전환!)
  ✓ completed_at = NOW()             (타임스탐프)
  ✓ current_phase = "proposal_complete" (Layer 2)

[5] review_proposal 게이트: 사용자 승인
  ✓ business_status = "submitted"    (Layer 1)
  ✓ submitted_at = NOW()             (타임스탐프)

[6] presentation 노드
  ✓ business_status = "presentation" (Layer 1)
  ✓ presentation_started_at = NOW()  (타임스탐프)

[7] eval_result 노드: 수주 결정
  ✓ business_status = "closed"       (Layer 1)
  ✓ win_result = "won"               (세부값)
  ✓ closed_at = NOW()                (타임스탐프)

[8] 30일 경과: CRON 자동 실행
  ✓ business_status = "archived"     (Layer 1)
  ✓ archived_at = NOW()              (타임스탐프)
```

### 시나리오 2: No-Go 조기 종료

```
초기:
  business_status = "in_progress"
  current_phase = "rfp_analyze"

[1] go_no_go 노드: No-Go 결정
  ✓ business_status = "closed"       (Layer 1 즉시 전환!)
  ✓ win_result = "no_go"             (세부값)
  ✓ closed_at = NOW()                (타임스탐프)
  ✓ current_phase = "end"            (Layer 2 조기 종료)

[2] 라우팅: route_after_gng_review
  → business_status == "closed" AND win_result == "no_go"
  → return "no_go"
  → END (전체 워크플로우 종료)

효과:
  - 전략수립, 제안서작성 노드는 실행 안됨
  - 시간·자원 절약
  - 타임라인에 정확한 no_go 시점 기록
```

### 시나리오 3: 부분 재작업

```
상태:
  business_status = "completed"
  current_phase = "proposal_complete"

[1] review_proposal: "제안서 재작성 필요"
  ✓ business_status = "in_progress"  (Layer 1 되돌림!)
  ✓ current_phase = "proposal_write_next" (Layer 2 복귀)

[2] rework_targets = ["section_1", "section_3"]
  → proposal_write_next: 해당 섹션만 재작성

[3] 모든 재작업 완료
  ✓ business_status = "completed"    (Layer 1 다시 전환)
  ✓ completed_at = UPDATE()          (타임스탐프 갱신)

효과:
  - in_progress ↔ completed 왕복 가능
  - 각 전환이 기록됨
  - 재작업 횟수 추적 가능
```

---

## 🚀 구현 순서 (4일 스케줄)

| Day | Phase | 시간 | 핵심 작업 |
|-----|-------|------|----------|
| 1 | A (기초) | 4h | state.py Enum + 신규필드 + state_utils |
| 2 | B (노드) + C (게이트) | 11h | go_no_go, review_node 개선 |
| 3 | D (라우팅) + E (API) | 7h | edges.py, routes_workflow.py 수정 |
| 4 | F (테스트) | 3h | E2E 테스트, 배포 준비 |

**병렬화**: Phase B/C/D는 독립적이므로 동시 진행 가능 (3일로 단축)

---

## 📊 변경 요약

### 코드 규모
- **신규 파일**: 3개 (state_utils.py, 테스트, 분석문서)
- **수정 파일**: 8개 (state.py, graph.py, nodes/*.py, edges.py, routes_workflow.py)
- **평균 변경**: 노드당 3-5줄 추가 (상태 업데이트)
- **전체 LOC**: +150~200줄 (신규 로직)

### 호환성
- **기존 필드 유지**: current_step 계속 지원 (v5.1에서 제거)
- **라우팅 호환성**: 기존 route_after_* 함수 유지
- **데이터베이스**: 마이그레이션 필수 (unified-state-system.plan.md 참조)

### 성능
- **상태 조회**: 추가 복잡도 없음 (dict 접근)
- **라우팅 성능**: 동일 (조건 분기만 추가)
- **DB 쿼리**: 타임스탐프 인덱싱으로 성능 개선 가능

---

## ✅ 기대 효과

| 측면 | 현황 | 개선 |
|------|------|------|
| **명확성** | 상태가 3곳에 산재 | 3-레이어로 계층화 |
| **추적성** | 현재 위치 불명확 | Layer 2 + 8개 타임스탐프로 정확 추적 |
| **자동화** | 상태 업데이트 수동 | 노드에서 자동 |
| **버그 감소** | 상태 불일치 빈번 | 일관된 전환 규칙 |
| **라우팅** | current_step 임의값 의존 | Layer 1/2 기반 명확 분기 |
| **조기종료** | No-Go 후에도 다음 노드 실행 | 즉시 closed 상태로 단축 |
| **재작업** | 상태 복구 불가 | in_progress ↔ completed 왕복 지원 |

---

## 🔗 관련 문서

1. **[langgraph-node-architecture-analysis.md](langgraph-node-architecture-analysis.md)**
   - 현황 상세 분석
   - 문제점 파악
   - 3-레이어 설계 상세

2. **[langgraph-implementation-roadmap.md](langgraph-implementation-roadmap.md)**
   - 구현 단계별 가이드
   - 코드 예시 (복사-붙여넣기 가능)
   - 테스트 방법

3. **[unified-state-system.plan.md](../01-plan/features/unified-state-system.plan.md)**
   - DB 마이그레이션 계획
   - 기존 16개 상태 매핑
   - 3일 실행 계획

---

## 🎬 다음 액션

### 즉시 (오늘)
- [ ] 이 문서 검토 후 피드백
- [ ] 3-레이어 모델 타당성 확인
- [ ] Phase A 시작 승인

### 24시간 내
- [ ] 브랜치 생성: `feature/langgraph-3layer`
- [ ] state.py Enum 정의 + PR
- [ ] 첫 노드 (go_no_go) 수정 + 테스트

### 이후
- [ ] 매일 1-2개 노드 개선
- [ ] 4일 내 전체 완성
- [ ] staging 환경 배포
- [ ] 프로덕션 배포

---

**핵심 메시지**:
> 현재 LangGraph는 40개 노드가 순차적으로 실행되면서 상태를 명시적으로 업데이트하지 않고 있습니다.
> 3-레이어 모델을 도입하면 각 노드가 명확한 책임을 지고, 상태 전환이 추적 가능해지며,
> 라우팅 로직이 단순해집니다. 구현은 점진적이므로 위험이 낮습니다.
