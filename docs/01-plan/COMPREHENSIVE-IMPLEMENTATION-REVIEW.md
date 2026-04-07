# 전체 Workflow (STEP 0~12) 구현 현황 & 계획 수립

> **검토일**: 2026-03-29
> **목표**: STEP 0부터 STEP 12까지 전체 워크플로우 검토 후 통합 구현 계획 수립
> **상태**: 계획 수립 단계

---

## 📊 STEP별 구현 현황 분석

### STEP 0: 제안 착수 (Intake)

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| 노드명 | ✅ 정의됨 | graph.py | `rfp_search`, `rfp_fetch` |
| 기능 | ✅ 구현됨 | `rfp_search.py`, `rfp_fetch.py` | G2B 공고 검색 + RFP 업로드 |
| State | ✅ 정의됨 | state.py | `search_query`, `picked_bid_no`, `bid_detail`, `rfp_raw` |
| 라우팅 | ✅ 구현됨 | edges.py | - |
| Review Node | ❌ 없음 | - | Human 검토 단계 없음 (자동 진행) |

**상태**: ✅ **COMPLETE** — G2B 검색, RFP 업로드까지 구현됨

---

### STEP 1: RFP 분석 & Research

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| **STEP 1-①: RFP 분석** |
| 노드명 | ✅ 정의됨 | graph.py | `rfp_analyze`, `review_rfp` |
| 기능 | ✅ 구현됨 | `rfp_analyze.py` | RFP 분석, Compliance Matrix 생성 |
| State | ✅ 정의됨 | state.py | `rfp_analysis`, `compliance_matrix` |
| 라우팅 | ✅ 구현됨 | edges.py | `route_after_rfp_review` |
| Human Review | ✅ 구현됨 | `review_node.py` | `review_rfp` |
| **STEP 1-②: Research** |
| 노드명 | ✅ 정의됨 | graph.py | `research_gather` |
| 기능 | ✅ 구현됨 | `research_gather.py` | RFP 기반 동적 리서치 (v3.2) |
| State | ✅ 정의됨 | state.py | `research_brief` |
| 라우팅 | ✅ 구현됨 | edges.py | (자동 진행 to go_no_go) |

**상태**: ✅ **COMPLETE** — RFP 분석 + 리서치까지 구현됨

---

### STEP 2: Go/No-Go 의사결정

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| 노드명 | ✅ 정의됨 | graph.py | `go_no_go`, `review_gng` |
| 기능 | ✅ 구현됨 | `go_no_go.py` | 4축 정량 스코어링 (v4.0) |
| State | ✅ 정의됨 | state.py | `go_no_go` (GoNoGoResult) |
| 라우팅 | ✅ 구현됨 | edges.py | `route_after_gng_review` (3방향) |
| Human Review | ✅ 구현됨 | `review_node.py` | `review_gng` |

**상태**: ✅ **COMPLETE** — 4축 점수 기반 Go/No-Go

---

### STEP 3: 제안 전략 수립

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| **STEP 3-①: 전략 수립** |
| 노드명 | ✅ 정의됨 | graph.py | `strategy_generate`, `review_strategy` |
| 기능 | ✅ 구현됨 | `strategy_generate.py` | 포지셔닝 매트릭스 + SWOT + 시나리오 |
| State | ✅ 정의됨 | state.py | `strategy` (Strategy) |
| 라우팅 | ✅ 구현됨 | edges.py | `route_after_strategy_review` (3방향) |
| Human Review | ✅ 구현됨 | `review_node.py` | `review_strategy` |

**상태**: ✅ **COMPLETE** — 전략 수립까지 구현됨

---

### STEP 4: 분기 (Fork)

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| 노드명 | ✅ 정의됨 | graph.py | `fork_gate` |
| 기능 | ✅ 구현됨 | `gate_nodes.py` | PATH A + PATH B 병렬 분기 |
| State | ✅ 정의됨 | state.py | - |
| 라우팅 | ✅ 구현됨 | edges.py | `fork_to_branches` |

**상태**: ✅ **COMPLETE**

---

## 🌳 PATH A: 제안서 작성 경로 (STEP 5A~8A)

