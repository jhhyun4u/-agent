# 섹션별 Gap 분석 & Gap Analysis: hwp-output
Cohesion: 0.17 | Nodes: 12

## Key Nodes
- **섹션별 Gap 분석** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\hwp-output.analysis.md) -- 10 connections
  - -> contains -> [[1-hwpxbuilderpy-100]]
  - -> contains -> [[2-phaseexecutorpy-90]]
  - -> contains -> [[3-db-30]]
  - -> contains -> [[4-routesv31py-100]]
  - -> contains -> [[5-80]]
  - -> contains -> [[6-100]]
  - -> contains -> [[p1-critical]]
  - -> contains -> [[p2-major]]
  - -> contains -> [[p3-minor]]
  - <- contains <- [[gap-analysis-hwp-output]]
- **Gap Analysis: hwp-output** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\hwp-output.analysis.md) -- 2 connections
  - -> contains -> [[gap]]
  - -> contains -> [[match-rate]]
- **1. hwpx_builder.py (100%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\hwp-output.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **2. phase_executor.py 통합 (90%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\hwp-output.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **3. DB 스키마 (30%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\hwp-output.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **4. routes_v31.py (100%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\hwp-output.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **5. 프론트엔드 버튼 (80%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\hwp-output.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **6. 의존성 (100%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\hwp-output.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **Match Rate 계산** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\hwp-output.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-hwp-output]]
- **P1 — Critical (즉시 수정 필요)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\hwp-output.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **P2 — Major (수정 권장)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\hwp-output.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **P3 — Minor (문서 수정)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\hwp-output.analysis.md) -- 1 connections
  - <- contains <- [[gap]]

## Internal Relationships
- 섹션별 Gap 분석 -> contains -> 1. hwpx_builder.py (100%) [EXTRACTED]
- 섹션별 Gap 분석 -> contains -> 2. phase_executor.py 통합 (90%) [EXTRACTED]
- 섹션별 Gap 분석 -> contains -> 3. DB 스키마 (30%) [EXTRACTED]
- 섹션별 Gap 분석 -> contains -> 4. routes_v31.py (100%) [EXTRACTED]
- 섹션별 Gap 분석 -> contains -> 5. 프론트엔드 버튼 (80%) [EXTRACTED]
- 섹션별 Gap 분석 -> contains -> 6. 의존성 (100%) [EXTRACTED]
- 섹션별 Gap 분석 -> contains -> P1 — Critical (즉시 수정 필요) [EXTRACTED]
- 섹션별 Gap 분석 -> contains -> P2 — Major (수정 권장) [EXTRACTED]
- 섹션별 Gap 분석 -> contains -> P3 — Minor (문서 수정) [EXTRACTED]
- Gap Analysis: hwp-output -> contains -> 섹션별 Gap 분석 [EXTRACTED]
- Gap Analysis: hwp-output -> contains -> Match Rate 계산 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 섹션별 Gap 분석, Gap Analysis: hwp-output, 1. hwpx_builder.py (100%)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 hwp-output.analysis.md이다.

### Key Facts
- 1. hwpx_builder.py (100%)
- | 항목 | 설계 | 구현 | 상태 | | ---- | ---- | ---- | ---- | | `build_hwpx()` 동기 함수 | ✅ | ✅ | ✅ | | `build_hwpx_async()` 비동기 래퍼 | ✅ | `asyncio.to_thread` 사용 | ✅ | | 표지 (_add_cover) | 제목/사업명/발주처/제안업체 | 완전 구현 | ✅ | | 평가항목 참조표 (_add_evaluation_table) | 5열 동적 테이블 | 구현 + 텍스트 폴백 | ✅ | | 목차 (_add_toc) | 4장 고정 목차 |…
- | 항목 | 설계 | 구현 | 상태 | | ---- | ---- | ---- | ---- | | HWPX 빌드 호출 | `build_hwpx` after Phase 4 | 완전 구현 | ✅ | | hwpx_metadata 자동 조립 | session.rfp_metadata 기반 | 완전 구현 | ✅ | | soft fail 처리 | warning + hwpx_path="" | `logger.warning` + `hwpx_path=""` | ✅ | | `_upload_to_storage` hwpx 파라미터 |…
- | 항목 | 설계 | schema.sql 현황 | 상태 | | ---- | ---- | --------------- | ---- | | `proposals.storage_path_hwpx TEXT` | 필요 | **컬럼 없음** | ❌ G1 | | `proposals.status` CHECK에 `'running'` | 필요 | `'running'` 미포함 (processing/initialized/...) | ❌ G2 | | `proposal_phases.phase_num` | 설계/코드 기준 | `phase_number` (이름…
- | 항목 | 설계 | 구현 | 상태 | | ---- | ---- | ---- | ---- | | `file_type` 검증 (docx/pptx/hwpx) | ✅ | 완전 구현 | ✅ | | Storage 서명 URL 생성 | ✅ | `create_signed_url` 5분 유효 | ✅ | | 로컬 파일 폴백 | ✅ | `FileResponse` | ✅ | | 라우트 형식 | `/download/{file_type}` (path param) | `/download/{file_type}` | ✅ |
