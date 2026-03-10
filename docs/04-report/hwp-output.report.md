# Completion Report: hwp-output

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | hwp-output |
| 보고서 작성일 | 2026-03-07 |
| PDCA 시작일 | 2026-03-07 |
| 완료일 | 2026-03-07 (서식 표준화: 2026-03-07) |
| 최종 Match Rate | **98%** |
| PDCA 반복 횟수 | 2회 (Act-1 + Act-2) |
| 상태 | **Completed** |

---

## 1. 개요

공공입찰 제안서 자동 생성 시스템에 **HWPX 출력 기능**을 추가.
나라장터(G2B) 제출 서류의 사실상 표준 형식인 HWP/HWPX를 지원함으로써,
기존 DOCX + PPTX 파이프라인에 HWPX를 완전 통합.

기술 접근 방식: **python-hwpx v2.5** (Option C — 라이브러리 활용)

---

## 2. PDCA 흐름 요약

```text
[Plan] ✅ → [Design] ✅ → [Do] ✅ → [Check] ✅ → [Act-1] ✅ → [Act-2] ✅ → [Report] ✅
  03-07       03-07        03-07      03-07        03-07        03-07         03-07
```

| 단계 | 주요 산출물 | 비고 |
|------|------------|------|
| Plan | hwp-output.plan.md | FR-01~05 정의, 기술 옵션 A/B/C 검토 |
| Design | hwp-output.design.md | python-hwpx v2.5 선택, 전체 파이프라인 설계 |
| Do | hwpx_builder.py + 파이프라인 통합 | proposal-platform-v1 Act-2에서 구현 |
| Check | hwp-output.analysis.md | Match Rate 85% — DB 스키마 갭 발견 |
| Act-1 | G1~G6 수정 (schema.sql + frontend + 설계문서) | Match Rate 85% → 95% |
| Act-2 | 서식 표준화 (샘플 2종 분석 기반) | Match Rate 95% → 98% |
| Report | 본 문서 | |

---

## 3. 구현 완료 기능

### 3-1. `app/services/hwpx_builder.py` (신규 + Act-2 서식 표준화)

| 기능 | 설명 |
|------|------|
| `build_hwpx()` | sections dict → .hwpx 파일 동기 생성 |
| `build_hwpx_async()` | `asyncio.to_thread` 기반 비동기 래퍼 |
| 표지 | 사업명, 입찰공고번호, 제출일, 발주처, 제안업체 |
| 평가항목 참조표 | `evaluation_weights` dict 기반 5열 동적 테이블 + 텍스트 폴백 |
| 목차 | 4장(Ⅰ~Ⅳ), 7개 소절 고정 목차 |
| 본문 기호 체계 | □/❍/☞/【】/- 기호 단계별 스타일 처리 |
| 부록 | `_CHAPTER_MAP` 매핑 외 섹션 자동 추가 |
| **서식 표준화** (Act-2) | 샘플 2종 분석 기반 폰트·크기 표준 적용 |

#### Act-2: 서식 표준화 상세 (샘플 분석 기반)

샘플 파일 2종 (`O-Prize 사업기획`, `국토교통R&D 파급효과`) XML 분석을 통해 도출한 표준:

| 스타일 | 폰트 | 크기 | 굵기 | 적용 대상 |
| ------ | ---- | ---- | ---- | --------- |
| body | 맑은 고딕 | 12pt | — | 본문 일반 텍스트 |
| content | 맑은 고딕 | 12pt | — | □ ❍ ☞ - 기호 내용 |
| table | 맑은 고딕 | 10pt | — | 표 제목·내용 |
| section | 맑은 고딕 | 12pt | bold | 소제목 (1. 2.) |
| chapter | 맑은 고딕 | 14pt | bold | 장제목 (Ⅰ~Ⅳ), 목차 |
| cover_title | HY헤드라인M | 22pt | — | 표지 "제   안   서" |
| cover_name | 맑은 고딕 | 14pt | bold | 표지 사업명·업체명 |

**구현 방식**: `_inject_fonts()` + `_inject_char_styles()` 로 header XML에 직접 주입.
`_patch_hwpx_library()`로 lxml/stdlib ET 호환성 확보.

### 3-2. `app/services/phase_executor.py` — 파이프라인 통합

| 항목 | 내용 |
|------|------|
| 빌드 시점 | Phase 4 완료 후 DOCX/PPTX와 함께 생성 |
| hwpx_metadata | `session.rfp_metadata` 기반 자동 조립 |
| soft fail | 예외 발생 시 `logger.warning` + `hwpx_path=""` (DOCX/PPTX 계속 진행) |
| Storage 업로드 | `proposal-files` 버킷 `{proposal_id}/proposal.hwpx` |
| 실패 플래그 | `storage_upload_failed` 컬럼 업데이트 |

### 3-3. `app/api/routes_v31.py` — 다운로드 엔드포인트

