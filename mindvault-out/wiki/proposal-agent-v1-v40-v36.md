# proposal-agent-v1 v4.0 아키텍처 진화 & v3.6 설계
Cohesion: 0.15 | Nodes: 18

## Key Nodes
- **proposal-agent-v1 v4.0 아키텍처 진화** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 11 connections
  - -> contains -> [[1-step-0-api-driven-architecture-vs]]
  - -> contains -> [[2-path-ab]]
  - -> contains -> [[3-ppt-fan-out-3]]
  - -> contains -> [[4-step-68]]
  - -> contains -> [[5-v40]]
  - -> contains -> [[6]]
  - -> contains -> [[7-conditional-edges-v40]]
  - -> contains -> [[8]]
  - -> contains -> [[9]]
  - -> contains -> [[10]]
  - -> contains -> [[references]]
- **v3.6 설계** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 5 connections
  - <- contains <- [[1-step-0-api-driven-architecture-vs]]
  - <- contains <- [[2-path-ab]]
  - <- contains <- [[3-ppt-fan-out-3]]
  - <- contains <- [[4-step-68]]
  - <- contains <- [[7-conditional-edges-v40]]
- **1. STEP 0: API-Driven Architecture (설계 vs 구현 변경)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 3 connections
  - -> contains -> [[v36]]
  - -> contains -> [[v40]]
  - <- contains <- [[proposal-agent-v1-v40]]
- **2. Path A/B 브랜치: 제안서 + 제출/비딩 병렬 실행** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 3 connections
  - -> contains -> [[v36]]
  - -> contains -> [[v40-ab]]
  - <- contains <- [[proposal-agent-v1-v40]]
- **3. PPT 파이프라인: Fan-out → 3단계 순차** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 3 connections
  - -> contains -> [[v36]]
  - -> contains -> [[v40-3]]
  - <- contains <- [[proposal-agent-v1-v40]]
- **4. 평가 및 종료: 새로운 STEP 6~8** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 3 connections
  - -> contains -> [[v36]]
  - -> contains -> [[v40]]
  - <- contains <- [[proposal-agent-v1-v40]]
- **5. 상태 필드 추가 (v4.0)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 3 connections
  - -> contains -> [[v36-state]]
  - -> contains -> [[v40]]
  - <- contains <- [[proposal-agent-v1-v40]]
- **7. 그래프 라우팅: Conditional Edges (v4.0 변경)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 3 connections
  - -> contains -> [[v36]]
  - -> contains -> [[v40-path-b]]
  - <- contains <- [[proposal-agent-v1-v40]]
- **v4.0 구현 (실제)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 3 connections
  - <- contains <- [[1-step-0-api-driven-architecture-vs]]
  - <- contains <- [[4-step-68]]
  - <- contains <- [[5-v40]]
- **10. 테스트 체크리스트** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 1 connections
  - <- contains <- [[proposal-agent-v1-v40]]
- **6. 노드 개수 확장** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 1 connections
  - <- contains <- [[proposal-agent-v1-v40]]
- **8. 설계-구현 차이 요약 및 이유** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 1 connections
  - <- contains <- [[proposal-agent-v1-v40]]
- **9. 구현 가이드** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 1 connections
  - <- contains <- [[proposal-agent-v1-v40]]
- **References** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 1 connections
  - <- contains <- [[proposal-agent-v1-v40]]
- **v3.6 설계 State 필드** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 1 connections
  - <- contains <- [[5-v40]]
- **v4.0 구현 (3단계 순차)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 1 connections
  - <- contains <- [[3-ppt-fan-out-3]]
- **v4.0 구현 (A/B 병렬)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 1 connections
  - <- contains <- [[2-path-ab]]
- **v4.0 구현 (Path B 추가)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\proposal-agent-v4.0-architecture.md) -- 1 connections
  - <- contains <- [[7-conditional-edges-v40]]

