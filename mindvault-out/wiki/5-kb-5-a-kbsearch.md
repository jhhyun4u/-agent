# 5. 지식 베이스 (`/kb/*`) & 5-A. 통합 검색 (`/kb/search`)
Cohesion: 0.22 | Nodes: 9

## Key Nodes
- **5. 지식 베이스 (`/kb/*`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 8 connections
  - -> contains -> [[5-a-kbsearch]]
  - -> contains -> [[5-b-kbcontent]]
  - -> contains -> [[5-c-kbclients]]
  - -> contains -> [[5-d-kbcompetitors]]
  - -> contains -> [[5-e-kblessons]]
  - -> contains -> [[5-f-qa-kbqa]]
  - -> contains -> [[5-g-kblabor-rates]]
  - -> contains -> [[5-h-kbmarket-prices]]
- **5-A. 통합 검색 (`/kb/search`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-B. 콘텐츠 (`/kb/content`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-C. 발주기관 (`/kb/clients`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-D. 경쟁사 (`/kb/competitors`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-E. 교훈 (`/kb/lessons`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-F. Q&A (`/kb/qa`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-G. 노임단가 (`/kb/labor-rates`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-H. 시장가격 (`/kb/market-prices`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[5-kb]]

## Internal Relationships
- 5. 지식 베이스 (`/kb/*`) -> contains -> 5-A. 통합 검색 (`/kb/search`) [EXTRACTED]
- 5. 지식 베이스 (`/kb/*`) -> contains -> 5-B. 콘텐츠 (`/kb/content`) [EXTRACTED]
- 5. 지식 베이스 (`/kb/*`) -> contains -> 5-C. 발주기관 (`/kb/clients`) [EXTRACTED]
- 5. 지식 베이스 (`/kb/*`) -> contains -> 5-D. 경쟁사 (`/kb/competitors`) [EXTRACTED]
- 5. 지식 베이스 (`/kb/*`) -> contains -> 5-E. 교훈 (`/kb/lessons`) [EXTRACTED]
- 5. 지식 베이스 (`/kb/*`) -> contains -> 5-F. Q&A (`/kb/qa`) [EXTRACTED]
- 5. 지식 베이스 (`/kb/*`) -> contains -> 5-G. 노임단가 (`/kb/labor-rates`) [EXTRACTED]
- 5. 지식 베이스 (`/kb/*`) -> contains -> 5-H. 시장가격 (`/kb/market-prices`) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 5. 지식 베이스 (`/kb/*`), 5-A. 통합 검색 (`/kb/search`), 5-B. 콘텐츠 (`/kb/content`)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 test-checklist-frontend.md이다.

### Key Facts
- 5-A. 통합 검색 (`/kb/search`)
- | # | 테스트 항목 | 확인 | |---|-----------|------| | 5A-1 | 검색어 입력 → 통합 결과 표시 | ☐ | | 5A-2 | 카테고리별 필터 (콘텐츠/발주기관/경쟁사/교훈) | ☐ | | 5A-3 | 결과 항목 클릭 → 상세 페이지 이동 | ☐ | | 5A-4 | 빈 결과: "검색 결과 없음" 안내 | ☐ | | 5A-5 | KbUsageHistory: KB 사용 이력 표시 | ☐ |
- | # | 테스트 항목 | 확인 | |---|-----------|------| | 5B-1 | 콘텐츠 목록 렌더링 | ☐ | | 5B-2 | 콘텐츠 추가/수정/삭제 | ☐ | | 5B-3 | 검색/필터 동작 | ☐ |
- | # | 테스트 항목 | 확인 | |---|-----------|------| | 5C-1 | 발주기관 목록 렌더링 | ☐ | | 5C-2 | 기관 상세 정보 보기 | ☐ | | 5C-3 | 기관 추가/수정 | ☐ |
- | # | 테스트 항목 | 확인 | |---|-----------|------| | 5D-1 | 경쟁사 목록 렌더링 | ☐ | | 5D-2 | 경쟁사 상세 정보 보기 | ☐ | | 5D-3 | 경쟁사 추가/수정 | ☐ |
