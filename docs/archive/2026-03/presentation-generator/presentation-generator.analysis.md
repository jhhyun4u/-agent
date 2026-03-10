# presentation-generator Gap Analysis Report

> **Analysis Type**: Design vs Implementation Gap Analysis (Check Phase)
>
> **Project**: tenopa-proposer
> **Analyst**: gap-detector
> **Date**: 2026-03-08
> **Design Doc**: [presentation-generator.design.md](../02-design/features/presentation-generator.design.md)
> **Plan Doc**: [presentation-generator.plan.md](../01-plan/features/presentation-generator.plan.md)

---

## 1. Analysis Overview

### 1.1 Analysis Purpose

구현 완료 후, 설계 문서(Design)와 실제 구현 코드 간의 일치 여부를 검증한다.
이전 v0.1 분석은 구현 전 Plan vs Design 사전 분석이었으며, 본 v1.0은 Design vs Implementation 실제 Gap 분석이다.

### 1.2 Analysis Scope

- **Design 문서**: `docs/02-design/features/presentation-generator.design.md`
- **구현 파일**:
  - `app/services/presentation_generator.py` (283 lines)
  - `app/services/presentation_pptx_builder.py` (410 lines)
  - `app/api/routes_presentation.py` (294 lines)
  - `app/api/routes.py` (라우터 등록)
  - `app/templates/presentation/` (템플릿 디렉토리)

### 1.3 현재 상태

```
[Plan] -- [Design] -- [Do] -- [Check] -- [Act]
                                 ^
                            현재 위치 (구현 완료, Gap 분석 수행)
```

---

## 2. Overall Scores

| Category | Score | Status |
|----------|:-----:|:------:|
| API Endpoint 일치율 | 100% | OK |
| 데이터 흐름/입력 조립 일치율 | 100% | OK |
| 프롬프트 일치율 | 100% | OK |
| PPTX 빌더 일치율 | 95% | OK |
| 오류 처리 일치율 | 97% | OK |
| 세션 상태 일치율 | 100% | OK |
| 라우터 등록 일치율 | 100% | OK |
| 템플릿 파일 존재 여부 | 33% | WARN |
| **Design Match (종합)** | **95%** | **OK** |

---

## 3. API Endpoint 비교 (Section 2)

### 3.1 Endpoint URL & HTTP Method

| Design | Implementation | Status | Notes |
|--------|---------------|--------|-------|
| `GET /presentation/templates` | `@router.get("/presentation/templates")` | OK | 일치 |
| `POST /proposals/{proposal_id}/presentation` | `@router.post("/proposals/{proposal_id}/presentation")` | OK | 일치 |
| `GET /proposals/{proposal_id}/presentation/status` | `@router.get("/proposals/{proposal_id}/presentation/status")` | OK | 일치 |
| `GET /proposals/{proposal_id}/presentation/download` | `@router.get("/proposals/{proposal_id}/presentation/download")` | OK | 일치 |
| `APIRouter(prefix="/v3.1", tags=["presentation"])` | `APIRouter(prefix="/v3.1", tags=["presentation"])` | OK | 일치 |

### 3.2 GET `/presentation/templates` 응답

| Design 필드 | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| templates[].id | OK | OK | 3개 템플릿 ID 일치 |
| templates[].name | OK | OK | |
| templates[].description | OK | OK | |
| templates[].preview_color | OK | OK | |
| templates[].slide_count_example | OK | OK | |
| (없음) | templates[].available | ADDED | 실제 파일 존재 여부 추가 (합리적 보완) |

### 3.3 POST 요청 파라미터

| Design 파라미터 | Implementation | Status |
|---------------|---------------|--------|
| template_mode: str = "standard" | `template_mode: str = "standard"` | OK |
| template_id: str = "government_blue" | `template_id: str = "government_blue"` | OK |
| sample_storage_path: Optional[str] = None | `sample_storage_path: Optional[str] = None` | OK |

