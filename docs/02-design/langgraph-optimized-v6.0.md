# LangGraph 최적화 설계 v6.0
## (40개 노드 → 16개 핵심 노드로 단순화)

> **설계일**: 2026-03-29
> **기준**: 사용자 제시 워크플로우 구조
> **목표**: 단순하고 명확한 LangGraph
> **노드 감소**: 40개 → 16개 (60% 감소)

---

## 🎯 개선 목표

### 현재 문제
```
❌ 40개 노드 (너무 많음)
  - 각 노드 책임 불명확
  - 라우팅 복잡 (15개 라우팅 함수)
  - Review 게이트가 16개로 산재
  - 병렬 노드 관리 어려움

❌ 복잡한 병렬 처리
  - plan_team, plan_assign, plan_schedule, plan_story, plan_price
  - 병합 로직 복잡
  - 상태 동기화 어려움

❌ 불명확한 사용자 상호작용
  - interrupt가 16개 노드에 분산
  - 어디서 사용자 입력이 필요한지 명확하지 않음
```

### 개선 원칙
```
✅ 큰 단위로 묶기 (Step 단위)
   - 여러 AI 작업 → 1개 노드로
   - 관련 Review → 1개 Review 노드로

✅ 사용자 상호작용 명확화
   - Review = interrupt 발생 지점
   - 데이터 입력 = 명시적 필드

✅ 병렬 처리 단순화
   - 병렬 노드 수 최소화
   - 병렬 내 협력 고려

✅ 라우팅 로직 단순화
   - 조건부 엣지 최소화
   - 각 review 후 명확한 분기
```

---

## 🗺️ 최적화된 워크플로우 (16개 노드)

