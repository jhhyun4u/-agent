# Design: 제안서 품질 강화 v3 (proposal-quality-v3)

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-quality-v3 |
| 작성일 | 2026-03-08 |
| 기반 Plan | docs/01-plan/features/proposal-quality-v3.plan.md |

---

## 1. 변경 파일 목록

| 파일 | 유형 | 변경 내용 |
|------|------|----------|
| `app/models/phase_schemas.py` | 수정 | Phase3Artifact에 `objection_responses` 필드 추가 |
| `app/services/phase_prompts.py` | 수정 | PHASE3_USER `objection_responses` JSON + 지침, PHASE4_SYSTEM 원칙 3줄 추가 |

---

## 2. phase_schemas.py 변경 설계

### Phase3Artifact — `objection_responses` 필드 추가

**추가 위치:** `logic_model` 필드 다음

```python
    objection_responses: list[dict] = Field(
        default_factory=list,
        description="평가위원 예상 반론 및 선제 대응 (objection/acknowledge/response/evidence)"
    )
```

---

## 3. phase_prompts.py 변경 설계

### 3-1. PHASE3_USER — `objection_responses` 필드 추가

**추가 위치:** `logic_model` 닫는 `}}` 다음, 최종 `}}` 앞

```python
    "objection_responses": [
        {{
            "objection": "평가위원이 가질 수 있는 예상 반론 (구체적, 예: '경험 부족' '가격 고가' '일정 촉박')",
            "acknowledge": "이 우려가 타당한 이유를 인정하는 표현 (1문장, 신뢰 구축용)",
            "response": "우리의 대응 논리 (새로운 관점 제시, 기존 전제를 뒤집는 방식)",
            "evidence": "정량 근거 1~2개 (수치, 유사 사례, 인증·레퍼런스)"
        }}
    ]
```

**추가 지침 (기존 지침 끝에 삽입):**
```
- objection_responses: 평가위원이 가질 수 있는 주요 반론 3~5개를 Acknowledge→Response→Evidence 구조로 선제 대응하세요.
```

---

### 3-2. PHASE4_SYSTEM — 원칙 3줄 추가

**추가 위치:** line 206 `Logic Model 표` 원칙 다음

```python
- 섹션 제목(Assertion Title): 토픽 레이블("사업 이해도") 대신 핵심 주장 문장("X 현황의 Y 문제를 Z 방법으로 W% 개선")으로 작성하세요. 평가위원이 제목만으로 핵심 가치를 인식하게 합니다.
- 내러티브 구조(Narrative Arc): 각 섹션을 ①문제 제기(발주처가 처한 현실) → ②긴장감 고조(미해결 시 결과) → ③해결책 제시(우리 방안의 효과) 3단계로 서술하세요.
- 반론 선제 대응(Objection Handling): Phase 3의 objection_responses를 활용하여 평가위원이 가질 우려를 본문 곳곳에서 자연스럽게 해소하세요.
```

---

## 4. 변경 전후 비교

### Phase3Artifact 필드 변화

```
변경 전 (15개 필드): ... logic_model
변경 후 (16개 필드): +1
  + objection_responses
```

### PHASE3_USER 최상위 필드 변화

```
변경 전 (15개 필드): ... logic_model
변경 후 (16개 필드): +1
  + objection_responses
```

### PHASE4_SYSTEM 원칙 변화

```
변경 전 (9개 원칙): ... Logic Model 표
변경 후 (12개 원칙): +3
  + 섹션 제목(Assertion Title)
  + 내러티브 구조(Narrative Arc)
  + 반론 선제 대응(Objection Handling)
```

---

## 5. 토큰 영향 분석

| Phase | 추가 프롬프트 토큰 | 추가 출력 토큰 |
|-------|-----------------|--------------|
| Phase 3 | ~120 (objection 스키마 + 지침 1줄) | ~350 (반론 3~5개) |
| Phase 4 | ~60 (원칙 3줄) | ~250 (본문 반론 대응 + 제목 변경) |
| **합계** | **~180** | **~600** |

---

## 6. 하위 호환성

- `objection_responses: list[dict] = Field(default_factory=list)` — 기존 세션 복원 시 빈 리스트
- `extra="ignore"` 설정으로 구버전 artifact_json 오류 없음

---

## 7. 구현 순서

```
Step 1: app/models/phase_schemas.py
  - Phase3Artifact: objection_responses 필드 추가 (logic_model 다음)

Step 2: app/services/phase_prompts.py
  - PHASE3_USER: objection_responses JSON 필드 추가 (logic_model }} 다음)
  - PHASE3_USER: 작성 지침 1줄 추가
  - PHASE4_SYSTEM: Assertion Title 원칙 추가 (Logic Model 표 다음)
  - PHASE4_SYSTEM: Narrative Arc 원칙 추가
  - PHASE4_SYSTEM: Objection Handling 원칙 추가
```

---

## 8. 성공 기준

| 기준 | 검증 방법 |
|------|----------|
| Phase3Artifact에 `objection_responses` 필드 존재 | `uv run python -c "from app.models.phase_schemas import Phase3Artifact; print('objection_responses' in Phase3Artifact.model_fields)"` |
| PHASE3_USER에 `objection_responses` 키워드 존재 | `grep objection_responses app/services/phase_prompts.py` |
| PHASE4_SYSTEM에 `Assertion Title` 존재 | `grep "Assertion Title" app/services/phase_prompts.py` |
| PHASE4_SYSTEM에 `Narrative Arc` 존재 | `grep "Narrative Arc" app/services/phase_prompts.py` |
| PHASE4_SYSTEM에 `Objection Handling` 존재 | `grep "Objection Handling" app/services/phase_prompts.py` |
| unit 테스트 통과 | `uv run pytest --ignore=tests/integration --ignore=tests/api` |