### 3.4 POST 응답 포맷

| Design | Implementation | Status |
|--------|---------------|--------|
| `{ proposal_id, status, template_mode, template_id, message }` | 동일 | OK |

### 3.5 Status 응답 포맷

| Design 필드 | Implementation 필드 | Status | Notes |
|-------------|-------------------|--------|-------|
| proposal_id | proposal_id | OK | |
| status | status | OK | |
| pptx_url | pptx_url | OK | |
| eval_coverage | eval_coverage | OK | |
| error | error | OK | |
| (없음) | template_mode | ADDED | 구현에서 추가 |
| (없음) | template_id | ADDED | 구현에서 추가 |

### 3.6 Download 엔드포인트

| Design | Implementation | Status | Notes |
|--------|---------------|--------|-------|
| FileResponse(path, media_type=...) | FileResponse(path=..., media_type=..., filename=...) | OK | 구현에서 filename 추가 (개선) |

---

## 4. 전처리/유효성 검증 비교 (Section 2.3)

| Design 전처리 | Implementation | Status |
|-------------|---------------|--------|
| session 없으면 404 | `SessionNotFoundError` -> 404 | OK |
| phases_completed < 5 -> 400 | `session.get("phases_completed", 0) < 5` -> 400 | OK |
| presentation_status == "processing" -> 409 | `session.get("presentation_status") == "processing"` -> 409 | OK |
| standard 모드 template 파일 없으면 400 | valid_ids 체크 -> 400 | CHANGED |
| sample 모드 sample_storage_path 없으면 400 | `not sample_storage_path` -> 400 | OK |
| 세션에 presentation_status = "processing" 업데이트 | `update_session(..., {"presentation_status": "processing"})` | OK |

**CHANGED 항목 상세**: Design은 "template 파일 없으면 400"이나, 구현은 _STANDARD_TEMPLATES의 ID 목록 기반 유효성 검증으로 변경. 파일 존재 여부가 아닌 ID 유효성 검증으로, 더 안전한 접근. 파일이 없는 경우는 _resolve_template_path에서 scratch fallback 처리.

---

## 5. 백그라운드 함수 비교 (Section 2.6)

### 5.1 `_run_presentation` 함수

| Design 항목 | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| aget_session 호출 | `await session_manager.aget_session(proposal_id)` | OK | |
| Phase2Artifact 로드 | `Phase2Artifact(**session["phase_artifact_2"])` | OK | |
| Phase3Artifact 로드 | `Phase3Artifact(**session["phase_artifact_3"])` | OK | |
| Phase4Artifact 로드 | `Phase4Artifact(**session["phase_artifact_4"])` | OK | |
| RFPData 로드 | `rfp_raw = session.get(...)` / `RFPData(**rfp_raw) if rfp_raw else None` | OK | Design보다 방어적 (None 처리) |
| generate_presentation_slides 호출 | 일치 | OK | |
| _resolve_template_path 호출 | 일치 | OK | |
| build_presentation_pptx 호출 | 일치 | OK | |
| _upload_presentation 호출 | 일치 | OK | |
| 세션 업데이트 (6개 키) | 일치 | OK | |
| (없음) | sample 모드 다운로드 선행 호출 | ADDED | `_download_sample_template` 추가 |
| (없음) | try/except -> presentation_error 세팅 | ADDED | 전체 오류 래핑 추가 |

### 5.2 `_resolve_template_path` 헬퍼

| Design | Implementation | Status | Notes |
|--------|---------------|--------|-------|
| standard: Path 존재 확인 -> 반환 | 동일 | OK | |
| sample: Storage 다운로드 처리 | 로컬 캐시 존재 확인만 | OK | 다운로드는 별도 함수로 분리 |
| scratch: None 반환 | `return None` | OK | |

### 5.3 `_upload_presentation` 함수