```
START
  │
  ▼
┌──────────────────────────────────────────────────┐
│  STEP 0: 제안 착수 (1개 노드)                    │
├──────────────────────────────────────────────────┤
│                                                  │
│  intake_proposal                                 │
│  ├─ 프로젝트 기본정보 수집                        │
│  ├─ RFP 업로드 / G2B 공고 링크                   │
│  └─ output: rfp_content, team_info              │
│
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│  STEP 1: RFP 분석 + Research (1개 노드)          │
├──────────────────────────────────────────────────┤
│                                                  │
│  analyze_and_research                            │
│  ├─ RFP 분석 (요구사항, 평가기준, 일정)           │
│  ├─ 동적 리서치 (RFP 기반 키워드)                │
│  ├─ KB 조회 (유사실적, 경쟁사, 역량)             │
│  ├─ 시장 조사 (G2B 낙찰정보, 경쟁강도)           │
│  └─ output: rfp_analysis, research_brief        │
│
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│  STEP 2: 제안 여부 결정 (Human Review #1)        │
├──────────────────────────────────────────────────┤
│                                                  │
│  review_go_no_go                                 │
│  ├─ interrupt: 4축 정량 스코어 + 분석            │
│  ├─ decision: 제안 진행 / No-Go 중단             │
│  ├─ (No-Go → END)                              │
│  └─ output: go_no_go_result, decision_gate      │
│
└──────────────┬───────────────────────────────────┘
               │ (제안 진행)
               ▼
┌──────────────────────────────────────────────────┐
│  STEP 3: 제안 전략 수립 (1개 노드)                │
├──────────────────────────────────────────────────┤
│                                                  │
│  formulate_strategy                              │
│  ├─ 포지셔닝 (defensive/offensive/adjacent)     │
│  ├─ Win Theme & Ghost Theme                      │
│  ├─ 전략 2안 (가격, 기술, 위험 분석)             │
│  └─ output: strategy, positioning_options       │
│
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│  STEP 4: 전략 검토 (Human Review #2)             │
├──────────────────────────────────────────────────┤
│                                                  │
│  review_strategy                                 │
│  ├─ interrupt: 포지셔닝 + 2안 선택                │
│  ├─ (가능) 포지셔닝 변경 → formulate_strategy    │
│  ├─ (가능) 추가 리서치 → analyze_and_research   │
│  └─ output: approved_strategy, selected_alt     │
│
└──────────────┬───────────────────────────────────┘
               │ (전략 승인)
               ▼
        ┌──────┴──────┐
        │  FORK       │ (A/B 병렬 시작)
        └──────┬──────┘
               │
        ┌──────┴──────────┐
        │                 │
        ▼                 ▼
   [PATH A]          [PATH B]
제안서 경로         입찰 경로

═══════════════════════════════════════════════════════════

PATH A: 제안서 작성 경로 (STEP 5A~8A)

        │
        ▼
   ┌─────────────────────────────────────┐
   │ STEP 5A: 제안 계획 수립 (1개 노드)    │
   ├─────────────────────────────────────┤
   │                                     │
   │ plan_proposal_writing               │
   │ ├─ 목차 구성 (RFP 평가기준 기반)     │
   │ ├─ 스토리라인 설계                   │
   │ │ ├─ 전체 내러티브                  │
   │ │ ├─ 섹션별 주요 메시지              │
   │ │ ├─ 근거 데이터 계획                │
   │ │ └─ Win Theme 연결                  │
   │ ├─ 섹션별 담당자 배치                │
   │ └─ output: table_of_contents,       │
   │           storylines, assignments   │
   │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 6A: 계획 검토 (Human Review #3) │
   ├─────────────────────────────────────┤
   │                                     │
   │ review_proposal_plan                │
   │ ├─ interrupt: 목차 + 스토리라인      │
   │ ├─ (가능) 목차 순서 변경              │
   │ ├─ (가능) 스토리라인 수정             │
   │ ├─ (가능) 담당자 재배치               │
   │ └─ output: approved_plan,           │
   │           final_toc, final_storyline│
   │
   └────────┬────────────────────────────┘
            │ (계획 승인)
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 7A: 목차별 제안서 작성 (1개 노드)│
   │         (섹션 루프)                  │
   ├─────────────────────────────────────┤
   │                                     │
   │ write_proposal_sections             │
   │ ├─ for each section in toc:         │
   │ │  ├─ 유형 판별 (기술/가격/관리)     │
   │ │  ├─ 해당 스토리라인 주입            │
   │ │  ├─ KB 참조 (유사실적, 기술)        │
   │ │  ├─ AI 작성 (섹션별 프롬프트)       │
   │ │  ├─ self-check (완성도/일관성)     │
   │ │  └─ 다음 섹션으로 (context 누적)   │
   │ └─ output: proposal_draft           │
   │           (모든 섹션)                │
   │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 8A: 섹션별 검토 (Human Review #4)│
   │         (섹션 루프)                  │
   ├─────────────────────────────────────┤
   │                                     │
   │ review_proposal_sections            │
   │ ├─ for each section:                │
   │ │  ├─ interrupt: 섹션 콘텐츠         │
   │ │  ├─ feedback: AI 인라인 수정 제안   │
   │ │  ├─ (가능) 재작성                  │
   │ │  ├─ (가능) 다음 섹션으로            │
   │ │  └─ (가능) 자가진단으로 (모두 완료) │
   │ └─ output: revised_sections         │
   │
   └────────┬────────────────────────────┘
            │ (모든 섹션 완료)
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 9A: 제안서 통합 & 최종 검토      │
   │         (Human Review #5)            │
   ├─────────────────────────────────────┤
   │                                     │
   │ finalize_proposal                   │
   │ ├─ DOCX/HWPX 생성                   │
   │ ├─ 자가진단 (4축 평가)                │
   │ │  ├─ 완성도 (기술/형식)              │
   │ │  ├─ 차별성 (경쟁우위)               │
   │ │  ├─ 설득력 (메시지 일관성)          │
   │ │  └─ 적합성 (요구사항 충족)          │
   │ ├─ 점수 < 70점 → 부분 재작성 제안    │
   │ ├─ interrupt (필요시): 재검토 피드백 │
   │ └─ output: final_proposal_docx,     │
   │           self_assessment_score     │
   │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 10A: PPT 자료 작성 (1개 노드)    │
   ├─────────────────────────────────────┤
   │                                     │
   │ generate_presentation               │
   │ ├─ 평가방식 확인 (발표예정/서류심사)  │
   │ ├─ (발표예정인 경우만)               │
   │ ├─ PPT 생성                         │
   │ │ ├─ 목차                           │
   │ │ ├─ 시각화 (다이어그램, 표)         │
   │ │ ├─ Key Message 스토리보드          │
   │ │ ├─ 질의응답 Q&A                   │
   │ │ └─ 리허설 타이밍                   │
   │ ├─ (서류심사인 경우) 모의평가 로직  │
   │ └─ output: ppt_slides, qa_template │
   │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 11A: PPT 검토 (Human Review #6) │
   ├─────────────────────────────────────┤
   │                                     │
   │ review_presentation                 │
   │ ├─ interrupt: PPT 슬라이드           │
   │ ├─ (가능) 슬라이드 수정/추가          │
   │ ├─ (가능) 타이밍 조정                │
   │ ├─ (가능) Q&A 추가                  │
   │ └─ output: approved_ppt             │
   │
   └────────┬────────────────────────────┘
            │ (PPT 완료)
            │
            └──→ [CONVERGENCE]

═══════════════════════════════════════════════════════════

PATH B: 입찰 경로 (STEP 5B~8B)

        │
        ▼
   ┌─────────────────────────────────────┐
   │ STEP 5B: 입찰 준비 계획 (1개 노드)    │
   ├─────────────────────────────────────┤
   │                                     │
   │ plan_bidding_process                │
   │ ├─ 제출서류 목록 (RFP 기반)          │
   │ ├─ 각 서류 담당자 배치                │
   │ ├─ 일정 계획 (마감일 역산)            │
   │ ├─ 행정 체크리스트 구성               │
   │ └─ output: submission_docs_list,    │
   │           bidding_schedule,         │
   │           checklist_template        │
   │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 6B: 입찰가 결정 (1개 노드)       │
   ├─────────────────────────────────────┤
   │                                     │
   │ recommend_and_set_bid_price         │
   │ ├─ 원가 계산 (노임단가 + 경비)        │
   │ ├─ 시장 조사 (유사과제 낙찰율)        │
   │ ├─ 수주확률 추정 (가격대별)           │
   │ ├─ 2~3안 제시 (보수/적정/공격)       │
   │ ├─ interrupt (Human Decision)       │
   │ │  ├─ 입찰가 선택                   │
   │ │  └─ 할인율 승인                   │
   │ └─ output: approved_bid_price,      │
   │           cost_breakdown           │
   │
   └────────┬────────────────────────────┘
            │ (입찰가 결정)
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 7B: 산출내역서 작성 (1개 노드)   │
   ├─────────────────────────────────────┤
   │                                     │
   │ generate_cost_sheets                │
   │ ├─ 노임단가 기준 확인                 │
   │ ├─ 용역 / 기술 / 경비 항목화           │
   │ ├─ 단가 × 수량 계산                  │
   │ ├─ 양식별 내역서 생성                 │
   │ │ ├─ Excel 샘플                    │
   │ │ ├─ HWPX 양식                     │
   │ │ └─ 검증 (합계 일치 확인)           │
   │ └─ output: cost_sheets (HWPX/Excel)│
   │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 8B: 입찰 최종 체크 (Human #7)   │
   ├─────────────────────────────────────┤
   │                                     │
   │ review_bidding_submission           │
   │ ├─ interrupt: 체크리스트             │
   │ │  ├─ 필수서류 완성도                 │
   │ │  ├─ 양식 준수 여부                  │
   │ │  ├─ 입찰가 최종확인                 │
   │ │  └─ 제출일시 확인                  │
   │ ├─ (가능) 문서 수정 요청              │
   │ ├─ (최종 OK) 제출 준비              │
   │ └─ output: submission_approved,     │
   │           submission_timestamp     │
   │
   └────────┬────────────────────────────┘
            │ (제출 준비 완료)
            │
            └──→ [CONVERGENCE]

═══════════════════════════════════════════════════════════

CONVERGENCE: A + B 경로 합류

        │
        ▼
   ┌─────────────────────────────────────┐
   │ convergence_gate (대기 노드)         │
   ├─────────────────────────────────────┤
   │                                     │
   │ ├─ PATH A 완료 대기 (PPT 또는 모의평가)
   │ ├─ PATH B 완료 대기 (제출 준비)      │
   │ └─ 모두 완료 → 다음 노드로           │
   │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 9: 발표 Q&A 준비 (1개 노드)     │
   ├─────────────────────────────────────┤
   │                                     │
   │ prepare_qa_and_presentation         │
   │ ├─ 평가위원 프로필 분석              │
   │ ├─ 예상 질문 도출                    │
   │ ├─ 답변 초안 작성 (AI)               │
   │ ├─ 리허설 Q&A 세션                  │
   │ ├─ 발표 연습 타이밍                  │
   │ └─ output: qa_scenarios,            │
   │           rehearsal_notes           │
   │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 10: 발표 준비 검토 (Human #8)   │
   ├─────────────────────────────────────┤
   │                                     │
   │ review_presentation_readiness       │
   │ ├─ interrupt: Q&A 시나리오           │
   │ ├─ (가능) Q&A 추가/수정              │
   │ ├─ (가능) 리허설 일정 조정            │
   │ ├─ (가능) 발표팀 재구성              │
   │ └─ output: final_qa_package,        │
   │           presentation_approval    │
   │
   └────────┬────────────────────────────┘
            │ (발표 준비 완료)
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 11: 평가 결과 기록 (1개 노드)    │
   ├─────────────────────────────────────┤
   │                                     │
   │ record_evaluation_result            │
   │ ├─ 평가점수 입력 (Human)             │
   │ ├─ 낙찰 여부 (당/당락)               │
   │ ├─ 낙찰가 입력                       │
   │ ├─ 평가위원 피드백 (선택)            │
   │ ├─ 자체 평가 점수 vs 실제 점수 비교   │
   │ ├─ 교훈 도출 (AI 분석)               │
   │ └─ output: evaluation_record,       │
   │           lessons_learned,         │
   │           win_analysis             │
   │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 12: 학습 기록 & 종료 (1개 노드) │
   ├─────────────────────────────────────┤
   │                                     │
   │ finalize_and_archive                │
   │ ├─ KB 업데이트                      │
   │ │ ├─ (당) 수주실적 추가               │
   │ │ ├─ (당) 노하우 기록                │
   │ │ ├─ (당) 고객사 선호도 기록          │
   │ │ ├─ (당) 기술 스택 업데이트          │
   │ │ └─ (패) 경쟁사 분석 업데이트        │
   │ ├─ 제안 아카이브                      │
   │ ├─ 타임라인 기록 (생명주기)           │
   │ └─ output: archive_summary,         │
   │           kb_updates,              │
   │           project_closed           │
   │
   └────────┬────────────────────────────┘
            │
            ▼
           END

```

