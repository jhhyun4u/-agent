# Plan: ppt-enhancement

## 기능 개요

발표 자료(PPTX) 생성 기능의 품질과 완성도를 McKinsey 발표 설계 원칙 기준으로 개선한다.
현재 기능은 구조적으로 동작하나, 전문 발표 자료로서 갖춰야 할 7가지 핵심 결함이 있다.

---

## 배경 및 문제 정의

### 현황
- `presentation_generator.py`: Claude API 2-Step (TOC → 스토리보드) 파이프라인
- `presentation_pptx_builder.py`: 7종 레이아웃 PPTX 렌더링
- `routes_presentation.py`: 백그라운드 생성 + Supabase Storage 업로드

### 핵심 문제 (우선순위 순)

| # | 문제 | 영향도 | 복잡도 |
|---|------|--------|--------|
| P1 | `comparison`/`team` 레이아웃 — 프롬프트에 JSON 구조 없음 → 항상 bullets fallback | Critical | Low |
| P2 | Action Title 부재 — 제목이 주장(assertion)이 아닌 토픽 | High | Medium |
| P3 | 슬라이드 번호 없음 — 공공기관 발표 필수 요건 | High | Low |
| P4 | `/tmp` 경로 하드코딩 — Windows 환경 비호환 | High | Low |
| P5 | Step 2 max_tokens=6,000 — 12장 스토리보드 생성 시 JSON 잘림 위험 | Medium | Low |
| P6 | 표준 템플릿 PPTX 파일 없음 — 항상 scratch로 fallback | Medium | High |
| P7 | 차트/그래프 렌더링 없음 — 낙찰가 시나리오, 간트 등 설득력 부족 | Medium | High |

---

## 목표

### 기능 목표
1. `comparison` / `team` 레이아웃이 프롬프트에서 올바른 JSON 구조를 받아 실제 표를 렌더링한다
2. 슬라이드 제목이 Action Title(주장 문장) 형식으로 생성된다
3. 모든 슬라이드에 슬라이드 번호가 표시된다
4. 파일 경로가 OS 독립적으로 동작한다 (Windows/Linux 공통)
5. Step 2 토큰 한계를 8,192로 높여 JSON 잘림을 방지한다

### 비목표 (이번 범위 제외)
- 차트/그래프 렌더링 (P7) — 별도 피처로 분리
- 표준 템플릿 PPTX 파일 디자인 (P6) — 디자이너 작업 필요

---

## 요구사항

### FR-01: comparison 레이아웃 프롬프트 수정
- STORYBOARD_USER 예시에 `comparison` 슬라이드 JSON 구조 추가
- 필드: `table: [{dimension, competitor, ours}]` 형식
- Claude가 `differentiation_strategy`에서 비교 데이터를 추출하도록 지시

### FR-02: team 레이아웃 프롬프트 수정
- STORYBOARD_USER 예시에 `team` 슬라이드 JSON 구조 추가
- 필드: `team_rows: [{role, grade, duration, task}]` 형식
- Claude가 `team_plan`에서 인력 데이터를 추출하도록 지시

### FR-03: Action Title 규칙 추가
- TOC_SYSTEM에 "슬라이드 제목은 완결된 주장 문장(assertion)으로 작성"하는 규칙 추가
- STORYBOARD_SYSTEM에 "title은 TOC의 assertion title 그대로" 규칙 유지
- 예: "사업 이해도" → "당사는 현장 5년 경험으로 발주처 핵심 요구사항을 정확히 이해함"

### FR-04: 슬라이드 번호 추가
- `presentation_pptx_builder.py`에 `_add_slide_number(slide, num)` 헬퍼 추가
- 위치: 슬라이드 우측 하단 (Inches 12.5, 6.9)
- 스타일: 14pt, COLOR_DARK_TEXT, 표지(cover)는 제외

### FR-05: 파일 경로 OS 독립화
- `routes_presentation.py`의 `/tmp/{id}/presentation.pptx`를
  `tempfile.gettempdir()` 또는 `settings`의 `output_dir` 설정값으로 교체

### FR-06: Step 2 토큰 증가
- `generate_presentation_slides()`의 Step 2 `max_tokens` 6,000 → 8,192

---

## 구현 범위

### 수정 파일
1. `app/services/presentation_generator.py` — FR-01, FR-02, FR-03, FR-06
2. `app/services/presentation_pptx_builder.py` — FR-04
3. `app/api/routes_presentation.py` — FR-05

### 신규 파일
없음

---

## 성공 기준

- [ ] `comparison` 레이아웃 슬라이드에 3컬럼 비교표가 렌더링된다
- [ ] `team` 레이아웃 슬라이드에 4컬럼 인력표가 렌더링된다
- [ ] 슬라이드 제목이 "주어 + 서술어" 형식의 주장 문장이다
- [ ] 표지를 제외한 모든 슬라이드에 번호가 표시된다
- [ ] Windows 환경(로컬)에서 PPTX가 정상 생성된다
- [ ] 12장 슬라이드 생성 시 JSON 파싱 오류 없음

---

## 일정

| 단계 | 내용 | 예상 |
|------|------|------|
| Design | 상세 설계 (프롬프트 변경 내용 확정) | 0.5일 |
| Do | 코드 수정 (3개 파일) | 1일 |
| Check | Gap 분석 + 로컬 테스트 | 0.5일 |

---

## 참고

- McKinsey Pyramid Principle: Barbara Minto, 1987
- Action Title 원칙: 제목만 읽어도 핵심 주장을 파악할 수 있어야 함
- 수평 논리 (Horizontal Logic): 제목 시퀀스가 독립적 스토리를 형성
- 현재 검토 결과: `docs/archive/` — 이번 분석 세션