### STEP 5A: 제안 계획 수립

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| 노드명 | ✅ 정의됨 | graph.py | `plan_fan_out_gate`, `plan_team`, `plan_assign`, `plan_schedule`, `plan_story`, `plan_price`, `plan_merge`, `review_plan` |
| 기능 | ✅ 구현됨 | `plan_nodes.py` | 5개 병렬 + merge (v3.5 순차) |
| State | ✅ 정의됨 | state.py | `plan` (ProposalPlan) |
| 라우팅 | ✅ 구현됨 | edges.py | `route_after_plan_review` (4방향) |
| Human Review | ✅ 구현됨 | `review_node.py` | `review_plan` |

**상태**: ✅ **COMPLETE** — 목차, 팀, 일정, 가격 계획 + 스토리라인 설계

---

### STEP 6A: 제안서 작성 & 검토

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| **6A-①: 제안서 작성** |
| 노드명 | ✅ 정의됨 | graph.py | `proposal_start_gate`, `proposal_write_next`, `review_section` |
| 기능 | ✅ 구현됨 | `proposal_nodes.py` | 섹션별 순차 작성 (v3.5) |
| State | ✅ 정의됨 | state.py | `proposal_sections` (list[ProposalSection]) |
| 라우팅 | ✅ 구현됨 | edges.py | `route_after_section_review` (3방향) |
| Human Review | ✅ 구현됨 | `review_node.py` | `review_section` (섹션별) |
| **6A-②: 자가진단** |
| 노드명 | ✅ 정의됨 | graph.py | `self_review`, `review_proposal` |
| 기능 | ✅ 구현됨 | `proposal_nodes.py` | 4축 100점 자가진단 (v3.3) |
| State | ✅ 정의됨 | state.py | `evaluation_simulation` |
| 라우팅 | ✅ 구현됨 | edges.py | `route_after_self_review` (5방향), `route_after_proposal_review` (2방향) |
| Human Review | ✅ 구현됨 | `review_node.py` | `review_proposal` |

**상태**: ✅ **COMPLETE** — 섹션별 순차 작성 + 자가진단

---

### STEP 7A: PPT 작성

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| **7A-①: 발표 전략** |
| 노드명 | ✅ 정의됨 | graph.py | `presentation_strategy` |
| 기능 | ✅ 구현됨 | `ppt_nodes.py` | 평가 방식별 조건부 (서류심사 시 스킵) |
| State | ✅ 정의됨 | state.py | `presentation_strategy` |
| 라우팅 | ✅ 구현됨 | edges.py | `route_after_presentation_strategy` (2방향) |
| **7A-②: PPT 작성** |
| 노드명 | ✅ 정의됨 | graph.py | `ppt_toc`, `ppt_visual_brief`, `ppt_storyboard`, `review_ppt` |
| 기능 | ✅ 구현됨 | `ppt_nodes.py` | 3단계 파이프라인 (TOC, Visual, Storyboard) |
| State | ✅ 정의됨 | state.py | `ppt_slides`, `ppt_storyboard` |
| 라우팅 | ✅ 구현됨 | edges.py | `route_after_ppt_review` (2방향) |
| Human Review | ✅ 구현됨 | `review_node.py` | `review_ppt` |

**상태**: ✅ **COMPLETE** — PPT 작성까지 구현됨

---