---

## 📋 노드 상세 정의 (16개)

### STEP 0: intake_proposal
```python
async def intake_proposal(state: ProposalState) -> dict:
    """제안 착수 - 기본 정보 수집"""
    return {
        "project_name": state.get("project_name"),
        "client_name": state.get("client_name"),
        "team_id": state.get("team_id"),
        "rfp_content": state.get("rfp_content"),  # 업로드된 RFP
        "deadline": state.get("deadline"),
        "current_phase": "intake",
    }
```

### STEP 1: analyze_and_research (1개 노드 = 기존 rfp_analyze + research_gather)
```python
async def analyze_and_research(state: ProposalState) -> dict:
    """RFP 분석 + 동적 리서치 (AI 작업만)"""
    # 1. RFP 분석 (기존 rfp_analyze)
    rfp_analysis = await _analyze_rfp(state)

    # 2. 동적 리서치 (기존 research_gather)
    research_brief = await _gather_research(state, rfp_analysis)

    # 3. KB 조회 (역량, 유사실적, 경쟁사)
    kb_refs = await _query_kb(state, rfp_analysis)

    # 4. 시장 조사 (G2B 낙찰정보)
    market_data = await _research_market(state, rfp_analysis)

    return {
        "rfp_analysis": rfp_analysis,
        "research_brief": research_brief,
        "kb_references": kb_refs,
        "market_data": market_data,
        "current_phase": "analyze_and_research",
    }
```

