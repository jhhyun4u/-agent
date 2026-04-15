# 3. 공고 모니터링 `/monitoring` & 3-1. 공고 목록
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **3. 공고 모니터링 `/monitoring`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 5 connections
  - -> contains -> [[3-1]]
  - -> contains -> [[3-2-monitoringbidno]]
  - -> contains -> [[3-3-monitoringbidnoreview]]
  - -> contains -> [[3-4-monitoringsettings]]
  - -> contains -> [[3-5]]
- **3-1. 공고 목록** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[3-monitoring]]
- **3-2. 공고 상세 `/monitoring/[bidNo]`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[3-monitoring]]
- **3-3. 공고 검토 `/monitoring/[bidNo]/review`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[3-monitoring]]
- **3-4. 모니터링 설정 `/monitoring/settings`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[3-monitoring]]
- **3-5. 중복 공고 경고** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[3-monitoring]]

## Internal Relationships
- 3. 공고 모니터링 `/monitoring` -> contains -> 3-1. 공고 목록 [EXTRACTED]
- 3. 공고 모니터링 `/monitoring` -> contains -> 3-2. 공고 상세 `/monitoring/[bidNo]` [EXTRACTED]
- 3. 공고 모니터링 `/monitoring` -> contains -> 3-3. 공고 검토 `/monitoring/[bidNo]/review` [EXTRACTED]
- 3. 공고 모니터링 `/monitoring` -> contains -> 3-4. 모니터링 설정 `/monitoring/settings` [EXTRACTED]
- 3. 공고 모니터링 `/monitoring` -> contains -> 3-5. 중복 공고 경고 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 3. 공고 모니터링 `/monitoring`, 3-1. 공고 목록, 3-2. 공고 상세 `/monitoring/[bidNo]`를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend-manual-test-checklist.md이다.

### Key Facts
- 3-1. 공고 목록 - [ ] 페이지 정상 렌더링 - [ ] 공고 목록 테이블 표시 (공고번호, 공고명, 마감일 등) - [ ] 페이지네이션 동작 - [ ] 검색/필터 기능 동작 - [ ] 마감일 3일 이내 건 시각적 강조
- 3-2. 공고 상세 `/monitoring/[bidNo]` - [ ] 공고 클릭 → 상세 페이지 이동 - [ ] 공고 기본 정보 표시 (공고번호, 발주기관, 예산 등) - [ ] RFP 첨부파일 목록
- 3-3. 공고 검토 `/monitoring/[bidNo]/review` - [ ] 검토 화면 접근 가능 - [ ] Go/No-Go 판단 UI 표시 - [ ] "제안 프로젝트 생성" 버튼 동작
- 3-4. 모니터링 설정 `/monitoring/settings` - [ ] 설정 페이지 렌더링 - [ ] 키워드/조건 설정 변경 가능 - [ ] 저장 후 반영 확인
- 3-5. 중복 공고 경고 - [ ] 이미 등록된 공고 접근 시 DuplicateBidWarning 표시
