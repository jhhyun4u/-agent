# API 엔드포인트 설계 & python
Cohesion: 0.47 | Nodes: 6

## Key Nodes
- **API 엔드포인트 설계** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_STORAGE_REDESIGN.md) -- 4 connections
  - -> has_code_example -> [[typescript]]
  - -> contains -> [[phase-1]]
  - -> contains -> [[phase-2]]
  - -> contains -> [[phase-3-api]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_STORAGE_REDESIGN.md) -- 2 connections
  - <- has_code_example <- [[phase-1]]
  - <- has_code_example <- [[phase-2]]
- **typescript** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_STORAGE_REDESIGN.md) -- 2 connections
  - <- has_code_example <- [[api]]
  - <- has_code_example <- [[phase-3-api]]
- **Phase 1: 신규 구조로 저장 (즉시)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_STORAGE_REDESIGN.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[api]]
- **Phase 2: 기존 파일 이관 (선택)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_STORAGE_REDESIGN.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[api]]
- **Phase 3: API 업데이트 (즉시)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_STORAGE_REDESIGN.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[api]]

## Internal Relationships
- API 엔드포인트 설계 -> has_code_example -> typescript [EXTRACTED]
- API 엔드포인트 설계 -> contains -> Phase 1: 신규 구조로 저장 (즉시) [EXTRACTED]
- API 엔드포인트 설계 -> contains -> Phase 2: 기존 파일 이관 (선택) [EXTRACTED]
- API 엔드포인트 설계 -> contains -> Phase 3: API 업데이트 (즉시) [EXTRACTED]
- Phase 1: 신규 구조로 저장 (즉시) -> has_code_example -> python [EXTRACTED]
- Phase 2: 기존 파일 이관 (선택) -> has_code_example -> python [EXTRACTED]
- Phase 3: API 업데이트 (즉시) -> has_code_example -> typescript [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 API 엔드포인트 설계, python, typescript를 중심으로 has_code_example 관계로 연결되어 있다. 주요 소스 파일은 INTRANET_STORAGE_REDESIGN.md이다.

### Key Facts
- 프로젝트 검색 & 문서 조회 ```typescript // 프로젝트 목록 + 문서 요약 GET /api/intranet/projects?keyword=AI&budget_min=500000000
- Phase 1: 신규 구조로 저장 (즉시) ```python 새 파일은 new_storage_path로 저장 storage_path = f"projects/{project_id}/documents/{doc_type}/{filename}" ```
- 프로젝트 검색 & 문서 조회 ```typescript // 프로젝트 목록 + 문서 요약 GET /api/intranet/projects?keyword=AI&budget_min=500000000
- Phase 2: 기존 파일 이관 (선택) ```python 기존 org_id 기반 파일을 프로젝트 중심으로 재정렬 파일 이동 스크립트 실행 intranet_documents.storage_path 갱신 ```
- Phase 3: API 업데이트 (즉시) ```typescript // 다운로드 경로 → 신규 storage_path 기반 // 검색 API 유지 (org_id는 내부 RLS 용도) ```