### STEP 2: review_go_no_go (Human Review)
```python
def review_go_no_go():
    """제안 여부 결정 (Go/No-Go)"""
    def _review(state: ProposalState) -> dict:
        # 4축 정량 스코어 계산
        rfp = state.get("rfp_analysis")
        score_breakdown = await _score_feasibility(state, rfp)

        interrupt_data = {
            "step": "go_no_go",
            "scores": score_breakdown,
            "research": state.get("research_brief"),
            "message": "이 제안에 참여할까요?",
            "decision_options": ["go", "no_go"],
        }

        human_input = interrupt(interrupt_data)

        if human_input.get("decision") == "no_go":
            return {
                "go_no_go_decision": "no_go",
                "current_phase": "end",
            }

        return {
            "go_no_go_decision": "go",
            "go_no_go_score": score_breakdown,
        }
    return _review
```

### STEP 3: formulate_strategy
```python
async def formulate_strategy(state: ProposalState) -> dict:
    """제안 전략 수립 (포지셔닝 + 2안)"""
    rfp = state.get("rfp_analysis")
    research = state.get("research_brief")

    # 포지셔닝 (defensive/offensive/adjacent)
    positioning = await _determine_positioning(state, rfp, research)

    # 전략 2안 (각각 win/ghost theme, 가격, 위험 분석)
    alternatives = await _generate_strategy_alternatives(state, rfp, positioning)

    return {
        "strategy": {
            "positioning": positioning,
            "alternatives": alternatives,  # 2~3안
        },
        "current_phase": "formulate_strategy",
    }
```

### STEP 4: review_strategy (Human Review)
```python
def review_strategy():
    """전략 검토 (포지셔닝 확인, 대안 선택)"""
    def _review(state: ProposalState) -> dict:
        strategy = state.get("strategy")

        interrupt_data = {
            "step": "strategy",
            "positioning": strategy["positioning"],
            "alternatives": strategy["alternatives"],
            "message": "포지셔닝과 전략을 검토하세요",
        }

        human_input = interrupt(interrupt_data)

        # 라우팅 결정
        if human_input.get("action") == "back_to_research":
            return {
                "routing_decision": "restart_research",
            }
        elif human_input.get("positioning_change"):
            return {
                "routing_decision": "restart_strategy",
                "positioning_override": human_input.get("positioning_change"),
            }
        else:
            return {
                "routing_decision": "fork_to_paths",
                "selected_strategy": strategy,
                "selected_alt_id": human_input.get("selected_alt_id"),
            }
    return _review
```

