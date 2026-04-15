# 2. 대시보드 `/dashboard` & 2-1. 레이아웃
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **2. 대시보드 `/dashboard`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 5 connections
  - -> contains -> [[2-1]]
  - -> contains -> [[2-2-kpi]]
  - -> contains -> [[2-3]]
  - -> contains -> [[2-4]]
  - -> contains -> [[2-5]]
- **2-1. 레이아웃** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[2-dashboard]]
- **2-2. KPI 위젯** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[2-dashboard]]
- **2-3. 파이프라인 뷰** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[2-dashboard]]
- **2-4. 분석 차트** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[2-dashboard]]
- **2-5. 가이드 투어** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[2-dashboard]]

## Internal Relationships
- 2. 대시보드 `/dashboard` -> contains -> 2-1. 레이아웃 [EXTRACTED]
- 2. 대시보드 `/dashboard` -> contains -> 2-2. KPI 위젯 [EXTRACTED]
- 2. 대시보드 `/dashboard` -> contains -> 2-3. 파이프라인 뷰 [EXTRACTED]
- 2. 대시보드 `/dashboard` -> contains -> 2-4. 분석 차트 [EXTRACTED]
- 2. 대시보드 `/dashboard` -> contains -> 2-5. 가이드 투어 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 2. 대시보드 `/dashboard`, 2-1. 레이아웃, 2-2. KPI 위젯를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend-manual-test-checklist.md이다.

### Key Facts
- 2-1. 레이아웃 - [ ] AppSidebar 정상 표시 (좌측) - [ ] 사이드바 접기/펼치기 동작 - [ ] 사이드바 너비 드래그 조절 - [ ] 현재 메뉴 "대시보드" 활성 상태 표시 - [ ] 반응형: 모바일 너비에서 햄버거 메뉴
- 2-2. KPI 위젯 - [ ] 진행 중 프로젝트 수 카드 - [ ] 수주율 카드 - [ ] 마감 임박 프로젝트 카드 - [ ] 각 카드 숫자가 실제 데이터와 일치
- 2-3. 파이프라인 뷰 - [ ] 프로젝트 파이프라인 (단계별 현황) 표시 - [ ] 프로젝트 클릭 → 상세 페이지 이동
- 2-4. 분석 차트 - [ ] 실패 사유 파이차트 렌더링 - [ ] 월별 추이 라인차트 렌더링 - [ ] 발주기관별 수주율 바차트 렌더링
- 2-5. 가이드 투어 - [ ] 첫 방문 시 GuidedTour 팝업 (또는 수동 시작 버튼)
