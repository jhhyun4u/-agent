# proposal-agent-v1 v4.0 아키텍처 진화

| 항목 | 내용 |
|------|------|
| 문서 버전 | v4.0 |
| 작성일 | 2026-03-29 |
| 기반 | proposal-agent-v1 v3.6 설계 + 실제 구현 |
| 상태 | 설계-구현 동기화 (갭 분석 후 작성) |

---

## 개요

v3.6 설계는 단순 선형 workflow(STEP 0→1→2→3→4→5)를 가정했습니다. 그러나 실제 구현은 **v4.0으로 진화**하여 다음과 같은 아키텍처 변경이 도입되었습니다:

1. **STEP 0이 그래프 외부로 이동** (API-driven)
2. **전략 승인 후 A/B 브랜치 병렬 실행**
3. **PPT 파이프라인 3단계화** (sequential)
4. **추가 평가 및 종료 로직**

---

## 1. STEP 0: API-Driven Architecture (설계 vs 구현 변경)

### v3.6 설계
```
START → route_start
    ├─ Path 1: rfp_search → review_search → rfp_fetch (검색 경로)
    ├─ Path 2: rfp_upload (파일 업로드 경로)
    └─ Path 3: rfp_direct (공고 지정 경로)
    ↓
rfp_analyze (STEP 1-①)
```

**설계 의도**: STEP 0 노드를 StateGraph에 등록하여 LangGraph 프레임워크 내에서 검색·결과 재시도 등을 관리.

### v4.0 구현 (실제)
```
FastAPI Route: POST /api/proposals/from-rfp, /api/proposals/from-bid
    ├─ rfp_search() — G2B API 호출 + 캐싱
    ├─ rfp_fetch() — PDF/HWP/HWPX 다운로드
    └─ Validation 및 제안서 메타 수집
    ↓ (이후 graph.start() 호출)
START → rfp_analyze (STEP 1-①)
```

**구현 변경 이유**:
- STEP 0은 **검색/다운로드**에 특화 (AI 처리 불필요, 외부 API 호출)
- LangGraph StateGraph 내에서 동작할 필요 없음 (interrupt 불필요)
- **성능**: API 응답을 기다리지 않고 제안서 생성 가능 (비동기 처리)
- **에러 처리**: 검색 실패 시 별도 폴백 로직 (graph restart vs manual upload)

**설계 업데이트**: ✅ STEP 0은 **API 엔드포인트**로서 동작하며, 그 결과(rfp_content, rfp_title, budget 등)를 초기 state로 전달하여 graph.start() 호출.

---

## 2. Path A/B 브랜치: 제안서 + 제출/비딩 병렬 실행

### v3.6 설계 (선형)
```
strategy_generate (STEP 2)
    ↓
plan_* (STEP 3) — 5개 병렬: team, assign, schedule, story, price
    ↓
proposal_write_next (STEP 4A) — 순차 섹션 작성
    ↓
ppt_* (STEP 5A) — PPT 생성
    ↓
END
```

### v4.0 구현 (A/B 병렬)
```
strategy_generate (STEP 2)
    ↓
fork_gate → Send()
    ├─ Path A: 제안서 (STEP 3~5)
    │   ├─ plan_fan_out_gate
    │   │   └─ plan_team, plan_assign, plan_schedule, plan_story, plan_price (병렬)
    │   ├─ plan_merge
    │   ├─ review_plan
    │   ├─ proposal_start_gate
    │   ├─ proposal_write_next (순차 섹션)
    │   ├─ self_review
    │   ├─ ppt_toc → ppt_visual_brief → ppt_storyboard (3단계 순차)
    │   └─ stream1_complete_hook
    │
    └─ Path B: 제출/비딩 (STEP 3B~5B)
        ├─ submission_plan (제출서류 계획)
        ├─ bid_plan (입찰가 전략)
        ├─ cost_sheet_generate (산출내역서)
        └─ submission_checklist (제출 체크리스트)

convergence_gate (양쪽 경로 동기화 대기)
    ↓
mock_evaluation (STEP 6A) — 모의평가
    ↓
eval_result_node (STEP 7) — 평가 결과
    ↓
project_closing (STEP 8) — 종료 처리
    ↓
END
```

**v4.0 도입 이유**:

| 측면 | v3.6 설계 | v4.0 구현 |
|------|----------|----------|
| **제안서 + 비딩** | 순차 (제안서 完료 후 비딩) | 병렬 (동시 진행) |
| **실무 맥락** | 제안서 작성이 최종 단계 | 제출/비딩도 동시 진행 (3-Stream) |
| **효율성** | 전체 소요 시간 = T_proposal + T_bid | 전체 소요 시간 ≈ max(T_proposal, T_bid) |
| **유연성** | 제안서 완료 후에야 비딩 전략 수립 | 병렬 수립 (상호 피드백 가능) |

---

## 3. PPT 파이프라인: Fan-out → 3단계 순차

### v3.6 설계
```
presentation_strategy (전략 수립)
    ↓
ppt_fan_out_gate
    └─ ppt_slide (각 섹션별) [병렬]
    ├─ ppt_slide (Executive Summary)
    ├─ ppt_slide (Technical Approach)
    ├─ ppt_slide (Team & Resources)
    └─ ...
    ↓
ppt_merge (병합)
    ↓
review_ppt
    ↓
END
```

**설계 의도**: 각 섹션별 슬라이드를 병렬로 생성하여 효율화.

### v4.0 구현 (3단계 순차)
```
presentation_strategy (전략 수립 - 조건: 서류심사 SKIP 경우 SKIP)
    ↓
ppt_toc (목차 + Outline 생성)
    ↓
ppt_visual_brief (비주얼 레이아웃 + 이미지 키워드)
    ↓
ppt_storyboard (최종 스토리보드 + 스피커 노트)
    ↓
[PPTX 렌더링] (별도 서비스)
```

**v4.0 변경 이유**:

| 측면 | v3.6 병렬 Fan-out | v4.0 순차 3단계 |
|------|-----------------|----------------|
| **PPT 생성 시간** | 빠름 (병렬) | 더 느림 (순차) |
| **품질** | 슬라이드 독립 생성 → 일관성 낮음 | 전체 스토리 기반 → 일관성 높음 |
| **서류심사** | 모든 경우 PPT 생성 | 평가 방식이 서류심사인 경우 SKIP |
| **컨텍스트** | 각 섹션만 참고 | 전체 제안 맥락 유지 |

**설계 업데이트**: ✅ PPT는 3단계 sequential pipeline (TOC → Visual Brief → Storyboard)으로 변경. 품질 > 속도.

---

## 4. 평가 및 종료: 새로운 STEP 6~8

### v3.6 설계
```
END (PPT 생성 후 종료)
```

### v4.0 구현
```
STEP 6A: mock_evaluation
    ├─ 제안서 내용 기반 모의평가 (기술점수, 가격점수)
    ├─ 자격요건 심사
    ├─ 시스템 심사 (형식/컴플라이언스)
    └─ State: mock_evaluation_result 저장

STEP 7: eval_result_node
    ├─ 평가 결과 종합 (점수 계산, 순위 예측)
    ├─ AI 피드백 (강점/약점/개선안)
    └─ State: eval_result 저장

STEP 8: project_closing
    ├─ 제안 완료 상태 마킹
    ├─ 산출물 최종 패키징
    ├─ 아카이브 스냅샷
    └─ 성과 추적 준비

END
```

**도입 이유**: 제안 완료 후 평가 예측 및 최종 피드백 제공. 용역 수주의 성공 확률 사전 예측.

---

## 5. 상태 필드 추가 (v4.0)

### v3.6 설계 State 필드
```
- rfp_content, rfp_analysis, go_no_go_result
- strategy, compliance_matrix
- proposal_sections, dynamic_sections
- ppt_slides
```

### v4.0 구현 추가 필드
```
# Path B (제출/비딩)
- submission_plan: SubmissionDocsPlan
- bid_plan: BidPlanResult
- cost_sheet: CostSheetPayload
- submission_checklist_result: SubmissionChecklistResult

# 평가
- mock_evaluation_result: MockEvaluationResult
- eval_result: EvaluationResult

# 메타
- quality_warnings: List[str]
- node_errors: Dict[str, str]
- ppt_storyboard: PPTStoryboardPayload
```

---

## 6. 노드 개수 확장

| 범주 | v3.6 | v4.0 | 추가 |
|------|:----:|:----:|:----:|
| STEP 0 | - | - | - |
| STEP 1 | 4 | 4 | - |
| STEP 2 | 2 | 2 | - |
| STEP 3 (plan) | 4 + merge | **5** + merge | +1 (plan_price) |
| STEP 3B (new) | - | 1 | +1 (submission_plan) |
| STEP 4A | 3 | 3 | - |
| STEP 5A (PPT) | 4 (ppt_* + merge) | **3** | -1 (3단계 순차) |
| STEP 2.5B (new) | - | 1 | +1 (bid_plan) |
| STEP 5B (new) | - | 2 | +2 (cost_sheet, submission_checklist) |
| STEP 6A (new) | - | 1 | +1 (mock_evaluation) |
| STEP 7 (new) | - | 1 | +1 (eval_result) |
| STEP 8 (new) | - | 1 | +1 (project_closing) |
| Gate/Fork | 3 | **6** | +3 (fork_gate, convergence_gate, stream1_complete_hook) |
| **합계** | ~28 | **40** | **+12** |