### STEP 8A: 제안서 통합 & 모의평가 ⭐ **신규 설계**

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| **8A-①: 고객 요구분석** |
| 노드명 | ❌ 미구현 | - | `proposal_customer_analysis` (NEW) |
| 기능 | 📋 설계됨 | STEP-8A-implementation-guide.md | RFP → 고객 pain points, success criteria 추출 |
| State | ❌ 미정의 | - | `customer_context` (NEW) |
| 라우팅 | 📋 설계됨 | - | (자동 진행) |
| **8A-②: 섹션별 검토** |
| 노드명 | ❌ 수정 필요 | - | `proposal_write_next` (강화) |
| 기능 | 📋 설계됨 | STEP-8A-customer-centric-proposal-review.md | 고객 관점 프롬프트, AI 검증, Human Review |
| State | ❌ 미정의 | - | `section_validation_results` (NEW) |
| 라우팅 | 📋 설계됨 | - | `route_after_section_review` (4방향) |
| Human Review | 📋 설계됨 | - | 섹션별 AI 자체 검증 + Human 피드백 |
| **8A-③: 통합 검증** |
| 노드명 | ❌ 미구현 | - | `proposal_sections_consolidation` (NEW) |
| 기능 | 📋 설계됨 | STEP-8A-customer-centric-proposal-review.md | 전체 섹션 일관성, 고객니즈 커버, 평가항목 충족도 |
| State | ❌ 미정의 | - | `sections_consolidation_result` (NEW) |
| 라우팅 | 📋 설계됨 | - | `route_after_section_consolidation` (3방향) |
| **8A-④: 모의평가** |
| 노드명 | ✅ 구현됨 | graph.py | `mock_evaluation`, `review_mock_eval` |
| 기능 | ✅ 구현됨 (v6.0) | `evaluation_nodes.py` | 6명 평가위원 (산학연 2명씩) |
| State | ✅ 정의됨 | state.py | `mock_evaluation_result` |
| **8A-⑤: 평가의견 분석** |
| 노드명 | ❌ 미구현 | - | `mock_evaluation_analysis` (NEW) |
| 기능 | 📋 설계됨 | mock-evaluation-human-review-feedback.md | 6명 평가의견 정렬, 우려사항 추출 |
| State | ❌ 미정의 | - | `mock_evaluation_analysis` (NEW) |
| 라우팅 | 📋 설계됨 | - | (자동 진행) |
| **8A-⑥: 평가 검토 & 피드백** |
| 노드명 | 📋 설계됨 | - | `review_mock_eval` (강화) |
| 기능 | 📋 설계됨 | mock-evaluation-human-review-feedback.md | Executive Summary, 항목별 분석, 평가위원별 관점 |
| 라우팅 | 📋 설계됨 | - | `route_after_mock_eval_review` (4방향) |
| Human Review | 📋 설계됨 | - | 평가의견 기반 피드백 (Approved/Rework/Re-evaluate) |
| **8A-⑦: 피드백 처리** |
| 노드명 | ❌ 미구현 | - | `process_mock_eval_feedback` (NEW) |
| 기능 | 📋 설계됨 | mock-evaluation-human-review-feedback.md | 피드백 → 수정 지시 변환 |
| State | ❌ 미정의 | - | `mock_eval_feedback`, `rework_instructions` (NEW) |
| 라우팅 | 📋 설계됨 | - | 3방향 (approved/rework/re_evaluate) |

**상태**: ⭐ **NEW DESIGN + PARTIAL IMPL**
- ✅ mock_evaluation (v6.0) 구현됨
- ❌ STEP 8A (고객 관점 섹션 검토) 미구현
- ❌ 평가의견 분석 & feedback 루프 미구현

---

## 🌳 PATH B: 입찰 & 제출서류 경로 (STEP 5B~8B)

### STEP 5B: 제출서류 계획

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| 노드명 | ✅ 정의됨 | graph.py | `submission_plan`, `review_submission_plan` |
| 기능 | ✅ 구현됨 | `submission_nodes.py` | 제출서류 계획 (3B) |
| State | ✅ 정의됨 | state.py | `submission_plan` |
| 라우팅 | ✅ 구현됨 | edges.py | `route_after_submission_plan_review` (2방향) |
| Human Review | ✅ 구현됨 | `review_node.py` | `review_submission_plan` |

**상태**: ✅ **COMPLETE**

---

### STEP 6B: 입찰가 결정

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| **6B-①: 입찰가 계획** |
| 노드명 | ✅ 정의됨 | graph.py | `bid_plan`, `review_bid_plan` |
| 기능 | ✅ 구현됨 | `bid_plan.py` (v3.8) | 시나리오 분석, 가격 추천 |
| State | ✅ 정의됨 | state.py | `bid_plan` (BidPlanResult) |
| 라우팅 | ✅ 구현됨 | edges.py | `route_after_bid_plan_review` (3방향) |
| Human Review | ✅ 구현됨 | `review_node.py` | `review_bid_plan` |
| **6B-②: 산출내역서** |
| 노드명 | ✅ 정의됨 | graph.py | `cost_sheet_generate`, `review_cost_sheet` |
| 기능 | ✅ 구현됨 | `submission_nodes.py` | 산출내역서 생성 (5B) |
| State | ✅ 정의됨 | state.py | `cost_sheet` |
| 라우팅 | ✅ 구현됨 | edges.py | `route_after_cost_sheet_review` (2방향) |
| Human Review | ✅ 구현됨 | `review_node.py` | `review_cost_sheet` |