### STEP 5A: plan_proposal_writing
```python
async def plan_proposal_writing(state: ProposalState) -> dict:
    """제안서 계획: 목차 + 스토리라인"""
    rfp = state.get("rfp_analysis")
    strategy = state.get("strategy")

    # 목차 구성 (RFP 평가기준 기반)
    toc = await _generate_toc(rfp, strategy)

    # 스토리라인 설계
    storylines = await _design_storylines(rfp, strategy, toc)
    # {
    #   "overall_narrative": "...",
    #   "sections": [
    #     {
    #       "section_id": "기술",
    #       "key_message": "...",
    #       "narrative_arc": "...",
    #       "supporting_points": [...],
    #       "evidence": [...],
    #       "win_theme_connection": "...",
    #     }
    #   ]
    # }

    # 담당자 배치
    assignments = await _assign_section_owners(state, toc)

    return {
        "plan": {
            "table_of_contents": toc,
            "storylines": storylines,
            "assignments": assignments,
        },
        "current_phase": "plan_proposal_writing",
    }
```

### STEP 6A: review_proposal_plan (Human Review)
```python
def review_proposal_plan():
    """제안 계획 검토 (목차+스토리라인)"""
    def _review(state: ProposalState) -> dict:
        plan = state.get("plan")

        interrupt_data = {
            "step": "proposal_plan",
            "table_of_contents": plan["table_of_contents"],
            "storylines": plan["storylines"],
            "assignments": plan["assignments"],
            "message": "목차와 스토리라인을 확인하세요",
        }

        human_input = interrupt(interrupt_data)

        if human_input.get("sections_reorder"):
            # 목차 순서 조정 가능
            plan["table_of_contents"] = human_input["sections_reorder"]

        if human_input.get("storylines_update"):
            # 스토리라인 수정 가능
            plan["storylines"] = human_input["storylines_update"]

        return {
            "approved_plan": plan,
            "current_phase": "approved_proposal_plan",
        }
    return _review
```

### STEP 7A: write_proposal_sections
```python
async def write_proposal_sections(state: ProposalState) -> dict:
    """목차별 제안서 작성 (섹션 루프, AI 작업만)"""
    toc = state.get("approved_plan")["table_of_contents"]
    storylines = state.get("approved_plan")["storylines"]
    rfp = state.get("rfp_analysis")

    proposal_sections = []

    for idx, section in enumerate(toc):
        # 해당 섹션의 스토리라인 찾기
        section_storyline = _find_storyline(storylines, section)

        # 섹션 유형 판별 (기술/가격/관리/조직)
        section_type = classify_section_type(section)

        # KB 참조 조회
        kb_context = await _query_kb_for_section(state, section, section_type)

        # 섹션별 프롬프트로 작성
        content = await _generate_section(
            rfp,
            section,
            section_type,
            section_storyline,
            kb_context,
            previous_sections=proposal_sections,  # 이전 섹션 컨텍스트
        )

        # 자체 검증 (완성도/일관성)
        self_check = await _self_check_section(content, section_storyline)

        proposal_sections.append({
            "section_id": section,
            "content": content,
            "self_check_score": self_check["score"],
            "review_notes": self_check["notes"],
        })

    return {
        "proposal_sections": proposal_sections,
        "proposal_draft": "\n".join([s["content"] for s in proposal_sections]),
        "current_phase": "write_proposal_sections",
    }
```

### STEP 8A: review_proposal_sections (Human Review)
```python
def review_proposal_sections():
    """섹션별 검토 (루프)"""
    def _review(state: ProposalState) -> dict:
        sections = state.get("proposal_sections")
        current_section_idx = state.get("section_review_index", 0)

        if current_section_idx >= len(sections):
            # 모든 섹션 완료
            return {
                "routing_decision": "finalize",
                "current_phase": "proposal_sections_complete",
            }

        section = sections[current_section_idx]

        interrupt_data = {
            "step": f"review_section_{current_section_idx}",
            "section_id": section["section_id"],
            "content": section["content"],
            "self_check": section["self_check_score"],
            "message": f"섹션 {current_section_idx+1}/{len(sections)}: {section['section_id']}를 검토하세요",
        }

        human_input = interrupt(interrupt_data)

        if human_input.get("action") == "rewrite":
            # 재작성 요청
            sections[current_section_idx]["feedback"] = human_input.get("feedback")
            sections[current_section_idx]["status"] = "rewrite_needed"
            return {
                "routing_decision": "rewrite_section",
                "section_to_rewrite": current_section_idx,
                "updated_sections": sections,
            }
        elif human_input.get("action") == "finalize":
            # 모든 섹션 완료
            sections[current_section_idx]["status"] = "approved"
            return {
                "routing_decision": "finalize",
                "updated_sections": sections,
                "current_phase": "proposal_sections_approved",
            }
        else:
            # 다음 섹션
            sections[current_section_idx]["status"] = "approved"
            return {
                "routing_decision": "next_section",
                "updated_sections": sections,
                "section_review_index": current_section_idx + 1,
            }
    return _review
```

