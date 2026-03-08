# Plan: 제안서 품질 강화 v4 (proposal-quality-v4)

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-quality-v4 |
| 작성일 | 2026-03-08 |
| 우선순위 | High |
| 참조 | travisjneuman/.claude — investment-memo-generator, monetization-strategy, contract-redliner SKILL.md |
| 대상 파일 | `app/services/phase_prompts.py` 만 (스키마 변경 불필요) |

---

## 1. 핵심 문제

| 누락 요소 | 현재 상태 | 영향 |
|---------|----------|------|
| **Scenario Pricing** | bid_price_strategy에 단일 추천가만 존재 | 경쟁 상황 변화에 대응하는 가격 유연성 부재 |
| **Value-based Pricing** | 원가 대비 비율만 계산, 발주처 인지 가치 미반영 | 가격 논리가 "싸게 할게요" 수준에 머묾 |
| **Risk Score 숫자화** | probability/impact가 high/medium/low 텍스트 | 리스크 우선순위 비교가 주관적, 설득력 부족 |
| **Price Anchoring** | Phase 4 가격 제시 원칙 없음 | 발주처가 가격을 먼저 인식 → 가치보다 비용에 집중 |

---

## 2. 변경 계획

### 2-1. bid_price_strategy — 시나리오화 + 가치 기반 논리 추가

```json
"bid_price_strategy": {
  "value_basis": "발주처가 이 사업에서 인지하는 핵심 가치 (정량적 효과 추정, 예: 업무 효율 30% 향상 = 연 X억 절감)",
  "scenarios": {
    "bear": { "price_ratio": "85%", "condition": "경쟁사 3개 이상, 가격 경쟁 심화 시" },
    "base": { "price_ratio": "88%", "condition": "일반적 경쟁 환경 (기본 추천)" },
    "bull": { "price_ratio": "92%", "condition": "경쟁사 1~2개, 기술 차별성 확보 시" }
  },
  "recommended_scenario": "base",
  "rationale": "추천 시나리오 선택 이유 (경쟁 분석 기반, 3문장)",
  "price_competitiveness_message": "가격 경쟁력 어필 방식 (가치 대비 합리적 투자로 포지셔닝)"
}
```

### 2-2. risks_mitigations — 숫자 점수화

```json
"risks_mitigations": [{
  "risk": "리스크 설명",
  "probability": 3,       // 1(매우 낮음)~5(매우 높음)
  "impact": 4,            // 1(경미)~5(치명적)
  "risk_score": 12,       // probability × impact (자동 계산)
  "priority": "high",     // 20-25:critical, 12-19:high, 6-11:medium, 1-5:low
  "mitigation": "대응 방안"
}]
```

### 2-3. PHASE4_SYSTEM — Price Anchoring 원칙 추가

```
- 가격 앵커링(Price Anchoring): 가격을 언급하기 전에 먼저 사업의 기대 ROI와 가치를 제시하여, 발주처가 비용이 아닌 투자 효과의 관점에서 가격을 인식하게 하세요.
```

---

## 3. YAGNI 검토

### v4 포함
- PHASE3_USER: `bid_price_strategy` 구조 확장 (value_basis + scenarios)
- PHASE3_USER: `risks_mitigations` 숫자화 (probability/impact 1-5 + risk_score + priority)
- PHASE3_USER: 지침 2줄 추가
- PHASE4_SYSTEM: Price Anchoring 원칙 1줄

### 보류
- Phase 2 price_analysis에 perceived_value 추가 → Phase 3에서 직접 도출하면 Phase 2 변경 불필요
- phase_schemas.py 변경 → bid_price_strategy/risks_mitigations 이미 dict/list[dict] 타입, 구조적 변경 불필요

---

## 4. 성공 기준

| 기준 | 검증 방법 |
|------|----------|
| PHASE3_USER bid_price_strategy에 `value_basis` 존재 | `grep value_basis phase_prompts.py` |
| PHASE3_USER bid_price_strategy에 `scenarios` 존재 | `grep scenarios phase_prompts.py` |
| PHASE3_USER risks_mitigations에 `risk_score` 존재 | `grep risk_score phase_prompts.py` |
| PHASE4_SYSTEM에 `Price Anchoring` 존재 | `grep "Price Anchoring" phase_prompts.py` |
| unit 테스트 통과 | `uv run pytest --ignore=tests/integration --ignore=tests/api` |
