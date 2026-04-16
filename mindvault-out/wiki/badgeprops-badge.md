# BadgeProps & Badge
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **BadgeProps** (C:\project\tenopa proposer\frontend\components\ui\Badge.tsx) -- 1 connections
  - <- contains <- [[badge]]
- **Badge** (C:\project\tenopa proposer\frontend\components\ui\Badge.tsx) -- 1 connections
  - -> contains -> [[badgeprops]]

## Internal Relationships
- Badge -> contains -> BadgeProps [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 BadgeProps, Badge를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 Badge.tsx이다.

### Key Facts
- interface BadgeProps { children: React.ReactNode; variant?: "success" | "warning" | "error" | "info" | "neutral"; size?: "xs" | "sm"; }
- /** * Badge — 공통 상태 배지 컴포넌트 */