### STEP 9A: finalize_proposal
```python
async def finalize_proposal(state: ProposalState) -> dict:
    """제안서 통합 및 자가진단"""
    sections = state.get("proposal_sections")
    plan = state.get("approved_plan")
    strategy = state.get("selected_strategy")

    # DOCX/HWPX 생성
    docx_path = await _generate_docx(
        sections,
        plan["table_of_contents"],
        strategy,
    )

    # 자가진단 (4축)
    self_assessment = await _self_assess_proposal(
        sections,
        plan["storylines"],
        strategy,
    )
    # {
    #   "completeness": score,     # 기술/형식 완성도
    #   "differentiation": score,  # 경쟁우위
    #   "persuasiveness": score,   # 메시지 일관성
    #   "compliance": score,       # 요구사항 충족
    #   "total": score,
    #   "recommendations": [...],  # 70점 미만일 때 개선안
    # }

    return {
        "proposal_docx": docx_path,
        "self_assessment": self_assessment,
        "current_phase": "finalize_proposal",
    }
```

### STEP 10A: generate_presentation
```python
async def generate_presentation(state: ProposalState) -> dict:
    """PPT + Q&A 준비"""
    rfp = state.get("rfp_analysis")
    sections = state.get("proposal_sections")
    plan = state.get("approved_plan")
    strategy = state.get("selected_strategy")

    # 평가방식 확인
    eval_method = rfp.get("eval_method", "")

    if "서류심사" in eval_method:
        # PPT 없음, 모의평가 로직
        mock_eval = await _run_mock_evaluation(state)
        return {
            "mock_evaluation": mock_eval,
            "current_phase": "mock_evaluation",
        }

    # 발표 예정 → PPT 생성
    ppt_slides = await _generate_ppt_slides(
        sections,
        plan["table_of_contents"],
        strategy,
    )

    # Q&A 시나리오
    qa_scenarios = await _generate_qa_scenarios(
        rfp,
        sections,
        strategy,
    )

    return {
        "ppt_slides": ppt_slides,
        "qa_scenarios": qa_scenarios,
        "current_phase": "generate_presentation",
    }
```

### STEP 11A: review_presentation (Human Review)
```python
def review_presentation():
    """PPT 및 Q&A 검토"""
    def _review(state: ProposalState) -> dict:
        ppt = state.get("ppt_slides")
        qa = state.get("qa_scenarios")

        interrupt_data = {
            "step": "presentation",
            "ppt": ppt,
            "qa": qa,
            "message": "PPT와 Q&A를 검토하세요",
        }

        human_input = interrupt(interrupt_data)

        return {
            "approved_ppt": human_input.get("ppt_feedback") or ppt,
            "approved_qa": human_input.get("qa_feedback") or qa,
            "current_phase": "presentation_approved",
        }
    return _review
```

### STEP 5B: plan_bidding_process
```python
async def plan_bidding_process(state: ProposalState) -> dict:
    """입찰 준비 계획"""
    rfp = state.get("rfp_analysis")
    team = state.get("team_info")

    # 제출서류 목록 (RFP 기반)
    submission_docs = await _extract_submission_docs(rfp)

    # 담당자 배치
    assignments = await _assign_bidding_owners(team, submission_docs)

    # 일정 계획 (마감일 역산)
    schedule = _calculate_bidding_schedule(
        rfp["deadline"],
        submission_docs,
    )

    # 체크리스트
    checklist = await _generate_submission_checklist(submission_docs)

    return {
        "bidding_plan": {
            "submission_docs": submission_docs,
            "assignments": assignments,
            "schedule": schedule,
            "checklist": checklist,
        },
        "current_phase": "plan_bidding_process",
    }
```

