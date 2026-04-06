# ARTIFACT_VERSION System 기획서

> **작성일**: 2026-03-30
> **목표**: 노드 간 자유 이동 시 산출물 버전 관리 및 의존성 해결 시스템 구현
> **선행 요구사항**: COMPREHENSIVE-IMPLEMENTATION-REVIEW.md (노드 의존성 맵 기반)
> **후행 연계**: STEP 8A 구현 전 완료 예정

---

## 🎯 핵심 목표

### 문제 정의

현재 LangGraph 워크플로에서:
```
❌ 문제 1: 노드 재실행 시 기존 산출물 삭제
   → 히스토리 추적 불가, Rollback 불가

❌ 문제 2: 한 노드가 여러 산출물 생성 시 후행 노드가 어느 버전 사용?
   → 불명확한 의존성, 데이터 일관성 깨짐

❌ 문제 3: 버전 충돌 시 Human의 수동 선택 방안 부재
   → 의사결정 과정 추적 불가
```

### 해결 방안

```
✅ 해결 1: 모든 산출물 자동 버전화
   → 모든 노드 실행 후 v1, v2, v3... 생성

✅ 해결 2: 스마트 버전 선택 (의존성 기반)
   → 버전 충돌 시에만 Human 개입
   → 자동 추천 (최신, 가장 많이 사용, 창작 시점)

✅ 해결 3: 완전한 의사결정 추적
   → 버전 선택 이력 DB 저장
   → Audit log 기록
```

---

## 📋 요구사항

### Functional Requirements (FR)

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-01 | 모든 노드 산출물의 자동 버전화 | 🔴 필수 |
| FR-02 | 버전 간 의존성 추적 및 표시 | 🔴 필수 |
| FR-03 | 버전 선택 메커니즘 (Human 개입) | 🔴 필수 |
| FR-04 | 버전 비교 기능 (diff view) | 🟡 권장 |
| FR-05 | 버전 복원/Rollback 기능 | 🟡 권장 |
| FR-06 | 자동 아카이빙 정책 (용량 관리) | 🟢 선택 |

### Non-Functional Requirements (NFR)

| ID | 요구사항 | 목표 |
|----|---------|------|
| NFR-01 | 버전 조회 응답 시간 | < 100ms |
| NFR-02 | DB 저장소 증가 | 평균 프로젝트당 < 50MB |
| NFR-03 | State 복잡도 증가 | 기존 대비 +20% |
| NFR-04 | API 응답 시간 | < 500ms |

---

## 🔄 아키텍처 개요

### 계층 구조

```
┌─────────────────────────────────────┐
│ Frontend: VersionSelectionModal     │ (Phase 2)
│ - 버전 선택 UI
│ - 의존성 경고 표시
│ - 추천 버전 안내
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ API Layer (routes_workflow.py)      │ (Phase 1-2)
│ - move_to_node_with_version_resolution
│ - get_node_dependencies
│ - validate_move_and_resolve_versions
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ Service Layer (version_manager.py) │ (Phase 1)
│ - execute_node_and_create_version
│ - _check_dependency_mismatch
│ - _recommend_version
│ - artifact_controller
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ State Layer (state.py)              │ (Phase 1)
│ - artifact_versions: dict[str, list]
│ - active_versions: dict[str, int]
│ - version_selection_history: list
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ DB Layer (Supabase)                 │ (Phase 1)
│ - proposal_artifacts
│ - proposal_artifact_choices
└─────────────────────────────────────┘
```

---

## 📊 데이터 모델

### DB 테이블

**1. proposal_artifacts** (산출물 버전 저장소)
```sql
- id, proposal_id, node_name, output_key, version
- created_at, created_by
- is_active, is_deprecated
- parent_node_name, parent_version
- artifact_data (JSONB), artifact_size, checksum
- used_by (JSONB), created_reason, notes
```

**2. proposal_artifact_choices** (Human 선택 이력)
```sql
- id, proposal_id
- choice_point, from_node, to_node
- required_input, available_versions, selected_version
- decision_at, decided_by, reason
```

### State 모델

```python
class ArtifactVersion(BaseModel):
    node_name: str
    output_key: str
    version: int
    created_at: str
    created_by: str
    is_active: bool
    parent_version: Optional[int]
    used_by: list[dict]

ProposalState additions:
- artifact_versions: dict[str, list[ArtifactVersion]]
- active_versions: dict[str, int]
- version_selection_history: list[dict]
```

---

## 📈 구현 범위 & 일정

### Phase 1: 기본 버전 관리 (필수, 2일)

