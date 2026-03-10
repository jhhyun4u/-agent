# 제안발표 자료 자동 생성 기능 계획서 (v3)

## 1. 개요

### 목적

완성된 제안서(Phase 4 sections)의 내용을 기반으로,
**공고문 평가항목·배점 구조를 목차 설계의 기준**으로 삼아
기술성 평가 최고점을 목표로 하는 발표 자료 PPTX를 자동 생성한다.

### 핵심 설계 원칙

| 원칙 | 설명 |
|------|------|
| **평가항목이 목차를 결정한다** | section_plan의 target_criteria + score_weight 순으로 슬라이드 우선순위 결정 |
| **evaluator_check_points가 bullet을 결정한다** | 각 슬라이드 bullet은 평가위원 확인 항목을 하나씩 커버 |
| **콘텐츠 원천은 제안서 본문이다** | Phase4 sections에서 추출·압축, 새 내용 창작 없음 |
| **win_theme은 모든 슬라이드를 관통하는 내러티브다** | 목차 구성 후, 각 슬라이드에 win_theme 메시지로 연결 |

---

## 2. 데이터 흐름

```text
[Phase 2]  evaluation_weights       ← 평가항목별 배점 (예: 기술능력:40, 수행계획:30, 가격:30)
           evaluator_perspective     ← 평가위원 판단 기준, 선호 도급사 프로파일

[Phase 3]  section_plan[]           ← 각 섹션의 target_criteria + score_weight + evaluator_check_points
           win_theme                 ← primary_message + evidence_pillars
           win_strategy              ← 핵심 차별화 전략
           differentiation_strategy ← 경쟁자 대비 차별점
           implementation_checklist ← 단계별 추진 계획

[Phase 4]  sections{}               ← 실제 작성된 제안서 본문 (섹션명 → 텍스트)

           ↓ Claude API (1회 호출)

지시: "section_plan을 score_weight 내림차순으로 정렬하여 슬라이드 목차를 구성하라.
      각 슬라이드 bullet은 해당 섹션의 evaluator_check_points를 모두 커버하되,
      반드시 Phase4 sections 본문에서 근거를 찾아 압축하라.
      win_theme.primary_message가 각 슬라이드 마지막 bullet 또는 speaker_notes에 연결되도록 하라."

           ↓

[출력] 슬라이드 JSON
  - 고정 슬라이드: 표지(1) + Win Theme(2) + 마무리(last)
  - 가변 슬라이드: score_weight 높은 순으로 평가항목별 슬라이드 자동 배치

           ↓ presentation_pptx_builder.py

[출력] PPTX 파일 → Supabase Storage 업로드
```

---

## 3. 슬라이드 목차 구성 로직

### 3.1 고정 슬라이드 (3장)

| 위치 | 슬라이드 | 내용 |
|------|---------|------|
| 첫 번째 | **표지** | 사업명 + Win Theme primary_message (부제목) |
| 두 번째 | **이기는 전략** | win_strategy + win_theme evidence_pillars 3개 |
| 마지막 | **마무리 — 왜 우리인가** | win_theme 재강조 + differentiation_strategy 상위 3개 |

### 3.2 가변 슬라이드 — 평가항목 기반 자동 생성

```text
section_plan[]을 score_weight 내림차순 정렬
  → 배점 15점 이상: 전용 슬라이드 1장
  → 배점 10~14점 : 전용 슬라이드 1장 (bullet 압축)
  → 배점 9점 이하 : 유사 섹션과 병합하여 1장 공유
```

**예시 (evaluation_weights: 기술이해도40, 수행방법론30, 추진일정15, 인력구성15)**

| 순서 | 슬라이드 제목 | target_criteria | score_weight |
|------|-------------|-----------------|:------------:|
| 3 | 사업 이해 & 발주처 핵심 과제 | 기술이해도 | 40 |
| 4 | 수행 방법론 & 차별화 | 수행방법론 | 30 |
| 5 | 추진 일정 | 추진일정 | 15 |
| 6 | 투입 인력 & 역량 | 인력구성 | 15 |

> 총 슬라이드 = 고정 3장 + 가변 N장 (최소 8장, 최대 12장)

### 3.3 각 슬라이드의 구성 규칙