### STEP 6B: recommend_and_set_bid_price
```python
async def recommend_and_set_bid_price(state: ProposalState) -> dict:
    """입찰가 결정"""
    rfp = state.get("rfp_analysis")
    strategy = state.get("selected_strategy")

    # 원가 계산
    cost_breakdown = await _calculate_cost(state)

    # 시장 조사 (유사과제 낙찰률)
    market_analysis = state.get("market_data")

    # 수주확률 추정
    win_probability = await _estimate_win_probability(
        cost_breakdown,
        market_analysis,
        strategy,
    )

    # 가격 옵션 (보수/적정/공격)
    price_options = await _generate_price_options(
        cost_breakdown,
        win_probability,
        strategy,
    )

    interrupt_data = {
        "step": "bid_price",
        "cost_breakdown": cost_breakdown,
        "price_options": price_options,
        "win_probability": win_probability,
        "message": "입찰가를 선택하세요",
    }

    human_input = interrupt(interrupt_data)

    return {
        "approved_bid_price": human_input.get("selected_price"),
        "cost_breakdown": cost_breakdown,
        "current_phase": "bid_price_approved",
    }
```

### STEP 7B: generate_cost_sheets
```python
async def generate_cost_sheets(state: ProposalState) -> dict:
    """산출내역서 작성"""
    cost = state.get("approved_bid_price")
    rfp = state.get("rfp_analysis")

    # 노임단가 조회
    labor_rates = await _get_labor_rates(state)

    # 산출내역서 생성 (다양한 양식)
    cost_sheets = await _generate_cost_sheets_multi_format(
        cost,
        labor_rates,
        rfp,
    )
    # Excel, HWPX, PDF 등

    # 검증
    validation = _validate_cost_sheets(cost_sheets, cost)

    return {
        "cost_sheets": cost_sheets,
        "validation": validation,
        "current_phase": "cost_sheets_generated",
    }
```

### STEP 8B: review_bidding_submission (Human Review)
```python
def review_bidding_submission():
    """입찰 최종 체크"""
    def _review(state: ProposalState) -> dict:
        plan = state.get("bidding_plan")
        cost_sheets = state.get("cost_sheets")
        bid_price = state.get("approved_bid_price")

        interrupt_data = {
            "step": "bidding_submission",
            "checklist": plan["checklist"],
            "documents_status": await _check_document_status(state),
            "bid_price": bid_price,
            "cost_sheets": cost_sheets,
            "deadline": state.get("deadline"),
            "message": "입찰 제출을 최종 확인하세요",
        }

        human_input = interrupt(interrupt_data)

        if human_input.get("action") == "submit_now":
            # 제출 준비
            return {
                "submission_approved": True,
                "submission_timestamp": datetime.now().isoformat(),
                "current_phase": "bidding_submission_approved",
            }
        else:
            # 수정 필요
            return {
                "submission_approved": False,
                "revision_requests": human_input.get("revisions"),
            }
    return _review
```

### STEP 9: prepare_qa_and_presentation
```python
async def prepare_qa_and_presentation(state: ProposalState) -> dict:
    """발표 Q&A 준비"""
    proposal = state.get("proposal_docx")
    ppt = state.get("approved_ppt")
    rfp = state.get("rfp_analysis")

    # 평가위원 프로필 분석 (선택사항)
    evaluator_profile = await _analyze_evaluator_profile(rfp)

    # 예상 질문
    qa_scenarios = await _generate_qa_scenarios(
        rfp,
        state.get("proposal_sections"),
        evaluator_profile,
    )

    # 리허설 노트
    rehearsal_notes = await _generate_rehearsal_notes(
        ppt,
        qa_scenarios,
    )

    return {
        "qa_package": {
            "scenarios": qa_scenarios,
            "rehearsal_notes": rehearsal_notes,
            "evaluator_profile": evaluator_profile,
        },
        "current_phase": "prepare_qa",
    }
```

### STEP 10: review_presentation_readiness (Human Review)
```python
def review_presentation_readiness():
    """발표 준비 최종 검토"""
    def _review(state: ProposalState) -> dict:
        qa_package = state.get("qa_package")

        interrupt_data = {
            "step": "presentation_readiness",
            "qa_scenarios": qa_package["scenarios"],
            "rehearsal_notes": qa_package["rehearsal_notes"],
            "message": "발표 준비를 최종 확인하세요",
        }

        human_input = interrupt(interrupt_data)

        return {
            "presentation_approved": True,
            "current_phase": "presentation_ready",
        }
    return _review
```

