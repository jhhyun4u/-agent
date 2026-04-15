# 제안 결정 워크플로우 수정 (2026-04-06) & 2. 제안 프로젝트 생성 엔드포인트 개선 (`app/api/routes_proposal.py`)
Cohesion: 0.25 | Nodes: 9

## Key Nodes
- **제안 결정 워크플로우 수정 (2026-04-06)** (C:\project\tenopa proposer\-agent-master\FIXES_SUMMARY.md) -- 4 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-appapiroutesproposalpy]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
- **2. 제안 프로젝트 생성 엔드포인트 개선 (`app/api/routes_proposal.py`)** (C:\project\tenopa proposer\-agent-master\FIXES_SUMMARY.md) -- 3 connections
  - -> contains -> [[21]]
  - -> contains -> [[22-db]]
  - <- contains <- [[2026-04-06]]
- **python** (C:\project\tenopa proposer\-agent-master\FIXES_SUMMARY.md) -- 2 connections
  - <- has_code_example <- [[21]]
  - <- has_code_example <- [[22-db]]
- **2.1 저장소 다운로드 타임아웃 추가** (C:\project\tenopa proposer\-agent-master\FIXES_SUMMARY.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-appapiroutesproposalpy]]
- **2.2 DB 스키마 불일치 해결** (C:\project\tenopa proposer\-agent-master\FIXES_SUMMARY.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-appapiroutesproposalpy]]
- **3. 마이그레이션 필요** (C:\project\tenopa proposer\-agent-master\FIXES_SUMMARY.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[2026-04-06]]
- **sql** (C:\project\tenopa proposer\-agent-master\FIXES_SUMMARY.md) -- 1 connections
  - <- has_code_example <- [[3]]
- **1. 테스트 프로포절 삭제 ✓** (C:\project\tenopa proposer\-agent-master\FIXES_SUMMARY.md) -- 1 connections
  - <- contains <- [[2026-04-06]]
- **4. 모니터링 목록 필터링 확인** (C:\project\tenopa proposer\-agent-master\FIXES_SUMMARY.md) -- 1 connections
  - <- contains <- [[2026-04-06]]

## Internal Relationships
- 제안 결정 워크플로우 수정 (2026-04-06) -> contains -> 1. 테스트 프로포절 삭제 ✓ [EXTRACTED]
- 제안 결정 워크플로우 수정 (2026-04-06) -> contains -> 2. 제안 프로젝트 생성 엔드포인트 개선 (`app/api/routes_proposal.py`) [EXTRACTED]
- 제안 결정 워크플로우 수정 (2026-04-06) -> contains -> 3. 마이그레이션 필요 [EXTRACTED]
- 제안 결정 워크플로우 수정 (2026-04-06) -> contains -> 4. 모니터링 목록 필터링 확인 [EXTRACTED]
- 2.1 저장소 다운로드 타임아웃 추가 -> has_code_example -> python [EXTRACTED]
- 2.2 DB 스키마 불일치 해결 -> has_code_example -> python [EXTRACTED]
- 2. 제안 프로젝트 생성 엔드포인트 개선 (`app/api/routes_proposal.py`) -> contains -> 2.1 저장소 다운로드 타임아웃 추가 [EXTRACTED]
- 2. 제안 프로젝트 생성 엔드포인트 개선 (`app/api/routes_proposal.py`) -> contains -> 2.2 DB 스키마 불일치 해결 [EXTRACTED]
- 3. 마이그레이션 필요 -> has_code_example -> sql [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 제안 결정 워크플로우 수정 (2026-04-06), 2. 제안 프로젝트 생성 엔드포인트 개선 (`app/api/routes_proposal.py`), python를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 FIXES_SUMMARY.md이다.

### Key Facts
- 주요 이슈 1. 공고 모니터링 > 제안 검토에서 "제안결정"을 선택했을 때 - 공고 모니터링 목록에서 제거되지 않음 - 제안 프로젝트 목록에 등록되지 않음 - 요청이 계속 타임아웃
- 2.1 저장소 다운로드 타임아웃 추가 ```python 마크다운 파일 다운로드에 5초 타임아웃 설정 - analyze 엔드포인트의 백그라운드 작업이 진행 중일 수 있음 - 파일이 존재하지 않으면 무시하고 계속 진행 ```
- 2.1 저장소 다운로드 타임아웃 추가 ```python 마크다운 파일 다운로드에 5초 타임아웃 설정 - analyze 엔드포인트의 백그라운드 작업이 진행 중일 수 있음 - 파일이 존재하지 않으면 무시하고 계속 진행 ```
- **문제**: analyze 엔드포인트가 즉시 반환되고 마크다운 생성은 백그라운드에서 처리 - 프로포절 생성 시 마크다운 파일을 다운로드하려고 하면 아직 존재하지 않을 수 있음 - 무한 대기로 인한 타임아웃 발생
- ```python 1차 시도: 모든 선택적 필드 포함 실패 시: 최소 필드(id, title, owner_id, status, rfp_content)만 사용하여 재시도 ```
