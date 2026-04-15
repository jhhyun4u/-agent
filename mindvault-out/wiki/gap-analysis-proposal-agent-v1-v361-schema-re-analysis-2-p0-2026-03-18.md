# Gap Analysis: proposal-agent-v1 (v3.6.1 Schema Re-Analysis) & 2. P0 수정 완료 (2026-03-18)
Cohesion: 0.13 | Nodes: 15

## Key Nodes
- **Gap Analysis: proposal-agent-v1 (v3.6.1 Schema Re-Analysis)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 6 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-p0-2026-03-18]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
- **2. P0 수정 완료 (2026-03-18)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 4 connections
  - -> contains -> [[21-proposals]]
  - -> contains -> [[22-pgrst205]]
  - -> contains -> [[23-schemav34sql-ddl]]
  - <- contains <- [[gap-analysis-proposal-agent-v1-v361-schema-re-analysis]]
- **3. 테스트 결과** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 3 connections
  - -> contains -> [[31-api-1414-pass]]
  - -> contains -> [[32-88-pass]]
  - <- contains <- [[gap-analysis-proposal-agent-v1-v361-schema-re-analysis]]
- **4. 잔여 갭** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 3 connections
  - -> contains -> [[41-langgraph-state-vs-db]]
  - -> contains -> [[42-low]]
  - <- contains <- [[gap-analysis-proposal-agent-v1-v361-schema-re-analysis]]
- **1. 분석 개요** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 2 connections
  - -> contains -> [[11-4]]
  - <- contains <- [[gap-analysis-proposal-agent-v1-v361-schema-re-analysis]]
- **1.1 누락 테이블 4개 생성 완료** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 1 connections
  - <- contains <- [[1]]
- **2.1 proposals 테이블 컬럼 정합성 수정** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 1 connections
  - <- contains <- [[2-p0-2026-03-18]]
- **2.2 PGRST205 방어 코드 추가** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 1 connections
  - <- contains <- [[2-p0-2026-03-18]]
- **2.3 schema_v3.4.sql DDL 동기화** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 1 connections
  - <- contains <- [[2-p0-2026-03-18]]
- **3.1 백엔드 API (14/14 PASS)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 1 connections
  - <- contains <- [[3]]
- **3.2 프론트엔드 (8/8 PASS)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 1 connections
  - <- contains <- [[3]]
- **4.1 LangGraph State vs DB 컬럼 (의도적 분리)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 1 connections
  - <- contains <- [[4]]
- **4.2 LOW 잔여** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 1 connections
  - <- contains <- [[4]]
- **5. 매치율 계산** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-proposal-agent-v1-v361-schema-re-analysis]]
- **6. 이력** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\proposal-agent-v1.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-proposal-agent-v1-v361-schema-re-analysis]]

## Internal Relationships
- 1. 분석 개요 -> contains -> 1.1 누락 테이블 4개 생성 완료 [EXTRACTED]
- 2. P0 수정 완료 (2026-03-18) -> contains -> 2.1 proposals 테이블 컬럼 정합성 수정 [EXTRACTED]
- 2. P0 수정 완료 (2026-03-18) -> contains -> 2.2 PGRST205 방어 코드 추가 [EXTRACTED]
- 2. P0 수정 완료 (2026-03-18) -> contains -> 2.3 schema_v3.4.sql DDL 동기화 [EXTRACTED]
- 3. 테스트 결과 -> contains -> 3.1 백엔드 API (14/14 PASS) [EXTRACTED]
- 3. 테스트 결과 -> contains -> 3.2 프론트엔드 (8/8 PASS) [EXTRACTED]
- 4. 잔여 갭 -> contains -> 4.1 LangGraph State vs DB 컬럼 (의도적 분리) [EXTRACTED]
- 4. 잔여 갭 -> contains -> 4.2 LOW 잔여 [EXTRACTED]
- Gap Analysis: proposal-agent-v1 (v3.6.1 Schema Re-Analysis) -> contains -> 1. 분석 개요 [EXTRACTED]
- Gap Analysis: proposal-agent-v1 (v3.6.1 Schema Re-Analysis) -> contains -> 2. P0 수정 완료 (2026-03-18) [EXTRACTED]
- Gap Analysis: proposal-agent-v1 (v3.6.1 Schema Re-Analysis) -> contains -> 3. 테스트 결과 [EXTRACTED]
- Gap Analysis: proposal-agent-v1 (v3.6.1 Schema Re-Analysis) -> contains -> 4. 잔여 갭 [EXTRACTED]
- Gap Analysis: proposal-agent-v1 (v3.6.1 Schema Re-Analysis) -> contains -> 5. 매치율 계산 [EXTRACTED]
- Gap Analysis: proposal-agent-v1 (v3.6.1 Schema Re-Analysis) -> contains -> 6. 이력 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Gap Analysis: proposal-agent-v1 (v3.6.1 Schema Re-Analysis), 2. P0 수정 완료 (2026-03-18), 3. 테스트 결과를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-agent-v1.analysis.md이다.

### Key Facts
- > **Date**: 2026-03-18 > **Previous Match Rate**: 99% (feature logic) > **Current Match Rate**: 97% (feature) / 89% (overall adjusted)
- 2.1 proposals 테이블 컬럼 정합성 수정
- 3.1 백엔드 API (14/14 PASS)
- 4.1 LangGraph State vs DB 컬럼 (의도적 분리)
- 통합 테스트 중 발견된 DB 스키마-코드 괴리를 중심으로 재분석. 실제 Supabase DB 컬럼명과 코드의 컬럼 참조를 전수 비교.
