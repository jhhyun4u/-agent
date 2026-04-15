# tsx & UI 컴포넌트 사용 가이드
Cohesion: 0.26 | Nodes: 12

## Key Nodes
- **tsx** (C:\project\tenopa proposer\-agent-master\frontend\COMPONENT_USAGE.md) -- 6 connections
  - <- has_code_example <- [[button]]
  - <- has_code_example <- [[card]]
  - <- has_code_example <- [[formfield]]
  - <- has_code_example <- [[typography]]
  - <- has_code_example <- [[status-badge]]
  - <- has_code_example <- [[react]]
- **UI 컴포넌트 사용 가이드** (C:\project\tenopa proposer\-agent-master\frontend\COMPONENT_USAGE.md) -- 5 connections
  - -> contains -> [[button]]
  - -> contains -> [[card]]
  - -> contains -> [[formfield]]
  - -> contains -> [[typography]]
  - -> contains -> [[status-badge]]
- **상태 배지 (Status Badge)** (C:\project\tenopa proposer\-agent-master\frontend\COMPONENT_USAGE.md) -- 4 connections
  - -> has_code_example -> [[tsx]]
  - -> has_code_example -> [[css]]
  - -> contains -> [[react]]
  - <- contains <- [[ui]]
- **버튼 (Button)** (C:\project\tenopa proposer\-agent-master\frontend\COMPONENT_USAGE.md) -- 3 connections
  - -> has_code_example -> [[tsx]]
  - -> contains -> [[button-props]]
  - <- contains <- [[ui]]
- **카드 (Card)** (C:\project\tenopa proposer\-agent-master\frontend\COMPONENT_USAGE.md) -- 3 connections
  - -> has_code_example -> [[tsx]]
  - -> contains -> [[card-props]]
  - <- contains <- [[ui]]
- **폼 필드 (FormField)** (C:\project\tenopa proposer\-agent-master\frontend\COMPONENT_USAGE.md) -- 3 connections
  - -> has_code_example -> [[tsx]]
  - -> contains -> [[formfield-props]]
  - <- contains <- [[ui]]
- **버튼 클래스 (React 컴포넌트 권장)** (C:\project\tenopa proposer\-agent-master\frontend\COMPONENT_USAGE.md) -- 3 connections
  - -> has_code_example -> [[css]]
  - -> has_code_example -> [[tsx]]
  - <- contains <- [[status-badge]]
- **css** (C:\project\tenopa proposer\-agent-master\frontend\COMPONENT_USAGE.md) -- 2 connections
  - <- has_code_example <- [[status-badge]]
  - <- has_code_example <- [[react]]
- **타이포그래피 (Typography)** (C:\project\tenopa proposer\-agent-master\frontend\COMPONENT_USAGE.md) -- 2 connections
  - -> has_code_example -> [[tsx]]
  - <- contains <- [[ui]]
- **Button Props** (C:\project\tenopa proposer\-agent-master\frontend\COMPONENT_USAGE.md) -- 1 connections
  - <- contains <- [[button]]
- **Card Props** (C:\project\tenopa proposer\-agent-master\frontend\COMPONENT_USAGE.md) -- 1 connections
  - <- contains <- [[card]]
- **FormField Props** (C:\project\tenopa proposer\-agent-master\frontend\COMPONENT_USAGE.md) -- 1 connections
  - <- contains <- [[formfield]]

## Internal Relationships
- 버튼 (Button) -> has_code_example -> tsx [EXTRACTED]
- 버튼 (Button) -> contains -> Button Props [EXTRACTED]
- 카드 (Card) -> has_code_example -> tsx [EXTRACTED]
- 카드 (Card) -> contains -> Card Props [EXTRACTED]
- 폼 필드 (FormField) -> has_code_example -> tsx [EXTRACTED]
- 폼 필드 (FormField) -> contains -> FormField Props [EXTRACTED]
- 버튼 클래스 (React 컴포넌트 권장) -> has_code_example -> css [EXTRACTED]
- 버튼 클래스 (React 컴포넌트 권장) -> has_code_example -> tsx [EXTRACTED]
- 상태 배지 (Status Badge) -> has_code_example -> tsx [EXTRACTED]
- 상태 배지 (Status Badge) -> has_code_example -> css [EXTRACTED]
- 상태 배지 (Status Badge) -> contains -> 버튼 클래스 (React 컴포넌트 권장) [EXTRACTED]
- 타이포그래피 (Typography) -> has_code_example -> tsx [EXTRACTED]
- UI 컴포넌트 사용 가이드 -> contains -> 버튼 (Button) [EXTRACTED]
- UI 컴포넌트 사용 가이드 -> contains -> 카드 (Card) [EXTRACTED]
- UI 컴포넌트 사용 가이드 -> contains -> 폼 필드 (FormField) [EXTRACTED]
- UI 컴포넌트 사용 가이드 -> contains -> 타이포그래피 (Typography) [EXTRACTED]
- UI 컴포넌트 사용 가이드 -> contains -> 상태 배지 (Status Badge) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 tsx, UI 컴포넌트 사용 가이드, 상태 배지 (Status Badge)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 COMPONENT_USAGE.md이다.

### Key Facts
- ```tsx import { Button } from "@/components/ui/Button";
- 이 가이드는 새롭게 표준화된 UI 컴포넌트 사용법을 설명합니다.
- ```tsx export default function Example() { return ( <div className="space-y-2"> <p> <span className="status-success">완료</span> </p> <p> <span className="status-warning">진행 중</span> </p> <p> <span className="status-error">오류</span> </p> <p> <span className="status-info">정보</span> </p> </div> ); } ```
- ```tsx import { Button } from "@/components/ui/Button";
- ```tsx import { Card, CardHeader, CardBody, CardFooter } from "@/components/ui/Card"; import { Button } from "@/components/ui/Button";
