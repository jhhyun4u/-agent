# Design: 프롬프트 강화 (prompt-enhancement)

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | prompt-enhancement |
| 작성일 | 2026-03-08 |
| 기반 Plan | docs/01-plan/features/prompt-enhancement.plan.md |

---

## 1. 변경 파일 목록

| 파일 | 유형 | 변경 내용 |
|------|------|----------|
| `app/services/phase_prompts.py` | 수정 | PHASE3_USER, PHASE4_SYSTEM, PHASE5_USER JSON 스키마 확장 |
| `app/models/phase_schemas.py` | 수정 | Phase3Artifact, Phase5Artifact 신규 필드 추가 |

---

## 2. phase_prompts.py 변경 설계

### 2-1. PHASE3_USER — JSON 스키마 끝에 3개 필드 추가

**추가 위치:** 기존 `"bid_price_strategy"` 필드 바로 다음

```python
    "alternatives_considered": [
        {{
            "approach": "일반적 접근법 또는 경쟁사가 취할 방식 (구체적으로)",
            "our_approach": "우리가 선택한 접근법",
            "why_better": "우리 접근법이 우월한 이유 (정량 근거 또는 사례 포함)"
        }}
    ],
    "risks_mitigations": [
        {{
            "risk": "리스크 설명 (구체적)",
            "probability": "high/medium/low",
            "impact": "high/medium/low",
            "mitigation": "구체적 대응 방안 (선제 조치 포함)"
        }}
    ],
    "implementation_checklist": [
        {{
            "phase": "단계명 (예: 1단계: 착수 및 환경 구성)",
            "duration": "소요 기간 (예: 1~2개월)",
            "deliverables": ["산출물1", "산출물2"],
            "milestones": ["마일스톤1"]
        }}
    ]
```

**추가 지침 문장 (기존 지침 바로 앞에 삽입):**
```
- alternatives_considered: 발주처가 고려할 수 있는 다른 접근법과 우리 방안을 비교하여 우월성을 논증하세요.
- risks_mitigations: 사업 수행 중 발생 가능한 주요 리스크 3~5개와 각각의 대응 방안을 명시하세요.
- implementation_checklist: 사업 전체를 3~5단계로 나눠 단계별 산출물과 마일스톤을 구체적으로 제시하세요.
```

---

### 2-2. PHASE4_SYSTEM — 작성 원칙 3개 추가

**추가 위치:** 기존 마지막 원칙("경쟁사를 직접 언급하지 않되...") 다음 줄

```python
- 대안 비교(Alternatives Considered): 발주처가 고려했을 다른 접근법 대비 우리 방안의 우월성을 자연스럽게 서술하세요.
- 리스크 대응(Risks/Mitigations): 예상 리스크와 선제 대응 방안을 표 또는 항목 형식으로 포함하세요.
- 추진 체계(Implementation Plan): 단계별 산출물과 마일스톤을 체크리스트 형식으로 제시하세요.
```

---

### 2-3. PHASE5_USER — JSON 스키마에 3개 검증 항목 추가

**추가 위치:** `"win_probability"` 필드 바로 앞

```python
    "alternatives_quality": "Alternatives Considered의 설득력 평가 (1~2문장, 비교 근거의 구체성·정량성 기준)",
    "risks_coverage": "Risks/Mitigations의 완성도 평가 (1~2문장, 리스크 식별 범위와 대응 방안 실현 가능성 기준)",
    "checklist_specificity": "Implementation Checklist의 구체성 평가 (1~2문장, 단계별 산출물 명확성 기준)",
```

---

## 3. phase_schemas.py 변경 설계

### 3-1. Phase3Artifact — 3개 필드 추가

```python
class Phase3Artifact(PhaseArtifact):
    # ... 기존 필드 ...
    alternatives_considered: list[dict] = Field(
        default_factory=list,
        description="접근법 대안 비교 (approach, our_approach, why_better)"
    )
    risks_mitigations: list[dict] = Field(
        default_factory=list,
        description="리스크-대응방안 표 (risk, probability, impact, mitigation)"
    )
    implementation_checklist: list[dict] = Field(
        default_factory=list,
        description="단계별 추진 체계 (phase, duration, deliverables, milestones)"
    )
```

### 3-2. Phase5Artifact — 3개 검증 필드 추가

```python
class Phase5Artifact(PhaseArtifact):
    # ... 기존 필드 ...
    alternatives_quality: str = Field(default="", description="대안 비교 설득력 평가")
    risks_coverage: str = Field(default="", description="리스크 대응 완성도 평가")
    checklist_specificity: str = Field(default="", description="추진 체계 구체성 평가")
```

---

## 4. 변경 전후 비교

### Phase3 JSON 스키마 변경

```
변경 전 (11개 필드):
  summary, win_strategy, win_theme, business_understanding_strategy,
  section_plan, page_allocation, team_plan, team_composition,
  procurement_method, estimated_competitor_count,
  differentiation_strategy, bid_price_strategy

변경 후 (14개 필드): +3
  + alternatives_considered
  + risks_mitigations
  + implementation_checklist
```

### Phase5 JSON 스키마 변경

```
변경 전 (10개 필드):
  summary, quality_score, detailed_scores, win_theme_consistency,
  quantitative_metrics_count, issues, win_probability, executive_summary

변경 후 (13개 필드): +3
  + alternatives_quality
  + risks_coverage
  + checklist_specificity
```

---

## 5. 토큰 영향 분석

| Phase | 추가 프롬프트 토큰 (추정) | 추가 출력 토큰 (추정) |
|-------|------------------------|---------------------|
| Phase 3 | ~200 (지침 + 스키마) | ~500 (3개 필드 응답) |
| Phase 4 | ~80 (원칙 3줄) | Phase 4 본문에 내용 반영 (~300) |
| Phase 5 | ~150 (스키마 + 지침) | ~150 (3개 평가 문장) |
| **합계** | **~430** | **~950** |

총 ~1,400 토큰 증가 — `max_output_tokens: 16,000` 대비 무시 가능.

---

## 6. 하위 호환성

- Phase3Artifact 신규 필드 모두 `default_factory=list` — 기존 세션 복원 시 빈 리스트로 초기화, 오류 없음
- Phase5Artifact 신규 필드 모두 `default=""` — 하위 호환 보장
- `extra="ignore"` 설정(`app/config.py`) 덕분에 구버전 DB artifact_json에 신규 필드가 없어도 오류 없음

---

## 7. 구현 순서

```
Step 1: app/models/phase_schemas.py
  - Phase3Artifact: alternatives_considered, risks_mitigations, implementation_checklist 추가
  - Phase5Artifact: alternatives_quality, risks_coverage, checklist_specificity 추가

Step 2: app/services/phase_prompts.py
  - PHASE3_USER: JSON 스키마에 3개 필드 + 작성 지침 추가
  - PHASE4_SYSTEM: 작성 원칙 3줄 추가
  - PHASE5_USER: JSON 스키마에 3개 검증 항목 추가
```

---

## 8. 성공 기준

| 기준 | 검증 방법 |
|------|----------|
| Phase3Artifact에 3개 신규 필드 존재 | `Phase3Artifact.model_fields` 확인 |
| PHASE3_USER에 `alternatives_considered` 키워드 존재 | `grep alternatives_considered phase_prompts.py` |
| PHASE4_SYSTEM에 대안 비교 원칙 존재 | `grep alternatives phase_prompts.py` |
| PHASE5_USER에 3개 검증 항목 존재 | `grep alternatives_quality phase_prompts.py` |
| 기존 테스트 통과 | `uv run pytest` |
