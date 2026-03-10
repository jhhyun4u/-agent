# Design: 제안서 품질 강화 v2 (proposal-quality-v2)

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-quality-v2 |
| 작성일 | 2026-03-08 |
| 기반 Plan | docs/01-plan/features/proposal-quality-v2.plan.md |

---

## 1. 변경 파일 목록

| 파일 | 유형 | 변경 내용 |
|------|------|----------|
| `app/models/phase_schemas.py` | 수정 | Phase3Artifact에 `logic_model` 필드 추가 |
| `app/services/phase_prompts.py` | 수정 | PHASE3_USER section_plan 구조 확장 + `logic_model` 필드 추가 + PHASE4_SYSTEM 원칙 추가 |

---

## 2. phase_schemas.py 변경 설계

### Phase3Artifact — `logic_model` 필드 추가

**추가 위치:** `implementation_checklist` 필드(line 82) 다음

```python
    logic_model: dict = Field(
        default_factory=dict,
        description="사업 논리 모델 (inputs→activities→outputs→단기성과→장기성과)"
    )
```

---

## 3. phase_prompts.py 변경 설계

### 3-1. PHASE3_USER — section_plan 항목에 2개 필드 추가

**추가 위치:** line 126 `"win_theme_alignment"` 값 바로 다음 줄 (line 127 `}}` 앞)

```python
            "target_criteria": "이 섹션이 공략하는 평가항목명 (Phase 2 evaluation_weights와 매핑, 예: 기술 이해도)",
            "score_weight": 40
```

**변경 전 (line 115-128):**
```python
    "section_plan": [
        {{
            "section": "사업 이해도",
            "approach": "작성 접근 방법",
            "page_limit": 5,
            "priority": "high",
            "evaluator_check_points": [
                "평가위원이 이 섹션에서 확인하는 항목 1",
                "확인 항목 2",
                "확인 항목 3"
            ],
            "win_theme_alignment": "이 섹션이 Win Theme과 연결되는 방식"
        }}
    ],
```

**변경 후:**
```python
    "section_plan": [
        {{
            "section": "사업 이해도",
            "approach": "작성 접근 방법",
            "page_limit": 5,
            "priority": "high",
            "evaluator_check_points": [
                "평가위원이 이 섹션에서 확인하는 항목 1",
                "확인 항목 2",
                "확인 항목 3"
            ],
            "win_theme_alignment": "이 섹션이 Win Theme과 연결되는 방식",
            "target_criteria": "이 섹션이 공략하는 평가항목명 (Phase 2 evaluation_weights와 매핑, 예: 기술 이해도)",
            "score_weight": 40
        }}
    ],
```

---

### 3-2. PHASE3_USER — `logic_model` 필드 추가

**추가 위치:** line 169 `implementation_checklist` 배열 닫는 `}}` 다음 줄, 최종 `}}` 바로 앞

```python
    "logic_model": {{
        "inputs": ["투입 자원1 (전문 인력, 기술 스택, 인프라 등)", "투입 자원2"],
        "activities": ["핵심 수행 활동1 (구체적 작업 내용)", "활동2"],
        "outputs": ["직접 산출물1 (시스템, 보고서, 교육 결과물 등)", "산출물2"],
        "short_term_outcomes": ["6개월~1년 내 측정 가능한 기대 성과 (수치 포함)", "성과2"],
        "long_term_outcomes": ["2~3년 장기 효과 (사회·행정적 임팩트)", "효과2"]
    }}
```

**추가 지침 문장 (기존 작성 지침 끝에 삽입):**

```
- target_criteria / score_weight: Phase 2 evaluation_weights의 항목명을 각 섹션에 정확히 매핑하고 배점을 기입하세요.
- logic_model: 투입→활동→산출→단기성과→장기성과 인과 체계를 명확히 제시하세요. 단기/장기성과에는 측정 가능한 수치를 포함하세요.
```

---

### 3-3. PHASE4_SYSTEM — Logic Model 표 원칙 추가