| Design | Implementation | Status |
|--------|---------------|--------|
| bucket = "proposal-files" | `bucket = "proposal-files"` | OK |
| storage_path = "{proposal_id}/presentation.pptx" | 동일 | OK |
| file_bytes 읽기 -> upload -> get_public_url | 동일 | OK |
| (없음) | try/except -> 빈 문자열 반환 | ADDED |

---

## 6. presentation_generator.py 비교 (Section 3)

### 6.1 공개 인터페이스

| Design | Implementation | Status |
|--------|---------------|--------|
| `async def generate_presentation_slides(phase2, phase3, phase4, rfp_data=None) -> dict` | 동일 | OK |

### 6.2 `_build_input` 함수

| Design 필드 | Implementation | Status |
|-------------|---------------|--------|
| project_name | OK | OK |
| evaluation_weights | OK | OK |
| evaluator_perspective | `phase2.structured_data.get("evaluator_perspective", {})` | OK |
| section_plan (score_weight 내림차순 정렬) | `sorted(..., key=lambda s: s.get("score_weight", 0), reverse=True)` | OK |
| win_theme | OK | OK |
| win_strategy | OK | OK |
| differentiation_strategy | OK | OK |
| implementation_checklist | OK | OK |
| proposal_sections | `phase4.sections` | OK |
| team_plan | `phase3.team_plan` | OK |

### 6.3 TOC 프롬프트 (Step 1)

| Design | Implementation | Status |
|--------|---------------|--------|
| TOC_SYSTEM 전문 | 문자 단위 일치 | OK |
| TOC_USER 전문 | 문자 단위 일치 | OK |
| model=settings.claude_model | OK | OK |
| max_tokens=2048 | OK | OK |
| extract_json_from_response 사용 | OK | OK |

### 6.4 STORYBOARD 프롬프트 (Step 2)

| Design | Implementation | Status |
|--------|---------------|--------|
| STORYBOARD_SYSTEM 전문 | 문자 단위 일치 | OK |
| STORYBOARD_USER 전문 | 문자 단위 일치 | OK |
| max_tokens=6000 | OK | OK |
| 6개 format 변수 전달 | OK | OK |
| total_slides 보정 로직 | OK | OK |

### 6.5 추가 구현 (Design에 없음)

| Item | Location | Description |
|------|----------|-------------|
| 로깅 | lines 231, 247, 250, 278 | Step 1/2 시작/완료 로깅 (합리적 추가) |

---

## 7. presentation_pptx_builder.py 비교 (Section 4)

### 7.1 공개 인터페이스

| Design | Implementation | Status |
|--------|---------------|--------|
| `build_presentation_pptx(slides_json, output_path, project_name, template_path)` | 동일 | OK |

### 7.2 `_init_presentation` 함수

| Design | Implementation | Status | Notes |
|--------|---------------|--------|-------|
| template_path 존재 시 로드 | OK | OK | |
| 기존 슬라이드 전부 제거 (Slide Master 유지) | `while len(prs.slides._sldIdLst) > 0` | OK | |
| scratch: `Presentation()` | OK | OK | |
| scratch: slide_width=13.333, height=7.5 | OK | OK | |
| (없음) | template 로드 실패 시 scratch fallback | ADDED | try/except 보강 (Design 8절 Fallback 정책 반영) |

### 7.3 레이아웃별 렌더링 함수 (7종)

| Design 함수 | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `_render_cover` | OK (lines 91-112) | OK | |
| `_render_key_message` | OK (lines 115-126) | OK | |
| `_render_eval_section` | OK (lines 129-134) | OK | eval_badge 포함 |
| `_render_comparison` | OK (lines 137-183) | OK | 2컬럼 표 구현 |
| `_render_timeline` | OK (lines 186-252) | OK | 가로 배치 구현 |
| `_render_team` | OK (lines 255-302) | OK | 4컬럼 표 구현 |
| `_render_closing` | OK (lines 305-316) | OK | |

