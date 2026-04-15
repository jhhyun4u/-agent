# 3. 기능 상세 & Phase 4 계획: G2B 클라이언트 + 성과 추적
Cohesion: 0.13 | Nodes: 17

## Key Nodes
- **3. 기능 상세** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 7 connections
  - -> contains -> [[4-1-g2b]]
  - -> contains -> [[4-2-api]]
  - -> contains -> [[4-3-materialized-view]]
  - -> contains -> [[4-4-api]]
  - -> contains -> [[4-5-lessons-learned]]
  - -> contains -> [[4-6-kb]]
  - <- contains <- [[phase-4-g2b]]
- **Phase 4 계획: G2B 클라이언트 + 성과 추적** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 6 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-scope]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
- **2. 범위 (Scope)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 3 connections
  - -> contains -> [[in-scope]]
  - -> contains -> [[out-of-scope-phase]]
  - <- contains <- [[phase-4-g2b]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 2 connections
  - <- has_code_example <- [[4-2-api]]
  - <- has_code_example <- [[4-5-lessons-learned]]
- **sql** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 2 connections
  - <- has_code_example <- [[4-1-g2b]]
  - <- has_code_example <- [[4-3-materialized-view]]
- **4-1. G2B 낙찰정보 클라이언트** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[3]]
- **4-2. 제안 결과 등록 API** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3]]
- **4-3. 성과 추적 Materialized View** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[3]]
- **4-5. 교훈(Lessons Learned) 등록** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3]]
- **1. 목적** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 1 connections
  - <- contains <- [[phase-4-g2b]]
- **4. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 1 connections
  - <- contains <- [[phase-4-g2b]]
- **4-4. 분석 대시보드 API** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **4-6. 성과 기반 KB 업데이트** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **5. 검증 방법** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 1 connections
  - <- contains <- [[phase-4-g2b]]
- **6. 잔여 갭 해소 계획** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 1 connections
  - <- contains <- [[phase-4-g2b]]
- **In-Scope** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 1 connections
  - <- contains <- [[2-scope]]
- **Out-of-Scope (이번 Phase 제외)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\proposal-agent-phase4.plan.md) -- 1 connections
  - <- contains <- [[2-scope]]

## Internal Relationships
- 2. 범위 (Scope) -> contains -> In-Scope [EXTRACTED]
- 2. 범위 (Scope) -> contains -> Out-of-Scope (이번 Phase 제외) [EXTRACTED]
- 3. 기능 상세 -> contains -> 4-1. G2B 낙찰정보 클라이언트 [EXTRACTED]
- 3. 기능 상세 -> contains -> 4-2. 제안 결과 등록 API [EXTRACTED]
- 3. 기능 상세 -> contains -> 4-3. 성과 추적 Materialized View [EXTRACTED]
- 3. 기능 상세 -> contains -> 4-4. 분석 대시보드 API [EXTRACTED]
- 3. 기능 상세 -> contains -> 4-5. 교훈(Lessons Learned) 등록 [EXTRACTED]
- 3. 기능 상세 -> contains -> 4-6. 성과 기반 KB 업데이트 [EXTRACTED]
- 4-1. G2B 낙찰정보 클라이언트 -> has_code_example -> sql [EXTRACTED]
- 4-2. 제안 결과 등록 API -> has_code_example -> python [EXTRACTED]
- 4-3. 성과 추적 Materialized View -> has_code_example -> sql [EXTRACTED]
- 4-5. 교훈(Lessons Learned) 등록 -> has_code_example -> python [EXTRACTED]
- Phase 4 계획: G2B 클라이언트 + 성과 추적 -> contains -> 1. 목적 [EXTRACTED]
- Phase 4 계획: G2B 클라이언트 + 성과 추적 -> contains -> 2. 범위 (Scope) [EXTRACTED]
- Phase 4 계획: G2B 클라이언트 + 성과 추적 -> contains -> 3. 기능 상세 [EXTRACTED]
- Phase 4 계획: G2B 클라이언트 + 성과 추적 -> contains -> 4. 구현 순서 [EXTRACTED]
- Phase 4 계획: G2B 클라이언트 + 성과 추적 -> contains -> 5. 검증 방법 [EXTRACTED]
- Phase 4 계획: G2B 클라이언트 + 성과 추적 -> contains -> 6. 잔여 갭 해소 계획 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 3. 기능 상세, Phase 4 계획: G2B 클라이언트 + 성과 추적, 2. 범위 (Scope)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-agent-phase4.plan.md이다.

### Key Facts
- | 항목 | 내용 | |------|------| | 문서 버전 | v1.0 | | 작성일 | 2026-03-16 | | 상태 | 초안 | | 기반 설계 | docs/02-design/features/proposal-agent-v1/_index.md (v3.6) | | 선행 Phase | Phase 0~3 완료 (98% match rate) | | 제외 항목 | PPTX 빌더 (별도 Phase로 분리) |
- Out-of-Scope (이번 Phase 제외) - PPTX 빌더 (python-pptx) — 별도 Phase - 프론트엔드 구현 — Phase 5 이후 - 실시간 G2B 모니터링 스케줄러 — OPS-01 (LOW)
- **데이터 모델** (기존 `market_price_data` 테이블 활용): ```sql -- database/schema_v3.4.sql §15-5i 이미 정의됨 -- 추가 필요 컬럼 없음, 기존 스키마 그대로 사용 ```
- **목적**: 나라장터 낙찰정보를 조회하여 `market_price_data` 테이블에 저장
- **목적**: 프로젝트의 입찰 결과(수주/패찰/유찰)를 등록하고 KB에 반영