- `GET /proposals/{proposal_id}/download/hwpx`
- `file_type` 검증: `docx | pptx | hwpx`
- Storage 서명 URL (5분 유효) → `RedirectResponse`
- 로컬 파일 폴백 (Storage 미업로드 시)

### 3-4. `frontend/app/proposals/[id]/page.tsx` — 다운로드 버튼

- HWPX 다운로드 버튼 (teal 스타일)
- `status.hwpx_path` 존재 시에만 렌더링 (soft fail 시 자동 숨김)

### 3-5. DB 스키마 (`database/schema.sql`)

| 변경 항목 | 내용 |
|----------|------|
| `proposals.storage_path_hwpx TEXT` | HWPX Storage 경로 저장 컬럼 추가 |
| `proposals.status CHECK` | `'running'` 상태값 추가 |
| `proposals.failed_phase` | `TEXT` → `INTEGER` 타입 변경 |
| `proposal_phases.phase_num` | `phase_number` → `phase_num` 컬럼명 수정 |
| `proposal_phases.artifact_json` | `artifact` → `artifact_json` 컬럼명 수정 |
| `UNIQUE (proposal_id, phase_num)` | UNIQUE 제약 컬럼명 동기화 |

---

## 4. Act 수정 내역

### Act-1 (DB 스키마 갭 수정)

| ID | 파일 | 수정 전 | 수정 후 |
|----|------|---------|---------|
| G1 | database/schema.sql | `storage_path_hwpx` 컬럼 없음 | `TEXT` 컬럼 추가 |
| G2 | database/schema.sql | CHECK에 `'running'` 없음 | `'running'` 추가 |
| G3 | database/schema.sql | `phase_number`, `artifact` | `phase_num`, `artifact_json` |
| G4 | database/schema.sql | `failed_phase TEXT` | `failed_phase INTEGER` |
| G5 | frontend/page.tsx | HWPX 버튼 항상 표시 | `status.hwpx_path` 조건부 렌더링 |
| G6 | hwp-output.design.md | URL 형식 오류 (`?file_type=`) | path param `/download/hwpx` |

### Act-2 (서식 표준화)

| ID | 파일 | 내용 |
| -- | ---- | ---- |
| S1 | hwpx_builder.py | `_inject_fonts()` — 맑은 고딕/휴먼명조/HY헤드라인M header 주입 |
| S2 | hwpx_builder.py | `_inject_char_styles()` — 7종 charPr 스타일 생성 (본문·내용·표·소제목·장제목·표지) |
| S3 | hwpx_builder.py | `_setup_styles()` — 빌드 시 스타일 ID 동적 할당 |
| S4 | hwpx_builder.py | 모든 `add_paragraph` / `add_run` 에 `char_pr_id_ref` 명시 |
| S5 | hwpx_builder.py | 본문 12pt, 표 10pt 로 크기 표준화 |

---

## 5. 성공 기준 달성 현황

| 기준 (Plan FR) | 결과 |
|---------------|------|
| FR-01: HWPX 형식 출력 | ✅ python-hwpx v2.5 기반 생성 완료 |
| FR-02: DOCX와 동일한 섹션 구성 | ✅ 동일한 `sections` dict 입력 인터페이스 |
| FR-03: Supabase Storage 업로드 | ✅ `proposal-files` 버킷 업로드 + 실패 플래그 |
| FR-04: 다운로드 API 엔드포인트 | ✅ `/proposals/{id}/download/hwpx` |
| FR-05: 프론트엔드 다운로드 버튼 | ✅ 조건부 렌더링 (soft fail 시 숨김) |

---

## 6. 품질 지표

| 지표 | 값 |
|------|-----|
| 최종 Match Rate | 98% |
| PDCA 반복 횟수 | 2회 (Act-1 + Act-2) |
| 구현 기간 | 1일 (2026-03-07) |
| 수정된 갭 수 | 6개 (Act-1) + 5개 서식 개선 (Act-2) |
| 신규 파일 수 | 3개 (hwpx_builder.py, hwp-output.design.md, hwp-output.analysis.md) |
| 성공 기준 달성 | 5/5 (100%) |
| 서식 표준화 | 7종 스타일, 3종 폰트 (맑은 고딕·휴먼명조·HY헤드라인M) |

---

## 7. 잔여 항목 (v2 이관)

| 항목 | 설명 |
|------|------|
| ~~스타일 템플릿~~ | ✅ Act-2에서 샘플 분석 기반 서식 표준화 완료 |
| 한글 검증 자동화 | 한글 프로그램 실제 열기 CI 미구성 |
| 복잡한 레이아웃 | 표/이미지/차트 미지원 (텍스트+제목만) |
| 줄 간격·단락 간격 | paraPr lineSpacing 미적용 (기본값 사용) |

---

## 8. 다음 단계

```bash
# Supabase에 schema 적용 (schema.sql 변경사항)
# Dashboard > SQL Editor 또는 supabase db push

# 의존성 확인
uv sync  # python-hwpx>=2.5 설치 확인
```
