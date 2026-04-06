# 모의평가 시스템 — 개발자 빠른 참고가이드

## 📍 위치

| 구성 | 파일 경로 |
|-----|---------|
| **메인 구현** | `app/graph/nodes/evaluation_nodes.py` |
| **라우팅 로직** | `app/graph/edges.py` (`route_after_mock_eval_review`) |
| **그래프 연결** | `app/graph/graph.py` (STEP 10A-11A) |
| **상태 정의** | `app/graph/state.py` (ProposalState.mock_evaluation_result) |
| **설계 문서** | `docs/02-design/mock-evaluation-detailed-design.md` |
| **구현 보고서** | `docs/02-design/mock-evaluation-implementation-summary.md` |

---

## 🔑 핵심 함수

### `async def mock_evaluation(state: ProposalState) -> dict`

**목적**: RFP eval_items 기반 6명 평가위원 모의평가 실행

**입력**
```python
state: {
    "rfp_analysis": RFPAnalysis,  # eval_items 포함
    "strategy": Strategy,          # win_theme, positioning
    "proposal_sections": [ProposalSection, ...],  # 제안서 콘텐츠
}
```

**출력**
```python
{
    "mock_evaluation_result": {
        "evaluation_metadata": {...},
        "evaluators": [...],
        "evaluation_items": {...},
        "evaluator_scores": {...},
        "category_scores": {...},
        "final_score": 72.5,
        "win_probability": "보통 (70-84점)",
        "strengths": [...],
        "weaknesses": [...],
        "high_consensus_items": [...],
        "low_consensus_items": [...],
    },
    "current_phase": "mock_evaluation_complete",
}
```

**에러 처리**
```python
return {
    "mock_evaluation_result": {"error": str(e)},
    "current_phase": "mock_evaluation_error",
}
```

---

## 👥 평가위원 6명 프로필

### `_create_evaluator_profiles() -> list[dict]`

**반환**: 6명 평가위원 프로필 (산학연 2명씩)

```python
[
    {
        "id": "evaluator_1",
        "name": "이산업",
        "type": "산업계",
        "subtype": "발주유사",
        "perspective": ["사업 실현가능성", "비용 효율성", ...],
        "evaluation_bias": {
            "tendency": "보수적",  # 보수적/중도/낙관적
            "scoring_range": (0, 90),  # 점수 상한선
            "weight": 1.0
        }
    },
    ...  # 총 6명
]
```

**평가위원 타입**

| 번호 | 이름 | 직책 | 타입 | 특징 |
|-----|-----|-----|------|------|
| 1 | 이산업 | 개발이사 | 산업계 | 보수적, 실현가능성 중시 |
| 2 | 박경쟁 | 경쟁사CEO | 산업계 | 중도, 차별화 중시 |
| 3 | 최교수 | 대학교수 | 학계 | 낙관적, 혁신성 중시 |
| 4 | 정소장 | 연구소장 | 학계 | 중도, 현실성 중시 |
| 5 | 홍정책 | 정부과장 | 연구계/공공 | 보수적, 정책부합 중시 |
| 6 | 강협회 | 협회부회장 | 연구계/공공 | 중도, 표준준수 중시 |

---

## 📊 평가 로직

### `async def _score_evaluation_item(item, evaluator, sections, strategy) -> dict`

**프로세스**
1. 평가항목 정보 추출
2. 제안서에서 관련 콘텐츠 요약
3. AI(Claude)에게 평가위원 관점으로 평가 요청
4. 점수 범위 제한 (evaluator bias 반영)
5. 배점 단위로 정규화

**AI 프롬프트 특징**
- 평가위원의 직책, 경험, 성향 명시
- 평가항목의 배점과 평가기준 제시
- JSON 응답 강제 (점수+이유+강점+약점)
- 온도 0.3 (일관성)

---

## 📈 분석 함수들

### `_calculate_distribution(scores) -> dict`
**분포 통계** (6명 점수)
- mean (평균), median (중앙값), stdev (표준편차)
- min/max, range, variance

### `_assess_consensus(scores) -> dict`
**합의도 판정**
- `stdev < 3`: "높음 (강한 합의)"
- `3 ≤ stdev < 6`: "중간"
- `stdev ≥ 6`: "낮음 (의견 분분)" 🚩

### `_assess_win_probability(final_score) -> str`
**수주 가능성**
- `≥ 85`: "높음"
- `70-84`: "보통"
- `< 70`: "낮음"