### STEP 11: record_evaluation_result
```python
async def record_evaluation_result(state: ProposalState) -> dict:
    """평가 결과 기록"""

    # 평가점수 입력 (Human input)
    evaluation_record = {
        "eval_scores": state.get("eval_scores"),  # interrupt에서 입력
        "decision": state.get("eval_decision"),   # 당/당락
        "awarded_price": state.get("awarded_price"),
    }

    # 모의평가 점수와 비교
    self_assessment = state.get("self_assessment")
    comparison = _compare_assessments(self_assessment, evaluation_record)

    # 교훈 도출
    lessons = await _extract_lessons(state, evaluation_record, comparison)

    # 당/패에 따른 KB 업데이트 계획
    kb_updates = await _plan_kb_updates(state, evaluation_record, lessons)

    return {
        "evaluation_record": evaluation_record,
        "assessment_comparison": comparison,
        "lessons_learned": lessons,
        "kb_updates": kb_updates,
        "current_phase": "evaluation_recorded",
    }
```

### STEP 12: finalize_and_archive
```python
async def finalize_and_archive(state: ProposalState) -> dict:
    """학습 기록 & 종료"""

    # KB 업데이트 실행
    await _execute_kb_updates(state.get("kb_updates"))

    # 제안서 아카이브
    archive_summary = await _archive_proposal(state)

    # 타임라인 기록
    timeline = _generate_proposal_timeline(state)

    return {
        "archive_summary": archive_summary,
        "timeline": timeline,
        "kb_updates_completed": True,
        "current_phase": "complete",
    }
```

---

## 🔀 라우팅 로직 (단순화됨)

| From | Condition | To | 비고 |
|------|-----------|-----|------|
| review_go_no_go | no_go | END | 조기 종료 |
| review_go_no_go | go | formulate_strategy | 제안 진행 |
| review_strategy | back_research | analyze_and_research | 재리서치 |
| review_strategy | retry_strategy | formulate_strategy | 전략 재수립 |
| review_strategy | approved | fork_to_paths | A/B 분기 |
| fork_to_paths | - | plan_proposal_writing + plan_bidding_process | 병렬 |
| review_proposal_plan | approved | write_proposal_sections | 섹션 작성 |
| review_proposal_sections (마지막) | approved | finalize_proposal | 통합 |
| finalize_proposal | - | generate_presentation | PPT |
| review_presentation | approved | convergence_gate | A 경로 완료 |
| review_bidding_submission | approved | convergence_gate | B 경로 완료 |
| convergence_gate | A+B 완료 | prepare_qa_and_presentation | 수렴 |
| review_presentation_readiness | approved | record_evaluation_result | 평가 |
| record_evaluation_result | - | finalize_and_archive | 종료 |

---

## 📊 구조 비교

| 항목 | 기존 (v4.0) | 최적화 (v6.0) |
|------|-----------|-------------|
| **노드 수** | 40개 | 16개 |
| **Review 게이트** | 16개 (산재) | 8개 (명확) |
| **라우팅 함수** | 15개 | 12개 (단순) |
| **병렬 노드** | 5개 (plan_*) | 2개 (plan_path + bidding_path) |
| **복잡도** | 높음 | 낮음 |
| **유지보수성** | 어려움 | 쉬움 |
| **사용자 이해도** | 낮음 | 높음 |

---

## 🚀 마이그레이션 전략

### Phase 1: 신규 노드 구현 (병렬)
```
- intake_proposal
- analyze_and_research (rfp_analyze + research_gather 통합)
- formulate_strategy
- plan_proposal_writing (plan_* 통합)
- plan_bidding_process
- write_proposal_sections (proposal_write_next 개선)
- generate_presentation (ppt_nodes 통합)
- record_evaluation_result
- finalize_and_archive
```

### Phase 2: Review 게이트 통합
```
- review_go_no_go (기존 + go_no_go 노드의 결정 로직)
- review_strategy
- review_proposal_plan
- review_proposal_sections (섹션 루프)
- review_bidding_submission
- review_presentation
- review_presentation_readiness
- 모의평가 (generate_presentation 내 조건부)
```

### Phase 3: 라우팅 개선
```
- 조건부 엣지 재정의
- route_* 함수 통합/제거
- fork_to_branches 개선
- convergence_gate 유지
```

### Phase 4: 기존 노드 제거
```
- 40개 → 16개로 축소
- 호환성 레이어 점진 제거
```

---

## ✅ 장점

1. **명확성**: 각 노드의 책임이 명확함
2. **유지보수성**: 코드 양 60% 감소
3. **성능**: 라우팅 로직 단순화 → 빠른 의사결정
4. **사용자 이해도**: "지금 뭐하는 단계인가"가 명확함
5. **확장성**: 새 기능 추가 시 노드 추가만 하면 됨

---

## 📌 다음 액션

1. **이 설계 검토** → 16개 노드 구조 타당성 확인
2. **상세 구현** → 각 노드의 프롬프트/로직 작성
3. **기존 코드 리팩토링** → 40개 노드 → 16개로 축소
4. **테스트 & 배포**
