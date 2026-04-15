# 그림자 체계 (Shadow System) & tsx
Cohesion: 0.50 | Nodes: 5

## Key Nodes
- **그림자 체계 (Shadow System)** (C:\project\tenopa proposer\-agent-master\frontend\SPACING_AND_SHADOWS.md) -- 3 connections
  - -> has_code_example -> [[tsx]]
  - -> has_code_example -> [[css]]
  - <- contains <- [[spacing-shadow]]
- **tsx** (C:\project\tenopa proposer\-agent-master\frontend\SPACING_AND_SHADOWS.md) -- 2 connections
  - <- has_code_example <- [[spacing-system]]
  - <- has_code_example <- [[shadow-system]]
- **간격(Spacing) 및 그림자(Shadow) 시스템** (C:\project\tenopa proposer\-agent-master\frontend\SPACING_AND_SHADOWS.md) -- 2 connections
  - -> contains -> [[spacing-system]]
  - -> contains -> [[shadow-system]]
- **간격 체계 (Spacing System)** (C:\project\tenopa proposer\-agent-master\frontend\SPACING_AND_SHADOWS.md) -- 2 connections
  - -> has_code_example -> [[tsx]]
  - <- contains <- [[spacing-shadow]]
- **css** (C:\project\tenopa proposer\-agent-master\frontend\SPACING_AND_SHADOWS.md) -- 1 connections
  - <- has_code_example <- [[shadow-system]]

## Internal Relationships
- 그림자 체계 (Shadow System) -> has_code_example -> tsx [EXTRACTED]
- 그림자 체계 (Shadow System) -> has_code_example -> css [EXTRACTED]
- 간격(Spacing) 및 그림자(Shadow) 시스템 -> contains -> 간격 체계 (Spacing System) [EXTRACTED]
- 간격(Spacing) 및 그림자(Shadow) 시스템 -> contains -> 그림자 체계 (Shadow System) [EXTRACTED]
- 간격 체계 (Spacing System) -> has_code_example -> tsx [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 그림자 체계 (Shadow System), tsx, 간격(Spacing) 및 그림자(Shadow) 시스템를 중심으로 has_code_example 관계로 연결되어 있다. 주요 소스 파일은 SPACING_AND_SHADOWS.md이다.

### Key Facts
- 시각적 계층을 표현하기 위한 그림자 스케일입니다.
- ```tsx // Padding (내부 간격) <div className="p-md">콘텐츠</div> <div className="p-lg">큰 영역</div> <div className="px-md py-lg">좌우 16px, 상하 24px</div>
- 간격 체계 (Spacing System)
- 8px 기반 일관된 간격 시스템을 사용합니다.
- | 변수  | 크기 | CSS        | Tailwind        | 사용 예               | | ----- | ---- | ---------- | --------------- | --------------------- | | `xs`  | 6px  | `0.375rem` | `gap-xs`        | 아이콘과 텍스트 사이  | | `sm`  | 8px  | `0.5rem`   | `gap-sm`        | 인라인 요소 간격      | | `md`  | 16px | `1rem`     |…