---

## 🔄 라우팅

### `route_after_mock_eval_review(state) -> str`

**4가지 경로**

```python
# 1. 승인 → 발표 준비 진행
if approval.status == "approved":
    return "approved"  # → convergence_gate

# 2. 특정 섹션 개선 → 재작성
if rework_targets (특정):
    return "rework_sections"  # → proposal_start_gate

# 3. 전략 재검토
if "strategy_generate" in rework_targets:
    return "rework_strategy"  # → strategy_generate

# 4. 모의평가 재실행
else:
    return "rejected"  # → mock_evaluation
```

**활용**: Human이 review_mock_eval 노드에서 approval.status와 feedback_history.rework_targets을 설정

---

## 🔗 그래프 통합 (graph.py)

```python
# STEP 10A: 모의평가 AI 실행
g.add_edge("mock_evaluation", "review_mock_eval")

# STEP 11A: 모의평가 Human Review
g.add_conditional_edges("review_mock_eval", route_after_mock_eval_review, {
    "approved": "convergence_gate",       # ✅ 승인
    "rework_sections": "proposal_start_gate",  # 🔄 섹션 개선
    "rework_strategy": "strategy_generate",    # 🔄 전략 재검토
    "rejected": "mock_evaluation",        # ❌ 재평가
})
```

---

## 🧪 테스트 팁

### 1. 평가위원 프로필 확인
```python
from app.graph.nodes.evaluation_nodes import _create_evaluator_profiles

evaluators = _create_evaluator_profiles()
for e in evaluators:
    print(f"{e['name']} ({e['type']}): {e['perspective']}")
```

### 2. 분포 분석 테스트
```python
from app.graph.nodes.evaluation_nodes import _calculate_distribution, _assess_consensus

scores = [68, 75, 78, 62, 80, 85]
dist = _calculate_distribution(scores)
consensus = _assess_consensus(scores)

print(f"평균: {dist['mean']:.1f}, 표준편차: {dist['stdev']:.1f}")
print(f"합의도: {consensus['consensus_level']}")
```

### 3. 라우팅 로직 테스트
```python
from app.graph.edges import route_after_mock_eval_review
from app.graph.state import ProposalState

# 테스트 state 구성
state = {
    "approval": {
        "mock_evaluation": {
            "status": "approved"  # or "rejected"
        }
    },
    "feedback_history": [
        {
            "rework_targets": ["strategy_generate"]  # or ["section_1"]
        }
    ]
}

route = route_after_mock_eval_review(state)
print(f"다음 경로: {route}")
```

---

## ⚙️ 설정 변경

### 평가위원 프로필 커스터마이징
`_create_evaluator_profiles()`의 반환값을 수정:

```python
{
    "evaluation_bias": {
        "tendency": "낙관적",  # 변경
        "scoring_range": (50, 100),  # 변경
        "weight": 1.2  # 변경
    }
}
```

### 분석 임계값 조정
`_assess_consensus()` 함수의 stdev 임계값:

```python
if stdev < 2:  # 기존: 3
    consensus_level = "높음"
```

### 수주 가능성 범위 조정
`_assess_win_probability()` 함수의 점수 범위:

```python
if final_score >= 80:  # 기존: 85
    return "높음"
```

---

## 🐛 디버깅

### 로그 확인
```bash
# 모의평가 에러 로그
grep "mock_evaluation 실패" /var/log/app.log
grep "평가항목 점수 산출 실패" /var/log/app.log
```

### 상태 점검
```python
# state에서 모의평가 결과 확인
result = state.get("mock_evaluation_result", {})
print(result.get("final_score"))
print(result.get("win_probability"))
```

### AI 응답 검증
```python
# JSON 파싱 오류 확인
if "error" in result:
    print(f"AI 오류: {result['error']}")
```

---

## 📋 체크리스트

구현/배포 전 확인 사항:

- [ ] 모든 함수 import 가능 확인
- [ ] 평가위원 6명 프로필 확인
- [ ] 라우팅 4방향 모두 테스트
- [ ] 분포 분석 결과 정확성 확인
- [ ] AI 호출 폴백 동작 확인
- [ ] 에러 처리 확인
- [ ] 그래프 엣지 연결 확인
- [ ] 상태 필드 존재 확인

---

**Version**: v6.0
**Updated**: 2026-03-29
**Author**: Claude Code
