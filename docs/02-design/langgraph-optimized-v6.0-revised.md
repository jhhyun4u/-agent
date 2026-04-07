# LangGraph 최적화 설계 v6.0 (수정)
## 모의평가 노드 명시화 + Human 검토 루프 추가

> **설계일**: 2026-03-29 (수정: 모의평가 명시)
> **노드 수**: 16개 → **18개** (모의평가 2개 노드 추가)
> **핵심**: 모의평가 → Human 검토 → 수정보완 루프

---

## 🗺️ 수정된 워크플로우 (18개 노드)

```
START
  │
  ▼
┌──────────────────────────────────────────────────┐
│  STEP 0: 제안 착수 (1개 노드)                    │
├──────────────────────────────────────────────────┤
│ intake_proposal                                  │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│  STEP 1: RFP 분석 + Research (1개 노드)          │
├──────────────────────────────────────────────────┤
│ analyze_and_research                             │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│  STEP 2: 제안 여부 결정 (Human Review #1)        │
├──────────────────────────────────────────────────┤
│ review_go_no_go                                  │
│ ├─ No-Go → END                                  │
│ └─ Go → 계속                                     │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│  STEP 3: 제안 전략 수립 (1개 노드)                │
├──────────────────────────────────────────────────┤
│ formulate_strategy                               │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│  STEP 4: 전략 검토 (Human Review #2)             │
├──────────────────────────────────────────────────┤
│ review_strategy                                  │
│ ├─ 재리서치 / 전략 재수립 가능                    │
│ └─ 승인 → FORK                                  │
└──────────────┬───────────────────────────────────┘
               │
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

PATH A: 제안서 작성 경로 (STEP 5A~7A)

        │
        ▼
   ┌─────────────────────────────────────┐
   │ STEP 5A: 제안 계획 수립 (1개 노드)    │
   ├─────────────────────────────────────┤
   │ plan_proposal_writing                │
   │ └─ 목차 + 스토리라인 설계            │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 6A: 계획 검토 (Human Review #3) │
   ├─────────────────────────────────────┤
   │ review_proposal_plan                 │
   │ └─ 목차/스토리라인 수정 가능          │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 7A: 목차별 제안서 작성 (1개 노드)│
   ├─────────────────────────────────────┤
   │ write_proposal_sections              │
   │ └─ 섹션 루프 (context 누적)         │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 8A: 섹션별 검토 (Human Review #4)│
   ├─────────────────────────────────────┤
   │ review_proposal_sections             │
   │ └─ 섹션 루프 + 재작성 가능           │
   └────────┬────────────────────────────┘
            │ (모든 섹션 완료)
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 9A: 제안서 최종 통합 (1개 노드)  │
   ├─────────────────────────────────────┤
   │ finalize_proposal                    │
   │ ├─ DOCX/HWPX 생성                   │
   │ ├─ 자가진단 (4축 평가)               │
   │ └─ 점수 < 70점 시 개선 제안         │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 10A: 모의평가 실행 (1개 노드)   │
   │       ★ 신규 추가 ★                 │
   ├─────────────────────────────────────┤
   │ run_mock_evaluation                  │
   │ ├─ 평가위원 관점에서 평가            │
   │ │ ├─ 기술점수 평가                   │
   │ │ ├─ 가격점수 평가                   │
   │ │ ├─ 관리점수 평가                   │
   │ │ ├─ 기술+가격 종합점수               │
   │ │ └─ 약점 분석 + 개선 제안           │
   │ ├─ 자가진단 vs 모의평가 비교         │
   │ │ ├─ 점수 차이 분석                  │
   │ │ └─ 강점/약점 파악                  │
   │ └─ output: mock_eval_report,        │
   │           score_analysis,           │
   │           improvement_suggestions   │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 11A: 모의평가 검토+수정 (Human #5)│
   │       ★ 신규 추가 ★                 │
   ├─────────────────────────────────────┤
   │ review_mock_evaluation              │
   │ ├─ interrupt: 모의평가 결과          │
   │ │ ├─ 점수 상세 (기술/가격/관리)      │
   │ │ ├─ 약점 분석                      │
   │ │ ├─ 자가진단 vs 실제 비교           │
   │ │ └─ 개선 제안                      │
   │ └─ 라우팅:                          │
   │   ├─ "수정보완" → 섹션 재작성       │
   │   │  (rework_targets 설정)          │
   │   ├─ "추가 검토" → review_proposal  │
   │   │  (전체 검토)                    │
   │   └─ "진행" → PPT 작성              │
   └────────┬────────────────────────────┘
            │
        ┌───┴──────────────────┐
        │                      │
    (수정보완)             (진행)
        │                      │
        ▼                      ▼
   write_proposal_sections  generate_presentation
   (재작성 루프)            (PPT 생성)
        │                      │
        ▼                      ▼
   review_proposal_sections  review_presentation
   (섹션별 검토)            (Human Review #6)
        │                      │
        └──────────┬───────────┘
                   │
                   ▼
            (PPT 완료)
                   │
                   └──→ [CONVERGENCE]

═══════════════════════════════════════════════════════════

PATH B: 입찰 경로 (STEP 5B~8B, 기존과 동일)

        │
        ▼
   ┌─────────────────────────────────────┐
   │ STEP 5B: 입찰 준비 계획 (1개 노드)    │
   ├─────────────────────────────────────┤
   │ plan_bidding_process                 │
   │ └─ 제출서류 목록/일정/체크리스트      │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 6B: 입찰가 결정 (Human Review #7)│
   ├─────────────────────────────────────┤
   │ recommend_and_set_bid_price          │
   │ └─ 원가 + 시장조사 + 수주확률 기반   │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 7B: 산출내역서 작성 (1개 노드)   │
   ├─────────────────────────────────────┤
   │ generate_cost_sheets                 │
   │ └─ 노임단가 + 경비 계산              │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 8B: 입찰 최종 체크 (Human #8)   │
   ├─────────────────────────────────────┤
   │ review_bidding_submission            │
   │ └─ 서류 준비상황 최종 확인           │
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
   │ ├─ PATH A 완료 대기 (PPT 또는 모의평가)
   │ ├─ PATH B 완료 대기 (제출 준비)      │
   │ └─ 모두 완료 → 다음 노드로           │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 9: 발표 Q&A 준비 (1개 노드)     │
   ├─────────────────────────────────────┤
   │ prepare_qa_and_presentation          │
   │ └─ 예상 질문 + 답변 준비             │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 10: 발표 준비 검토 (Human #9)   │
   ├─────────────────────────────────────┤
   │ review_presentation_readiness        │
   │ └─ Q&A 시나리오 최종 확인            │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 11: 평가 결과 기록 (1개 노드)    │
   ├─────────────────────────────────────┤
   │ record_evaluation_result             │
   │ ├─ 평가점수 입력 (Human)             │
   │ ├─ 모의평가 vs 실제 점수 비교        │
   │ └─ 교훈 도출                        │
   └────────┬────────────────────────────┘
            │
            ▼
   ┌─────────────────────────────────────┐
   │ STEP 12: 학습 기록 & 종료 (1개 노드) │
   ├─────────────────────────────────────┤
   │ finalize_and_archive                 │
   │ └─ KB 업데이트 + 아카이브             │
   └────────┬────────────────────────────┘
            │
            ▼
           END
```