**추가 위치:** line 194 마지막 원칙(`- 추진 체계(Implementation Plan)...`) 다음 줄

```python
- Logic Model 표: inputs→activities→outputs→단기성과→장기성과 구조의 표를 사업 이해도 섹션에 포함하여 투자 효과의 인과관계를 시각화하세요.
```

---

## 4. 변경 전후 비교

### Phase3Artifact 필드 변화

```
변경 전 (14개 필드):
  phase_num, phase_name, summary, structured_data, token_count, created_at,
  rfp_data, history_summary, g2b_competitor_data → (상속)
  key_requirements... (Phase2 아님)
  win_strategy, section_plan, page_allocation, team_plan, differentiation_strategy,
  bid_price_strategy, win_theme, alternatives_considered, bid_calculation,
  alternatives_considered, risks_mitigations, implementation_checklist

변경 후 (15개 필드): +1
  + logic_model
```

### PHASE3_USER section_plan 변화

```
변경 전 (6개 키):
  section, approach, page_limit, priority, evaluator_check_points, win_theme_alignment

변경 후 (8개 키): +2
  + target_criteria
  + score_weight
```

### PHASE3_USER 최상위 필드 변화

```
변경 전 (14개 필드):
  summary → ... → implementation_checklist

변경 후 (15개 필드): +1
  + logic_model
```

### PHASE4_SYSTEM 원칙 변화

```
변경 전 (8개 원칙):
  ...평가위원 심리 원칙 5개 + 대안비교 + 리스크대응 + 추진체계

변경 후 (9개 원칙): +1
  + Logic Model 표
```

---

## 5. 토큰 영향 분석

| Phase | 추가 프롬프트 토큰 | 추가 출력 토큰 |
|-------|-----------------|--------------|
| Phase 3 | ~150 (section_plan 2필드 + logic_model 스키마 + 지침 2줄) | ~400 (logic_model 5항목 + section_plan 확장) |
| Phase 4 | ~30 (원칙 1줄) | ~200 (Logic Model 표 본문 반영) |
| **합계** | **~180** | **~600** |

총 ~780 토큰 증가 — `max_output_tokens: 16,000` 대비 허용 범위 내.

---

## 6. 하위 호환성

- `logic_model: dict = Field(default_factory=dict)` — 기존 세션 복원 시 빈 dict, 오류 없음
- `section_plan`은 프롬프트 출력 구조이므로 스키마 변경 없음 (Phase3Artifact의 `section_plan: list[dict]` 그대로)
- `extra="ignore"` 덕분에 구버전 artifact_json에 신규 필드 없어도 오류 없음

---

## 7. 구현 순서

```
Step 1: app/models/phase_schemas.py
  - Phase3Artifact: logic_model 필드 추가 (implementation_checklist 다음)

Step 2: app/services/phase_prompts.py
  - PHASE3_USER: section_plan 항목에 target_criteria, score_weight 추가
  - PHASE3_USER: logic_model 최상위 필드 추가 (implementation_checklist 닫는 }} 다음)
  - PHASE3_USER: 작성 지침 2줄 추가
  - PHASE4_SYSTEM: Logic Model 표 원칙 1줄 추가
```

---

## 8. 성공 기준

| 기준 | 검증 방법 |
|------|----------|
| Phase3Artifact에 `logic_model` 필드 존재 | `uv run python -c "from app.models.phase_schemas import Phase3Artifact; print('logic_model' in Phase3Artifact.model_fields)"` |
| PHASE3_USER section_plan에 `target_criteria` 존재 | `grep target_criteria app/services/phase_prompts.py` |
| PHASE3_USER에 `logic_model` 키워드 존재 | `grep logic_model app/services/phase_prompts.py` |
| PHASE4_SYSTEM에 `Logic Model` 원칙 존재 | `grep "Logic Model" app/services/phase_prompts.py` |
| 기존 테스트 통과 | `uv run pytest` |