**상태**: ✅ **COMPLETE**

---

### STEP 7B: 제출서류 확인

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| 노드명 | ✅ 정의됨 | graph.py | `submission_checklist`, `review_submission` |
| 기능 | ✅ 구현됨 | `submission_nodes.py` | 제출서류 체크리스트 (6B) |
| State | ✅ 정의됨 | state.py | `submission_checklist_result` |
| 라우팅 | ✅ 구현됨 | edges.py | `route_after_submission_checklist_review` (2방향) |
| Human Review | ✅ 구현됨 | `review_node.py` | `review_submission` |

**상태**: ✅ **COMPLETE**

---

## 🔗 TAIL: 통합 & 종료 (STEP 9~12)

### STEP 9: A/B 수렴 (Convergence)

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| 노드명 | ✅ 정의됨 | graph.py | `convergence_gate` |
| 기능 | ✅ 구현됨 | `gate_nodes.py` | PATH A + B 병합 |
| State | ✅ 정의됨 | state.py | - |
| 라우팅 | ✅ 구현됨 | edges.py | (자동 진행) |

**상태**: ✅ **COMPLETE**

---

### STEP 10: 평가 결과 등록

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| 노드명 | ✅ 정의됨 | graph.py | `eval_result`, `review_eval_result` |
| 기능 | ✅ 구현됨 | `evaluation_nodes.py` | 모의평가 결과 기반 기본값 |
| State | ✅ 정의됨 | state.py | `eval_result` |
| 라우팅 | ✅ 구현됨 | edges.py | `route_after_eval_result_review` (2방향) |
| Human Review | ✅ 구현됨 | `review_node.py` | `review_eval_result` |

**상태**: ✅ **COMPLETE**

---

### STEP 11: Closing (종료)

| 항목 | 상태 | 파일 | 설명 |
|-----|-----|-----|-----|
| 노드명 | ✅ 정의됨 | graph.py | `project_closing` |
| 기능 | ✅ 구현됨 | `evaluation_nodes.py` | KB 업데이트, 아카이브 |
| State | ✅ 정의됨 | state.py | `project_closing_result` |
| 라우팅 | ✅ 구현됨 | edges.py | END |

**상태**: ✅ **COMPLETE**

---

## 📋 구현 현황 요약

```
STEP 0:     ✅ 완료 (제안 착수)
STEP 1:     ✅ 완료 (RFP 분석 + Research)
STEP 2:     ✅ 완료 (Go/No-Go)
STEP 3:     ✅ 완료 (전략 수립)
STEP 4:     ✅ 완료 (분기)

PATH A:
STEP 5A:    ✅ 완료 (제안 계획)
STEP 6A:    ✅ 완료 (제안서 작성 + 자가진단)
STEP 7A:    ✅ 완료 (PPT)
STEP 8A:    ⭐ NEW (고객 관점 섹션 검토 + 모의평가)
            - ✅ mock_evaluation (v6.0)
            - 📋 설계: 고객분석, 섹션검토, 통합검증, 평가의견분석, feedback
            - ❌ 미구현: STEP 8A 전체 구현

PATH B:
STEP 5B:    ✅ 완료 (제출서류 계획)
STEP 6B:    ✅ 완료 (입찰가 + 산출내역서 + 확인)
STEP 7B:    ✅ 완료 (제출서류 확인)

TAIL:
STEP 9:     ✅ 완료 (수렴)
STEP 10:    ✅ 완료 (평가 결과)
STEP 11:    ✅ 완료 (Closing)

총 STEP: 12개
✅ 완료: 10개 (STEP 0~7)
⭐ 신규/강화: 2개 (STEP 8A)
```

---

## 🚀 STEP 8A: 신규 설계 상세

### STEP 8A의 7가지 서브단계

