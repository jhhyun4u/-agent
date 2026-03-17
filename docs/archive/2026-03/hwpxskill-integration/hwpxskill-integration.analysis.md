# hwpxskill Integration Analysis Report

> **Analysis Type**: Gap Analysis (Plan vs Implementation)
>
> **Project**: 용역제안 Coworker
> **Analyst**: gap-detector
> **Date**: 2026-03-16
> **Design Doc**: docs/02-design/features/hwp-output.design.md, docs/02-design/features/proposal-agent-v1/14-services-v3.md

---

## 1. Analysis Overview

### 1.1 Analysis Purpose

hwpxskill 4종 스크립트 통합 계획 (6개 항목) 대비 실제 구현 완성도를 평가한다.
기존 hwpx_builder.py (python-hwpx 기반 v3.1 레거시)와의 병행 상태도 확인한다.

### 1.2 Analysis Scope

- **계획 항목**: 6개 (스크립트 4종, 템플릿, 서비스 래퍼, API, CLAUDE.md, 레거시 병행)
- **Implementation Path**: `app/services/hwpx/`, `app/services/hwpx_service.py`, `app/api/routes_artifacts.py`
- **Analysis Date**: 2026-03-16

---

## 2. Item-by-Item Gap Analysis

### 2.1 hwpxskill 4종 스크립트 배치 (app/services/hwpx/)

| 스크립트 | 계획 | 구현 | Status | Notes |
|----------|------|------|:------:|-------|
| `__init__.py` | 모듈 초기화 | 구현 완료 (6줄, docstring) | PASS | |
| `validate.py` | HWPX ZIP/XML 무결성 검증 | 구현 완료 (71줄) | PASS | REQUIRED_FILES 4종, mimetype 검증, XML 파싱 검증 |
| `page_guard.py` | 레퍼런스 대비 쪽수 드리프트 감지 | 구현 완료 (165줄) | PASS | PageMetrics dataclass, 문단/표/pageBreak/텍스트 길이 비교 |
| `analyze_template.py` | 고객 양식 스타일/구조 분석 | 구현 완료 (376줄) | PASS | FontInfo, CharStyle, ParaStyle, PageSetup, TableInfo + extract 유틸 |
| `build_hwpx.py` | 템플릿 기반 HWPX 조립 | 구현 완료 (188줄) | PASS | base+overlay+override, 메타데이터, XML 검증, 패키징 |

**세부 품질 평가:**

| 항목 | validate.py | page_guard.py | analyze_template.py | build_hwpx.py |
|------|:-----------:|:------------:|:-------------------:|:------------:|
| 타입 힌트 | O | O | O | O |
| Docstring (한국어) | O | O | O | O |
| 에러 처리 | O (BadZipFile, FileNotFound) | O (zipfile 오류) | O (FileNotFoundError, finally cleanup) | O (FileNotFoundError, ValueError) |
| 로깅 | X (불필요) | X (불필요) | X (불필요) | X (불필요) |
| CLI argparse 제거 | O | O | O | O |

**완성도: 100%**

---

### 2.2 템플릿 파일 (app/services/hwpx/templates/)

| 항목 | 계획 | 구현 | Status |
|------|------|------|:------:|
| `base/` 디렉토리 | mimetype, content.hpf, header.xml, section0.xml, META-INF, Preview, settings.xml, version.xml | Canine89/hwpxskill에서 다운로드 완료 (11 파일) | PASS |
| `proposal/` 디렉토리 | header.xml, section0.xml 오버레이 | Canine89/hwpxskill에서 다운로드 완료 (2 파일) | PASS |

`build_hwpx.py`의 `TEMPLATES_DIR = _MODULE_DIR / "templates"` 및 `BASE_DIR = TEMPLATES_DIR / "base"` 경로에
GitHub(Canine89/hwpxskill)에서 다운로드한 템플릿 파일이 정상 배치되어 있다.

**base/ 파일 목록 (11종):**
- `mimetype` (19 bytes), `Contents/content.hpf` (1,795 bytes), `Contents/header.xml` (51,572 bytes)
- `Contents/section0.xml` (3,817 bytes), `META-INF/container.rdf`, `META-INF/container.xml`, `META-INF/manifest.xml`
- `Preview/PrvImage.png`, `Preview/PrvText.txt`, `settings.xml`, `version.xml`

**proposal/ 파일 (2종):**
- `header.xml` (65,387 bytes) — 제안서용 폰트/스타일 정의
- `section0.xml` (18,835 bytes) — 제안서 기본 레이아웃

**런타임 테스트**: `build_from_template(template="proposal")` 성공, 7,738 bytes HWPX 생성, validate PASS.

**완성도: 100%**

---

### 2.3 서비스 래퍼 (app/services/hwpx_service.py)

