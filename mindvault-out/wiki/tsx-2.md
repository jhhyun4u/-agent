# tsx & 방법 2: 전체 마이그레이션
Cohesion: 0.53 | Nodes: 6

## Key Nodes
- **tsx** (C:\project\tenopa proposer\-agent-master\frontend\UI_IMPROVEMENT_COMPLETION.md) -- 3 connections
  - <- has_code_example <- [[1]]
  - <- has_code_example <- [[2]]
  - <- has_code_example <- [[typescript]]
- **방법 2: 전체 마이그레이션** (C:\project\tenopa proposer\-agent-master\frontend\UI_IMPROVEMENT_COMPLETION.md) -- 3 connections
  - -> has_code_example -> [[tsx]]
  - -> has_code_example -> [[bash]]
  - <- contains <- [[uiux]]
- **TypeScript 검사** (C:\project\tenopa proposer\-agent-master\frontend\UI_IMPROVEMENT_COMPLETION.md) -- 3 connections
  - -> has_code_example -> [[bash]]
  - -> has_code_example -> [[tsx]]
  - <- contains <- [[uiux]]
- **UI/UX 디자인 개선 완료 가이드** (C:\project\tenopa proposer\-agent-master\frontend\UI_IMPROVEMENT_COMPLETION.md) -- 3 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[typescript]]
- **bash** (C:\project\tenopa proposer\-agent-master\frontend\UI_IMPROVEMENT_COMPLETION.md) -- 2 connections
  - <- has_code_example <- [[2]]
  - <- has_code_example <- [[typescript]]
- **방법 1: 점진적 마이그레이션 (권장)** (C:\project\tenopa proposer\-agent-master\frontend\UI_IMPROVEMENT_COMPLETION.md) -- 2 connections
  - -> has_code_example -> [[tsx]]
  - <- contains <- [[uiux]]

## Internal Relationships
- 방법 1: 점진적 마이그레이션 (권장) -> has_code_example -> tsx [EXTRACTED]
- 방법 2: 전체 마이그레이션 -> has_code_example -> tsx [EXTRACTED]
- 방법 2: 전체 마이그레이션 -> has_code_example -> bash [EXTRACTED]
- TypeScript 검사 -> has_code_example -> bash [EXTRACTED]
- TypeScript 검사 -> has_code_example -> tsx [EXTRACTED]
- UI/UX 디자인 개선 완료 가이드 -> contains -> 방법 1: 점진적 마이그레이션 (권장) [EXTRACTED]
- UI/UX 디자인 개선 완료 가이드 -> contains -> 방법 2: 전체 마이그레이션 [EXTRACTED]
- UI/UX 디자인 개선 완료 가이드 -> contains -> TypeScript 검사 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 tsx, 방법 2: 전체 마이그레이션, TypeScript 검사를 중심으로 has_code_example 관계로 연결되어 있다. 주요 소스 파일은 UI_IMPROVEMENT_COMPLETION.md이다.

### Key Facts
- - ✅ `lib/typography.ts` — 타이포그래피 시스템 (TEXT_SIZES, TEXT_PRESETS) - ✅ `components/ui/Button.tsx` — 버튼 컴포넌트 (4가지 variant) - ✅ `components/ui/Card.tsx` — 카드 컴포넌트 체계 - ✅ `components/ui/FormField.tsx` — 폼 필드 컴포넌트 (TextInput, TextArea, Select)
- 모든 페이지를 한 번에 업데이트합니다 (시간이 오래 걸릴 수 있음).
- ```bash 타입 에러 확인 npm run typecheck ```
- 모든 UI/UX 개선 사항이 구현되었습니다. 이 가이드는 새로운 시스템을 프로젝트에 적용하는 방법을 설명합니다.
- ```bash 빌드 테스트 npm run build
