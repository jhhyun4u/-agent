# Gap Analysis: hwp-output

## 메타 정보

| 항목 | 내용 |
| ---- | ---- |
| Feature | hwp-output |
| 분석일 | 2026-03-07 |
| 기준 설계 | docs/02-design/features/hwp-output.design.md |
| **Match Rate** | **85%** |
| 상태 | P1 DB 스키마 갭 즉시 수정 필요 → 95%+ 달성 가능 |

---

## 요약

`hwpx_builder.py`, `phase_executor.py` 통합, `routes_v31.py` 다운로드, 프론트엔드 버튼 모두 구현 완료.
**DB 스키마**(`schema.sql`)가 코드 변경을 반영하지 못한 것이 핵심 갭이며, 실제 배포 시 런타임 오류를 유발함.

---

## 섹션별 Gap 분석

### 1. hwpx_builder.py (100%)

| 항목 | 설계 | 구현 | 상태 |
| ---- | ---- | ---- | ---- |
| `build_hwpx()` 동기 함수 | ✅ | ✅ | ✅ |
| `build_hwpx_async()` 비동기 래퍼 | ✅ | `asyncio.to_thread` 사용 | ✅ |
| 표지 (_add_cover) | 제목/사업명/발주처/제안업체 | 완전 구현 | ✅ |
| 평가항목 참조표 (_add_evaluation_table) | 5열 동적 테이블 | 구현 + 텍스트 폴백 | ✅ |
| 목차 (_add_toc) | 4장 고정 목차 | 완전 구현 | ✅ |
| 본문 기호 체계 | □/❍/☞/【】/- | `_add_content_paragraph` 완전 구현 | ✅ |
| 부록 처리 | 매핑 외 섹션 자동 추가 | 완전 구현 | ✅ |
| metadata 스펙 | client_name/proposer_name 등 5개 | 완전 구현 | ✅ |

### 2. phase_executor.py 통합 (90%)

| 항목 | 설계 | 구현 | 상태 |
| ---- | ---- | ---- | ---- |
| HWPX 빌드 호출 | `build_hwpx` after Phase 4 | 완전 구현 | ✅ |
| hwpx_metadata 자동 조립 | session.rfp_metadata 기반 | 완전 구현 | ✅ |
| soft fail 처리 | warning + hwpx_path="" | `logger.warning` + `hwpx_path=""` | ✅ |
| `_upload_to_storage` hwpx 파라미터 | `hwpx_path=""` 기본값 | 완전 구현 | ✅ |
| `storage_path_hwpx` DB 업데이트 | proposals 테이블 업데이트 | 코드 존재하나 DB 컬럼 없음 | ❌ G1 |

### 3. DB 스키마 (30%)

| 항목 | 설계 | schema.sql 현황 | 상태 |
| ---- | ---- | --------------- | ---- |
| `proposals.storage_path_hwpx TEXT` | 필요 | **컬럼 없음** | ❌ G1 |
| `proposals.status` CHECK에 `'running'` | 필요 | `'running'` 미포함 (processing/initialized/...) | ❌ G2 |
| `proposal_phases.phase_num` | 설계/코드 기준 | `phase_number` (이름 불일치) | ❌ G3 |
| `proposal_phases.artifact_json` | 설계/코드 기준 | `artifact` (이름 불일치) | ❌ G3 |
| `proposals.failed_phase TEXT` | INTEGER 설계 | `TEXT` 타입 | ⚠️ G4 |

> G2~G4는 hwp-output 신규 갭이 아닌 proposal-platform-v1 Act-1에서 코드만 수정하고 **schema.sql을 업데이트하지 않아** 발생한 잔여 갭.

### 4. routes_v31.py (100%)

| 항목 | 설계 | 구현 | 상태 |
| ---- | ---- | ---- | ---- |
| `file_type` 검증 (docx/pptx/hwpx) | ✅ | 완전 구현 | ✅ |
| Storage 서명 URL 생성 | ✅ | `create_signed_url` 5분 유효 | ✅ |
| 로컬 파일 폴백 | ✅ | `FileResponse` | ✅ |
| 라우트 형식 | `/download/{file_type}` (path param) | `/download/{file_type}` | ✅ |