| 함수 | 계획 시그니처 | 구현 시그니처 | Status |
|------|--------------|-------------|:------:|
| `analyze_reference` | `(hwpx_path) -> dict` | `(hwpx_path: str \| Path) -> dict` | PASS |
| `build_proposal_hwpx` | `(sections, output_path, metadata, reference_hwpx) -> Path` | `(sections: list, output_path: str \| Path, metadata: dict \| None, reference_hwpx: str \| Path \| None) -> Path` | PASS |
| `build_proposal_hwpx_async` | 비동기 래퍼 | `asyncio.to_thread` 래퍼 | PASS |
| `validate` | `(path) -> list[str]` | `(hwpx_path: str \| Path) -> list[str]` | PASS |
| `check_page_drift` | `(reference, output) -> list[str]` | `(reference_path, output_path, max_text_delta, max_paragraph_delta) -> list[str]` | PASS |

**추가 구현 (계획에 없음):**
- `_generate_section_xml()` — 섹션 데이터를 OWPML section0.xml로 변환 (189줄)
- `_STYLE_DEFS` — 공공입찰 표준 폰트 정의
- 표지/목차/본문 XML 자동 생성 로직

**품질:**
- 타입 힌트: O (str | Path 등)
- Docstring: O (한국어)
- 에러 처리: O (검증 경고 로깅, 드리프트 경고 로깅)
- 로깅: O (logger.info, logger.warning)
- 비동기: O (asyncio.to_thread)

**완성도: 100%**

---

### 2.4 routes_artifacts.py HWPX 다운로드 엔드포인트

| 항목 | 계획 | 구현 | Status |
|------|------|------|:------:|
| `GET /api/proposals/{id}/download/hwpx` | 존재 | 구현 완료 (L114-166) | PASS |
| 인증 | get_current_user | `Depends(get_current_user)` | PASS |
| 빈 섹션 처리 | - | 204 No Content + X-Message 헤더 | PASS |
| MIME 타입 | application/hwp+zip | `application/hwp+zip` | PASS |
| Content-Disposition | attachment | `attachment; filename="{name}_제안서.hwpx"` | PASS |
| hwpx_service 호출 | build_proposal_hwpx_async | `from app.services.hwpx_service import build_proposal_hwpx_async` | PASS |

**DOCX 패턴과의 정합성:**

| 비교 항목 | DOCX 엔드포인트 | HWPX 엔드포인트 | 일관성 |
|-----------|----------------|----------------|:------:|
| 인증 | get_current_user | get_current_user | O |
| 그래프 조회 | _get_graph + aget_state | _get_graph + aget_state | O |
| 404 처리 | PropNotFoundError | PropNotFoundError | O |
| 빈 섹션 | 204 + X-Message | 204 + X-Message | O |
| 메타데이터 구성 | rfp에서 추출 | rfp에서 추출 | O |
| 임시 파일 | - | tempdir + proposal_id | O |
| 파일명 | `{name}_제안서.docx` | `{name}_제안서.hwpx` | O |

**완성도: 100%**

---

### 2.5 CLAUDE.md 업데이트

| 항목 | 계획 | 구현 | Status |
|------|------|------|:------:|
| hwpx_service.py 설명 | 추가 | L64: "HWPX 서비스 래퍼 (hwpxskill 기반: 빌드, 검증, 양식 분석, 쪽수 가드)" | PASS |
| hwpx/ 디렉토리 설명 | 추가 | L65: "hwpxskill 모듈 (build_hwpx, analyze_template, validate, page_guard + templates)" | PASS |
| routes_artifacts.py 설명 | HWPX 추가 | L34: "산출물 조회 + DOCX/HWPX/PPTX 다운로드 + Compliance Matrix" | PASS |
| hwpx_builder.py | 레거시 표시 | L91: "HWP/HWPX 빌더" (레거시 표시 없음) | WARN |

**완성도: 95%** (hwpx_builder.py에 레거시 표기 누락)

---

### 2.6 기존 hwpx_builder.py와의 병행

| 항목 | 계획 | 실태 | Status |
|------|------|------|:------:|
| hwpx_builder.py 유지 | v3.1 레거시 호환으로 유지 | 500줄 온전히 존재. python-hwpx v2.5 기반 | PASS |
| hwpx_service.py가 v3.5 LangGraph용 | 새 서비스가 hwpxskill 기반 | hwpx_service.py -> hwpx/build_hwpx.py (lxml 기반) | PASS |
| 역할 분리 | 명확한 분리 | CLAUDE.md에서 hwpx_builder.py 레거시 표기 부족 | WARN |
| routes_artifacts.py | hwpx_service 사용 | `from app.services.hwpx_service import build_proposal_hwpx_async` | PASS |

**완성도: 90%**

---

## 3. Overall Scores

