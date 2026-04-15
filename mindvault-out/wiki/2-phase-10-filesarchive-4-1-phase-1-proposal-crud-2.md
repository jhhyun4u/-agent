# 2. Phase 10: Files/Archive (4개 실패) & 1. Phase 1: Proposal CRUD (2개 실패)
Cohesion: 0.20 | Nodes: 10

## Key Nodes
- **2. Phase 10: Files/Archive (4개 실패)** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 5 connections
  - -> contains -> [[testlistprojectfiles]]
  - -> contains -> [[testsaveartifactincrementsversion]]
  - -> contains -> [[testdeleteproposal]]
  - -> contains -> [[testdeleterunningproposalblocked]]
  - <- contains <- [[6]]
- **1. Phase 1: Proposal CRUD (2개 실패)** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 3 connections
  - -> contains -> [[testcreatefrombid]]
  - -> contains -> [[testdeleteproposalsuccess]]
  - <- contains <- [[6]]
- **🔴 실패한 테스트 (6개)** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 2 connections
  - -> contains -> [[1-phase-1-proposal-crud-2]]
  - -> contains -> [[2-phase-10-filesarchive-4]]
- **test_create_from_bid** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[1-phase-1-proposal-crud-2]]
- **python** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 1 connections
  - <- has_code_example <- [[testcreatefrombid]]
- **test_delete_proposal** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 1 connections
  - <- contains <- [[2-phase-10-filesarchive-4]]
- **test_delete_proposal_success** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 1 connections
  - <- contains <- [[1-phase-1-proposal-crud-2]]
- **test_delete_running_proposal_blocked** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 1 connections
  - <- contains <- [[2-phase-10-filesarchive-4]]
- **test_list_project_files** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 1 connections
  - <- contains <- [[2-phase-10-filesarchive-4]]
- **test_save_artifact_increments_version** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 1 connections
  - <- contains <- [[2-phase-10-filesarchive-4]]

## Internal Relationships
- 1. Phase 1: Proposal CRUD (2개 실패) -> contains -> test_create_from_bid [EXTRACTED]
- 1. Phase 1: Proposal CRUD (2개 실패) -> contains -> test_delete_proposal_success [EXTRACTED]
- 2. Phase 10: Files/Archive (4개 실패) -> contains -> test_list_project_files [EXTRACTED]
- 2. Phase 10: Files/Archive (4개 실패) -> contains -> test_save_artifact_increments_version [EXTRACTED]
- 2. Phase 10: Files/Archive (4개 실패) -> contains -> test_delete_proposal [EXTRACTED]
- 2. Phase 10: Files/Archive (4개 실패) -> contains -> test_delete_running_proposal_blocked [EXTRACTED]
- 🔴 실패한 테스트 (6개) -> contains -> 1. Phase 1: Proposal CRUD (2개 실패) [EXTRACTED]
- 🔴 실패한 테스트 (6개) -> contains -> 2. Phase 10: Files/Archive (4개 실패) [EXTRACTED]
- test_create_from_bid -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 2. Phase 10: Files/Archive (4개 실패), 1. Phase 1: Proposal CRUD (2개 실패), 🔴 실패한 테스트 (6개)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 TEST_REPORT.md이다.

### Key Facts
- test_list_project_files ``` ❌ AssertionError: assert 0 == 2 원인: proposal_files 테이블 조회에서 빈 배열 반환 상세: fixture에서 proposal_files 데이터 미설정 영향: 프로젝트 파일 목록 조회 ```
- test_create_from_bid ``` ❌ AssertionError: Status 500 원인: MockQueryBuilder.maybe_single() 배열 추적 실패 상세: bid_announcements 조회 시 배열이 아닌 첫 원소를 기대하는데 배열 반환 영향: from-bid 진입 경로 (공고 기반 제안 생성) ```
- 1. Phase 1: Proposal CRUD (2개 실패)
- **근본 원인 분석:** ```python 문제 코드 class MockQueryBuilder: def maybe_single(self): self._is_single = True return self
- **작성일**: 2026-04-01 **테스트 대상**: Phase 0 ~ 10 (141개 테스트) **실행 환경**: Python 3.12, pytest 9.0.2, FastAPI mock