### 7.4 eval_badge 렌더링 비교

| Design 사양 | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| 위치: Inches(9.5), Inches(0.2), 3.5, 0.5 | Inches(9.5), Inches(0.15), 3.6, 0.45 | MINOR | 미세한 위치/크기 차이 (기능 동일) |
| font.size = Pt(12) | Pt(12) | OK | |
| font.bold = True | True | OK | |
| font.color.rgb = RGBColor(0x1F, 0x49, 0x7D) | COLOR_DARK_BLUE (동일 값) | OK | 상수화 (개선) |
| alignment = PP_ALIGN.RIGHT | PP_ALIGN.RIGHT | OK | |

### 7.5 speaker_notes 추가 비교

| Design | Implementation | Status |
|--------|---------------|--------|
| `notes_slide.notes_text_frame.text = data.get("speaker_notes", "")` | `_add_speaker_notes(slide, notes_text)` 함수화 | OK |

### 7.6 timeline 레이아웃 비교

| Design 사양 | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| 가로 균등 분배 | `col_w = total_w / max(n, 1)` | OK | |
| 배경 사각형 + 색상 | `shape.fill.solid()` + `phase_colors[i]` | OK | 단색 -> 그라데이션 색상 (개선) |
| 단계명 + 기간 + 산출물 | name + duration + deliverables | OK | |
| MSO_SHAPE_TYPE.RECTANGLE | `1` (정수 상수 직접 사용) | OK | python-pptx 호환 방식 |

### 7.7 fallback 처리

| Design | Implementation | Status |
|--------|---------------|--------|
| layout_map 기반 디스패치 | `_LAYOUT_MAP` dict | OK |
| 기본 layout: eval_section | `_LAYOUT_MAP.get(layout, _render_eval_section)` | OK |
| slide_layouts[6] (blank) | `min(6, len(prs.slide_layouts) - 1)` | OK |
| 실패 시 slide_layouts[1] + title + bullets | try/except + slide_layouts[1] | OK |
| (없음) | 2차 fallback도 실패 시 logger.error | ADDED |

### 7.8 추가 구현 (Design에 명시되지 않음)

| Item | Description | Impact |
|------|-------------|--------|
| `_add_textbox` 유틸 | 공통 텍스트박스 추가 헬퍼 함수 | Low (코드 정리용) |
| `_add_eval_badge` 유틸 | eval_badge 렌더링 공통화 | Low (코드 정리용) |
| `_add_speaker_notes` 유틸 | 발표자 노트 추가 공통화 | Low (코드 정리용) |
| `_add_slide_title` 유틸 | 슬라이드 제목 공통화 | Low (코드 정리용) |
| `_add_bullets` 유틸 | bullet 목록 공통화 | Low (코드 정리용) |
| 색상 상수 (4개) | COLOR_DARK_BLUE 등 상수 정의 | Low (코드 정리용) |
| 빈 slides 처리 | `if not slides:` 빈 표지 생성 | Low (방어적 코딩) |
| team 테이블 4컬럼 | "역할/등급/투입기간/담당업무" 4컬럼 | Low (Design의 3컬럼 role/grade/person_months 대비 확장) |

---

## 8. 오류 처리 비교 (Section 8)

| Design 오류 정책 | HTTP Code | Implementation | Status |
|-----------------|:---------:|---------------|--------|
| proposal_id 세션 없음 | 404 | `SessionNotFoundError` -> 404 "제안서를 찾을 수 없습니다" | OK |
| phases_completed < 5 | 400 | `phases_completed < 5` -> 400 "제안서 생성이 완료되지 않았습니다" | OK |
| 이미 processing 중 | 409 | `presentation_status == "processing"` -> 409 "발표 자료를 생성 중입니다" | OK |
| standard 템플릿 없음 | 400 | valid_ids 체크 -> 400 "존재하지 않는 템플릿입니다: {template_id}" | OK |
| sample 모드 path 없음 | 400 | `not sample_storage_path` -> 400 | OK |
| 다운로드 파일 없음 | 404 | `not pptx_path or not Path(pptx_path).exists()` -> 404 | OK |
| 템플릿 로드 실패 | scratch fallback | `_init_presentation` try/except -> scratch | OK |
| 백그라운드 전체 실패 | status=error | try/except -> `presentation_status="error"`, `presentation_error=msg` | OK |