**목표**: 모든 산출물 자동 버전화 + DB 저장

**작업 항목**:
- [ ] proposal_artifacts, proposal_artifact_choices 테이블 생성
- [ ] ArtifactVersion State 모델 정의
- [ ] execute_node_and_create_version() 함수 구현
- [ ] 모든 노드에 자동 버전 생성 로직 추가
- [ ] 버전 조회 API 작성

**산출물**:
- `database/migrations/XXX_artifact_versioning.sql`
- `app/graph/state.py` (State 확장)
- `app/services/version_manager.py` (신규)
- `app/api/routes_artifacts.py` 강화

**검증**:
- 단위 테스트: 각 노드별 버전 생성 확인
- 통합 테스트: 노드 재실행 시 v2 생성 확인
- DB 테스트: artifact 저장 및 조회 확인

---

### Phase 2: 버전 선택 메커니즘 (권장, 2일)

**목표**: 버전 충돌 감지 + Human 선택 + 의존성 추적

**작업 항목**:
- [ ] validate_move_and_resolve_versions() 함수 구현
- [ ] move_to_node_with_version_resolution() API 구현
- [ ] VersionSelectionModal 프론트엔드 컴포넌트
- [ ] 의존성 경고 표시 로직
- [ ] 버전 추천 로직

**산출물**:
- `app/services/version_manager.py` 확장 (resolve 함수)
- `app/api/routes_workflow.py` 신규 엔드포인트
- `frontend/components/VersionSelectionModal.tsx` (신규)
- 선택 이력 DB 기록

**검증**:
- 시나리오 테스트: 1개 버전, 3개 버전, 모두 누락 케이스
- UI 테스트: 모달 표시 및 선택 동작
- E2E 테스트: 이동 후 올바른 버전 사용 확인

---

### Phase 3: 고급 기능 (선택, 2-3일)

**목표**: 버전 비교, Rollback, 자동 아카이빙

**작업 항목**:
- [ ] 버전 비교 (diff) 기능
- [ ] 버전 복원 (Rollback) API
- [ ] 자동 아카이빙 정책 (4개 이상 유지, 이전 버전 아카이브)
- [ ] 버전별 의존성 트레이싱
- [ ] 저장소 용량 모니터링

**산출물**:
- `app/services/artifact_comparison.py` (신규)
- `app/services/artifact_archiver.py` (신규)
- 버전 비교 UI 컴포넌트

---

## 🔗 STEP 8A와의 통합

### 영향 범위

```
STEP 8A의 모든 노드가 자동으로 버전 관리 대상:

proposal_customer_analysis
  ├─ customer_context v1, v2, v3 (재실행할 때마다)

proposal_section_validator
  ├─ section_validation_results v1, v2

proposal_sections_consolidation
  ├─ sections_consolidation_result v1, v2

mock_evaluation_analysis
  ├─ mock_evaluation_analysis v1, v2

mock_evaluation_feedback_processor
  ├─ mock_eval_feedback v1, v2
  └─ rework_instructions v1, v2
```

### 통합 시나리오

```
시나리오: STEP 8A-① → STEP 8A-② → STEP 8A-③ → 전략 재검토

1️⃣ proposal_customer_analysis 실행
   → customer_context v1 생성

2️⃣ proposal_write_next (섹션 1-3)
   → proposal_sections v1 생성

3️⃣ proposal_sections_consolidation 진행
   → sections_consolidation_result v1 생성

4️⃣ [사용자 결정] "전략부터 다시 해야 할 것 같아"
   → strategy 수정
   → strategy v2 생성

5️⃣ "proposal_write_next로 이동할래?"
   [시스템 검증]
   - customer_context: v1 (strategy v1 기반)
   - proposal_sections: v1 (strategy v1 기반)
   - 새 strategy v2가 있음!

   [버전 선택 필요]
   "proposal_write_next를 실행할 때, 어느 strategy를 사용할래?"
   ├─ Strategy v1 (기존 proposal_sections v1 유지)
   ├─ Strategy v2 (새로운 proposal_sections v2 생성) ⭐ 추천
   └─ Custom (v1 일부 + v2 일부)

6️⃣ User 선택: "Strategy v2로 새로 작성할래"
   → proposal_write_next (strategy v2 기반)
   → proposal_sections v2 생성
   → proposal_sections v1은 history로 보존
```

---

## 🎨 UI/UX 설계

### VersionSelectionModal