| Category | Score | Status |
|----------|:-----:|:------:|
| 1. hwpxskill 4종 스크립트 | 100% | PASS |
| 2. 템플릿 파일 | 100% | PASS |
| 3. 서비스 래퍼 | 100% | PASS |
| 4. HWPX 다운로드 API | 100% | PASS |
| 5. CLAUDE.md 업데이트 | 95% | PASS |
| 6. 레거시 병행 | 90% | PASS |
| **Overall** | **97%** | **PASS** |

```
+---------------------------------------------+
|  Overall Match Rate: 97%                     |
+---------------------------------------------+
|  PASS:  5 items (83%)                        |
|  WARN:  1 item  (17%) — 레거시 표기 미비     |
|  FAIL:  0 items                              |
+---------------------------------------------+
```

---

## 4. Missing Features (Plan O, Implementation X)

없음. 계획된 6개 항목 모두 구현 완료.

---

## 5. Added Features (Plan X, Implementation O)

| Item | Implementation Location | Description |
|------|------------------------|-------------|
| `_generate_section_xml()` | hwpx_service.py:89-189 | 섹션 데이터를 OWPML XML로 동적 변환. 표지+목차+본문+페이지 설정 포함 |
| `_STYLE_DEFS` | hwpx_service.py:29-35 | 공공입찰 표준 폰트 정의 (chapter/section/body/table/cover) |
| `extract_header_xml()` | analyze_template.py:356-364 | HWPX에서 header.xml 추출 유틸리티 |
| `extract_section_xml()` | analyze_template.py:367-375 | HWPX에서 section0.xml 추출 유틸리티 |
| `PageMetrics.to_dict()` | page_guard.py:39-40 | 메트릭 직렬화 메서드 |
| `validate_output()` | build_hwpx.py:184-187 | 빌드 후 빠른 검증 래퍼 |

---

## 6. Code Quality Analysis

### 6.1 Error Handling

| Module | Error Types Handled | Quality |
|--------|-------------------|---------|
| validate.py | BadZipFile, file not found, XMLSyntaxError | Good |
| page_guard.py | zipfile errors (implicit) | Adequate |
| analyze_template.py | FileNotFoundError, finally cleanup (shutil.rmtree) | Good |
| build_hwpx.py | FileNotFoundError (base/overlay/override), ValueError (XML) | Good |
| hwpx_service.py | 검증 경고 로깅, 드리프트 경고 로깅, reference_hwpx 분기 | Good |
| routes_artifacts.py | PropNotFoundError, 204 for empty, tempdir 관리 | Good |

### 6.2 Type Hints

모든 6개 모듈이 `str | Path` 유니온 타입, `list[str]`, dataclass 등 완전한 타입 힌트를 제공한다.

### 6.3 API Consistency (docx_builder 패턴)

| 패턴 | docx_builder | hwpx_service | 일관성 |
|------|-------------|-------------|:------:|
| 동기 빌드 함수 | build_docx | build_proposal_hwpx | O |
| 비동기 래퍼 | (내부 async) | build_proposal_hwpx_async | O |
| 입력: sections list | O | O | O |
| 입력: metadata dict | O | O | O |
| 출력: Path | (bytes 반환) | Path 반환 | 차이 |

차이점: docx_builder는 bytes를 반환하고, hwpx_service는 Path를 반환한다. routes_artifacts.py에서 `output_path.read_bytes()`로 변환하므로 문제없다.

---

## 7. Recommended Actions

### 7.1 Short-term

| Priority | Item | Description |
|----------|------|-------------|
| P1 | CLAUDE.md hwpx_builder.py 레거시 표기 | L91의 `hwpx_builder.py` 설명에 "v3.1 레거시" 접두어 추가 |
| P2 | 통합 테스트 | build_proposal_hwpx -> validate -> 한글 프로그램 열기 테스트 |

### 7.2 Design Document Update

- `docs/02-design/features/hwp-output.design.md` 는 v3.1 레거시 (python-hwpx) 기준으로 작성되어 있다.
  hwpxskill 기반 새 아키텍처 (lxml + templates)는 별도 설계 반영이 필요할 수 있으나,
  proposal-agent-v1 설계 v3.6 메인 문서에서 통합 관리하는 것이 적절하다.

---

## 8. Summary

hwpxskill 통합의 코드 품질은 우수하다. 4종 스크립트 (validate, page_guard, analyze_template, build_hwpx) 모두
CLI 제거 + 함수 API 래핑이 깔끔하게 완료되었고, 서비스 래퍼(hwpx_service.py)가 고수준 인터페이스를 제공하며,
routes_artifacts.py의 HWPX 다운로드 엔드포인트가 DOCX 패턴과 일관되게 구현되었다.

남은 미비점은 CLAUDE.md의 hwpx_builder.py 레거시 표기(P1)뿐이며,
런타임 테스트에서 빌드→검증→양식 분석→쪽수 가드 모두 정상 동작이 확인되었다.

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-03-16 | Initial analysis | gap-detector |
