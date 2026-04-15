# 5. 지식 베이스 `/kb` & 5-1. 통합 검색 `/kb/search`
Cohesion: 0.22 | Nodes: 9

## Key Nodes
- **5. 지식 베이스 `/kb`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 8 connections
  - -> contains -> [[5-1-kbsearch]]
  - -> contains -> [[5-2-kbcontent]]
  - -> contains -> [[5-3-kbclients]]
  - -> contains -> [[5-4-kbcompetitors]]
  - -> contains -> [[5-5-kblessons]]
  - -> contains -> [[5-6-qa-kbqa]]
  - -> contains -> [[5-7-kblabor-rates]]
  - -> contains -> [[5-8-kbmarket-prices]]
- **5-1. 통합 검색 `/kb/search`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-2. 콘텐츠 `/kb/content`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-3. 발주기관 `/kb/clients`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-4. 경쟁사 `/kb/competitors`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-5. 교훈 `/kb/lessons`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-6. Q&A `/kb/qa`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-7. 노임단가 `/kb/labor-rates`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[5-kb]]
- **5-8. 시장가격 `/kb/market-prices`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[5-kb]]

## Internal Relationships
- 5. 지식 베이스 `/kb` -> contains -> 5-1. 통합 검색 `/kb/search` [EXTRACTED]
- 5. 지식 베이스 `/kb` -> contains -> 5-2. 콘텐츠 `/kb/content` [EXTRACTED]
- 5. 지식 베이스 `/kb` -> contains -> 5-3. 발주기관 `/kb/clients` [EXTRACTED]
- 5. 지식 베이스 `/kb` -> contains -> 5-4. 경쟁사 `/kb/competitors` [EXTRACTED]
- 5. 지식 베이스 `/kb` -> contains -> 5-5. 교훈 `/kb/lessons` [EXTRACTED]
- 5. 지식 베이스 `/kb` -> contains -> 5-6. Q&A `/kb/qa` [EXTRACTED]
- 5. 지식 베이스 `/kb` -> contains -> 5-7. 노임단가 `/kb/labor-rates` [EXTRACTED]
- 5. 지식 베이스 `/kb` -> contains -> 5-8. 시장가격 `/kb/market-prices` [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 5. 지식 베이스 `/kb`, 5-1. 통합 검색 `/kb/search`, 5-2. 콘텐츠 `/kb/content`를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend-manual-test-checklist.md이다.

### Key Facts
- 5-1. 통합 검색 `/kb/search` - [ ] 검색 입력 필드 + 결과 표시 - [ ] 카테고리별 필터 - [ ] 검색 결과 클릭 → 상세 이동
- 5-2. 콘텐츠 `/kb/content` - [ ] 콘텐츠 목록 표시 - [ ] 등록/수정/삭제 동작 - [ ] 파일 첨부/다운로드
- 5-3. 발주기관 `/kb/clients` - [ ] 기관 목록 테이블 - [ ] 기관 상세 정보 조회 - [ ] 등록/수정 동작
- 5-4. 경쟁사 `/kb/competitors` - [ ] 경쟁사 목록 테이블 - [ ] 상세 정보 조회 - [ ] 등록/수정 동작
- 5-5. 교훈 `/kb/lessons` - [ ] 교훈 목록 표시 - [ ] 수주/패찰별 필터 - [ ] 상세 조회