```
┌──────────────────────────────────────────────┐
│ 산출물 버전 선택 필요                         │
├──────────────────────────────────────────────┤
│                                              │
│ 📋 strategy 버전 선택                        │
│ ┌────────────────────────────────────────┐  │
│ │ v1 (현재)  | v2 ⭐추천  | v3           │  │
│ │ 2026-03-29 | 2026-03-30 | 2026-03-30  │  │
│ │ 사용 2개   | 사용 0개   | 사용 0개    │  │
│ └────────────────────────────────────────┘  │
│                                              │
│ ⚠️ 의존성 경고                               │
│ proposal_sections v1이 strategy v1을 기반   │
│ strategy v2 선택 시 proposal_sections을 재생성해야 합니다.
│                                              │
│ [v1 유지] [v2로 새로 작성] [custom]  [취소] │
└──────────────────────────────────────────────┘
```

---

## 💾 DB 마이그레이션 계획

### Migration 파일

```sql
-- 001_artifact_versioning.sql
CREATE TABLE proposal_artifacts (
    id UUID PRIMARY KEY,
    proposal_id UUID NOT NULL REFERENCES proposals(id),
    node_name VARCHAR NOT NULL,
    output_key VARCHAR NOT NULL,
    version INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    parent_node_name VARCHAR,
    parent_version INT,
    artifact_data JSONB,
    artifact_size INT,
    checksum VARCHAR,
    used_by JSONB DEFAULT '[]'::jsonb,
    created_reason VARCHAR,
    notes TEXT,
    UNIQUE(proposal_id, node_name, output_key, version)
);

CREATE TABLE proposal_artifact_choices (
    id UUID PRIMARY KEY,
    proposal_id UUID NOT NULL,
    choice_point VARCHAR NOT NULL,
    from_node VARCHAR NOT NULL,
    to_node VARCHAR NOT NULL,
    required_input VARCHAR NOT NULL,
    available_versions JSONB,
    selected_version INT,
    decision_at TIMESTAMP,
    decided_by UUID NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_artifact_version
ON proposal_artifacts(proposal_id, node_name, output_key, version DESC);
```

---

## 🧪 검증 기준

### Phase 1 검증

- [ ] 모든 노드 재실행 후 v2 생성 확인
- [ ] artifact_versions state 필드 정상 업데이트
- [ ] DB 저장 및 조회 성공
- [ ] 버전 메타데이터 (created_at, created_by 등) 정확

### Phase 2 검증

- [ ] 1개 버전만 있을 때 자동 선택
- [ ] 3개 버전 있을 때 모달 표시
- [ ] 버전 선택 이력 DB 저장
- [ ] 선택 후 올바른 버전 사용

### Phase 3 검증

- [ ] Diff view에서 버전 간 차이 표시
- [ ] Rollback 후 이전 상태 복원
- [ ] 자동 아카이빙 정책 동작

---

## 📚 참고 문서

- [COMPREHENSIVE-IMPLEMENTATION-REVIEW.md](../../../docs/01-plan/COMPREHENSIVE-IMPLEMENTATION-REVIEW.md)
  - 노드 의존성 맵

- [mock-evaluation-human-review-feedback.md](../../../docs/02-design/mock-evaluation-human-review-feedback.md)
  - 버전 선택 필요성 언급

- [LangGraph State Design](https://python.langchain.com/docs/langgraph/concepts/agentic_loops)
  - State 관리 모범 사례

---

## 🚀 다음 단계

1. ✅ Plan 완료 (이 문서)
2. ⏭️ **[Design]** artifact_version_system.design.md 작성
   - DB 스키마 상세 설계
   - API 엔드포인트 명세
   - State 모델 정의

3. ⏭️ **[Do]** Phase 1 구현 시작
   - 마이그레이션 실행
   - version_manager.py 작성
   - 노드 통합

4. ⏭️ **[Check]** Gap Analysis
   - Phase 1 구현 vs Design 비교
   - Match Rate 확인

5. ⏭️ **[Report]** 완료 보고서
   - Phase 1-2 완료 후 생성

---

## 📝 메모

- **우선순위**: STEP 8A 구현 전에 Phase 1 완료 필수
- **블로커**: Phase 1 완료 없이 STEP 8A 구현 불가 (버전 추적 필요)
- **병렬성**: Phase 1과 Design 병렬 진행 가능
- **복잡도**: 중간 (DB + State + API 모두 확장)
- **대안 검토**: 버전 관리 없이 진행? (불권장 - 추적 불가)

---

**Plan 작성자**: Claude
**작성 일시**: 2026-03-30
**상태**: ✅ Plan 완료, Design 대기 중
