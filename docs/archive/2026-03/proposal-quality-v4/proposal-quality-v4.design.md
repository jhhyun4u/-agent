# Design: 제안서 품질 강화 v4 (proposal-quality-v4)

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-quality-v4 |
| 작성일 | 2026-03-08 |
| 기반 Plan | docs/01-plan/features/proposal-quality-v4.plan.md |

---

## 1. 변경 파일

| 파일 | 유형 | 변경 |
|------|------|------|
| `app/services/phase_prompts.py` | 수정 | PHASE3_USER 2개 필드 구조 변경 + 지침 2줄 + PHASE4_SYSTEM 원칙 1줄 |

phase_schemas.py 변경 없음 — `bid_price_strategy: dict`, `risks_mitigations: list[dict]` 타입이 이미 임의 구조 허용.

---

## 2. PHASE3_USER 변경 설계

### 2-1. bid_price_strategy 구조 교체

**변경 전 (line 144-148):**
```python
    "bid_price_strategy": {{
        "recommended_price_ratio": "예산 대비 추천 입찰가 비율 (예: 88%)",
        "rationale": "이 입찰가를 추천하는 이유 (기술-가격 트레이드오프, 경쟁 예상 가격 포함, 3문장)",
        "price_competitiveness_message": "제안서 본문에서 가격 경쟁력을 어필하는 방식 (1~2문장)"
    }},
```

**변경 후:**
```python
    "bid_price_strategy": {{
        "value_basis": "발주처가 이 사업에서 인지하는 핵심 가치 (정량적 효과 추정, 예: 업무 효율 30% 향상 = 연 X억 절감)",
        "scenarios": {{
            "bear": {{"price_ratio": "85%", "condition": "경쟁사 3개 이상, 가격 경쟁 심화 시"}},
            "base": {{"price_ratio": "88%", "condition": "일반적 경쟁 환경 (기본 추천)"}},
            "bull": {{"price_ratio": "92%", "condition": "경쟁사 1~2개, 기술 차별성 확보 시"}}
        }},
        "recommended_scenario": "base",
        "rationale": "추천 시나리오 선택 이유 (경쟁 분석 기반, 3문장)",
        "price_competitiveness_message": "가격 경쟁력 어필 방식 (가치 대비 합리적 투자로 포지셔닝)"
    }},
```

### 2-2. risks_mitigations 구조 교체

**변경 전 (line 156-163):**
```python
    "risks_mitigations": [
        {{
            "risk": "사업 수행 중 발생 가능한 리스크 (구체적)",
            "probability": "high/medium/low",
            "impact": "high/medium/low",
            "mitigation": "구체적 선제 대응 방안"
        }}
    ],
```

**변경 후:**
```python
    "risks_mitigations": [
        {{
            "risk": "사업 수행 중 발생 가능한 리스크 (구체적)",
            "probability": 3,
            "impact": 4,
            "risk_score": 12,
            "priority": "high",
            "mitigation": "구체적 선제 대응 방안"
        }}
    ],
```

### 2-3. 작성 지침 2줄 추가 (기존 지침 끝에)

```
- bid_price_strategy: value_basis에 발주처 인지 가치를 정량화하고, 경쟁 시나리오에 따라 bear/base/bull 3개 입찰가를 제시하세요.
- risks_mitigations: probability(1-5) × impact(1-5) = risk_score를 계산하고, 20-25:critical / 12-19:high / 6-11:medium / 1-5:low로 priority를 기입하세요.
```

---

## 3. PHASE4_SYSTEM 변경 설계

**추가 위치:** `반론 선제 대응(Objection Handling)` 원칙 다음 줄

```python
- 가격 앵커링(Price Anchoring): 가격을 언급하기 전에 먼저 사업의 기대 ROI와 가치를 제시하여, 발주처가 비용이 아닌 투자 효과의 관점에서 가격을 인식하게 하세요.
```

---

## 4. 변경 전후 비교

### PHASE3_USER 필드 변화

```
bid_price_strategy 키 변화:
  전: recommended_price_ratio, rationale, price_competitiveness_message (3개)
  후: value_basis, scenarios(bear/base/bull), recommended_scenario, rationale, price_competitiveness_message (6개)

risks_mitigations 아이템 키 변화:
  전: risk, probability(텍스트), impact(텍스트), mitigation (4개)
  후: risk, probability(숫자1-5), impact(숫자1-5), risk_score, priority, mitigation (6개)
```

### PHASE4_SYSTEM 원칙 변화

```
전: 12개 원칙
후: 13개 원칙 (+Price Anchoring)
```

---

## 5. 성공 기준

| 기준 | 검증 방법 |
|------|----------|
| `value_basis` 키워드 | `grep value_basis phase_prompts.py` |
| `scenarios` 키워드 | `grep '"scenarios"' phase_prompts.py` |
| `risk_score` 키워드 | `grep risk_score phase_prompts.py` |
| `Price Anchoring` 키워드 | `grep "Price Anchoring" phase_prompts.py` |
| unit 테스트 통과 | `uv run pytest --ignore=tests/integration --ignore=tests/api` |
