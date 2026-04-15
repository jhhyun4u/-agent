# PDCA 사이클 요약 & 요구사항 5건
Cohesion: 0.40 | Nodes: 6

## Key Nodes
- **PDCA 사이클 요약** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\stream3-docs-readiness.report.md) -- 4 connections
  - -> contains -> [[plan]]
  - -> contains -> [[do]]
  - -> contains -> [[check]]
  - <- contains <- [[stream-3]]
- **요구사항 5건** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\stream3-docs-readiness.report.md) -- 2 connections
  - <- contains <- [[plan]]
  - <- contains <- [[do]]
- **Do 단계 (구현)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\stream3-docs-readiness.report.md) -- 2 connections
  - -> contains -> [[5]]
  - <- contains <- [[pdca]]
- **Plan 단계** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\stream3-docs-readiness.report.md) -- 2 connections
  - -> contains -> [[5]]
  - <- contains <- [[pdca]]
- **Check 단계 (갭 분석)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\stream3-docs-readiness.report.md) -- 1 connections
  - <- contains <- [[pdca]]
- **Stream 3 제출서류 준비 판단 로직 개선 완료 보고서** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\stream3-docs-readiness.report.md) -- 1 connections
  - -> contains -> [[pdca]]

## Internal Relationships
- Do 단계 (구현) -> contains -> 요구사항 5건 [EXTRACTED]
- PDCA 사이클 요약 -> contains -> Plan 단계 [EXTRACTED]
- PDCA 사이클 요약 -> contains -> Do 단계 (구현) [EXTRACTED]
- PDCA 사이클 요약 -> contains -> Check 단계 (갭 분석) [EXTRACTED]
- Plan 단계 -> contains -> 요구사항 5건 [EXTRACTED]
- Stream 3 제출서류 준비 판단 로직 개선 완료 보고서 -> contains -> PDCA 사이클 요약 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 PDCA 사이클 요약, 요구사항 5건, Do 단계 (구현)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 stream3-docs-readiness.report.md이다.

### Key Facts
- Plan 단계 사용자가 직접 5개 개선 요구사항과 구현 계획을 제시. 별도 Plan 문서 없이 대화 내 인라인 계획으로 진행.
- 스코프 - **In**: 진행률 자동 계산, 원본 확인, 사본 번들, 산출물 연결, 프론트 완료 UX - **Out**: DB 마이그레이션 (기존 스키마 충족), 새 테이블
- > **Summary**: 제출서류(Stream 3)의 사본/원본 구분, 자동 진행률, 산출물 자동 연결, PDF 묶음 다운로드 등 5개 개선 구현 완료 > > **Author**: PDCA Report Generator > **Created**: 2026-03-21 > **Last Modified**: 2026-03-21 > **Status**: Approved > **Match Rate**: 99%
