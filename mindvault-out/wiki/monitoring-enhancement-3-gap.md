# Monitoring Enhancement — 설계-구현 갭 분석 보고서 & 3. 미구현 사항 (GAP)
Cohesion: 0.25 | Nodes: 8

## Key Nodes
- **Monitoring Enhancement — 설계-구현 갭 분석 보고서** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.analysis.md) -- 6 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3-gap]]
  - -> contains -> [[4]]
  - -> contains -> [[5-plan-8]]
  - -> contains -> [[6]]
- **3. 미구현 사항 (GAP)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.analysis.md) -- 2 connections
  - -> contains -> [[gap-1-nodeerrors-state-mon-02-resolved-v11]]
  - <- contains <- [[monitoring-enhancement]]
- **1. 전체 점수** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[monitoring-enhancement]]
- **2. 요구사항별 검증 결과** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[monitoring-enhancement]]
- **4. 추가/변경 사항** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[monitoring-enhancement]]
- **5. Plan §8 검증 기준 달성** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[monitoring-enhancement]]
- **6. 권장 조치** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[monitoring-enhancement]]
- **GAP-1: node_errors state 기록 (MON-02) — RESOLVED (v1.1)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[3-gap]]

## Internal Relationships
- 3. 미구현 사항 (GAP) -> contains -> GAP-1: node_errors state 기록 (MON-02) — RESOLVED (v1.1) [EXTRACTED]
- Monitoring Enhancement — 설계-구현 갭 분석 보고서 -> contains -> 1. 전체 점수 [EXTRACTED]
- Monitoring Enhancement — 설계-구현 갭 분석 보고서 -> contains -> 2. 요구사항별 검증 결과 [EXTRACTED]
- Monitoring Enhancement — 설계-구현 갭 분석 보고서 -> contains -> 3. 미구현 사항 (GAP) [EXTRACTED]
- Monitoring Enhancement — 설계-구현 갭 분석 보고서 -> contains -> 4. 추가/변경 사항 [EXTRACTED]
- Monitoring Enhancement — 설계-구현 갭 분석 보고서 -> contains -> 5. Plan §8 검증 기준 달성 [EXTRACTED]
- Monitoring Enhancement — 설계-구현 갭 분석 보고서 -> contains -> 6. 권장 조치 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Monitoring Enhancement — 설계-구현 갭 분석 보고서, 3. 미구현 사항 (GAP), 1. 전체 점수를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 monitoring-enhancement.analysis.md이다.

### Key Facts
- > **분석 유형**: Gap Analysis (설계 vs 구현) > > **프로젝트**: 용역제안 Coworker > **분석일**: 2026-03-26 > **설계 문서**: `docs/02-design/features/monitoring-enhancement.design.md` v1.0 > **요구사항**: `docs/01-plan/features/monitoring-enhancement.plan.md` v1.0
- GAP-1: node_errors state 기록 (MON-02) — RESOLVED (v1.1)
- | 카테고리 | v1.0 점수 | v1.1 점수 | 상태 | |----------|:--------:|:--------:|:----:| | Phase A (HIGH) | 88% | 100% | PASS | | Phase B (MEDIUM) | 100% | 100% | PASS | | Phase C (LOW) | 100% | 100% | PASS | | **종합** | **92%** | **100%** | **PASS** |
- | MON | 항목 | 배점 | 득점 | 판정 | |-----|------|:----:|:----:|:----:| | MON-01 | Silent except 26건 제거 | 15 | 15 | PASS | | MON-02 | node_errors state 기록 | 10 | 10 | PASS (v1.1) | | MON-03 | track_tokens 에러 경로 + DB 기록 | 15 | 15 | PASS | | MON-04 | fail_task → persist_log 연동 | 10 | 10 | PASS | | MON-05 |…
- | # | 유형 | 항목 | 영향 | |---|------|------|------| | ADD-1 | 추가 | token_tracking의 notify_err 예외 처리 | 긍정 (안정성) | | CHG-1 | 변경 | 마이그레이션 번호 013/014 → 015 | 없음 | | CHG-2 | 변경 | 프론트 경로 `src/lib/` → `lib/` | 없음 | | CHG-3 | 추가 | ErrorReporterInit 별도 컴포넌트 분리 | 긍정 (SSR 분리) |