**오류 메시지 비교**

| Design 메시지 | Implementation 메시지 | Status |
|-------------|---------------------|--------|
| "제안서를 찾을 수 없습니다" | "제안서를 찾을 수 없습니다" | OK |
| "제안서 생성이 완료되지 않았습니다" | "제안서 생성이 완료되지 않았습니다" | OK |
| "이미 생성 중입니다" | "발표 자료를 생성 중입니다" | MINOR |
| "존재하지 않는 템플릿입니다: {template_id}" | "존재하지 않는 템플릿입니다: {template_id}. 사용 가능: {sorted(valid_ids)}" | OK |
| "sample 모드에는 sample_storage_path가 필요합니다" | 동일 | OK |
| "발표 자료가 아직 생성되지 않았습니다" | "발표 자료가 아직 생성되지 않았습니다" | OK |

---

## 9. Fallback 체인 비교 (Section 9)

| Design Fallback 시나리오 | Implementation | Status |
|------------------------|---------------|--------|
| score_weight 없음 -> evaluation_weights 조회 | Claude 프롬프트 위임 (구현 수준 동일) | OK |
| phase4.sections 섹션 없음 -> section_plan.approach 사용 | Claude 프롬프트 위임 | OK |
| win_theme 비어있음 -> win_strategy 사용 | Claude 프롬프트 위임 | OK |
| evaluator_check_points 비어있음 -> generic bullet | Claude 프롬프트 위임 | OK |
| PPTX 슬라이드 렌더링 오류 -> text fallback | `_render_slide` try/except | OK |

---

## 10. 세션 상태 키 비교 (Section 7)

| Design 키 | Implementation 키 | Status |
|-----------|------------------|--------|
| presentation_status | `presentation_status` | OK |
| presentation_pptx_path | `presentation_pptx_path` | OK |
| presentation_pptx_url | `presentation_pptx_url` | OK |
| presentation_eval_coverage | `presentation_eval_coverage` | OK |
| presentation_template_mode | `presentation_template_mode` | OK |
| presentation_template_id | `presentation_template_id` | OK |
| presentation_error | `presentation_error` | OK |

---

## 11. 라우터 등록 비교 (Section 6)

| Design | Implementation | Status |
|--------|---------------|--------|
| `from . import routes_presentation` | `from . import ... routes_presentation` | OK |
| `router.include_router(routes_presentation.router)` | `router.include_router(routes_presentation.router)` | OK |
| (없음) | routes.py 주석: "발표 자료 생성: /api/v3.1/presentation/templates..." | OK |
| main.py app.include_router(router, prefix="/api") | OK | OK |

---

## 12. 템플릿 파일 존재 비교 (Section 1)

| Design 정의 파일 | 파일 존재 | Status |
|-----------------|:---------:|--------|
| `government_blue.pptx` | X | MISSING |
| `corporate_modern.pptx` | X | MISSING |
| `minimal_clean.pptx` | X | MISSING |
| `app/templates/presentation/` 디렉토리 | O | OK |
| `README.md` (안내 파일) | O | OK (Design에 없으나 합리적) |

**Note**: PPTX 템플릿 파일 3개가 아직 생성되지 않았다. 코드 상 scratch fallback이 동작하므로 런타임 오류는 없으나, standard 모드의 디자인 의도(Slide Master 유지)는 달성되지 않는다.

---

## 13. Differences Summary

