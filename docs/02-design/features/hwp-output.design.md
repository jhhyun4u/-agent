# Design: hwp-output

## 메타 정보

| 항목 | 내용 |
| ---- | ---- |
| Feature | hwp-output |
| 설계일 | 2026-03-07 |
| 기준 Plan | docs/01-plan/features/hwp-output.plan.md |
| 구현 상태 | 완료 (proposal-platform-v1 Act-2에서 통합) |
| 기술 접근 | Option C — python-hwpx 라이브러리 (v2.5) |

---

## 1. 아키텍처 개요

```text
RFP 파싱
  └─ Phase 4 실행 (proposal_generator)
       └─ Phase4Artifact.sections (dict)
            ├─ docx_builder.build_docx()     → .docx
            ├─ pptx_builder.build_pptx()     → .pptx
            └─ hwpx_builder.build_hwpx()     → .hwpx
                   └─ phase_executor._upload_to_storage()
                         └─ Supabase Storage (proposal-files 버킷)
                               └─ /proposals/{id}/download/hwpx
```

---

## 2. 컴포넌트 설계

### 2-1. `app/services/hwpx_builder.py`

기술 선택: python-hwpx (v2.5) — `HwpxDocument` API

#### 공개 함수

| 함수 | 시그니처 | 설명 |
| ---- | -------- | ---- |
| `build_hwpx` | `(sections, output_path, project_name, metadata) -> Path` | 동기 빌드 |
| `build_hwpx_async` | `(sections, output_path, project_name, metadata) -> Path` | asyncio.to_thread 래퍼 |

#### 문서 구조

```text
표지 (_add_cover)
  - 제목 "제   안   서" (bold)
  - 사업명, 입찰공고번호, 제출일, 발주처, 제안업체
평가항목 참조표 (_add_evaluation_table)
  - 5열 테이블: 구분/평가항목/심사항목/배점/해당 페이지
  - evaluation_weights dict 기반 동적 생성
  - 테이블 생성 실패 시 텍스트 폴백
목차 (_add_toc)
  - 4개 장(Ⅰ~Ⅳ), 7개 소절 고정 목차
본문 (_add_body)
  - _CHAPTER_MAP: 4개 장 → sections 키 매핑
  - _add_content_paragraph: □/❍/☞/【】/- 기호 체계 처리
  - 매핑 외 섹션 → "부록" 자동 추가
```

#### 기호 체계 매핑

| 기호 | 처리 | 스타일 |
| ---- | ---- | ------ |
| `□` | 대분류 | bold prefix |
| `❍` | 중분류 | 2칸 들여쓰기 |
| `☞` | 후속과제 | 2칸 들여쓰기 |
| `【】` | 핵심강조 | bold 전체 |
| `(근거:)` | 법령출처 | 4칸 들여쓰기 |
| `-` | 소분류 | 4칸 들여쓰기 |
| `숫자.` | 번호목록 | bold 전체 |

#### metadata 스펙

```python
{
    "client_name": str,          # 발주처
    "proposer_name": str,        # 제안업체명
    "submit_date": str,          # "2026. 3." 형식
    "bid_notice_number": str,    # 입찰공고번호
    "evaluation_weights": dict,  # {"항목명": 배점, ...}
}
```

---

### 2-2. `app/services/phase_executor.py` — HWPX 통합

#### Phase 4 완료 후 빌드 순서

```python
# Phase 4 artifact 기준
docx_path = build_docx(sections, ...)
pptx_path = build_pptx(sections, ...)
hwpx_path = await asyncio.to_thread(build_hwpx, sections, Path(...), project_name, hwpx_metadata)
# 실패 시 hwpx_path = "" (무시, DOCX/PPTX는 계속 진행)
```

#### hwpx_metadata 구성 (phase_executor에서 자동 조립)

```python
hwpx_metadata = {
    "client_name":       session.rfp_metadata.client_name,
    "proposer_name":     session.rfp_metadata.proposer_name,
    "submit_date":       session.rfp_metadata.submit_date,
    "bid_notice_number": session.rfp_metadata.bid_notice_number,
    "evaluation_weights": session.rfp_metadata.evaluation_weights,
}
```

#### 실패 처리

- HWPX 생성 예외 → `logger.warning` + `hwpx_path = ""` (soft fail)
- Storage 업로드 실패 → `storage_upload_failed = True` 플래그 기록

---

### 2-3. `app/api/routes_v31.py` — 다운로드 엔드포인트

```http
GET /proposals/{proposal_id}/download/hwpx
```

- `file_type` 검증: `docx | pptx | hwpx` (그 외 400)
- `storage_path_hwpx` 컬럼에서 경로 조회
- Supabase Storage 서명 URL 생성 → `RedirectResponse`

---

### 2-4. `frontend/app/proposals/[id]/page.tsx` — 다운로드 버튼

```tsx
{status.hwpx_path && (
  <a href={downloadUrl("hwpx")}>HWPX 다운로드</a>
)}
```

- `downloadUrl(type)` 함수: `/v3.1/proposals/{id}/download/{type}`
- `status.hwpx_path` 존재 시에만 버튼 렌더링 (soft fail 시 숨김)

---

## 3. 데이터 흐름

```sql
-- proposals 테이블
storage_path_docx       TEXT,
storage_path_pptx       TEXT,
storage_path_hwpx       TEXT,   -- 신규 컬럼
storage_upload_failed   BOOLEAN
```

```text
Supabase Storage (proposal-files 버킷)
  └── {proposal_id}/
        ├── proposal.docx
        ├── proposal.pptx
        └── proposal.hwpx
```

---

## 4. 오류 처리 전략

| 시나리오 | 처리 |
| -------- | ---- |
| python-hwpx ImportError | 앱 시작 시 감지 — 의존성 설치 필요 |
| HWPX 빌드 예외 | soft fail — DOCX/PPTX 업로드는 계속 |
| 평가항목 테이블 생성 실패 | 텍스트 폴백으로 대체 |
| Storage 업로드 실패 | `storage_upload_failed=True` + 로컬 파일 유지 |
| `hwpx_path` 없는 상태에서 다운로드 요청 | 404 반환 |

---

## 5. 의존성

```toml
# pyproject.toml
python-hwpx = ">=2.5"
```

---

## 6. 미결 사항 (v2 이관)

| 항목 | 설명 |
| ---- | ---- |
| 스타일 템플릿 | 현재 스타일 없음 — v2에서 HWP 템플릿 기반 스타일 적용 |
| 한글 검증 자동화 | 한글 프로그램 실제 열기 테스트 CI 미구성 |
| 복잡한 레이아웃 | 표/이미지/차트 미지원 (텍스트+제목 구조만) |
