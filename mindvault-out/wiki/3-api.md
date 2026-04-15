# 3. 상세 내역 & API 리팩토링 완료 보고서
Cohesion: 0.13 | Nodes: 16

## Key Nodes
- **3. 상세 내역** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 9 connections
  - -> contains -> [[31-httpexception-tenopapierror]]
  - -> contains -> [[32]]
  - -> contains -> [[33-claude-api]]
  - -> contains -> [[34-g2b]]
  - -> contains -> [[35-prefix]]
  - -> contains -> [[36]]
  - -> contains -> [[37-configenv]]
  - <- contains <- [[api]]
  - <- contains <- [[7]]
- **API 리팩토링 완료 보고서** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 7 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5-check]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
- **7. 변경 파일 전체 목록** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 3 connections
  - -> contains -> [[3]]
  - -> contains -> [[33]]
  - <- contains <- [[api]]
- **1. 작업 목표** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 1 connections
  - <- contains <- [[api]]
- **2. 완료 항목 요약** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 1 connections
  - <- contains <- [[api]]
- **수정 파일 (33)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 1 connections
  - <- contains <- [[7]]
- **3.1 HTTPException → TenopAPIError 마이그레이션** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 1 connections
  - <- contains <- [[3]]
- **3.2 에러 핸들링 보강** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 1 connections
  - <- contains <- [[3]]
- **3.3 Claude API 에러 세분화** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 1 connections
  - <- contains <- [[3]]
- **3.4 G2B 재시도 로직 개선** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 1 connections
  - <- contains <- [[3]]
- **3.5 라우터 prefix 표준화** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 1 connections
  - <- contains <- [[3]]
- **3.6 중복 코드 제거 — 공유 모듈 추출** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 1 connections
  - <- contains <- [[3]]
- **3.7 하드코딩 → config/env 이동** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 1 connections
  - <- contains <- [[3]]
- **4. 품질 지표** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 1 connections
  - <- contains <- [[api]]
- **5. 갭 분석 결과 (Check 단계)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 1 connections
  - <- contains <- [[api]]
- **6. 잔여 작업 (향후 과제)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-refactoring.report.md) -- 1 connections
  - <- contains <- [[api]]

## Internal Relationships
- 3. 상세 내역 -> contains -> 3.1 HTTPException → TenopAPIError 마이그레이션 [EXTRACTED]
- 3. 상세 내역 -> contains -> 3.2 에러 핸들링 보강 [EXTRACTED]
- 3. 상세 내역 -> contains -> 3.3 Claude API 에러 세분화 [EXTRACTED]
- 3. 상세 내역 -> contains -> 3.4 G2B 재시도 로직 개선 [EXTRACTED]
- 3. 상세 내역 -> contains -> 3.5 라우터 prefix 표준화 [EXTRACTED]
- 3. 상세 내역 -> contains -> 3.6 중복 코드 제거 — 공유 모듈 추출 [EXTRACTED]
- 3. 상세 내역 -> contains -> 3.7 하드코딩 → config/env 이동 [EXTRACTED]
- 7. 변경 파일 전체 목록 -> contains -> 3. 상세 내역 [EXTRACTED]
- 7. 변경 파일 전체 목록 -> contains -> 수정 파일 (33) [EXTRACTED]
- API 리팩토링 완료 보고서 -> contains -> 1. 작업 목표 [EXTRACTED]
- API 리팩토링 완료 보고서 -> contains -> 2. 완료 항목 요약 [EXTRACTED]
- API 리팩토링 완료 보고서 -> contains -> 3. 상세 내역 [EXTRACTED]
- API 리팩토링 완료 보고서 -> contains -> 4. 품질 지표 [EXTRACTED]
- API 리팩토링 완료 보고서 -> contains -> 5. 갭 분석 결과 (Check 단계) [EXTRACTED]
- API 리팩토링 완료 보고서 -> contains -> 6. 잔여 작업 (향후 과제) [EXTRACTED]
- API 리팩토링 완료 보고서 -> contains -> 7. 변경 파일 전체 목록 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 3. 상세 내역, API 리팩토링 완료 보고서, 7. 변경 파일 전체 목록를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 api-refactoring.report.md이다.

### Key Facts
- 3.1 HTTPException → TenopAPIError 마이그레이션
- - **Feature**: api - **작업 기간**: 2026-03-25 ~ 2026-03-26 - **PDCA 단계**: Do → Check → Report (Plan/Design 없이 실행형)
- 신규 파일 (3) - `app/api/permissions.py` — 팀 권한 체크 공유 모듈 - `app/utils/pagination.py` — 페이지네이션 유틸리티 - `docs/03-analysis/features/api-error-migration.analysis.md` — 갭 분석
- 백엔드 API 레이어의 코드 품질, 일관성, 유지보수성 개선. 6개 영역을 순차 진행.
- | # | 작업 | 변경 파일 | 주요 지표 | |:-:|------|:---:|------| | 1 | HTTPException → TenopAPIError 마이그레이션 | 16 | 155건 → 0건 (100%) | | 2 | 에러 핸들링 보강 (CRITICAL) | 5 | 21개 엔드포인트 try/except 추가 | | 3 | Claude API 에러 세분화 (HIGH) | 2 | 429/504 구분, 스트리밍 에러 이벤트 | | 4 | G2B 재시도 로직 개선 (MEDIUM) | 2 | timeout 즉시 실패, 401…