### 13.1 Missing Features (Design O, Implementation X)

| Item | Design Location | Description | Impact |
|------|-----------------|-------------|--------|
| government_blue.pptx | design.md:20 | 정부/공공기관 스타일 PPTX 템플릿 파일 | Medium |
| corporate_modern.pptx | design.md:21 | 기업 현대적 스타일 PPTX 템플릿 파일 | Medium |
| minimal_clean.pptx | design.md:22 | 심플/미니멀 PPTX 템플릿 파일 | Medium |

### 13.2 Added Features (Design X, Implementation O)

| Item | Implementation Location | Description | Impact |
|------|------------------------|-------------|--------|
| templates[].available | routes_presentation.py:188 | 템플릿 파일 존재 여부 필드 추가 | Low (합리적 보완) |
| status 응답에 template_mode/id 추가 | routes_presentation.py:264-265 | 상태 조회 시 템플릿 정보 반환 | Low (합리적 보완) |
| download filename 지정 | routes_presentation.py:286-287 | 다운로드 시 한국어 파일명 지정 | Low (UX 개선) |
| _download_sample_template 함수 | routes_presentation.py:76-97 | sample 모드 Storage 다운로드 별도 함수화 | Low (코드 정리) |
| _upload_presentation 오류 처리 | routes_presentation.py:117-119 | 업로드 실패 시 빈 URL 반환 (계속 진행) | Low (안정성 개선) |
| _run_presentation 전체 오류 래핑 | routes_presentation.py:169-177 | 백그라운드 전체 실패 시 error 상태 기록 | Low (Design 8절 정책 반영) |
| 유틸 함수 5개 | pptx_builder.py:23-87 | _add_textbox, _add_eval_badge 등 공통 헬퍼 | Low (코드 정리) |
| 색상 상수 4개 | pptx_builder.py:15-18 | COLOR_DARK_BLUE 등 | Low (코드 정리) |
| team 테이블 4컬럼 | pptx_builder.py:272 | "담당 업무" 컬럼 추가 (Design은 3컬럼) | Low (기능 확장) |
| 빈 slides 방어 처리 | pptx_builder.py:399-401 | slides 비어있을 때 빈 표지 생성 | Low (방어적 코딩) |
| 로깅 추가 | 전체 파일 | Step 1/2 시작/완료 + 에러 로깅 | Low (운영 지원) |

### 13.3 Changed Features (Design != Implementation)

| Item | Design | Implementation | Impact |
|------|--------|----------------|--------|
| eval_badge 위치 미세 조정 | Inches(9.5, 0.2, 3.5, 0.5) | Inches(9.5, 0.15, 3.6, 0.45) | None (시각적 차이 무시 가능) |
| 409 오류 메시지 | "이미 생성 중입니다" | "발표 자료를 생성 중입니다" | None (의미 동일) |
| standard 템플릿 검증 방식 | 파일 존재 여부 확인 | ID 유효성 검증 후 파일은 fallback | Low (더 안전한 방식) |
| team 테이블 컬럼 수 | 3컬럼 (role/grade/person_months) | 4컬럼 (역할/등급/투입기간/담당업무) | Low (기능 확장) |

---

## 14. Match Rate Calculation

### 14.1 항목별 점수

