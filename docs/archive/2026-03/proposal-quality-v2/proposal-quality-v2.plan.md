# Plan: 제안서 품질 강화 v2 (proposal-quality-v2)

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-quality-v2 |
| 작성일 | 2026-03-08 |
| 우선순위 | High |
| 참조 | travisjneuman/claude-grant-proposal-builder SKILL.md 분석 |
| 대상 파일 | `app/services/phase_prompts.py`, `app/models/phase_schemas.py` |

---

## 1. 핵심 문제

Grant Proposal Builder SKILL.md 분석에서 발견한 2가지 고가치 누락 요소:

| 누락 요소 | 현재 상태 | 영향 |
|---------|----------|------|
| **평가항목-섹션 매핑** | section_plan에 `evaluator_check_points`만 있음 (어떤 평가항목 공략인지 연결 없음) | 섹션 작성 시 평가 배점과 연계가 없어 전략적 집중도 부족 |
| **Logic Model** | win_strategy에 효과 서술 있지만 인과 논리 체계 없음 | 발주처가 "투자→효과" 연결고리를 한눈에 볼 수 없음 |

---

## 2. 개선 목표

| 목표 | 측정 기준 |
|------|----------|
| section_plan 각 섹션이 어떤 평가항목을 공략하는지 명시 | Phase 3 output의 section_plan에 `target_criteria`, `score_weight` 포함 |
| Phase 3 output에 inputs→activities→outputs→outcomes 구조의 Logic Model 포함 | `logic_model` 필드 존재 여부 |
| Phase 4 본문에 Logic Model 표 반영 | PHASE4_SYSTEM에 Logic Model 원칙 추가 |

---

## 3. 현재 구조 분석

### section_plan 현재 필드 (PHASE3_USER line 115-128)

```json
{
  "section": "사업 이해도",
  "approach": "작성 접근 방법",
  "page_limit": 5,
  "priority": "high",
  "evaluator_check_points": ["확인 항목 1", "확인 항목 2"],
  "win_theme_alignment": "Win Theme 연결 방식"
}
```

**문제:** `evaluator_check_points`는 평가위원이 보는 항목이지만, Phase 2의 `evaluation_weights`(평가 배점표)와 연결되지 않음.

### Phase 2 evaluation_weights (이미 생성되는 데이터)

Phase 2 Artifact에 `evaluation_weights: dict`가 있고, Phase 3 프롬프트에 전달됨.
이 데이터를 Phase 3 section_plan에서 명시적으로 연결하는 구조가 없음.

---

## 4. 변경 계획 (YAGNI 검토 후)

### 4-1. 평가항목-섹션 매핑 — section_plan 구조 확장

**변경 대상:** PHASE3_USER JSON 스키마의 section_plan 항목

```json
// 추가 필드
{
  "target_criteria": "이 섹션이 공략하는 평가항목명 (예: 기술 이해도, 수행 방법론)",
  "score_weight": 40
}
```

**추가 지침:**
```
- target_criteria: Phase 2에서 분석된 evaluation_weights의 항목명을 정확히 매핑하세요.
- score_weight: 해당 평가항목의 배점을 기입하여 집필 우선순위를 명확히 하세요.
```

### 4-2. Logic Model — 새 최상위 필드 추가

**변경 대상:** PHASE3_USER JSON 스키마 끝 + PHASE4_SYSTEM

```json
"logic_model": {
  "inputs": ["투입 자원1 (예: 전문 인력 N명, 기술 스택)", "투입 자원2"],
  "activities": ["핵심 활동1 (구체적 수행 내용)", "핵심 활동2"],
  "outputs": ["직접 산출물1 (예: 시스템 구축, 보고서)", "산출물2"],
  "short_term_outcomes": ["6개월~1년 내 기대 성과 (측정 가능한 수치 포함)", "성과2"],
  "long_term_outcomes": ["2~3년 장기 효과 (사회·행정적 임팩트)", "효과2"]
}
```

**PHASE4_SYSTEM 추가 원칙:**
```
- Logic Model 표: inputs→activities→outputs→단기성과→장기성과 구조의 표를 사업 이해도 섹션에 포함하세요.
```

---

## 5. YAGNI 검토

### v2 포함 (필수)
- section_plan에 `target_criteria`, `score_weight` 추가
- Phase 3에 `logic_model` 최상위 필드 추가
- PHASE4_SYSTEM에 Logic Model 표 원칙 1줄 추가
- Phase3Artifact에 `logic_model: dict` 필드 추가

### v3 이후 (보류)
- SMART 목표 (`smart_objectives` 필드): section_plan의 approach로 현재도 처리 가능
- Needs Assessment 별도 수치화 지침: PHASE4_SYSTEM에 이미 "정량 지표 최소 2개" 원칙 존재
- Rejection Prevention 필드: Phase 5 issues 리스트로 이미 커버

---

## 6. 성공 기준

| 기준 | 검증 방법 |
|------|----------|
| PHASE3_USER section_plan에 `target_criteria` 존재 | `grep target_criteria phase_prompts.py` |
| PHASE3_USER에 `logic_model` 키워드 존재 | `grep logic_model phase_prompts.py` |
| PHASE4_SYSTEM에 Logic Model 원칙 존재 | `grep "Logic Model" phase_prompts.py` |
| Phase3Artifact에 `logic_model` 필드 존재 | `Phase3Artifact.model_fields` 확인 |
| 기존 테스트 통과 | `uv run pytest` |

---

## 7. 토큰 영향 분석

| Phase | 추가 프롬프트 토큰 (추정) | 추가 출력 토큰 (추정) |
|-------|------------------------|---------------------|
| Phase 3 | ~150 (section_plan 확장 + logic_model 스키마) | ~400 (logic_model 5개 항목) |
| Phase 4 | ~30 (원칙 1줄) | ~200 (본문 표 반영) |
| **합계** | **~180** | **~600** |

총 ~780 토큰 증가 — `max_output_tokens: 16,000` 대비 허용 범위 내.

---

## 8. 변경 파일 목록

| 순서 | 파일 | 작업 |
|------|------|------|
| 1 | `app/models/phase_schemas.py` | Phase3Artifact에 `logic_model: dict` 추가 |
| 2 | `app/services/phase_prompts.py` | PHASE3_USER section_plan에 2개 필드 추가 |
| 3 | `app/services/phase_prompts.py` | PHASE3_USER 끝에 `logic_model` 필드 추가 + 지침 |
| 4 | `app/services/phase_prompts.py` | PHASE4_SYSTEM에 Logic Model 원칙 1줄 추가 |

---

## 9. 다음 단계

```
/pdca design proposal-quality-v2
```