---

## 7. 그래프 라우팅: Conditional Edges (v4.0 변경)

### v3.6 설계
```
go_no_go (STEP 1-②)
    ├─ GO → strategy_generate
    └─ NO-GO → END

self_review (STEP 4)
    ├─ PASS → ppt_*
    ├─ retry_research → research_gather (재실행)
    ├─ retry_strategy → strategy_generate (재실행)
    ├─ retry_sections → proposal_write_next (재작성)
    └─ force_review → review_proposal
```

### v4.0 구현 (Path B 추가)
```
strategy_generate (STEP 2)
    └─ fork_gate → [Send(Path A), Send(Path B)]

self_review (STEP 4A)
    ├─ PASS → ppt_toc
    ├─ retry_research → research_gather
    ├─ retry_strategy → strategy_generate
    ├─ retry_sections → proposal_write_next
    └─ force_review → review_proposal

convergence_gate (양쪽 경로 동기화)
    └─ mock_evaluation

mock_evaluation → eval_result_node (조건없음)

eval_result_node → project_closing (조건없음)
```

---

## 8. 설계-구현 차이 요약 및 이유

| 항목 | v3.6 설계 | v4.0 구현 | 이유 |
|------|----------|----------|------|
| **STEP 0 위치** | 그래프 내부 | API 외부 | 외부 API 호출, interrupt 불필요 |
| **workflow** | 선형 | A/B 병렬 | 3-Stream 실무 요구사항 |
| **PPT 생성** | 병렬 fan-out | 순차 3단계 | 품질 향상, 컨텍스트 유지 |
| **평가 단계** | 없음 | STEP 6~8 추가 | 수주율 예측, 최종 피드백 |
| **plan_price 그래프** | ✅ ALL_PLAN_NODES 포함 | ❌ 누락 (v4.0 수정됨) | 버그, 이제 수정됨 |

---

## 9. 구현 가이드

### 코드 위치
- **Graph 정의**: `app/graph/graph.py` (v4.0 완전 구현)
- **STEP 0 노드**: `app/graph/nodes/rfp_search.py`, `rfp_fetch.py` (그래프 미등록)
- **Path A 노드**: `app/graph/nodes/plan_nodes.py`, `proposal_nodes.py`, `ppt_nodes.py`
- **Path B 노드**: `app/graph/nodes/submission_nodes.py`, `bid_plan.py` (별도 모듈)
- **게이트**: `app/graph/nodes/gate_nodes.py` (fork_gate, convergence_gate, stream1_complete_hook)
- **API 엔드포인트**: `app/api/routes_proposal.py` (STEP 0 entry), `routes_workflow.py` (graph.start/resume)

### 주의사항
1. **STEP 0 → graph.start()**: rfp_content를 fetch한 후 initial_state로 전달
2. **Send() 암시적 동기화**: `convergence_gate`에서 양쪽 경로 완료 대기
3. **plan_price**: ALL_PLAN_NODES에 포함 (v4.0 수정) → plan_merge에서 자동 수렴

---

## 10. 테스트 체크리스트

- [ ] STEP 0 API 엔드포인트 (from-rfp, from-bid) 정상 동작
- [ ] graph.start() 호출 후 rfp_analyze 시작 확인
- [ ] fork_gate에서 Path A + B 동시 시작 확인 (Send 로그 확인)
- [ ] plan_price가 ALL_PLAN_NODES에 포함되어 병렬 실행 확인
- [ ] convergence_gate에서 양쪽 경로 완료까지 대기 확인
- [ ] ppt_toc → ppt_visual_brief → ppt_storyboard 순차 실행 확인
- [ ] mock_evaluation, eval_result, project_closing 순차 실행 확인

---

## References
- 갭 분석: `docs/03-analysis/features/proposal-agent-v1.analysis.md` (v4.0 갭 2건 기록)
- 메인 설계: `docs/archive/2026-03/proposal-agent-v1/design/_index.md` (v3.6 baseline)