---

## 🎯 새로운 2개 노드 상세 설계

### STEP 10A: run_mock_evaluation (신규 AI 노드)

```python
async def run_mock_evaluation(state: ProposalState) -> dict:
    """모의평가 실행 - AI가 평가위원 관점에서 평가"""

    proposal_sections = state.get("proposal_sections")
    rfp = state.get("rfp_analysis")
    strategy = state.get("selected_strategy")
    self_assessment = state.get("self_assessment")

    # 1️⃣ 평가위원 프로필 분석
    evaluator_profile = await _analyze_evaluator_profile(rfp)

    # 2️⃣ 기술점수 평가 (RFP 평가기준 기반)
    technical_score = await _score_technical_proposal(
        proposal_sections,
        rfp,
        evaluator_profile,
    )
    # {
    #   "score": 0~100,
    #   "breakdown": {
    #     "requirement_compliance": score,
    #     "technical_innovation": score,
    #     "implementation_feasibility": score,
    #     "risk_management": score,
    #   },
    #   "strengths": [...],
    #   "weaknesses": [...],
    #   "concerns": [...]
    # }

    # 3️⃣ 가격점수 평가
    price_score = await _score_price_proposal(
        state.get("approved_bid_price"),
        rfp,
    )
    # {
    #   "score": 0~100,
    #   "competitiveness": "high/medium/low",
    #   "win_probability": 0.0~1.0,
    # }

    # 4️⃣ 관리점수 평가 (조직, 경험, 보증, 사후관리)
    management_score = await _score_management_proposal(
        proposal_sections,
        state.get("team_info"),
        evaluator_profile,
    )

    # 5️⃣ 종합점수 (기술 + 가격 + 관리)
    eval_method = rfp.get("eval_method", "")
    if "가격점수 제외" in eval_method:
        # 기술 + 관리만
        total_score = (technical_score["score"] + management_score["score"]) / 2
    else:
        # 일반: 기술 + 가격 + 관리
        weights = _parse_scoring_weights(rfp)
        total_score = (
            technical_score["score"] * weights.get("technical", 0.4)
            + price_score["score"] * weights.get("price", 0.3)
            + management_score["score"] * weights.get("management", 0.3)
        )

    # 6️⃣ 자가진단 vs 모의평가 비교
    self_assessment_score = state.get("self_assessment", {}).get("total", 0)
    score_comparison = {
        "self_assessment": self_assessment_score,
        "mock_evaluation": total_score,
        "difference": total_score - self_assessment_score,
        "analysis": await _analyze_score_gap(
            self_assessment_score,
            total_score,
            technical_score,
            price_score,
            management_score,
        ),
    }

    # 7️⃣ 주요 강점/약점 및 개선 제안
    improvement_suggestions = await _generate_improvement_suggestions(
        technical_score["weaknesses"],
        technical_score["concerns"],
        price_score,
        management_score,
    )

    return {
        "mock_evaluation": {
            "technical_score": technical_score,
            "price_score": price_score,
            "management_score": management_score,
            "total_score": total_score,
            "score_comparison": score_comparison,
            "improvement_suggestions": improvement_suggestions,
            "evaluator_insights": evaluator_profile,
        },
        "current_phase": "mock_evaluation_complete",
    }
```