```text
슬라이드 제목 헤더에 표기:
  [평가항목명 | 배점 XX점]

본문 bullet (3~5개):
  - evaluator_check_points 항목 순서로 배치
  - 각 bullet = Phase4 sections 본문에서 추출한 압축 문장 (15자 이내)
  - 정량 수치 포함 bullet 최소 1개 이상

speaker_notes (발표자 스크립트):
  - "평가위원이 이 항목에서 확인하는 것은 [check_point]입니다" 로 시작
  - 해당 bullet의 근거 문장 (Phase4 원문 인용)
  - win_theme 연결 마무리 1문장
```

---

## 4. Claude 프롬프트 설계

### 시스템 프롬프트

```text
당신은 공공 입찰 발표 자료 편집 전문가입니다.
평가위원이 배점표에 따라 채점하는 발표 심사를 위한 슬라이드를 구성합니다.

핵심 규칙:
1. section_plan의 score_weight 내림차순으로 슬라이드 목차를 결정하라.
2. 각 슬라이드의 bullet은 해당 섹션 evaluator_check_points를 순서대로 커버하라.
3. 모든 bullet의 근거는 반드시 제안서 본문(proposal_sections)에서 찾아라. 새 내용을 창작하지 말라.
4. 정량 수치(%, 기간, 비용 절감액)가 포함된 bullet을 슬라이드당 최소 1개 포함하라.
5. win_theme.primary_message는 슬라이드 2(이기는 전략)와 마지막 슬라이드에 명시하고,
   나머지 슬라이드의 speaker_notes 마지막 문장에서 해당 슬라이드 내용과 연결하라.
6. speaker_notes는 "평가위원이 이 항목에서 확인하는 것은 ~입니다" 형식으로 시작하라.
```

### 입력 JSON 구조

```json
{
  "evaluation_weights": { "기술이해도": 40, "수행방법론": 30 },
  "evaluator_perspective": {
    "decision_criteria": ["..."],
    "preferred_contractor_profile": "..."
  },
  "section_plan": [
    {
      "section": "사업 이해도",
      "target_criteria": "기술이해도",
      "score_weight": 40,
      "evaluator_check_points": ["확인항목1", "확인항목2", "확인항목3"],
      "win_theme_alignment": "..."
    }
  ],
  "win_theme": {
    "primary_message": "...",
    "evidence_pillars": ["근거1", "근거2", "근거3"]
  },
  "win_strategy": "...",
  "differentiation_strategy": ["..."],
  "implementation_checklist": [
    { "phase": "1단계", "duration": "1개월", "deliverables": ["산출물1"], "milestones": ["M1"] }
  ],
  "proposal_sections": {
    "사업 이해도": "...(Phase4 본문)...",
    "수행 방법론": "..."
  },
  "project_name": "사업명",
  "team_plan": "..."
}
```

### 출력 JSON 스키마

```json
{
  "slides": [
    {
      "slide_num": 1,
      "layout": "cover",
      "title": "사업명",
      "subtitle": "Win Theme primary_message",
      "speaker_notes": "발표 시작 스크립트"
    },
    {
      "slide_num": 2,
      "layout": "key_message",
      "title": "이기는 전략",
      "headline": "Win Theme primary_message",
      "bullets": ["evidence_pillar1", "evidence_pillar2", "evidence_pillar3"],
      "speaker_notes": "..."
    },
    {
      "slide_num": 3,
      "layout": "eval_section",
      "title": "사업 이해 & 발주처 핵심 과제",
      "eval_badge": "기술이해도 | 40점",
      "bullets": [
        "evaluator_check_point1 기반 압축 문장",
        "evaluator_check_point2 기반 압축 문장",
        "정량 수치 포함 문장"
      ],
      "speaker_notes": "평가위원이 이 항목에서 확인하는 것은 ~입니다. ..."
    },
    {
      "slide_num": 7,
      "layout": "timeline",
      "title": "추진 계획",
      "eval_badge": "추진일정 | 15점",
      "phases": [
        { "name": "1단계", "duration": "1개월", "deliverables": ["산출물1"] }
      ],
      "speaker_notes": "..."
    },
    {
      "slide_num": 8,
      "layout": "closing",
      "title": "왜 우리인가",
      "headline": "Win Theme primary_message",
      "bullets": ["차별화포인트1", "차별화포인트2", "차별화포인트3"],
      "speaker_notes": "..."
    }
  ],
  "total_slides": 8,
  "eval_coverage": {
    "기술이해도": "slide_3",
    "수행방법론": "slide_4"
  }
}
```

---

## 5. 신규 컴포넌트

### 5.1 파일 목록

