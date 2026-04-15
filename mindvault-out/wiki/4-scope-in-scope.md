# 4. 범위 (Scope) & In-Scope
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **4. 범위 (Scope)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bid-monitoring-pipeline.plan.md) -- 2 connections
  - -> contains -> [[in-scope]]
  - -> contains -> [[out-of-scope]]
- **In-Scope** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bid-monitoring-pipeline.plan.md) -- 1 connections
  - <- contains <- [[4-scope]]
- **Out-of-Scope** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bid-monitoring-pipeline.plan.md) -- 1 connections
  - <- contains <- [[4-scope]]

## Internal Relationships
- 4. 범위 (Scope) -> contains -> In-Scope [EXTRACTED]
- 4. 범위 (Scope) -> contains -> Out-of-Scope [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 4. 범위 (Scope), In-Scope, Out-of-Scope를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 bid-monitoring-pipeline.plan.md이다.

### Key Facts
- | # | 기능 | 설명 | 우선순위 | |---|------|------|:--------:| | P-1 | scored 결과 DB 자동 저장 | 상위 50건 → bid_announcements upsert | H | | P-2 | 첨부파일 자동 다운로드 | 과업지시서/제안요청서 우선 → Storage 저장 | H | | P-3 | content_text 자동 추출 | PDF/HWP/HWPX → 텍스트 파싱 → DB 저장 | H | | P-4 | AI 분석 백그라운드 실행 | 전처리 + 적합성 → 파일 캐시 저장 | H | |…
- | 항목 | 사유 | |------|------| | 공고 자동 분류/태깅 | 별도 피처로 분리 | | 첨부파일 전체 보관 (영구) | Storage 비용 관리 별도 검토 | | scored 알고리즘 개선 | 별도 피처 |