**세부 평가 함수**:

```python
async def _score_technical_proposal(sections, rfp, evaluator_profile) -> dict:
    """
    기술점수 평가 (4~5개 평가항목)
    - 요구사항 충족도
    - 기술 혁신성
    - 구현 가능성
    - 위험 관리

    출력: score (0~100), breakdown, strengths, weaknesses, concerns
    """
    pass

async def _score_price_proposal(bid_price, rfp) -> dict:
    """
    가격점수 평가
    - RFP의 가격점수 산정식 적용
    - 경쟁력 분석 (시장 낙찰률 기반)
    - 수주확률 추정

    출력: score (0~100), competitiveness, win_probability
    """
    pass

async def _score_management_proposal(sections, team_info, profile) -> dict:
    """
    관리점수 평가
    - 조직 및 경험 (유사실적, 핵심인력)
    - 보증 및 신뢰성
    - 사후관리 계획

    출력: score (0~100), breakdown, strengths, weaknesses
    """
    pass

async def _analyze_score_gap(self_score, mock_score, tech, price, mgmt) -> str:
    """
    자가진단 vs 모의평가 점수 차이 분석

    예:
    - 자가진단 85점 vs 모의평가 72점 (-13점)
    - 원인: 기술점수 과다평가, 가격경쟁력 낮음
    - 개선: 가격조정 검토, 기술 실현성 강조 필요
    """
    pass

async def _generate_improvement_suggestions(weaknesses, concerns, price, mgmt) -> list:
    """
    모의평가 결과 기반 개선 제안

    예:
    [
      {
        "category": "기술",
        "issue": "위험관리 계획 미흡",
        "suggestion": "위험 대응계획 상세화 (섹션 3)",
        "priority": "high",
        "estimated_impact": "+5점"
      },
      ...
    ]
    """
    pass
```

