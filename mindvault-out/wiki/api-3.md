# API 에러 마이그레이션 갭 분석 & 3. 발견된 갭
Cohesion: 0.25 | Nodes: 8

## Key Nodes
- **API 에러 마이그레이션 갭 분석** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\api-error-migration.analysis.md) -- 5 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
- **3. 발견된 갭** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\api-error-migration.analysis.md) -- 3 connections
  - -> contains -> [[medium]]
  - -> contains -> [[low]]
  - <- contains <- [[api]]
- **1. 분석 범위** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\api-error-migration.analysis.md) -- 1 connections
  - <- contains <- [[api]]
- **2. 마이그레이션 완성도** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\api-error-migration.analysis.md) -- 1 connections
  - <- contains <- [[api]]
- **4. 권장 조치** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\api-error-migration.analysis.md) -- 1 connections
  - <- contains <- [[api]]
- **5. 결론** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\api-error-migration.analysis.md) -- 1 connections
  - <- contains <- [[api]]
- **LOW (참고)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\api-error-migration.analysis.md) -- 1 connections
  - <- contains <- [[3]]
- **MEDIUM (개선 권장)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\api-error-migration.analysis.md) -- 1 connections
  - <- contains <- [[3]]

## Internal Relationships
- 3. 발견된 갭 -> contains -> MEDIUM (개선 권장) [EXTRACTED]
- 3. 발견된 갭 -> contains -> LOW (참고) [EXTRACTED]
- API 에러 마이그레이션 갭 분석 -> contains -> 1. 분석 범위 [EXTRACTED]
- API 에러 마이그레이션 갭 분석 -> contains -> 2. 마이그레이션 완성도 [EXTRACTED]
- API 에러 마이그레이션 갭 분석 -> contains -> 3. 발견된 갭 [EXTRACTED]
- API 에러 마이그레이션 갭 분석 -> contains -> 4. 권장 조치 [EXTRACTED]
- API 에러 마이그레이션 갭 분석 -> contains -> 5. 결론 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 API 에러 마이그레이션 갭 분석, 3. 발견된 갭, 1. 분석 범위를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 api-error-migration.analysis.md이다.

### Key Facts
- - **Feature**: api (HTTPException → TenopAPIError 마이그레이션) - **분석일**: 2026-03-26 - **Match Rate**: 93%
- | 항목 | 값 | |------|-----| | 대상 디렉토리 | `app/api/routes_*.py`, `app/exceptions.py` | | 검사 파일 수 | 24개 라우트 파일 + exceptions.py + main.py | | 마이그레이션 대상 | HTTPException 155건 (15개 파일) | | 신규 에러 클래스 | 16개 (TEAM 3, BID 2, G2B 2, FILE 2, GEN 7) |
- | 검사 항목 | 결과 | |-----------|------| | `raise HTTPException` in `app/api/` | **0건** — PASS | | `from fastapi import HTTPException` in `app/api/` | **0건** — PASS | | `except HTTPException` in `app/api/` | **0건** — PASS | | TenopAPIError handler (main.py) | **등록 확인** — PASS | | HTTP status code 보존 |…
- 1. **GAP-1**: `AdminValidationError(ADMIN_001, 422)` + `AdminInvalidInputError(ADMIN_006, 400)` 분리 2. **GAP-2**: `routes_admin.py:432`의 `KB_001` → `ADMIN_008` 등 별도 코드 사용 3. **GAP-3**: `PRICING_` 프리픽스 등록 또는 기존 `PROP_002`/`GEN_001`로 대체 4. **GAP-6**: 레거시 미들웨어 삭제 시 자동 해소 (낮은 우선순위) 5. **GAP-7**: 구현 시…
- | 지표 | 값 | |------|-----| | **Match Rate** | **93%** | | 마이그레이션 완성도 | 100% (app/api/) | | HIGH 갭 | 0건 | | MEDIUM 갭 | 3건 (에러 코드 충돌/불일치) | | LOW 갭 | 4건 (레거시, 참고사항) |
