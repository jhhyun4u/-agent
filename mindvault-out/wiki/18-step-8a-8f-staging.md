# 배포된 파일 (18개) & STEP 8A-8F Staging 배포 요약
Cohesion: 0.29 | Nodes: 7

## Key Nodes
- **배포된 파일 (18개)** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT_SUMMARY.md) -- 4 connections
  - -> contains -> [[6]]
  - -> contains -> [[1]]
  - -> contains -> [[4]]
  - <- contains <- [[step-8a-8f-staging]]
- **STEP 8A-8F Staging 배포 요약** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT_SUMMARY.md) -- 3 connections
  - -> contains -> [[git]]
  - -> contains -> [[18]]
  - -> contains -> [[2026-03-30-1900-utc]]
- **🔷 서비스 (1개)** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT_SUMMARY.md) -- 1 connections
  - <- contains <- [[18]]
- **🔧 배포 후 검증 (2026-03-30 19:00 UTC)** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT_SUMMARY.md) -- 1 connections
  - <- contains <- [[step-8a-8f-staging]]
- **🔷 보고서 (4개)** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT_SUMMARY.md) -- 1 connections
  - <- contains <- [[18]]
- **🔷 노드 구현 (6개)** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT_SUMMARY.md) -- 1 connections
  - <- contains <- [[18]]
- **Git 커밋 정보** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT_SUMMARY.md) -- 1 connections
  - <- contains <- [[step-8a-8f-staging]]

## Internal Relationships
- 배포된 파일 (18개) -> contains -> 🔷 노드 구현 (6개) [EXTRACTED]
- 배포된 파일 (18개) -> contains -> 🔷 서비스 (1개) [EXTRACTED]
- 배포된 파일 (18개) -> contains -> 🔷 보고서 (4개) [EXTRACTED]
- STEP 8A-8F Staging 배포 요약 -> contains -> Git 커밋 정보 [EXTRACTED]
- STEP 8A-8F Staging 배포 요약 -> contains -> 배포된 파일 (18개) [EXTRACTED]
- STEP 8A-8F Staging 배포 요약 -> contains -> 🔧 배포 후 검증 (2026-03-30 19:00 UTC) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 배포된 파일 (18개), STEP 8A-8F Staging 배포 요약, 🔷 서비스 (1개)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 STAGING_DEPLOYMENT_SUMMARY.md이다.

### Key Facts
- 🔷 노드 구현 (6개) - ✅ `app/graph/nodes/step8a_customer_analysis.py` (105 lines) - ✅ `app/graph/nodes/step8b_section_validator.py` (150 lines) - ✅ `app/graph/nodes/step8c_consolidation.py` (180 lines) - ✅ `app/graph/nodes/step8d_mock_evaluation.py` (150 lines) - ✅…
- **배포 시간:** 2026-03-30 14:45 UTC **배포 상태:** ✅ **COMPLETE** **Staging 환경:** Ready for Testing
- 🔷 헬퍼 (1개) - ✅ `app/graph/nodes/_constants.py` - 전역 상수 및 유틸리티
- 🔷 프롬프트 (6개, 한국어 번역) - ✅ `app/prompts/step8a.py` - 고객 분석 - ✅ `app/prompts/step8b.py` - 검증 - ✅ `app/prompts/step8c.py` - 통합 - ✅ `app/prompts/step8d.py` - 모의 평가 - ✅ `app/prompts/step8e.py` - 피드백 처리 - ✅ `app/prompts/step8f.py` - 재작성
