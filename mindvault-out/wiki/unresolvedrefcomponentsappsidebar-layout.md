# __unresolved__::ref::___components_appsidebar_ & layout
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **__unresolved__::ref::___components_appsidebar_** () -- 1 connections
  - <- imports <- [[layout]]
- **layout** (C:\project\tenopa proposer\frontend\app\(app)\layout.tsx) -- 1 connections
  - -> imports -> [[unresolvedrefcomponentsappsidebar]]

## Internal Relationships
- layout -> imports -> __unresolved__::ref::___components_appsidebar_ [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 __unresolved__::ref::___components_appsidebar_, layout를 중심으로 imports 관계로 연결되어 있다. 주요 소스 파일은 layout.tsx이다.

### Key Facts
- export default function AppLayout({ children }: { children: React.ReactNode }) { return ( <div className="flex h-screen bg-[#0f0f0f] overflow-hidden"> <AppSidebar /> <div className="flex-1 flex flex-col overflow-hidden">{children}</div> </div> ); }