### STEP 11A: review_mock_evaluation (신규 Human Review 노드)

```python
def review_mock_evaluation():
    """모의평가 검토 - 실제 평가 예상 시나리오 검토"""

    def _review(state: ProposalState) -> dict:
        mock_eval = state.get("mock_evaluation")
        proposal_sections = state.get("proposal_sections")

        # 모의평가 데이터 구성
        interrupt_data = {
            "step": "mock_evaluation",
            "scores": {
                "technical": mock_eval["technical_score"]["score"],
                "price": mock_eval["price_score"]["score"],
                "management": mock_eval["management_score"]["score"],
                "total": mock_eval["total_score"],
            },
            "score_breakdown": {
                "technical": mock_eval["technical_score"]["breakdown"],
                "price": mock_eval["price_score"],
                "management": mock_eval["management_score"]["breakdown"],
            },
            "strengths": {
                "technical": mock_eval["technical_score"].get("strengths", []),
                "price": mock_eval["price_score"].get("strengths", []),
                "management": mock_eval["management_score"].get("strengths", []),
            },
            "weaknesses": {
                "technical": mock_eval["technical_score"].get("weaknesses", []),
                "price": mock_eval["price_score"].get("weaknesses", []),
                "management": mock_eval["management_score"].get("weaknesses", []),
            },
            "concerns": {
                "technical": mock_eval["technical_score"].get("concerns", []),
            },
            "score_comparison": mock_eval["score_comparison"],
            "improvement_suggestions": mock_eval["improvement_suggestions"],
            "message": f"""
            모의평가 결과를 검토하세요.

            📊 종합점수: {mock_eval["total_score"]:.0f}점
            🚀 자가진단 대비: {mock_eval["score_comparison"]["difference"]:+.0f}점

            주요 약점:
            {chr(10).join([f"- {w}" for w in mock_eval["technical_score"].get("weaknesses", [])[:3]])}

            다음 중 선택하세요:
            1. "수정보완" - 약점을 보완하기 위해 섹션 재작성
            2. "추가검토" - 전체 제안서 재검토
            3. "진행" - 평가 결과 수용 후 PPT 작성
            """,
        }

        human_input = interrupt(interrupt_data)

        # 라우팅 결정
        action = human_input.get("action", "proceed")

        if action == "revise":
            # 수정보완: 약점 섹션 재작성
            rework_targets = human_input.get("rework_targets", [])
            return {
                "routing_decision": "revise_sections",
                "rework_targets": rework_targets,
                "revision_feedback": human_input.get("feedback", ""),
                "mock_eval_approved": mock_eval,
                "current_phase": "mock_evaluation_revising",
            }

        elif action == "full_review":
            # 추가 검토: 전체 제안서 재검토
            return {
                "routing_decision": "full_proposal_review",
                "mock_eval_approved": mock_eval,
                "current_phase": "proposal_full_review",
            }

        else:  # "proceed"
            # 진행: 모의평가 수용, PPT 작성으로
            return {
                "routing_decision": "proceed_to_ppt",
                "mock_eval_approved": mock_eval,
                "mock_eval_accepted": True,
                "current_phase": "mock_evaluation_accepted",
            }

    return _review
```

---

## 🔀 수정된 라우팅 로직

### PATH A의 라우팅 (섹션별 → 모의평가 → PPT)

```python
# STEP 8A: 섹션별 검토 완료 후
if all_sections_reviewed:
    → finalize_proposal (STEP 9A)

# STEP 9A: 제안서 최종 통합 후
→ run_mock_evaluation (STEP 10A)  ← 자동 진행

# STEP 10A: 모의평가 완료 후
→ review_mock_evaluation (STEP 11A)  ← Human 검토

# STEP 11A: Human 검토 결과
├─ "수정보완" (rework_targets 설정)
│  → write_proposal_sections (STEP 7A 재실행)
│     └─ review_proposal_sections (STEP 8A 재루프)
│        └─ (수정 완료 후)
│           → run_mock_evaluation (다시)
│
├─ "추가검토" (전체 재검토)
│  → review_proposal (전체 검토)
│
└─ "진행" (모의평가 수용)
   → generate_presentation (PPT 작성)
      → review_presentation (Human #6)
         → convergence_gate
```