```text
app/
├── api/
│   └── routes_presentation.py        # 신규
├── services/
│   ├── presentation_generator.py     # 신규: 평가항목 기반 슬라이드 JSON 생성
│   └── presentation_pptx_builder.py  # 신규: JSON → 발표용 PPTX 변환
```

### 5.2 API 엔드포인트

```text
POST /api/v3.1/proposals/{proposal_id}/presentation
  응답: { status: "processing" }

GET  /api/v3.1/proposals/{proposal_id}/presentation/status
  응답: { status, pptx_url, eval_coverage, error }

GET  /api/v3.1/proposals/{proposal_id}/presentation/download
  응답: FileResponse (PPTX)
```

### 5.3 presentation_generator.py

```python
async def generate_presentation_slides(
    phase2: Phase2Artifact,
    phase3: Phase3Artifact,
    phase4: Phase4Artifact,
    rfp_data: RFPData,
) -> dict:
    """
    평가항목(Phase2) + 전략(Phase3) + 제안서 본문(Phase4) →
    평가항목 배점 순 슬라이드 JSON 반환
    """
```

### 5.4 presentation_pptx_builder.py — 레이아웃 타입

| layout 값 | 슬라이드 형태 | eval_badge |
|-----------|-------------|:----------:|
| `cover` | 제목 + 부제목 (Win Theme) | 없음 |
| `key_message` | 헤드라인 + bullet 3~5개 | 없음 |
| `eval_section` | [평가항목 배지] + bullet 3~5개 | 있음 |
| `comparison` | 경쟁자 vs 우리 2컬럼 표 | 있음 |
| `timeline` | 단계별 가로 타임라인 | 있음 |
| `team` | 인력 구성 표 | 있음 |
| `closing` | Win Theme 재강조 + CTA | 없음 |

> `eval_section` 레이아웃은 슬라이드 우측 상단에 `[평가항목명 | XX점]` 배지를 표시하여
> 발표 중 평가위원이 해당 슬라이드의 배점 항목을 직관적으로 인식하도록 한다.

---

## 6. 라우터 등록

`app/api/routes.py`에 추가:

```python
from . import routes_presentation
router.include_router(routes_presentation.router)
```

---

## 7. 세션 상태 관리

```python
{
  "presentation_status": "idle | processing | done | error",
  "presentation_pptx_path": "...",
  "presentation_pptx_url": "...",
  "presentation_eval_coverage": { "기술이해도": "slide_3", ... }
}
```

---

## 8. 리스크 & 대응

| 리스크 | 대응 |
|--------|------|
| Phase 5 미완료 상태 호출 | 400: "제안서 생성이 완료되지 않았습니다" |
| section_plan에 score_weight 누락 | evaluation_weights 배점으로 fallback |
| Phase4 sections에 해당 섹션 텍스트 없음 | Phase3 section_plan.approach로 fallback |
| evaluator_check_points 비어있음 | evaluation_weights 항목명으로 generic bullet 구성 |
| PPTX 빌더 레이아웃 오류 | 슬라이드별 try/except → 텍스트 fallback |

---

## 9. 완료 기준 (Definition of Done)

- [ ] 슬라이드 목차가 section_plan score_weight 내림차순으로 자동 구성됨
- [ ] 각 슬라이드에 `eval_badge` (평가항목명 + 배점) 표시
- [ ] 각 슬라이드 bullet이 evaluator_check_points를 모두 커버
- [ ] 모든 bullet 근거가 Phase4 sections 본문에서 추출됨
- [ ] 슬라이드당 정량 수치 포함 bullet 최소 1개
- [ ] win_theme.primary_message가 슬라이드 2와 마지막 슬라이드에 명시
- [ ] speaker_notes가 "평가위원이 이 항목에서 확인하는 것은" 형식으로 시작
- [ ] eval_coverage 맵이 API 응답에 포함 (어떤 슬라이드가 어떤 평가항목 커버)
- [ ] Phase 5 미완료 시 400 오류 응답
- [ ] 생성 완료 후 Supabase Storage URL 반환

---

## 10. 참조 파일

| 파일 | 역할 |
|------|------|
| `app/models/phase_schemas.py` | Phase2/3/4Artifact 구조 |
| `app/services/phase_prompts.py` | 프롬프트 컨벤션 (이중 중괄호 `{{}}`) |
| `app/services/pptx_builder.py` | 기존 PPTX 빌더 (참조용) |
| `app/services/phase_executor.py` | Supabase Storage 업로드 패턴 |
| `app/api/routes.py` | 라우터 등록 위치 |