> 설계 문서(section 2-3)에 `?file_type=hwpx` 쿼리 파라미터로 기재됐으나 실제 구현은 path param `/download/{file_type}` — 문서 오류, 코드가 정확함.

### 5. 프론트엔드 버튼 (80%)

| 항목 | 설계 | 구현 | 상태 |
| ---- | ---- | ---- | ---- |
| HWPX 다운로드 버튼 존재 | ✅ | `href={downloadUrl("hwpx")}` | ✅ |
| `isCompleted` 조건부 렌더링 | ✅ | 완료 섹션 내에 존재 | ✅ |
| `hwpx_path` 존재 여부 조건부 | soft fail 시 버튼 비활성화 | 항상 표시 (조건 없음) | ❌ G5 |

### 6. 의존성 (100%)

| 항목 | 설계 | 구현 | 상태 |
| ---- | ---- | ---- | ---- |
| `python-hwpx>=2.5` | pyproject.toml | 완전 구현 | ✅ |

---

## 갭 목록

### P1 — Critical (즉시 수정 필요)

| ID | 파일 | 설계 | 구현 | 영향 |
| -- | ---- | ---- | ---- | ---- |
| G1 | database/schema.sql | `proposals.storage_path_hwpx TEXT` | 컬럼 없음 | HWPX Storage 경로 저장 실패 → 다운로드 불가 |
| G2 | database/schema.sql | `status CHECK` 에 `'running'` 포함 | `'running'` 미포함 | `status="running"` 업데이트 → CHECK 위반 |
| G3 | database/schema.sql | `proposal_phases.phase_num`, `artifact_json` | `phase_number`, `artifact` | upsert 컬럼명 불일치 → DB 오류 |

### P2 — Major (수정 권장)

| ID | 파일 | 설명 |
| -- | ---- | ---- |
| G4 | database/schema.sql | `proposals.failed_phase TEXT` → `INTEGER` 변경 필요 (코드는 int 저장) |
| G5 | frontend/app/proposals/[id]/page.tsx | `hwpx_path` 없을 때 HWPX 버튼 숨기기 (`status.hwpx_path` 조건 추가) |

### P3 — Minor (문서 수정)

| ID | 파일 | 설명 |
| -- | ---- | ---- |
| G6 | docs/02-design/features/hwp-output.design.md | section 2-3 URL 형식 오류: `?file_type=hwpx` → `/download/hwpx` (path param)으로 수정 |

---

## Match Rate 계산

| 영역 | 가중치 | 달성률 | 점수 |
| ---- | ------ | ------ | ---- |
| hwpx_builder.py | 25% | 100% | 25 |
| phase_executor 통합 | 25% | 90% | 22.5 |
| DB 스키마 | 15% | 30% | 4.5 |
| routes_v31.py | 15% | 100% | 15 |
| 프론트엔드 | 15% | 80% | 12 |
| 의존성 | 5% | 100% | 5 |
| **합계** | **100%** | — | **84 ≈ 85%** |

> P1 갭(G1~G3) 수정 시 예상 Match Rate: **95%+**

---

## 권장 수정 순서

```
1. [G1] database/schema.sql: proposals 테이블에 storage_path_hwpx TEXT 컬럼 추가  (5분)
2. [G2] database/schema.sql: proposals.status CHECK에 'running' 추가               (3분)
3. [G3] database/schema.sql: proposal_phases 컬럼명 phase_number→phase_num,
                              artifact→artifact_json 변경 (기존 데이터 없으면 rename) (5분)
4. [G4] database/schema.sql: proposals.failed_phase TEXT→INTEGER 타입 변경          (3분)
5. [G5] frontend: status.hwpx_path 존재 시에만 HWPX 버튼 렌더링                    (5분)
6. [G6] docs/02-design/hwp-output.design.md: URL 형식 오류 수정                    (2분)
```

P1 완료 후: `/pdca report hwp-output`