### 라우팅 함수

```python
def route_after_finalize_proposal(state: ProposalState) -> str:
    """제안서 최종 통합 후: 자동으로 모의평가로"""
    return "mock_evaluation"

def route_after_mock_evaluation(state: ProposalState) -> str:
    """모의평가 완료 후: Human 검토로"""
    return "review_mock_eval"

def route_after_review_mock_evaluation(state: ProposalState) -> str:
    """Human 검토 결과에 따라 분기"""
    routing = state.get("routing_decision", "proceed")

    if routing == "revise_sections":
        return "revise_sections"  # 섹션 재작성으로
    elif routing == "full_review":
        return "full_proposal_review"  # 전체 재검토로
    else:
        return "proceed_to_ppt"  # PPT 작성으로

def route_revise_sections(state: ProposalState) -> str:
    """재작성 후 다시 섹션 검토로"""
    # rework_targets이 지정되면 해당 섹션만 재작성
    return "review_proposal_sections"
```

---

## 📊 수정된 노드 수 비교

| 분류 | 기존 | 수정 | 변경 |
|------|------|------|------|
| AI 작업 노드 | 9개 | 10개 | +1 (run_mock_evaluation) |
| Human Review 노드 | 8개 | 9개 | +1 (review_mock_evaluation) |
| 게이트/병합 노드 | 4개 | 4개 | 변화 없음 |
| **합계** | **16개** | **18개** | **+2** |

---

## 🔄 모의평가 루프 흐름

```
제안서 완성 (자가진단 점수: 예 85점)
    │
    ▼
┌─────────────────────────┐
│ run_mock_evaluation     │  ← AI 평가위원 관점 평가
│ (5방향 다층 평가)       │
│                         │
│ 기술점수: 72점          │
│ 가격점수: 68점          │
│ 관리점수: 75점          │
│ 종합점수: 71점          │
│                         │
│ 주요 약점:              │
│ - 기술혁신성 부족       │
│ - 가격경쟁력 낮음       │
│ - 위험관리계획 미흡      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ review_mock_evaluation  │  ← Human 검토
│ (Interrupt)             │
│                         │
│ "자가진단 85점 vs       │
│  모의평가 71점"          │
│                         │
│ "14점 차이 분석:        │
│  - 기술점수 과평가      │
│  - 가격경쟁력 미흡      │
│  - 위험계획 상세화 필요" │
│                         │
│ 선택:                   │
│ ① "수정보완" (적극)     │
│ ② "추가검토"           │
│ ③ "진행" (현상 수용)   │
└────────┬────────────────┘
         │
    ┌────┼────┬────┐
    │    │    │    │
 [①]│ [②]│[③]│
    │    │    │
    ▼    ▼    ▼

┌──────────────────────────┐
│ write_proposal_sections  │   ┌──────────────────┐   ┌─────────────────┐
│ (rework_targets 섹션)    │   │ review_proposal  │   │ generate_      │
│                          │   │ (전체 재검토)    │   │ presentation   │
│ - 섹션 3: 위험관리 강화  │   │                  │   │ (PPT 작성)      │
│ - 섹션 5: 기술혁신 강조  │   │                  │   │                │
│                          │   │                  │   │                │
└────────┬─────────────────┘   └────────┬─────────┘   └────────┬────────┘
         │                             │                       │
         ▼                             │                       │
┌──────────────────────────┐          │                       │
│ review_proposal_sections │──────────┘                       │
│ (재작성 섹션 검토)       │                                  │
│                          │                                  │
│ - 섹션 3 OK             │                                  │
│ - 섹션 5 재작성 요청    │                                  │
└────────┬─────────────────┘                                  │
         │                                                    │
         ▼                                                    │
┌──────────────────────────┐                                  │
│ write_proposal_sections  │                                  │
│ (섹션 5 재작성)          │                                  │
└────────┬─────────────────┘                                  │
         │                                                    │
         ▼                                                    │
┌──────────────────────────┐                                  │
│ review_proposal_sections │                                  │
│ (섹션 5 최종 확인)       │                                  │
│ OK → 진행                │                                  │
└────────┬─────────────────┘                                  │
         │                                                    │
         ▼                                                    │
┌──────────────────────────┐                                  │
│ run_mock_evaluation      │  ← 다시 평가!                   │
│ (수정 후 재평가)         │                                  │
│                          │                                  │
│ 기술점수: 78점 (+6점)   │                                  │
│ 가격점수: 68점 (동일)   │                                  │
│ 관리점수: 75점 (동일)   │                                  │
│ 종합점수: 76점 (+5점)   │                                  │
│                          │                                  │
│ "만족" → 진행 승인      │                                  │
└────────┬─────────────────┘                                  │
         │                                                    │
         ▼                                                    │
┌──────────────────────────────────────────────────────────┐ │
│ convergence 방향으로 (PPT 또는 모의평가 승인 상태로)    │ │
└──────────────────────┬───────────────────────────────────┘ │
                       │◄──────────────────────────────────────┘
                       │
                       ▼
               ┌──────────────────┐
               │ convergence_gate │
               │ (A+B 합류)       │
               └──────────────────┘
```

