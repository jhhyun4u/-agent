# 사이드바(AppSidebar) 메뉴 구조 & 1단계 메뉴
Cohesion: 0.13 | Nodes: 16

## Key Nodes
- **사이드바(AppSidebar) 메뉴 구조** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 6 connections
  - -> contains -> [[navrest]]
  - -> contains -> [[knowledge-base]]
  - -> contains -> [[admin]]
  - -> contains -> [[ui]]
  - -> contains -> [[localstorage]]
  - -> contains -> [[footer]]
- **1단계 메뉴** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 4 connections
  - -> contains -> [[dashboard]]
  - -> contains -> [[bid-monitoring]]
  - -> contains -> [[proposals]]
  - <- contains <- [[navrest]]
- **🔧 하단 섹션 (Footer)** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 4 connections
  - -> has_code_example -> [[typescript]]
  - -> contains -> [[desktop-lg]]
  - -> contains -> [[tablet-mobile-lg]]
  - <- contains <- [[appsidebar]]
- **typescript** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 2 connections
  - <- has_code_example <- [[footer]]
  - <- has_code_example <- [[tablet-mobile-lg]]
- **👨‍💼 Admin (관리자 전용) - 그룹** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 2 connections
  - -> contains -> [[recent-proposals]]
  - <- contains <- [[appsidebar]]
- **🎯 메뉴 항목 (NAV_REST)** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 2 connections
  - -> contains -> [[1]]
  - <- contains <- [[appsidebar]]
- **Tablet / Mobile (lg 미만)** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[footer]]
- **🎨 UI 상태** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 2 connections
  - -> contains -> [[active]]
  - <- contains <- [[appsidebar]]
- **활성 상태 (Active)** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 1 connections
  - <- contains <- [[ui]]
- **공고 모니터링 (Bid Monitoring)** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 1 connections
  - <- contains <- [[1]]
- **대시보드 (Dashboard)** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 1 connections
  - <- contains <- [[1]]
- **Desktop (lg 이상)** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 1 connections
  - <- contains <- [[footer]]
- **📚 지식 베이스 (Knowledge Base) - 그룹** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 1 connections
  - <- contains <- [[appsidebar]]
- **💾 상태 관리 (localStorage)** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 1 connections
  - <- contains <- [[appsidebar]]
- **제안 프로젝트 (Proposals)** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 1 connections
  - <- contains <- [[1]]
- **최근 작업 (Recent Proposals)** (C:\project\tenopa proposer\-agent-master\frontend\SIDEBAR_MENU_STRUCTURE.md) -- 1 connections
  - <- contains <- [[admin]]

## Internal Relationships
- 1단계 메뉴 -> contains -> 대시보드 (Dashboard) [EXTRACTED]
- 1단계 메뉴 -> contains -> 공고 모니터링 (Bid Monitoring) [EXTRACTED]
- 1단계 메뉴 -> contains -> 제안 프로젝트 (Proposals) [EXTRACTED]
- 👨‍💼 Admin (관리자 전용) - 그룹 -> contains -> 최근 작업 (Recent Proposals) [EXTRACTED]
- 사이드바(AppSidebar) 메뉴 구조 -> contains -> 🎯 메뉴 항목 (NAV_REST) [EXTRACTED]
- 사이드바(AppSidebar) 메뉴 구조 -> contains -> 📚 지식 베이스 (Knowledge Base) - 그룹 [EXTRACTED]
- 사이드바(AppSidebar) 메뉴 구조 -> contains -> 👨‍💼 Admin (관리자 전용) - 그룹 [EXTRACTED]
- 사이드바(AppSidebar) 메뉴 구조 -> contains -> 🎨 UI 상태 [EXTRACTED]
- 사이드바(AppSidebar) 메뉴 구조 -> contains -> 💾 상태 관리 (localStorage) [EXTRACTED]
- 사이드바(AppSidebar) 메뉴 구조 -> contains -> 🔧 하단 섹션 (Footer) [EXTRACTED]
- 🔧 하단 섹션 (Footer) -> has_code_example -> typescript [EXTRACTED]
- 🔧 하단 섹션 (Footer) -> contains -> Desktop (lg 이상) [EXTRACTED]
- 🔧 하단 섹션 (Footer) -> contains -> Tablet / Mobile (lg 미만) [EXTRACTED]
- 🎯 메뉴 항목 (NAV_REST) -> contains -> 1단계 메뉴 [EXTRACTED]
- Tablet / Mobile (lg 미만) -> has_code_example -> typescript [EXTRACTED]
- 🎨 UI 상태 -> contains -> 활성 상태 (Active) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 사이드바(AppSidebar) 메뉴 구조, 1단계 메뉴, 🔧 하단 섹션 (Footer)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 SIDEBAR_MENU_STRUCTURE.md이다.

### Key Facts
- ``` 하단 섹션 ├── 테마 토글 (라이트/다크 모드) │ ├── 사용자 이메일 │   ├── 링크: /settings │   ├── 텍스트: development일 때 "dev@tenopa.co.kr" │   └── 호버 효과 있음 │ ├── 알림 벨 (NotificationBell 컴포넌트) │   └── 미읽음 알림 수 표시 │ └── 로그아웃 버튼 ├── 아이콘: 로그아웃 화살표 └── 클릭: Supabase 로그아웃 → /login 리다이렉트 ```
- ```typescript // 경로 변경 감지 pathname: "/kb/clients" → 지식베이스 자동 펼침 pathname: "/admin/prompts" → Admin 그룹 자동 펼침
- ``` ⚙️ Admin (Expandable Group - 관리자/매니저만 표시) ├── basePath: /admin ├── icon: settings ├── 권한: admin, manager ├── 상태 저장: sidebar-admin-expanded (localStorage) │ └── 하위 메뉴 (3개): ├── 👥 이용자 관리 │   └── href: /admin │   └── icon: users │   └── 설명: 사용자, 조직, 팀 관리 │ ├── 💬 프롬프트 관리 │   └── href:…
- - 햄버거 메뉴로 슬라이드 오버레이 형식 - 너비: 고정 256px - 드래그 불가능 - 페이지 이동 시 자동 닫기 - 배경 클릭 또는 Escape로 닫기 가능
- - **메인 메뉴**: 현재 경로와 일치하면 배경색 강조 - 배경: `bg-[#1c1c1c]` - 텍스트: `text-[#ededed]`