```
STEP 8A-①: proposal_customer_analysis
  └─ 고객 요구사항 분석 (1회)
     입력: RFP, Strategy
     출력: customer_context (pain points, success criteria, 니즈 매핑)

STEP 8A-②~④: proposal_write_customer_centric + validation
  └─ 섹션별 작성 (반복: dynamic_sections 수만큼)
     • proposal_write_next (강화): 고객 관점 프롬프트
     • validate_section_customer_focus: AI 자체 검증
     • review_section (강화): Human Review + 피드백

STEP 8A-⑤: proposal_sections_consolidation
  └─ 모든 섹션 완성 후 통합 검증
     입력: 모든 섹션
     출력: 고객니즈 커버, 평가항목 충족도, 개선 항목

STEP 8A-⑥: mock_evaluation_analysis
  └─ 평가의견 정렬 (자동, 1회)
     입력: mock_evaluation_result
     출력: 항목별/평가위원별/공통우려사항 정렬

STEP 8A-⑦: review_mock_eval (강화) → process_mock_eval_feedback
  └─ 평가의견 검토 + Human 피드백 수집
     입력: mock_evaluation_analysis
     출력: feedback (approved/rework/re_evaluate)
```

### 라우팅 흐름

```
proposal_customer_analysis
  ↓ (자동)
proposal_write_next (섹션 1)
  ↓
validate_section_customer_focus (AI 자체 검증)
  ↓
review_section (Human Review)
  ├─ next_section → proposal_write_next (섹션 2)
  ├─ rework_customer_focus → 고객 분석 재검토
  └─ rewrite → proposal_write_next (현재 섹션 재작성)

... (모든 섹션 반복) ...

proposal_sections_consolidation (모든 섹션 완성 후)
  ├─ ready → mock_evaluation
  ├─ needs_section_improvement → 해당 섹션 재작성
  └─ restart → proposal_customer_analysis부터 재시작

mock_evaluation (6명 평가)
  ↓ (자동)
mock_evaluation_analysis (평가의견 정렬)
  ↓ (자동)
review_mock_eval (Human Review)
  ├─ approved → convergence_gate (STEP 9)
  ├─ rework → proposal_write_next (지정 섹션 재작성)
  ├─ rework_strategy → strategy_generate (전략 재검토)
  └─ re_evaluate → mock_evaluation (재평가)
```

---

## 🔧 필요한 구현 작업

### NEW 노드 (신규 생성)

1. **proposal_customer_analysis.py** (NEW)
   - RFP → 고객 pain points, success criteria, 니즈 매핑

2. **proposal_customer_centric_section.py** (NEW)
   - _analyze_section_requirement
   - get_customer_centric_section_prompt
   - (proposal_write_next 강화)

3. **proposal_section_validator.py** (NEW)
   - validate_section_customer_focus
   - _check_customer_need_coverage
   - _check_specificity
   - _check_differentiation
   - _generate_improvement_suggestions

4. **proposal_sections_consolidation.py** (NEW)
   - validate_all_sections_integration
   - _check_all_customer_needs_covered
   - _check_all_eval_items_covered
   - _check_sections_coherence

5. **mock_evaluation_analysis.py** (NEW)
   - mock_evaluation_analysis (분석 노드)
   - 평가의견 정렬, 우려사항 추출, 우선순위 도출

6. **mock_evaluation_feedback_processor.py** (NEW)
   - process_mock_eval_feedback (피드백 처리)
   - _generate_rework_instructions
   - _map_eval_items_to_sections

### 기존 파일 수정

1. **proposal_nodes.py** (MODIFY)
   - proposal_write_next 함수 강화
   - 고객 관점 프롬프트 추가
   - _analyze_section_requirement 함수 추가

2. **evaluation_nodes.py** (MODIFY)
   - review_mock_eval 노드 강화 (이미 기본은 있음)

3. **graph.py** (MODIFY)
   - 6개 NEW 노드 등록
   - 라우팅 엣지 추가

4. **edges.py** (MODIFY)
   - route_after_section_review 강화 (4방향)
   - route_after_section_consolidation (NEW, 3방향)
   - route_after_mock_eval_review 강화 (4방향)

5. **state.py** (MODIFY)
   - customer_context
   - section_validation_results
   - sections_consolidation_result
   - mock_evaluation_analysis
   - mock_eval_feedback
   - rework_instructions