## Internal Relationships
- 1. STEP 0: API-Driven Architecture (설계 vs 구현 변경) -> contains -> v3.6 설계 [EXTRACTED]
- 1. STEP 0: API-Driven Architecture (설계 vs 구현 변경) -> contains -> v4.0 구현 (실제) [EXTRACTED]
- 2. Path A/B 브랜치: 제안서 + 제출/비딩 병렬 실행 -> contains -> v3.6 설계 [EXTRACTED]
- 2. Path A/B 브랜치: 제안서 + 제출/비딩 병렬 실행 -> contains -> v4.0 구현 (A/B 병렬) [EXTRACTED]
- 3. PPT 파이프라인: Fan-out → 3단계 순차 -> contains -> v3.6 설계 [EXTRACTED]
- 3. PPT 파이프라인: Fan-out → 3단계 순차 -> contains -> v4.0 구현 (3단계 순차) [EXTRACTED]
- 4. 평가 및 종료: 새로운 STEP 6~8 -> contains -> v3.6 설계 [EXTRACTED]
- 4. 평가 및 종료: 새로운 STEP 6~8 -> contains -> v4.0 구현 (실제) [EXTRACTED]
- 5. 상태 필드 추가 (v4.0) -> contains -> v3.6 설계 State 필드 [EXTRACTED]
- 5. 상태 필드 추가 (v4.0) -> contains -> v4.0 구현 (실제) [EXTRACTED]
- 7. 그래프 라우팅: Conditional Edges (v4.0 변경) -> contains -> v3.6 설계 [EXTRACTED]
- 7. 그래프 라우팅: Conditional Edges (v4.0 변경) -> contains -> v4.0 구현 (Path B 추가) [EXTRACTED]
- proposal-agent-v1 v4.0 아키텍처 진화 -> contains -> 1. STEP 0: API-Driven Architecture (설계 vs 구현 변경) [EXTRACTED]
- proposal-agent-v1 v4.0 아키텍처 진화 -> contains -> 2. Path A/B 브랜치: 제안서 + 제출/비딩 병렬 실행 [EXTRACTED]
- proposal-agent-v1 v4.0 아키텍처 진화 -> contains -> 3. PPT 파이프라인: Fan-out → 3단계 순차 [EXTRACTED]
- proposal-agent-v1 v4.0 아키텍처 진화 -> contains -> 4. 평가 및 종료: 새로운 STEP 6~8 [EXTRACTED]
- proposal-agent-v1 v4.0 아키텍처 진화 -> contains -> 5. 상태 필드 추가 (v4.0) [EXTRACTED]
- proposal-agent-v1 v4.0 아키텍처 진화 -> contains -> 6. 노드 개수 확장 [EXTRACTED]
- proposal-agent-v1 v4.0 아키텍처 진화 -> contains -> 7. 그래프 라우팅: Conditional Edges (v4.0 변경) [EXTRACTED]
- proposal-agent-v1 v4.0 아키텍처 진화 -> contains -> 8. 설계-구현 차이 요약 및 이유 [EXTRACTED]
- proposal-agent-v1 v4.0 아키텍처 진화 -> contains -> 9. 구현 가이드 [EXTRACTED]
- proposal-agent-v1 v4.0 아키텍처 진화 -> contains -> 10. 테스트 체크리스트 [EXTRACTED]
- proposal-agent-v1 v4.0 아키텍처 진화 -> contains -> References [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 proposal-agent-v1 v4.0 아키텍처 진화, v3.6 설계, 1. STEP 0: API-Driven Architecture (설계 vs 구현 변경)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-agent-v4.0-architecture.md이다.

### Key Facts
- | 항목 | 내용 | |------|------| | 문서 버전 | v4.0 | | 작성일 | 2026-03-29 | | 기반 | proposal-agent-v1 v3.6 설계 + 실제 구현 | | 상태 | 설계-구현 동기화 (갭 분석 후 작성) |
- | 항목 | 내용 | |------|------| | 문서 버전 | v4.0 | | 작성일 | 2026-03-29 | | 기반 | proposal-agent-v1 v3.6 설계 + 실제 구현 | | 상태 | 설계-구현 동기화 (갭 분석 후 작성) |
- v3.6 설계 ``` START → route_start ├─ Path 1: rfp_search → review_search → rfp_fetch (검색 경로) ├─ Path 2: rfp_upload (파일 업로드 경로) └─ Path 3: rfp_direct (공고 지정 경로) ↓ rfp_analyze (STEP 1-①) ```
- v3.6 설계 (선형) ``` strategy_generate (STEP 2) ↓ plan_* (STEP 3) — 5개 병렬: team, assign, schedule, story, price ↓ proposal_write_next (STEP 4A) — 순차 섹션 작성 ↓ ppt_* (STEP 5A) — PPT 생성 ↓ END ```
- v3.6 설계 ``` presentation_strategy (전략 수립) ↓ ppt_fan_out_gate └─ ppt_slide (각 섹션별) [병렬] ├─ ppt_slide (Executive Summary) ├─ ppt_slide (Technical Approach) ├─ ppt_slide (Team & Resources) └─ ... ↓ ppt_merge (병합) ↓ review_ppt ↓ END ```