---

## 📋 전체 노드 목록 (18개)

**공통 기초 (5개)**:
1. intake_proposal
2. analyze_and_research
3. review_go_no_go
4. formulate_strategy
5. review_strategy

**PATH A - 제안서 (8개)**:
6. plan_proposal_writing
7. review_proposal_plan
8. write_proposal_sections
9. review_proposal_sections
10. finalize_proposal
11. **run_mock_evaluation** ← 신규
12. **review_mock_evaluation** ← 신규
13. generate_presentation
14. review_presentation

**PATH B - 입찰 (4개)**:
15. plan_bidding_process
16. recommend_and_set_bid_price
17. generate_cost_sheets
18. review_bidding_submission

**게이트 (2개)**:
- fork_gate (FORK)
- convergence_gate (수렴)

---

## ✅ 핵심 개선점

### 1️⃣ 명시적 모의평가 프로세스
- **run_mock_evaluation**: AI가 평가위원 관점에서 객관적 평가
- **review_mock_evaluation**: Human이 평가 결과 검토 & 대응 결정

### 2️⃣ 수정보완 루프
```
약점 식별 (모의평가)
    ↓
수정보완 결정 (Human)
    ↓
섹션 재작성 (write_proposal_sections)
    ↓
섹션 검토 (review_proposal_sections)
    ↓
다시 모의평가 (run_mock_evaluation)
    ↓
효과 검증 (점수 개선 확인)
```

### 3️⃣ 자가진단 vs 모의평가 비교
- 자체 평가 vs 객관적 평가의 차이 파악
- "과신" 또는 "과소평가" 식별
- 개선 우선순위 결정

### 4️⃣ 다양한 대응 옵션
- 수정보완 (특정 섹션)
- 추가 검토 (전체)
- 현상 수용 (모의평가 결과 신뢰)

---

## 🚀 구현 우선순위

### Phase 1 (필수):
- `run_mock_evaluation`: 평가위원 관점 평가 로직
- `review_mock_evaluation`: Human 검토 인터페이스

### Phase 2 (병렬):
- 섹션 재작성 라우팅
- 재평가 자동화

### Phase 3 (최적화):
- 모의평가 점수 예측 모델 (ML)
- 개선 효과 추정 (점수 상향)

---

## 📌 문서 업데이트

**기존**:
- `docs/02-design/langgraph-optimized-v6.0.md`

**신규**:
- `docs/02-design/langgraph-optimized-v6.0-revised.md` ← 이 파일

**변경 사항 요약**:
- 노드 16개 → 18개 (+2)
- PATH A 라우팅 재정의
- 모의평가 루프 추가
- 수정보완 워크플로우 문서화