### API 라우트 (필요시)

1. **routes_proposal_feedback.py** (NEW, 선택사항)
   - Human의 섹션별 피드백 수집
   - Human의 모의평가 피드백 수집

---

## 📊 의존성 분석

### STEP 8A의 의존성

```
✅ prerequisite (완료된 STEP)
  ├─ STEP 0~7: RFP 분석, 전략, PPT 모두 완료
  ├─ STEP 6A-자가진단: evaluation_simulation 필요
  └─ STEP 7A-PPT: ppt_slides 필요

⭐ 신규 의존성
  ├─ customer_context (STEP 8A-①에서 생성)
  ├─ section_validation_results (STEP 8A-②에서 생성)
  ├─ sections_consolidation_result (STEP 8A-③에서 생성)
  ├─ mock_evaluation_result (이미 있음, v6.0)
  ├─ mock_evaluation_analysis (STEP 8A-⑥에서 생성)
  └─ mock_eval_feedback (Human 입력)

❌ 순환 의존성
  - STEP 8A-②(섹션 재작성) → STEP 8A-③(통합 검증) → STEP 8A-②
    (이는 "자동" 루프, OK)
```

### 병렬 구현 가능성

```
🟢 병렬 가능
  - proposal_customer_analysis (단독)
  - proposal_section_validator (단독)
  - proposal_sections_consolidation (단독)
  - mock_evaluation_analysis (mock_evaluation 완료 후)
  - mock_evaluation_feedback_processor (단독)

🟡 순차 필요
  - proposal_write_customer_centric (customer_context 필요)
  - review_section (validation 결과 필요)
```

---

## ⏱️ 구현 기간 추정

### Phase 1: Core Nodes (3일)

**Day 1: Customer Analysis + Section Validator**
- proposal_customer_analysis (AI 프롬프트)
- proposal_section_validator (5가지 검증)
- State 필드 추가
- 테스트

**Day 2: Section Consolidation + Analysis**
- proposal_sections_consolidation (통합 검증)
- mock_evaluation_analysis (평가의견 정렬)
- 테스트

**Day 3: Feedback Processing + Integration**
- mock_evaluation_feedback_processor (피드백 처리)
- proposal_write_next 강화
- graph.py 노드 등록
- edges.py 라우팅 추가

### Phase 2: Testing & Refinement (2일)

**Day 4: Unit Testing**
- 각 노드별 테스트
- AI 프롬프트 검증

**Day 5: Integration Testing**
- End-to-End 전체 흐름 테스트
- 라우팅 경로 검증
- 성능 최적화

### Phase 3: Frontend (Optional, 3일)

**Day 6-8: UI 개발**
- Human Review Panel 구현
- Feedback 입력 폼
- 평가의견 시각화

---

## ✅ 최종 검증 체크리스트

### 구현 전 확인사항

- [ ] STEP 0~7 구현 상태 재확인
- [ ] STEP 8A의 7가지 서브단계 정확히 이해
- [ ] 각 노드의 입출력 명확히 정의
- [ ] State 필드 충돌 검토
- [ ] 라우팅 경로의 순환 의존성 검토
- [ ] AI 프롬프트 템플릿 작성 완료
- [ ] 테스트 케이스 정의

### 구현 중 확인사항

- [ ] 각 노드별 단위 테스트 통과
- [ ] State 필드 정확히 저장/로드
- [ ] 라우팅 로직 모든 경로 검증
- [ ] AI 호출 폴백 처리
- [ ] Human interrupt 정상 동작
- [ ] 토큰 사용량 모니터링

### 구현 후 확인사항

- [ ] End-to-End 전체 흐름 테스트
- [ ] 각 라우팅 경로 (approved/rework/re_evaluate) 검증
- [ ] 섹션 재작성 루프 정상 동작
- [ ] 모의평가 재실행 정상 동작
- [ ] Performance 최적화 완료
- [ ] 에러 처리 검증

---

**검토 완료**: ✅ 2026-03-29
**다음 단계**: 최종 검토 회의 → 구현 착수 승인
**예상 구현**: 5일 (Phase 1~2) + 3일 (Frontend, 선택사항)
