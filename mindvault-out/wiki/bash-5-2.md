# bash & 5️⃣ 프로덕션 승인 (2일 이상)
Cohesion: 0.17 | Nodes: 15

## Key Nodes
- **bash** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 6 connections
  - <- has_code_example <- [[a]]
  - <- has_code_example <- [[b]]
  - <- has_code_example <- [[c]]
  - <- has_code_example <- [[d]]
  - <- has_code_example <- [[e]]
  - <- has_code_example <- [[2026-04-07-1500-utc]]
- **5️⃣ 프로덕션 승인 (2일 이상)** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 6 connections
  - -> contains -> [[qa]]
  - -> contains -> [[devops]]
  - -> contains -> [[2026-04-07-1500-utc]]
  - -> contains -> [[1]]
  - -> contains -> [[24]]
  - -> contains -> [[2-3]]
- **테스트 스크립트 - API 엔드포인트 검증** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 6 connections
  - -> contains -> [[a]]
  - -> contains -> [[b]]
  - -> contains -> [[c]]
  - -> contains -> [[d]]
  - -> contains -> [[e]]
  - <- contains <- [[2-1]]
- **현재 상태 (2026-04-07 15:00 UTC)** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[5-2]]
- **A. 문서 업로드 테스트** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[api]]
- **B. 문서 목록 조회 테스트** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[api]]
- **C. 문서 상세 조회 테스트** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[api]]
- **D. 청크 조회 테스트 (비동기 완료 후)** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[api]]
- **E. 문서 삭제 테스트** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[api]]
- **1시간 내 (스모크 테스트)** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 1 connections
  - <- contains <- [[5-2]]
- **24시간 (에러 로그 모니터링)** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 1 connections
  - <- contains <- [[5-2]]
- **2-3일 (최종 검증)** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 1 connections
  - <- contains <- [[5-2]]
- **2️⃣ 프로덕션 스모크 테스트 (1시간)** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 1 connections
  - -> contains -> [[api]]
- **DevOps 검증 체크리스트** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 1 connections
  - <- contains <- [[5-2]]
- **QA 검증 체크리스트** (C:\project\tenopa proposer\-agent-master\PRODUCTION_VALIDATION_REPORT.md) -- 1 connections
  - <- contains <- [[5-2]]

## Internal Relationships
- 현재 상태 (2026-04-07 15:00 UTC) -> has_code_example -> bash [EXTRACTED]
- 2️⃣ 프로덕션 스모크 테스트 (1시간) -> contains -> 테스트 스크립트 - API 엔드포인트 검증 [EXTRACTED]
- 5️⃣ 프로덕션 승인 (2일 이상) -> contains -> QA 검증 체크리스트 [EXTRACTED]
- 5️⃣ 프로덕션 승인 (2일 이상) -> contains -> DevOps 검증 체크리스트 [EXTRACTED]
- 5️⃣ 프로덕션 승인 (2일 이상) -> contains -> 현재 상태 (2026-04-07 15:00 UTC) [EXTRACTED]
- 5️⃣ 프로덕션 승인 (2일 이상) -> contains -> 1시간 내 (스모크 테스트) [EXTRACTED]
- 5️⃣ 프로덕션 승인 (2일 이상) -> contains -> 24시간 (에러 로그 모니터링) [EXTRACTED]
- 5️⃣ 프로덕션 승인 (2일 이상) -> contains -> 2-3일 (최종 검증) [EXTRACTED]
- A. 문서 업로드 테스트 -> has_code_example -> bash [EXTRACTED]
- 테스트 스크립트 - API 엔드포인트 검증 -> contains -> A. 문서 업로드 테스트 [EXTRACTED]
- 테스트 스크립트 - API 엔드포인트 검증 -> contains -> B. 문서 목록 조회 테스트 [EXTRACTED]
- 테스트 스크립트 - API 엔드포인트 검증 -> contains -> C. 문서 상세 조회 테스트 [EXTRACTED]
- 테스트 스크립트 - API 엔드포인트 검증 -> contains -> D. 청크 조회 테스트 (비동기 완료 후) [EXTRACTED]
- 테스트 스크립트 - API 엔드포인트 검증 -> contains -> E. 문서 삭제 테스트 [EXTRACTED]
- B. 문서 목록 조회 테스트 -> has_code_example -> bash [EXTRACTED]
- C. 문서 상세 조회 테스트 -> has_code_example -> bash [EXTRACTED]
- D. 청크 조회 테스트 (비동기 완료 후) -> has_code_example -> bash [EXTRACTED]
- E. 문서 삭제 테스트 -> has_code_example -> bash [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 bash, 5️⃣ 프로덕션 승인 (2일 이상), 테스트 스크립트 - API 엔드포인트 검증를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 PRODUCTION_VALIDATION_REPORT.md이다.

### Key Facts
- A. 문서 업로드 테스트 ```bash 1. PDF 파일 업로드 curl -X POST https://api.production.com/api/documents/upload \ -H "Authorization: Bearer YOUR_PROD_TOKEN" \ -F "file=@test.pdf" \ -F "doc_type=보고서"
- QA 검증 체크리스트 - [ ] 모든 엔드포인트 동작 확인 - [ ] 모든 파일 형식 지원 확인 - [ ] 에러 처리 정상 동작 - [ ] 성능 메트릭 목표 달성 - [ ] 보안 제어 적용됨
- A. 문서 업로드 테스트 ```bash 1. PDF 파일 업로드 curl -X POST https://api.production.com/api/documents/upload \ -H "Authorization: Bearer YOUR_PROD_TOKEN" \ -F "file=@test.pdf" \ -F "doc_type=보고서"
- 예상 타임라인 ``` 15:00 - PR #3 병합 (main) 15:00+ - CI/CD 배포 시작 15:30 - 배포 완료 예상 16:00 - 스모크 테스트 시작 17:00 - 초기 검증 완료 24시간 - 에러 로그 분석 48시간 - 성능 메트릭 검증 72시간 - 최종 승인
- Expected Response: 201 Created Response Body: { "id": "document_id_here", "filename": "test.pdf", "doc_type": "보고서", "processing_status": "extracting", "storage_path": "org_id/document_id/test.pdf", "created_at": "2026-04-07T...", "org_id": "your_org_id" } ```
