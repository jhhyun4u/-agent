# Plan: 제안서 품질 강화 v3 (proposal-quality-v3)

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-quality-v3 |
| 작성일 | 2026-03-08 |
| 우선순위 | High |
| 참조 | travisjneuman/.claude — battle-card-builder, research-presenter SKILL.md |
| 대상 파일 | `app/services/phase_prompts.py`, `app/models/phase_schemas.py` |

---

## 1. 핵심 문제

Battle Card Builder + Research Presenter SKILL.md 분석에서 발견한 3가지 누락 요소:

| 누락 요소 | 현재 상태 | 영향 |
|---------|----------|------|
| **Assertion-based section titles** | 섹션명이 토픽 레이블 ("사업 이해도") — 주장 없음 | 평가위원이 섹션을 열기 전에 핵심 메시지를 인식 불가 |
| **Narrative Arc** | 본문 작성 원칙에 구조적 스토리텔링 지침 없음 | 사실 나열식 서술 → 설득력 부족 |
| **Objection Handling** | 반론 선제 대응 필드 없음 | 평가위원의 의구심을 제안서에서 해소하지 못함 |

---

## 2. 개선 목표

| 목표 | 측정 기준 |
|------|----------|
| Phase 4 섹션 제목이 주장형 문장으로 생성됨 | PHASE4_SYSTEM에 assertion title 원칙 존재 |
| 각 섹션이 Setup→Confrontation→Resolution 구조로 작성됨 | PHASE4_SYSTEM에 narrative arc 지침 존재 |
| Phase 3 output에 `objection_responses` 필드 포함 | Phase3Artifact에 필드 존재 여부 |

---

## 3. 현재 구조 분석

### PHASE4_SYSTEM 현재 원칙 (line 197-206)

9개 원칙 존재. 섹션 제목 작성 방식 지침 없음. 스토리텔링 구조 지침 없음. 반론 대응 지침 없음.

### Phase3Artifact 현재 필드

`alternatives_considered`, `risks_mitigations`, `implementation_checklist`, `logic_model` — 반론 대응 필드 없음.

---

## 4. 변경 계획 (YAGNI 검토 후)

### 4-1. Assertion-based Section Titles

**변경 대상:** PHASE4_SYSTEM (원칙 1줄 추가)

```
- 섹션 제목(Assertion Title): 토픽 레이블("사업 이해도") 대신 핵심 주장 문장("X 현황의 Y 문제를 Z 방법으로 W% 개선")으로 작성하세요. 평가위원이 제목만으로 우리의 핵심 가치를 인식하게 합니다.
```

### 4-2. Narrative Arc (스토리텔링 구조)

**변경 대상:** PHASE4_SYSTEM (원칙 1줄 추가)

```
- 내러티브 구조(Narrative Arc): 각 섹션을 ①문제 제기(Setup: 발주처가 처한 현실) → ②긴장감 고조(Confrontation: 미해결 시 결과) → ③해결책 제시(Resolution: 우리 방안의 효과)의 3단계로 서술하세요.
```

### 4-3. Objection Handling (반론 선제 대응)

**Phase3Artifact 추가 필드:**
```python
objection_responses: list[dict] = Field(
    default_factory=list,
    description="평가위원 예상 반론 및 선제 대응 (objection/acknowledge/response/evidence)"
)
```

**PHASE3_USER JSON 추가 필드** (`logic_model` 다음):
```json
"objection_responses": [
    {
        "objection": "평가위원이 가질 수 있는 예상 반론 (구체적, 예: '경험 부족')",
        "acknowledge": "이 우려가 타당한 이유를 인정하는 표현 (1문장)",
        "response": "우리의 대응 논리 (Challenger 방식: 새로운 관점 제시)",
        "evidence": "정량 근거 1~2개 (수치, 사례, 레퍼런스)"
    }
]
```

**추가 지침:**
```
- objection_responses: 평가위원이 가질 수 있는 주요 반론 3~5개를 Acknowledge→Response→Evidence 구조로 선제 대응하세요.
```

**PHASE4_SYSTEM 추가 원칙:**
```
- 반론 선제 대응(Objection Handling): Phase 3의 objection_responses를 활용하여 평가위원이 가질 우려를 본문 곳곳에서 자연스럽게 해소하세요.
```

---

## 5. YAGNI 검토

### v3 포함 (필수)
- PHASE4_SYSTEM: Assertion Title 원칙 1줄
- PHASE4_SYSTEM: Narrative Arc 원칙 1줄
- Phase3Artifact: `objection_responses` 필드 추가
- PHASE3_USER: `objection_responses` JSON 스키마 + 지침
- PHASE4_SYSTEM: Objection Handling 원칙 1줄

### v4 이후 (보류)
- Blue Ocean 관점 (Phase 3 differentiation_strategy 확장)
- 3-year TCO 비교 (bid_price_strategy 확장)
- Challenger Sale 교육적 접근 (Phase 4 사업 이해도 섹션 심화)

---

## 6. 성공 기준

| 기준 | 검증 방법 |
|------|----------|
| PHASE4_SYSTEM에 "Assertion Title" 존재 | `grep "Assertion Title" phase_prompts.py` |
| PHASE4_SYSTEM에 "Narrative Arc" 존재 | `grep "Narrative Arc" phase_prompts.py` |
| PHASE3_USER에 `objection_responses` 존재 | `grep objection_responses phase_prompts.py` |
| Phase3Artifact에 `objection_responses` 필드 존재 | `Phase3Artifact.model_fields` 확인 |
| 기존 unit 테스트 통과 | `uv run pytest --ignore=tests/integration --ignore=tests/api` |

---

## 7. 토큰 영향 분석

| Phase | 추가 프롬프트 토큰 | 추가 출력 토큰 |
|-------|-----------------|--------------|
| Phase 3 | ~120 (objection 스키마 + 지침) | ~350 (반론 3~5개) |
| Phase 4 | ~60 (원칙 3줄) | ~250 (본문 반론 대응 반영) |
| **합계** | **~180** | **~600** |

누적 (v1+v2+v3): 프롬프트 ~790, 출력 ~2,150 — max_output_tokens: 16,000 대비 허용 범위.

---

## 8. 변경 파일 목록

| 순서 | 파일 | 작업 |
|------|------|------|
| 1 | `app/models/phase_schemas.py` | Phase3Artifact에 `objection_responses` 추가 |
| 2 | `app/services/phase_prompts.py` | PHASE3_USER `objection_responses` JSON + 지침 |
| 3 | `app/services/phase_prompts.py` | PHASE4_SYSTEM Assertion Title 원칙 추가 |
| 4 | `app/services/phase_prompts.py` | PHASE4_SYSTEM Narrative Arc 원칙 추가 |
| 5 | `app/services/phase_prompts.py` | PHASE4_SYSTEM Objection Handling 원칙 추가 |

---

## 9. 다음 단계

```
/pdca design proposal-quality-v3
```