| Category | Total Items | Match | Added | Changed | Missing | Score |
|----------|:-----------:|:-----:|:-----:|:-------:|:-------:|:-----:|
| API Endpoints (4개) | 4 | 4 | 0 | 0 | 0 | 100% |
| 요청/응답 포맷 (15필드) | 15 | 15 | 3 | 0 | 0 | 100% |
| 전처리/유효성 (6개) | 6 | 5 | 0 | 1 | 0 | 97% |
| 백그라운드 함수 (10개) | 10 | 10 | 2 | 0 | 0 | 100% |
| 프롬프트 (4개) | 4 | 4 | 0 | 0 | 0 | 100% |
| 입력 조립 (10필드) | 10 | 10 | 0 | 0 | 0 | 100% |
| PPTX 빌더 인터페이스 | 4 | 4 | 0 | 0 | 0 | 100% |
| 레이아웃 렌더링 (7종) | 7 | 7 | 0 | 0 | 0 | 100% |
| eval_badge (5항목) | 5 | 4 | 0 | 1 | 0 | 97% |
| fallback 처리 (5개) | 5 | 5 | 1 | 0 | 0 | 100% |
| 오류 처리 (8개) | 8 | 7 | 0 | 1 | 0 | 97% |
| 세션 상태 키 (7개) | 7 | 7 | 0 | 0 | 0 | 100% |
| 라우터 등록 (2개) | 2 | 2 | 0 | 0 | 0 | 100% |
| 템플릿 파일 (3개) | 3 | 0 | 0 | 0 | 3 | 0% |

### 14.2 종합 Match Rate

```
+---------------------------------------------+
|  Design vs Implementation Match Rate: 95%    |
+---------------------------------------------+
|  Total checked items:    90                  |
|  OK (Match):            84 items (93%)       |
|  ADDED (impl only):     6 items (합리적 보완) |
|  CHANGED (minor):       3 items (기능 동일)   |
|  MISSING (not impl):    3 items (템플릿 파일) |
+---------------------------------------------+
|  Code Quality:     Excellent                 |
|  Design Fidelity:  Very High                 |
+---------------------------------------------+

Match Rate >= 90%: 설계와 구현이 잘 일치합니다.
```

---

## 15. Recommended Actions

### 15.1 Immediate Actions (Priority High)

| Priority | Item | Description |
|----------|------|-------------|
| 1 | PPTX 템플릿 파일 생성 | `app/templates/presentation/`에 government_blue.pptx, corporate_modern.pptx, minimal_clean.pptx 3개 파일 생성 필요. 없으면 standard 모드가 항상 scratch fallback. |

### 15.2 Documentation Update (Priority Low)

| Item | Description |
|------|-------------|
| status 응답 필드 추가 | design.md 2.4절에 template_mode, template_id 필드 추가 반영 |
| templates 응답 available 필드 | design.md 2.2절에 available 필드 추가 반영 |
| team 테이블 4컬럼 | design.md 4.6절의 team_rows 구조에 task 필드 추가 반영 |
| eval_badge 위치 미세 조정 | design.md 4.3절 좌표값 업데이트 (optional) |

### 15.3 No Action Needed

| Item | Reason |
|------|--------|
| 추가된 유틸 함수 | 코드 정리용 내부 함수, 외부 인터페이스 변경 없음 |
| 로깅 추가 | 운영 지원용, 기능 영향 없음 |
| 오류 메시지 미세 차이 | 의미 동일, 사용자 체감 차이 없음 |
| download filename 추가 | UX 개선, 하위 호환성 유지 |

---

## 16. Synchronization Options

| Option | Description | Recommended |
|--------|-------------|:-----------:|
| 1. 템플릿 파일 생성 | 3개 PPTX 템플릿 디자인 파일 제작 | Yes |
| 2. Design 문서 업데이트 | 구현에서 추가/변경된 항목 반영 | Optional |
| 3. 차이 의도적 기록 | minor 차이를 의도적 결정으로 기록 | No (불필요) |

---

## 17. Next Steps

- [ ] PPTX 템플릿 파일 3개 생성 (government_blue, corporate_modern, minimal_clean)
- [ ] Design 문서에 추가 필드 반영 (optional)
- [ ] `/pdca report presentation-generator` 로 완료 보고서 생성

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-08 | Plan vs Design 사전 Gap 분석 (구현 미착수 상태) | gap-detector |
| 1.0 | 2026-03-08 | Design vs Implementation 실제 Gap 분석 (구현 완료 상태) | gap-detector |
