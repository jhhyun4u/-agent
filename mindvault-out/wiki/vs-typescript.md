# 사용자 요청 vs 현재 상태 & typescript
Cohesion: 0.21 | Nodes: 14

## Key Nodes
- **사용자 요청 vs 현재 상태** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 11 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-settings]]
  - -> contains -> [[1-dashboard]]
  - -> contains -> [[2-recent-proposals]]
  - -> contains -> [[3-navrest]]
  - -> contains -> [[4-admingroup]]
  - -> contains -> [[5]]
  - -> contains -> [[expand]]
  - -> contains -> [[priority-1]]
  - -> contains -> [[priority-2-settings]]
  - <- contains <- [[appsidebar]]
- **typescript** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 7 connections
  - <- has_code_example <- [[1-dashboard]]
  - <- has_code_example <- [[2-recent-proposals]]
  - <- has_code_example <- [[3-navrest]]
  - <- has_code_example <- [[4-admingroup]]
  - <- has_code_example <- [[5]]
  - <- has_code_example <- [[expand]]
  - <- has_code_example <- [[priority-2-settings]]
- **1️⃣ DASHBOARD (항상 표시)** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[vs]]
- **2️⃣ RECENT PROPOSALS (동적 표시)** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[vs]]
- **3️⃣ NAV_REST (공고~지식베이스)** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[vs]]
- **4️⃣ ADMIN_GROUP (관리자만)** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[vs]]
- **5️⃣ 하단 섹션 (항상 표시)** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[vs]]
- **자식 항목 (expand 내)** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[vs]]
- **👉 Priority 1: 메뉴 순서 변경** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 2 connections
  - -> has_code_example -> [[javascript]]
  - <- contains <- [[vs]]
- **👉 Priority 2: Settings 메뉴 추가** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[vs]]
- **javascript** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 1 connections
  - <- has_code_example <- [[priority-1]]
- **❌ 문제점 1: 메뉴 순서** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 1 connections
  - <- contains <- [[vs]]
- **❌ 문제점 2: Settings 메뉴** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 1 connections
  - <- contains <- [[vs]]
- **AppSidebar 메뉴 구조 및 설계** (C:\project\tenopa proposer\frontend\SIDEBAR_STRUCTURE.md) -- 1 connections
  - -> contains -> [[vs]]

## Internal Relationships
- 1️⃣ DASHBOARD (항상 표시) -> has_code_example -> typescript [EXTRACTED]
- 2️⃣ RECENT PROPOSALS (동적 표시) -> has_code_example -> typescript [EXTRACTED]
- 3️⃣ NAV_REST (공고~지식베이스) -> has_code_example -> typescript [EXTRACTED]
- 4️⃣ ADMIN_GROUP (관리자만) -> has_code_example -> typescript [EXTRACTED]
- 5️⃣ 하단 섹션 (항상 표시) -> has_code_example -> typescript [EXTRACTED]
- AppSidebar 메뉴 구조 및 설계 -> contains -> 사용자 요청 vs 현재 상태 [EXTRACTED]
- 자식 항목 (expand 내) -> has_code_example -> typescript [EXTRACTED]
- 👉 Priority 1: 메뉴 순서 변경 -> has_code_example -> javascript [EXTRACTED]
- 👉 Priority 2: Settings 메뉴 추가 -> has_code_example -> typescript [EXTRACTED]
- 사용자 요청 vs 현재 상태 -> contains -> ❌ 문제점 1: 메뉴 순서 [EXTRACTED]
- 사용자 요청 vs 현재 상태 -> contains -> ❌ 문제점 2: Settings 메뉴 [EXTRACTED]
- 사용자 요청 vs 현재 상태 -> contains -> 1️⃣ DASHBOARD (항상 표시) [EXTRACTED]
- 사용자 요청 vs 현재 상태 -> contains -> 2️⃣ RECENT PROPOSALS (동적 표시) [EXTRACTED]
- 사용자 요청 vs 현재 상태 -> contains -> 3️⃣ NAV_REST (공고~지식베이스) [EXTRACTED]
- 사용자 요청 vs 현재 상태 -> contains -> 4️⃣ ADMIN_GROUP (관리자만) [EXTRACTED]
- 사용자 요청 vs 현재 상태 -> contains -> 5️⃣ 하단 섹션 (항상 표시) [EXTRACTED]
- 사용자 요청 vs 현재 상태 -> contains -> 자식 항목 (expand 내) [EXTRACTED]
- 사용자 요청 vs 현재 상태 -> contains -> 👉 Priority 1: 메뉴 순서 변경 [EXTRACTED]
- 사용자 요청 vs 현재 상태 -> contains -> 👉 Priority 2: Settings 메뉴 추가 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 사용자 요청 vs 현재 상태, typescript, 1️⃣ DASHBOARD (항상 표시)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 SIDEBAR_STRUCTURE.md이다.

### Key Facts
- ```typescript const DASHBOARD = { href: "/dashboard", label: "대시보드", icon: "dashboard", }; ```
- ```typescript const DASHBOARD = { href: "/dashboard", label: "대시보드", icon: "dashboard", }; ```
- ```typescript if (recentProposals.length > 0) { // "최근 작업" 섹션 표시 // 렌더: 라인 360-383 } ```
- ```typescript const NAV_REST = [ { href: "/monitoring", label: "공고 모니터링", ... }, { href: "/proposals", label: "제안 프로젝트", ... }, { label: "지식 베이스", basePath: "/kb", children: [ { href: "/kb/search", label: "통합 검색", ... }, { href: "/kb/content", label: "콘텐츠", ... }, { href: "/kb/clients", label:…
- ```typescript if (userRole === "admin" || userRole === "manager") { const ADMIN_GROUP = { label: "Admin", basePath: "/admin", children: [ { href: "/admin", label: "이용자 관리", ... }, { href: "/admin/prompts", label: "프롬프트 관리", ... }, { href: "/admin/prompts/experiments", label: "A/B 실험", ... }, ] }; }…
