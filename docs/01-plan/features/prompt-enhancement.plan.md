# Plan: 프롬프트 강화 (prompt-enhancement)

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | prompt-enhancement |
| 작성일 | 2026-03-08 |
| 우선순위 | High |
| 참조 | foreline/js-editor proposal-writer SKILL.md 분석 |
| 대상 파일 | `app/services/phase_prompts.py`, `app/prompts/proposal.py` |

---

## 1. 핵심 문제

현재 Phase 3(전략)과 Phase 5(검증) 프롬프트에 **3가지 고품질 제안서 요소**가 누락됨:

| 누락 요소 | 현재 상태 | 영향 |
|---------|----------|------|
| **Alternatives Considered** | Phase 3에 차별화 포인트만 있음 (경쟁사 비교 없음) | 발주처 입장에서 우리 접근법의 우월성 논증 부족 |
| **Risks/Mitigations 표** | Phase 5 issues 리스트만 있음 (대응 방안 비구조화) | 리스크 인식 + 선제 대응 능력을 평가위원에게 증명 불가 |
| **Implementation Checklist** | Phase 3 section_plan에 체크리스트 없음 | 제안서 추진 단계별 구체성 부족 |

---

## 2. 개선 목표

| 목표 | 측정 기준 |
|------|----------|
| 제안서에 `Alternatives Considered` 섹션 자동 생성 | Phase 3 output에 `alternatives_considered` 필드 포함 |
| `Risks/Mitigations` 구조화 표 포함 | Phase 3/5 output에 `risks_mitigations` 배열 포함 |
| `Implementation Plan` 체크리스트 자동 생성 | Phase 3 output에 `implementation_checklist` 포함 |
| Phase 4 본문에 위 3요소 반영 | PHASE4_USER 프롬프트에 대응 섹션 지침 추가 |

---

## 3. 현재 프롬프트 구조 분석

```
app/prompts/proposal.py
  └── SYSTEM_PROMPT, PROPOSAL_GENERATION_PROMPT, RFP_ANALYSIS_PROMPT
      (레거시 — 현재 파이프라인에서 직접 사용 안 함)

app/services/phase_prompts.py
  ├── PHASE2_SYSTEM/USER  — RFP 분석, 평가위원 관점, 가격 분석
  ├── PHASE3_SYSTEM/USER  — 전략 수립, Win Theme, 섹션 계획  ← 주요 수정 대상
  ├── PHASE4_SYSTEM/USER  — 제안서 본문 작성                  ← 보조 수정
  └── PHASE5_SYSTEM/USER  — 품질 검증                        ← 보조 수정
```

---

## 4. 변경 계획 (YAGNI 검토 후)

### Phase 3 USER 프롬프트 — 핵심 3개 필드 추가

```json
// 기존
{
  "differentiation_strategy": [...],
  "bid_price_strategy": {...}
}

// 추가
{
  "alternatives_considered": [
    {
      "approach": "경쟁사 또는 일반적 접근법 1",
      "our_approach": "우리의 접근법",
      "why_better": "우리 접근법이 우월한 이유 (정량 근거 포함)"
    }
  ],
  "risks_mitigations": [
    {
      "risk": "리스크 설명",
      "probability": "high/medium/low",
      "impact": "high/medium/low",
      "mitigation": "구체적 대응 방안"
    }
  ],
  "implementation_checklist": [
    {
      "phase": "1단계: 착수 (1~2개월)",
      "deliverables": ["산출물1", "산출물2"],
      "milestones": ["마일스톤1"]
    }
  ]
}
```

### Phase 4 SYSTEM 프롬프트 — 3개 섹션 작성 원칙 추가

```
- Alternatives Considered: 우리 접근법의 우월성을 경쟁 대안과 비교하여 서술하세요.
- Risks/Mitigations: 위험 요소와 선제 대응 방안을 표 형식으로 포함하세요.
- Implementation Plan: 단계별 산출물과 마일스톤을 체크리스트 형식으로 제시하세요.
```

### Phase 5 USER 프롬프트 — 3요소 검증 항목 추가

```json
"alternatives_quality": "Alternatives Considered의 설득력 평가 (1~2문장)",
"risks_coverage": "Risks/Mitigations의 완성도 평가 (1~2문장)",
"checklist_specificity": "Implementation Checklist의 구체성 평가 (1~2문장)"
```

---

## 5. YAGNI 검토

### v1 포함 (필수)
- Phase 3 USER: `alternatives_considered`, `risks_mitigations`, `implementation_checklist` 필드 추가
- Phase 4 SYSTEM: 3개 섹션 작성 원칙 추가 (1~2줄)
- Phase 5 USER: 3개 검증 항목 추가

### v2 이후 (보류)
- Phase 3 SYSTEM 페르소나 변경 (현재도 충분히 구체적)
- Phase 2 hidden_intent 심층화 (현재도 잘 구현됨)
- 프롬프트 캐싱 최적화 (별도 성능 개선 이슈)

---

## 6. 성공 기준

| 기준 | 검증 방법 |
|------|----------|
| Phase 3 output에 3개 신규 필드 포함 | JSON 응답 키 확인 |
| Phase 4 본문에 대안 비교 서술 포함 | 생성된 제안서 본문 내 "대안" 또는 "비교" 단어 확인 |
| Phase 4 본문에 리스크 표 포함 | 생성된 제안서 내 리스크/대응방안 섹션 확인 |
| Phase 4 본문에 단계별 체크리스트 포함 | 추진 일정 섹션 구체성 향상 확인 |
| Phase 5 quality_score 변화 없거나 향상 | 기존 품질 저하 없음 확인 |

---

## 7. 작업 목록

| 순서 | 파일 | 작업 |
|------|------|------|
| 1 | `app/services/phase_prompts.py` | PHASE3_USER JSON 스키마에 3개 필드 추가 |
| 2 | `app/services/phase_prompts.py` | PHASE4_SYSTEM에 3개 섹션 작성 원칙 추가 |
| 3 | `app/services/phase_prompts.py` | PHASE5_USER JSON 스키마에 3개 검증 항목 추가 |
| 4 | `app/models/phase_schemas.py` | Phase3Artifact에 신규 필드 추가 (optional) |

---

## 8. 다음 단계

```
/pdca design prompt-enhancement
```
