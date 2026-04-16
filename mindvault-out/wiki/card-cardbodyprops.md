# Card & CardBodyProps
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **Card** (C:\project\tenopa proposer\frontend\components\ui\Card.tsx) -- 5 connections
  - -> contains -> [[cardprops]]
  - -> contains -> [[cardheaderprops]]
  - -> contains -> [[cardbodyprops]]
  - -> contains -> [[cardfooterprops]]
  - -> imports -> [[unresolvedrefreact]]
- **CardBodyProps** (C:\project\tenopa proposer\frontend\components\ui\Card.tsx) -- 1 connections
  - <- contains <- [[card]]
- **CardFooterProps** (C:\project\tenopa proposer\frontend\components\ui\Card.tsx) -- 1 connections
  - <- contains <- [[card]]
- **CardHeaderProps** (C:\project\tenopa proposer\frontend\components\ui\Card.tsx) -- 1 connections
  - <- contains <- [[card]]
- **CardProps** (C:\project\tenopa proposer\frontend\components\ui\Card.tsx) -- 1 connections
  - <- contains <- [[card]]

## Internal Relationships
- Card -> contains -> CardProps [EXTRACTED]
- Card -> contains -> CardHeaderProps [EXTRACTED]
- Card -> contains -> CardBodyProps [EXTRACTED]
- Card -> contains -> CardFooterProps [EXTRACTED]

## Cross-Community Connections
- Card -> imports -> __unresolved__::ref::_react_ (-> [[unresolvedrefreact-unresolvedreflibapi]])

## Context
이 커뮤니티는 Card, CardBodyProps, CardFooterProps를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 Card.tsx이다.

### Key Facts
- interface CardProps extends React.HTMLAttributes<HTMLDivElement> { children: React.ReactNode; }
- interface CardBodyProps extends React.HTMLAttributes<HTMLDivElement> { children: React.ReactNode; }
- interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> { children: React.ReactNode; }
- interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> { title?: string; subtitle?: string; action?: React.ReactNode; children?: React.ReactNode; }
- interface CardProps extends React.HTMLAttributes<HTMLDivElement> { children: React.ReactNode; }
