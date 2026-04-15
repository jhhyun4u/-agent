# Plan: proposal-platform-v2.1 & G-01: proposals/new 섹션 선택 스텝
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **Plan: proposal-platform-v2.1** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2.1\proposal-platform-v2.1.plan.md) -- 3 connections
  - -> contains -> [[g-01-proposalsnew]]
  - -> contains -> [[g-03-ui]]
  - -> contains -> [[g-09-assetextractorpy-ai]]
- **G-01: proposals/new 섹션 선택 스텝** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2.1\proposal-platform-v2.1.plan.md) -- 1 connections
  - <- contains <- [[plan-proposal-platform-v21]]
- **G-03: 버전 비교 UI** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2.1\proposal-platform-v2.1.plan.md) -- 1 connections
  - <- contains <- [[plan-proposal-platform-v21]]
- **G-09: asset_extractor.py (AI 섹션 자동 추출)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2.1\proposal-platform-v2.1.plan.md) -- 1 connections
  - <- contains <- [[plan-proposal-platform-v21]]

## Internal Relationships
- Plan: proposal-platform-v2.1 -> contains -> G-01: proposals/new 섹션 선택 스텝 [EXTRACTED]
- Plan: proposal-platform-v2.1 -> contains -> G-03: 버전 비교 UI [EXTRACTED]
- Plan: proposal-platform-v2.1 -> contains -> G-09: asset_extractor.py (AI 섹션 자동 추출) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: proposal-platform-v2.1, G-01: proposals/new 섹션 선택 스텝, G-03: 버전 비교 UI를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-platform-v2.1.plan.md이다.

### Key Facts
- 메타 정보 | 항목 | 내용 | |------|------| | Feature | proposal-platform-v2.1 | | 작성일 | 2026-03-08 | | 기반 | proposal-platform-v2 (archived, 91% match) | | 목표 | v2 잔여 P2 이슈 3건 해결 → Match Rate 97%+ |
- **현재 상태:** proposals/new 페이지에 파일 업로드 + 서식 선택 + 기본 정보 입력만 있음 **목표:** 섹션 라이브러리에서 관련 섹션을 선택하여 AI 컨텍스트에 포함
- **현재 상태:** 버전 드롭다운으로 전환만 가능, 나란히 비교 불가 **목표:** v1 vs v2 등 두 버전 결과물을 나란히 표시
- **현재 상태:** 회사 자료 업로드 시 Storage에 저장만 됨, AI 분석 없음 **목표:** 업로드된 PDF/DOCX에서 Claude API를 통해 섹션 자동 추출
